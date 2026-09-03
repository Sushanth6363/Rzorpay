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
from app.pipeline.tds import TdsDerivation, TdsPosition, derive_tds_position

# Sentinel used where withholding cannot apply. UNDETERMINED never suppresses and never
# restates an amount, so a non-receivable stream is left exactly as it was.
NOT_APPLICABLE_TDS = TdsDerivation(
    position=TdsPosition.UNDETERMINED,
    gross_amount_paise=0,
    amount_received_paise=0,
    shortfall_paise=0,
    section=None,
    payee_type="N/A",
    applied_rate_bps=0,
    expected_tds_paise=0,
    recoverable_amount_paise=0,
    rate_source="not applicable to this stream",
    explanation="Withholding does not apply to this event type and no section was supplied.",
)


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

        # Check B: TDS / Withholding Tax Exclusion (not recoverable customer debt)
        #
        # DERIVED, NOT DECLARED. The withholding position is computed from the invoice's
        # own facts - gross, section, payee constitution, PAN, amount actually remitted -
        # by app.pipeline.tds. A shortfall that equals the statutory withholding is money
        # the payer already remitted to the government on the payee's behalf: the customer
        # owes nothing and contacting them is a demand for money the law required them to
        # withhold. Where the shortfall EXCEEDS the withholding, only the excess is chased.
        # Withholding applies to receivables, so the derivation runs only where it can
        # mean something: a B2B invoice, or any event that explicitly carries a section.
        # Running it universally would let a stray `amount_received_paise` on an unrelated
        # stream suppress a legitimate recovery.
        tds_applicable = (
            opportunity.event_type == EventType.OVERDUE_B2B_INVOICE
            or context.get("tds_section") is not None
        )
        tds_derivation = (
            derive_tds_position(
                gross_amount_paise=opportunity.amount.amount_paise,
                context=context,
            )
            if tds_applicable
            else NOT_APPLICABLE_TDS
        )

        if tds_derivation.position in (TdsPosition.STATUTORY_WITHHOLDING, TdsPosition.NO_SHORTFALL):
            return Stage0Result(
                decision=Stage0Decision.NOT_RECOVERABLE,
                reason_code=Stage0Reason.TDS_WITHHOLDING_EXCLUSION,
                evidence={"tds_derivation": tds_derivation.to_dict()},
                evaluated_at=eval_time,
                recoverable_amount_paise=0,
            )

        # LEGACY PASSTHROUGH. Retained only for callers that supply a pre-computed boolean
        # and none of the facts needed to derive a position. It fires ONLY where the
        # derivation was unable to reach a conclusion: a flag may fill a silence, but it may
        # never contradict the invoice's own numbers. Otherwise any caller could suppress
        # any recovery by asserting a withholding the arithmetic does not support.
        derivation_reached_a_conclusion = tds_derivation.position != TdsPosition.UNDETERMINED
        if not derivation_reached_a_conclusion and (
            context.get("is_tds_withheld", False)
            or context.get("tax_exemption_reason") == "TDS_DEDUCTION"
        ):
            return Stage0Result(
                decision=Stage0Decision.NOT_RECOVERABLE,
                reason_code=Stage0Reason.TDS_WITHHOLDING_EXCLUSION,
                evidence={
                    "tds_amount_paise": context.get("tds_amount_paise", 0),
                    "basis": "DECLARED_FLAG_NOT_DERIVED",
                    "note": (
                        "Suppressed on a caller-supplied flag because the facts needed to "
                        "derive a withholding position were absent."
                    ),
                },
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

        # Genuine recoverable opportunity passed all Stage 0 filters.
        evidence: Dict[str, Any] = {
            "event_type": opportunity.event_type.value,
            "amount_paise": opportunity.amount.amount_paise,
            "customer_id": opportunity.customer_id,
        }

        # PARTIAL_WITH_TDS: the invoice is genuinely in arrears, but part of the shortfall
        # is the exchequer's. Restating the chaseable amount here is what stops the engine
        # from demanding - and from later reporting as "recovered" - money it never could
        # have collected. Any other derived position leaves the face amount untouched.
        restated: Optional[int] = None
        if tds_derivation.position != TdsPosition.UNDETERMINED:
            evidence["tds_derivation"] = tds_derivation.to_dict()
        if tds_derivation.position == TdsPosition.PARTIAL_WITH_TDS:
            restated = tds_derivation.recoverable_amount_paise

        return Stage0Result(
            decision=Stage0Decision.VALID_RECOVERY,
            reason_code=Stage0Reason.GENUINE_RECOVERABLE,
            evidence=evidence,
            evaluated_at=eval_time,
            recoverable_amount_paise=restated,
        )
