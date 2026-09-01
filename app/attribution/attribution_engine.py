"""Recovery Attribution Engine for Unified Recovery Engine (M6).

INVARIANTS:
1. Self-cure exclusion: If payment occurs before intervention delivery, or if NO_ACTION was taken,
   the payment is attributed_status = SELF_CURED and attributed_recovered_paise = 0 (₹0 AI attribution).
2. Integer paise representation: All recovery amounts strictly stored as integer paise.
3. Provenance: Every observation record tagged with simulated or real provenance.
"""

from typing import Optional
from app.clock import Clock, SystemClock
from app.domain.enums import (
    ActionType,
    AttributionStatus,
    DataProvenance,
    PaymentOutcome,
)
from app.domain.models import (
    AIRecoveryDecision,
    ContactLedgerEntry,
    RecoveryAttribution,
    RecoveryObservation,
    SandboxExecutionResult,
)


class AttributionEngine:
    """Evaluates causality and attributes gross and net revenue recovery."""

    def __init__(self, clock: Optional[Clock] = None) -> None:
        self.clock = clock or SystemClock()

    def attribute_recovery(
        self,
        decision: AIRecoveryDecision,
        execution_result: Optional[SandboxExecutionResult],
        amount_at_risk_paise: int,
        ledger_entry: Optional[ContactLedgerEntry] = None,
        evaluated_at: Optional[str] = None,
    ) -> RecoveryAttribution:
        """Classify payment outcome and attribute revenue between self-cure and intervention."""
        eval_time = evaluated_at or self.clock.now_iso()
        attr_id = f"attr_{decision.opportunity_id}_{decision.decision_id[:8]}"

        # 1. Handle NO_ACTION or SAFE_ABSTENTION
        if decision.selected_action == ActionType.NO_ACTION or execution_result is None:
            payment_outcome = (
                execution_result.payment_outcome
                if execution_result
                else PaymentOutcome.NO_PAYMENT
            )

            if payment_outcome == PaymentOutcome.SELF_CURED or payment_outcome == PaymentOutcome.PAYMENT_SUCCESS:
                return RecoveryAttribution(
                    attribution_id=attr_id,
                    opportunity_id=decision.opportunity_id,
                    merchant_id=decision.merchant_id,
                    customer_id=decision.customer_id,
                    decision_id=decision.decision_id,
                    ledger_id=ledger_entry.ledger_id if ledger_entry else None,
                    execution_id=execution_result.execution_id if execution_result else None,
                    selected_action=decision.selected_action,
                    attribution_status=AttributionStatus.SELF_CURED,
                    payment_outcome=PaymentOutcome.SELF_CURED,
                    gross_recovered_paise=amount_at_risk_paise,
                    attributed_recovered_paise=0,  # CRITICAL INVARIANT: ₹0 AI ATTRIBUTION FOR SELF-CURE
                    amount_at_risk_paise=amount_at_risk_paise,
                    evaluated_at=eval_time,
                    delivered_at=None,
                    payment_at=eval_time,
                    explanation="Customer naturally paid without intervention outreach. AI attribution = ₹0.",
                )
            else:
                return RecoveryAttribution(
                    attribution_id=attr_id,
                    opportunity_id=decision.opportunity_id,
                    merchant_id=decision.merchant_id,
                    customer_id=decision.customer_id,
                    decision_id=decision.decision_id,
                    ledger_id=ledger_entry.ledger_id if ledger_entry else None,
                    execution_id=execution_result.execution_id if execution_result else None,
                    selected_action=decision.selected_action,
                    attribution_status=AttributionStatus.FAILED_UNRECOVERED,
                    payment_outcome=PaymentOutcome.NO_PAYMENT,
                    gross_recovered_paise=0,
                    attributed_recovered_paise=0,
                    amount_at_risk_paise=amount_at_risk_paise,
                    evaluated_at=eval_time,
                    delivered_at=None,
                    payment_at=None,
                    explanation="NO_ACTION selected; opportunity remained unrecovered.",
                )

        # 2. Handle Action Interventions with Sandbox Execution Result
        outcome = execution_result.payment_outcome

        if outcome == PaymentOutcome.SELF_CURED:
            return RecoveryAttribution(
                attribution_id=attr_id,
                opportunity_id=decision.opportunity_id,
                merchant_id=decision.merchant_id,
                customer_id=decision.customer_id,
                decision_id=decision.decision_id,
                ledger_id=ledger_entry.ledger_id if ledger_entry else None,
                execution_id=execution_result.execution_id,
                selected_action=decision.selected_action,
                attribution_status=AttributionStatus.SELF_CURED,
                payment_outcome=PaymentOutcome.SELF_CURED,
                gross_recovered_paise=amount_at_risk_paise,
                attributed_recovered_paise=0,  # CRITICAL INVARIANT: ₹0 AI ATTRIBUTION FOR SELF-CURE
                amount_at_risk_paise=amount_at_risk_paise,
                evaluated_at=eval_time,
                delivered_at=execution_result.delivered_at,
                payment_at=execution_result.executed_at,
                explanation="Payment succeeded prior to/independently of contact delivery. AI attribution = ₹0.",
            )

        elif outcome == PaymentOutcome.PAYMENT_SUCCESS:
            return RecoveryAttribution(
                attribution_id=attr_id,
                opportunity_id=decision.opportunity_id,
                merchant_id=decision.merchant_id,
                customer_id=decision.customer_id,
                decision_id=decision.decision_id,
                ledger_id=ledger_entry.ledger_id if ledger_entry else None,
                execution_id=execution_result.execution_id,
                selected_action=decision.selected_action,
                attribution_status=AttributionStatus.RECOVERED,
                payment_outcome=PaymentOutcome.PAYMENT_SUCCESS,
                gross_recovered_paise=amount_at_risk_paise,
                attributed_recovered_paise=amount_at_risk_paise,
                amount_at_risk_paise=amount_at_risk_paise,
                evaluated_at=eval_time,
                delivered_at=execution_result.delivered_at,
                payment_at=eval_time,
                explanation=f"Intervention '{decision.selected_action.value}' delivered and payment recovered successfully.",
            )

        elif outcome == PaymentOutcome.EXECUTION_UNKNOWN:
            return RecoveryAttribution(
                attribution_id=attr_id,
                opportunity_id=decision.opportunity_id,
                merchant_id=decision.merchant_id,
                customer_id=decision.customer_id,
                decision_id=decision.decision_id,
                ledger_id=ledger_entry.ledger_id if ledger_entry else None,
                execution_id=execution_result.execution_id,
                selected_action=decision.selected_action,
                attribution_status=AttributionStatus.PENDING,
                payment_outcome=PaymentOutcome.EXECUTION_UNKNOWN,
                gross_recovered_paise=0,
                attributed_recovered_paise=0,
                amount_at_risk_paise=amount_at_risk_paise,
                evaluated_at=eval_time,
                delivered_at=None,
                payment_at=None,
                explanation="Execution status is EXECUTION_UNKNOWN; attribution pending reconciliation.",
            )

        else:
            return RecoveryAttribution(
                attribution_id=attr_id,
                opportunity_id=decision.opportunity_id,
                merchant_id=decision.merchant_id,
                customer_id=decision.customer_id,
                decision_id=decision.decision_id,
                ledger_id=ledger_entry.ledger_id if ledger_entry else None,
                execution_id=execution_result.execution_id,
                selected_action=decision.selected_action,
                attribution_status=AttributionStatus.FAILED_UNRECOVERED,
                payment_outcome=PaymentOutcome.PAYMENT_FAILED,
                gross_recovered_paise=0,
                attributed_recovered_paise=0,
                amount_at_risk_paise=amount_at_risk_paise,
                evaluated_at=eval_time,
                delivered_at=execution_result.delivered_at,
                payment_at=None,
                explanation=f"Intervention '{decision.selected_action.value}' attempted but payment failed.",
            )

    def create_observation(
        self,
        attribution: RecoveryAttribution,
        decision: AIRecoveryDecision,
        experiment_id: str = "exp_default_v1",
        arm: str = "A5_S_LEARNER",
    ) -> RecoveryObservation:
        """Create structured observation for future M7 experiment logging."""
        obs_id = f"obs_{attribution.opportunity_id}"
        return RecoveryObservation(
            observation_id=obs_id,
            experiment_id=experiment_id,
            arm=arm,
            opportunity_id=attribution.opportunity_id,
            merchant_id=attribution.merchant_id,
            customer_id=attribution.customer_id,
            decision_id=decision.decision_id,
            selected_action=decision.selected_action,
            outcome=attribution.payment_outcome,
            amount_at_risk_paise=attribution.amount_at_risk_paise,
            gross_recovered_paise=attribution.gross_recovered_paise,
            attributed_recovered_paise=attribution.attributed_recovered_paise,
            self_cured=attribution.is_self_cured,
            decision_timestamp=decision.decision_timestamp,
            outcome_timestamp=attribution.evaluated_at,
            model_version=decision.model_version,
            provenance=DataProvenance.SIMULATED_EXTERNAL_STATE,
        )
