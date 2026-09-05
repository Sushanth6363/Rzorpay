"""Razorpay Payment Link lifecycle, bound to a case (ADR-0023).

RESPONSIBILITIES
    1. Create a Payment Link for a case, IDEMPOTENTLY - a live unpaid link for the same
       case and amount is reused rather than duplicated, so a retried send, a follow-up,
       or a provider timeout cannot litter a customer's inbox with different links for the
       same debt.
    2. PERSIST the link against the case. This is the join that was missing: without it a
       `payment_link.paid` webhook carrying `plink_...` cannot reach the case opened from
       `pay_...`, and a customer who has paid keeps receiving reminders.
    3. Apply a verified payment to the case, and ONLY a verified one.

WHAT COUNTS AS PAID
    A provider webhook that passed HMAC verification. Not a click, not a redirect, not a
    form submission, not the customer saying so. `mark_paid_from_provider_event` is
    reachable only from the verified webhook path for exactly this reason.

TEST MODE
    Razorpay Test Mode is the demo environment. A real test key (`rzp_test_...`, as opposed
    to the placeholder `rzp_test_mock`) hits the real API and produces a real link and a
    real webhook - with no real money. The service records which mode produced each link so
    a reviewer can tell test data from live data in the database itself.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Optional, Tuple

from app.cases.models import (
    Case,
    CaseEvent,
    CaseEventKind,
    CaseStatus,
    PaymentLink,
    PaymentLinkStatus,
    now_iso,
)
from app.cases.repository import CaseRepository

logger = logging.getLogger("recovery.payments")

MOCK_KEY_PREFIX = "rzp_test_mock"
LIVE_KEY_PREFIX = "rzp_live"


class PaymentLinkService:
    """Creates, stores and resolves Razorpay Payment Links against cases."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        client: Optional[object] = None,
        repository: Optional[CaseRepository] = None,
    ) -> None:
        from app.integrations.razorpay_client import RazorpayIntegrationClient

        self.repo = repository or CaseRepository(conn)
        self.client = client or RazorpayIntegrationClient()

    # --- creation ------------------------------------------------------------------

    @property
    def is_configured(self) -> bool:
        """False when only placeholder credentials are present."""
        return not str(getattr(self.client, "key_id", "")).startswith(MOCK_KEY_PREFIX)

    @property
    def is_test_mode(self) -> bool:
        return not str(getattr(self.client, "key_id", "")).startswith(LIVE_KEY_PREFIX)

    def reference_for(self, case: Case) -> str:
        """Deterministic reference. Contains no wall-clock time, so a retry reuses it."""
        return f"case_{case.case_id}_{case.amount_paise}"

    def get_or_create_link(
        self,
        case: Case,
        customer_name: str = "",
        customer_email: str = "",
        customer_phone: str = "",
        description: str = "",
    ) -> Tuple[Optional[PaymentLink], str]:
        """Return (link, note). Reuses a live link for the same case and amount.

        A None link with a note is an honest failure, never a fabricated link.
        """
        existing = self.repo.find_reusable_link(case.case_id, case.amount_paise)
        if existing is not None:
            return existing, "reused existing unpaid link"

        if not self.is_configured:
            return None, (
                "NOT_CONFIGURED: set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to a real "
                "Razorpay test key (rzp_test_...) to create live test links"
            )

        reference_id = self.reference_for(case)
        try:
            result = self.client.create_payment_link(
                amount_paise=case.amount_paise,
                customer_name=customer_name or "Customer",
                customer_email=customer_email,
                customer_contact=customer_phone,
                description=description or f"Payment for {case.case_id}",
                reference_id=reference_id,
            )
        except Exception as exc:
            logger.exception("payment link creation failed for %s", case.case_id)
            return None, f"FAILED: {exc}"[:200]

        link_id = str(result.get("id") or "")
        if not link_id:
            return None, "FAILED: provider returned no payment link id"

        # A simulated link would make the whole loop untestable: it produces no webhook, so
        # the case could never close. Refuse it rather than let a demo silently dead-end.
        if result.get("is_simulated"):
            return None, (
                "FAILED: the client returned a simulated link. A simulated link fires no "
                "webhook, so the case could never close. Check the Razorpay API response."
            )

        link = PaymentLink(
            payment_link_id=link_id,
            case_id=case.case_id,
            merchant_id=case.merchant_id,
            customer_id=case.customer_id,
            amount_paise=case.amount_paise,
            short_url=str(result.get("short_url") or ""),
            reference_id=reference_id,
            opportunity_id=case.opportunity_id,
            status=PaymentLinkStatus.CREATED,
            is_test_mode=self.is_test_mode,
        )
        self.repo.save_payment_link(link)
        self.repo.add_event(CaseEvent(
            case_id=case.case_id, kind=CaseEventKind.PAYMENT_LINK_CREATED, actor="agent",
            summary=f"Payment link created for Rs {case.amount_paise / 100:,.2f}",
            detail={"payment_link_id": link_id, "short_url": link.short_url,
                    "test_mode": link.is_test_mode},
        ))
        return link, "created"

    # --- resolution ----------------------------------------------------------------

    def resolve_case_id(self, entity_id: str, reference_id: str = "") -> Optional[str]:
        """Map any provider entity id back to a case. See repository for the id shapes."""
        return self.repo.find_case_for_provider_entity(entity_id, reference_id)

    def mark_paid_from_provider_event(
        self,
        entity_id: str,
        event_name: str,
        amount_paise: Optional[int] = None,
        reference_id: str = "",
    ) -> Optional[str]:
        """Apply a VERIFIED payment event to its case. Returns the case_id, or None.

        Reachable only from the HMAC-verified webhook path. Idempotent: replaying the same
        event on an already-paid case is a no-op that still returns the case id, so the
        caller's cancellation logic runs exactly the same way on a redelivery.
        """
        case_id = self.resolve_case_id(entity_id, reference_id)
        if case_id is None:
            logger.warning(
                "verified payment %s (%s) could not be mapped to a case - "
                "it will not close anything", entity_id, event_name,
            )
            return None

        self.repo.mark_link_paid(entity_id)

        case = self.repo.get_case(case_id)
        if case is not None and case.status == CaseStatus.PAID:
            return case_id  # already applied; idempotent

        self.repo.set_status(case_id, CaseStatus.PAID, reason=f"verified by {event_name}")
        self.repo.add_event(CaseEvent(
            case_id=case_id, kind=CaseEventKind.PAYMENT_RECEIVED, actor="provider",
            summary=(
                f"Payment received"
                + (f" of Rs {amount_paise / 100:,.2f}" if amount_paise else "")
            ),
            detail={"entity_id": entity_id, "event": event_name,
                    "amount_paise": amount_paise},
        ))
        self.repo.add_event(CaseEvent(
            case_id=case_id, kind=CaseEventKind.CASE_CLOSED, actor="agent",
            summary="Case closed - payment verified. All pending contact cancelled.",
            detail={"trigger": event_name},
        ))
        logger.info("case %s closed by verified payment %s", case_id, entity_id)
        return case_id

    def record_payment_failure(self, entity_id: str, event_name: str) -> Optional[str]:
        """Record a verified payment FAILURE. The case stays open for re-evaluation."""
        case_id = self.resolve_case_id(entity_id)
        if case_id is None:
            return None
        self.repo.add_event(CaseEvent(
            case_id=case_id, kind=CaseEventKind.PAYMENT_FAILED, actor="provider",
            summary="Payment attempt failed",
            detail={"entity_id": entity_id, "event": event_name},
        ))
        return case_id
