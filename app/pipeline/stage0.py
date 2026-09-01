"""Stage 0 — Genuine Recoverability Validation for Unified Recovery Engine.

INVARIANTS:
1. INV-7: Feature and evidence point-in-time safety (observed_at <= decision_timestamp).
2. NO PHANTOM RECOVERY: Eliminates self-cured, completed checkout, resolved invoice, TDS withholding, and duplicate events.
3. DETERMINISTIC: Given identical input + observed state, output is 100% deterministic.
"""

from typing import Any, Dict, Optional
from app.clock import Clock, SystemClock
from app.domain.enums import EventType, Stage0Decision, Stage0Reason
from app.domain.models import CanonicalEvent, RecoveryOpportunity, Stage0Result


class PointInTimeLeakageError(Exception):
    """Raised when evidence observed_at timestamp is in the future relative to decision timestamp."""
    pass


class Stage0Evaluator:
    """Evaluates genuine recoverability of revenue events, filtering out phantom losses."""

    def __init__(self, clock: Optional[Clock] = None, max_recovery_window_days: int = 30) -> None:
        self.clock = clock or SystemClock()
        self.max_recovery_window_days = max_recovery_window_days

    def evaluate(
        self,
        opportunity: RecoveryOpportunity,
        decision_timestamp: Optional[str] = None,
        context_state: Optional[Dict[str, Any]] = None,
        strict_point_in_time: bool = True,
    ) -> Stage0Result:
        """Evaluate whether a RecoveryOpportunity represents genuine recoverable revenue.

        Returns Stage0Result with explicit decision, reason code, evidence, and evaluation timestamp.
        """
        eval_time = decision_timestamp or self.clock.now_iso()
        context = context_state or opportunity.context_data or {}

        # 1. Point-in-Time Leakage Verification (INV-7)
        evidence_observed_at = context.get("observed_at", opportunity.observed_at)
        if evidence_observed_at > eval_time:
            if strict_point_in_time:
                raise PointInTimeLeakageError(
                    f"Point-in-time leakage detected! Evidence observed_at '{evidence_observed_at}' is after decision timestamp '{eval_time}'."
                )
            return Stage0Result(
                decision=Stage0Decision.NOT_RECOVERABLE,
                reason_code=Stage0Reason.POINT_IN_TIME_LEAKAGE,
                evidence={"evidence_observed_at": evidence_observed_at, "decision_timestamp": eval_time},
                evaluated_at=eval_time,
            )

        # 2. Check for zero or negative amount (Invalid Event)
        if opportunity.amount.amount_paise <= 0:
            return Stage0Result(
                decision=Stage0Decision.NOT_RECOVERABLE,
                reason_code=Stage0Reason.INVALID_EVENT,
                evidence={"amount_paise": opportunity.amount.amount_paise},
                evaluated_at=eval_time,
            )

        # 3. Stream-specific and Contextual Phantom Recovery Checks

        # Check A: Self-Cure / Already Paid
        if context.get("is_paid", False) or context.get("payment_status") == "SUCCESS":
            paid_at = context.get("paid_at", opportunity.occurred_at)
            return Stage0Result(
                decision=Stage0Decision.NOT_RECOVERABLE,
                reason_code=Stage0Reason.SELF_CURED,
                evidence={"is_paid": True, "paid_at": paid_at, "status": context.get("payment_status")},
                evaluated_at=eval_time,
            )

        # Check B: TDS / Withholding Tax Exclusion (Not recoverable customer debt)
        if context.get("is_tds_withheld", False) or context.get("tax_exemption_reason") == "TDS_DEDUCTION":
            return Stage0Result(
                decision=Stage0Decision.NOT_RECOVERABLE,
                reason_code=Stage0Reason.TDS_WITHHOLDING_EXCLUSION,
                evidence={"tds_amount_paise": context.get("tds_amount_paise", 0)},
                evaluated_at=eval_time,
            )

        # Check C: Abandoned Checkout already completed
        if opportunity.event_type == EventType.ABANDONED_CHECKOUT:
            if context.get("checkout_completed", False) or context.get("cart_status") == "COMPLETED":
                return Stage0Result(
                    decision=Stage0Decision.NOT_RECOVERABLE,
                    reason_code=Stage0Reason.CHECKOUT_COMPLETED,
                    evidence={"cart_status": context.get("cart_status", "COMPLETED")},
                    evaluated_at=eval_time,
                )

        # Check D: B2B Invoice already settled or written off
        if opportunity.event_type == EventType.OVERDUE_B2B_INVOICE:
            if context.get("invoice_status") in ("PAID", "SETTLED", "WRITTEN_OFF"):
                return Stage0Result(
                    decision=Stage0Decision.NOT_RECOVERABLE,
                    reason_code=Stage0Reason.INVOICE_RESOLVED,
                    evidence={"invoice_status": context.get("invoice_status")},
                    evaluated_at=eval_time,
                )

        # Check E: Duplicate event flag
        if context.get("is_duplicate", False):
            return Stage0Result(
                decision=Stage0Decision.NOT_RECOVERABLE,
                reason_code=Stage0Reason.DUPLICATE_EVENT,
                evidence={"duplicate_event_id": context.get("duplicate_event_id")},
                evaluated_at=eval_time,
            )

        # Genuine recoverable opportunity passed all Stage 0 filters!
        return Stage0Result(
            decision=Stage0Decision.VALID_RECOVERY,
            reason_code=Stage0Reason.GENUINE_RECOVERABLE,
            evidence={
                "event_type": opportunity.event_type.value,
                "amount_paise": opportunity.amount.amount_paise,
                "customer_id": opportunity.customer_id,
            },
            evaluated_at=eval_time,
        )
