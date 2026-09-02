"""Stateful Deterministic Sandbox Simulator for Unified Recovery Engine (M6).

INVARIANTS:
1. Provider-neutral, credential-free, synthetic sandbox.
2. Deterministic: Seeded inputs produce identical execution and payment outcome timelines.
3. Self-cure support: Models payments occurring prior to or independently of intervention delivery.
4. Ambiguous execution: Supports simulating transport timeouts yielding EXECUTION_UNKNOWN.
"""

import hashlib
import random
from typing import Any, Dict, Optional
from app.clock import Clock, SystemClock
from app.domain.enums import (
    ActionType,
    DataProvenance,
    ExecutionStatus,
    PaymentOutcome,
)
from app.domain.models import (
    SandboxActionRequest,
    SandboxExecutionResult,
)


def _substream(random_seed, *parts) -> random.Random:
    """Deterministic per-opportunity RNG substream.

    CRITICAL (07_EXPERIMENT_METHODOLOGY): seeding on random_seed ALONE makes every
    opportunity within a seed draw the identical number, collapsing the effective
    sample size from N opportunities to N seeds and making reported confidence
    intervals far too narrow. Keying the stream on (seed, opportunity, action) gives
    each opportunity an independent draw while remaining fully reproducible, and
    supplies common random numbers across arms: the same opportunity given the same
    action draws the same outcome in every arm, so arms cannot differ by luck.
    """
    key = "|".join([str(random_seed if random_seed is not None else 42), *[str(p) for p in parts]])
    digest = hashlib.sha256(key.encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


class SandboxSimulator:
    """Simulates realistic customer payment response and transport mechanics for sandbox execution."""

    def __init__(self, clock: Optional[Clock] = None) -> None:
        self.clock = clock or SystemClock()

    def execute_action(
        self,
        request: SandboxActionRequest,
        force_outcome: Optional[PaymentOutcome] = None,
        force_status: Optional[ExecutionStatus] = None,
        random_seed: Optional[int] = None,
    ) -> SandboxExecutionResult:
        """Execute a candidate action against the simulated sandbox environment."""
        exec_id = f"exec_{request.action_id}"
        now_iso = request.requested_at or self.clock.now_iso()

        # Handle NO_ACTION explicit counterfactual baseline
        if request.action_type == ActionType.NO_ACTION:
            # Deterministic natural recovery decision based on seed
            rng = _substream(random_seed, request.opportunity_id, "NO_ACTION")
            # 15% natural recovery rate for NO_ACTION
            outcome = force_outcome or (
                PaymentOutcome.SELF_CURED if rng.random() < 0.15 else PaymentOutcome.NO_PAYMENT
            )
            return SandboxExecutionResult(
                execution_id=exec_id,
                action_id=request.action_id,
                decision_id=request.decision_id,
                opportunity_id=request.opportunity_id,
                merchant_id=request.merchant_id,
                customer_id=request.customer_id,
                action_type=ActionType.NO_ACTION,
                execution_status=ExecutionStatus.EXECUTED,
                payment_outcome=outcome,
                executed_at=now_iso,
                delivered_at=now_iso if outcome == PaymentOutcome.SELF_CURED else None,
                failure_reason=None,
                raw_response={"message": "NO_ACTION counterfactual evaluated. No contact dispatched."},
                provenance=DataProvenance.SIMULATED_EXTERNAL_STATE,
            )

        # Handle explicit forced overrides for deterministic scenario testing
        if force_status == ExecutionStatus.EXECUTION_UNKNOWN or force_outcome == PaymentOutcome.EXECUTION_UNKNOWN:
            return SandboxExecutionResult(
                execution_id=exec_id,
                action_id=request.action_id,
                decision_id=request.decision_id,
                opportunity_id=request.opportunity_id,
                merchant_id=request.merchant_id,
                customer_id=request.customer_id,
                action_type=request.action_type,
                execution_status=ExecutionStatus.EXECUTION_UNKNOWN,
                payment_outcome=PaymentOutcome.EXECUTION_UNKNOWN,
                executed_at=now_iso,
                delivered_at=None,
                failure_reason="SIMULATED_TRANSPORT_TIMEOUT",
                raw_response={
                    "error": "Gateway/channel timeout during dispatch.",
                    "status_code": 504,
                },
                provenance=DataProvenance.SIMULATED_EXTERNAL_STATE,
            )

        if force_status == ExecutionStatus.FAILED_CLOSED:
            return SandboxExecutionResult(
                execution_id=exec_id,
                action_id=request.action_id,
                decision_id=request.decision_id,
                opportunity_id=request.opportunity_id,
                merchant_id=request.merchant_id,
                customer_id=request.customer_id,
                action_type=request.action_type,
                execution_status=ExecutionStatus.FAILED_CLOSED,
                payment_outcome=PaymentOutcome.PAYMENT_FAILED,
                executed_at=now_iso,
                delivered_at=None,
                failure_reason="SIMULATED_CHANNEL_REJECT",
                raw_response={"error": "Channel provider rejected message delivery."},
                provenance=DataProvenance.SIMULATED_EXTERNAL_STATE,
            )

        if force_outcome == PaymentOutcome.SELF_CURED:
            return SandboxExecutionResult(
                execution_id=exec_id,
                action_id=request.action_id,
                decision_id=request.decision_id,
                opportunity_id=request.opportunity_id,
                merchant_id=request.merchant_id,
                customer_id=request.customer_id,
                action_type=request.action_type,
                execution_status=ExecutionStatus.EXECUTED,
                payment_outcome=PaymentOutcome.SELF_CURED,
                executed_at=now_iso,
                delivered_at=now_iso,
                failure_reason=None,
                raw_response={"message": "Payment succeeded prior to/independently of contact delivery."},
                provenance=DataProvenance.SIMULATED_EXTERNAL_STATE,
            )

        # Standard simulated execution
        rng = _substream(random_seed, request.opportunity_id, request.action_type.value)

        # Channel base success rates for simulation
        success_probabilities = {
            ActionType.RECOMMEND_RETRY: 0.65,
            ActionType.WHATSAPP_LINK: 0.55,
            ActionType.SMS_LINK: 0.40,
            ActionType.EMAIL_LINK: 0.30,
            ActionType.IVR_CALL: 0.35,
            ActionType.AGENT_DIAL: 0.70,
        }

        base_p = success_probabilities.get(request.action_type, 0.30)
        roll = rng.random()

        if force_outcome == PaymentOutcome.PAYMENT_SUCCESS or (force_outcome is None and roll < base_p):
            outcome = PaymentOutcome.PAYMENT_SUCCESS
            exec_status = ExecutionStatus.EXECUTED
            fail_reason = None
        else:
            outcome = PaymentOutcome.PAYMENT_FAILED
            exec_status = ExecutionStatus.EXECUTED
            fail_reason = "CUSTOMER_UNRESPONSIVE_OR_DECLINED"

        return SandboxExecutionResult(
            execution_id=exec_id,
            action_id=request.action_id,
            decision_id=request.decision_id,
            opportunity_id=request.opportunity_id,
            merchant_id=request.merchant_id,
            customer_id=request.customer_id,
            action_type=request.action_type,
            execution_status=exec_status,
            payment_outcome=outcome,
            executed_at=now_iso,
            delivered_at=now_iso,
            failure_reason=fail_reason,
            raw_response={
                "action_type": request.action_type.value,
                "amount_paise": request.amount_paise,
                "simulated_outcome": outcome.value,
            },
            provenance=DataProvenance.SIMULATED_EXTERNAL_STATE,
        )
