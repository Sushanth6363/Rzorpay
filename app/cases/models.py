"""Customer / Case / PaymentLink — the durable spine the closed loop needs (ADR-0023).

WHY THIS EXISTS
    The Recovery Engine reasons about a `RecoveryOpportunity`: one moment of revenue at
    risk. That is the right unit for a DECISION, and nothing here changes it.

    But a closed loop needs a unit that OUTLIVES a decision. A customer is contacted on
    Monday, pays on Thursday through a link created on Tuesday, and a follow-up scheduled
    on Wednesday must be cancelled. Nothing in the engine spanned those four days: the
    opportunity was reconstructed per event and the payment link's id was written to a
    display string and then discarded.

    The consequence was a broken invariant, not a missing nicety. A customer who paid
    through a recovery link produced `plink_...`, while every follow-up was keyed on the
    ORIGINAL failure's `pay_...`. The two never met, so "payment always wins" could not
    fire on the exact path the product depends on. `PaymentLink` below is the join that
    was missing.

WHAT THIS IS NOT
    Not a second decision engine, and not a state machine that decides anything. A Case
    records what is true; the existing engine decides what to do about it. `CaseStatus`
    exists so the dispatcher can ask one question - "may I still contact this person?" -
    without re-deriving it from ledger archaeology every time.

INVARIANTS:
1. INTEGER PAISE. No float touches money, consistent with the rest of the system.
2. PAID IS TERMINAL FOR CONTACT. Once a case is PAID, no customer-contact action may
   execute, ever, regardless of what was scheduled earlier.
3. PAID IS SET ONLY BY A VERIFIED PROVIDER EVENT. Never by a click, a redirect, a form
   submission, or a customer's assertion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CaseStatus(str, Enum):
    """Lifecycle of one recoverable debt, from the merchant's point of view."""

    OPEN = "OPEN"                    # created, not yet contacted
    IN_PROGRESS = "IN_PROGRESS"      # at least one contact confirmed
    PROMISED = "PROMISED"            # customer stated an intent to pay by a date
    PAID = "PAID"                    # verified by a provider webhook. Terminal for contact.
    CLOSED = "CLOSED"                # given up, written off, or wrong person

    @property
    def is_terminal_for_contact(self) -> bool:
        """True when no further customer contact may be executed for this case."""
        return self in (CaseStatus.PAID, CaseStatus.CLOSED)


class PaymentLinkStatus(str, Enum):
    CREATED = "CREATED"
    PAID = "PAID"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class CaseEventKind(str, Enum):
    """Timeline vocabulary. Provider-neutral by construction."""

    CASE_CREATED = "CASE_CREATED"
    OPPORTUNITY_CREATED = "OPPORTUNITY_CREATED"
    AGENT_DECIDED = "AGENT_DECIDED"
    PAYMENT_LINK_CREATED = "PAYMENT_LINK_CREATED"
    MESSAGE_SENT = "MESSAGE_SENT"
    MESSAGE_DELIVERED = "MESSAGE_DELIVERED"
    MESSAGE_FAILED = "MESSAGE_FAILED"
    MESSAGE_OPENED = "MESSAGE_OPENED"
    PAYMENT_LINK_CLICKED = "PAYMENT_LINK_CLICKED"
    CUSTOMER_RESPONDED = "CUSTOMER_RESPONDED"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    FOLLOWUP_SCHEDULED = "FOLLOWUP_SCHEDULED"
    ACTION_CANCELLED = "ACTION_CANCELLED"
    CASE_CLOSED = "CASE_CLOSED"


@dataclass
class Customer:
    """A person or business the merchant may contact."""

    customer_id: str
    merchant_id: str
    name: str = ""
    email: str = ""
    phone: str = ""
    created_at: str = field(default_factory=now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer_id": self.customer_id, "merchant_id": self.merchant_id,
            "name": self.name, "email": self.email, "phone": self.phone,
            "created_at": self.created_at,
        }


@dataclass
class Case:
    """One recoverable debt, tracked across every decision made about it."""

    case_id: str
    merchant_id: str
    customer_id: str
    amount_paise: int
    currency: str = "INR"
    due_date: str = ""
    # The originating provider entity (e.g. the failed payment id). Kept because a
    # `payment.captured` on the ORIGINAL attempt must also resolve back to this case.
    source_event_id: str = ""
    opportunity_id: str = ""
    # Which recovery stream this debt belongs to. It drives which actions the engine will
    # even CONSIDER: a receivable uploaded by a merchant has no stored instrument, so
    # RECOMMEND_RETRY is not a real option and the candidate generator correctly does not
    # offer it. Mislabelling a receivable as a FAILED_PAYMENT makes the engine recommend
    # retrying a charge that was never attempted.
    event_type: str = "OVERDUE_B2B_INVOICE"
    status: CaseStatus = CaseStatus.OPEN
    promised_date: str = ""
    close_reason: str = ""
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    closed_at: str = ""

    @property
    def may_contact(self) -> bool:
        """The single question the dispatcher asks before every send."""
        return not self.status.is_terminal_for_contact

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id, "merchant_id": self.merchant_id,
            "customer_id": self.customer_id, "amount_paise": self.amount_paise,
            "currency": self.currency, "due_date": self.due_date,
            "source_event_id": self.source_event_id, "opportunity_id": self.opportunity_id,
            "event_type": self.event_type,
            "status": self.status.value, "promised_date": self.promised_date,
            "close_reason": self.close_reason, "created_at": self.created_at,
            "updated_at": self.updated_at, "closed_at": self.closed_at,
        }


@dataclass
class PaymentLink:
    """A Razorpay Payment Link, and the case it belongs to.

    THIS RECORD IS THE FIX. Without it a `payment_link.paid` webhook carrying `plink_...`
    cannot be traced to the case created from `pay_...`, so the payment is invisible to
    the agent and scheduled contact still goes out to someone who has already paid.
    """

    payment_link_id: str          # Razorpay's plink_... id
    case_id: str
    merchant_id: str
    customer_id: str
    amount_paise: int
    short_url: str = ""
    reference_id: str = ""        # our id, echoed back by Razorpay
    opportunity_id: str = ""
    status: PaymentLinkStatus = PaymentLinkStatus.CREATED
    is_test_mode: bool = True
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    paid_at: str = ""

    @property
    def is_reusable(self) -> bool:
        """A live, unpaid link may be reused rather than duplicated."""
        return self.status == PaymentLinkStatus.CREATED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "payment_link_id": self.payment_link_id, "case_id": self.case_id,
            "merchant_id": self.merchant_id, "customer_id": self.customer_id,
            "amount_paise": self.amount_paise, "short_url": self.short_url,
            "reference_id": self.reference_id, "opportunity_id": self.opportunity_id,
            "status": self.status.value, "is_test_mode": self.is_test_mode,
            "created_at": self.created_at, "updated_at": self.updated_at,
            "paid_at": self.paid_at,
        }


@dataclass
class CaseEvent:
    """One entry on a case's timeline. Append-only."""

    case_id: str
    kind: CaseEventKind
    summary: str
    at: str = field(default_factory=now_iso)
    actor: str = "agent"          # agent | customer | provider | merchant
    detail: Dict[str, Any] = field(default_factory=dict)
    event_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id, "case_id": self.case_id, "at": self.at,
            "kind": self.kind.value, "actor": self.actor, "summary": self.summary,
            "detail": self.detail,
        }
