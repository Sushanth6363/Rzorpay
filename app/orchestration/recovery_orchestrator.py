"""End-to-End Closed-Loop Recovery Orchestrator for Unified Recovery Engine (M6).

INVARIANTS:
1. M4 -> M5 -> Reservation -> Execution -> Reconciliation -> Attribution pipeline composition.
2. Atomic contact budget reservation before intervention execution.
3. NO_ACTION consumes zero contact capacity.
4. Reservation failures safely fall back to uncontacted evaluation without slot leakage.
5. Execution unknown is never automatically re-dispatched.
6. Full correlation trace: event_id -> opportunity_id -> decision_id -> ledger_id -> execution_id -> attribution_id.
"""

import sqlite3
from typing import Any, Dict, Optional
from app.attribution.attribution_engine import AttributionEngine
from app.clock import Clock, SystemClock
from app.db.dal import TenantScopedDB
from app.db.init import init_db
from app.domain.enums import (
    ActionType,
    DecisionMode,
    ExecutionStatus,
    LedgerStatus,
    PaymentOutcome,
)
from app.domain.models import (
    AIRecoveryDecision,
    ContactLedgerEntry,
    EndToEndRecoveryResult,
    RecoveryDecisionContext,
    SandboxActionRequest,
    SandboxExecutionResult,
)
from app.ledger.engine import ContactLedgerEngine
from app.pipeline.downtime import DowntimeProvider
from app.pipeline.recovery_pipeline import RecoveryPipeline
from app.sandbox.simulator import SandboxSimulator
from app.scoring.engine import AIRecoveryDecisionEngine


class RecoveryOrchestrator:
    """Orchestrates closed-loop recovery: Pipeline -> AI Decision -> Reservation -> Sandbox -> Attribution."""

    def __init__(
        self,
        db_conn: Optional[sqlite3.Connection] = None,
        clock: Optional[Clock] = None,
        downtime_provider: Optional[DowntimeProvider] = None,
        ai_engine: Optional[AIRecoveryDecisionEngine] = None,
        simulator: Optional[SandboxSimulator] = None,
        stage0_enabled: bool = True,
        shared_ledger_enabled: bool = True,
    ) -> None:
        self.clock = clock or SystemClock()
        self.conn = db_conn or init_db(":memory:")
        self.downtime_provider = downtime_provider
        # stage0_enabled and downtime_provider are the experiment-arm seams (ADR-0011):
        # arms must differ by real capability, never by label alone.
        self.stage0_enabled = stage0_enabled
        # shared_ledger_enabled=False models INDEPENDENT per-stream agents: each acts without
        # a shared per-customer contact budget, so nothing arbitrates across streams and the
        # cap cannot bind. This is the A2ns vs A1 seam (D1). Turning it off does not disable
        # the ledger's bookkeeping - it removes the SHARED budget's power to suppress.
        self.shared_ledger_enabled = shared_ledger_enabled
        self.pipeline = RecoveryPipeline(
            clock=self.clock,
            downtime_provider=self.downtime_provider,
            stage0_enabled=stage0_enabled,
            shared_ledger_enabled=shared_ledger_enabled,
        )
        self.ai_engine = ai_engine or AIRecoveryDecisionEngine()
        self.simulator = simulator or SandboxSimulator(clock=self.clock)
        self.attribution_engine = AttributionEngine(clock=self.clock)

    def process_and_execute(
        self,
        raw_event: Dict[str, Any],
        merchant_id: Optional[str] = None,
        decision_timestamp: Optional[str] = None,
        force_mode: Optional[DecisionMode] = None,
        force_sandbox_outcome: Optional[PaymentOutcome] = None,
        force_sandbox_status: Optional[ExecutionStatus] = None,
        random_seed: Optional[int] = 42,
        reconcile_unknown_as: Optional[LedgerStatus] = None,
        experiment_id: str = "exp_sandbox_m6",
        arm: str = "A5_S_LEARNER",
    ) -> EndToEndRecoveryResult:
        """Execute full end-to-end recovery loop for a raw payment/recovery event."""
        eval_time = decision_timestamp or self.clock.now_iso()
        merch_id = merchant_id or raw_event.get("merchant_id", "default_merchant")

        # 1. Scoped DAL & Ledger Engine for Merchant Tenant
        ledger_engine = ContactLedgerEngine(conn=self.conn, merchant_id=merch_id, clock=self.clock)
        dal = TenantScopedDB(conn=self.conn, merchant_id=merch_id, clock=self.clock)
        self.pipeline.db = dal

        # 2. Run M4 Pipeline -> Context
        context: RecoveryDecisionContext = self.pipeline.process_raw_event(
            raw_data=raw_event,
            decision_timestamp=eval_time,
        )

        amount_at_risk_paise = context.opportunity.amount.amount_paise
        customer_id = context.opportunity.customer_id
        opportunity_id = context.opportunity.opportunity_id

        # 3. Run M5 AI Decision Engine -> AIRecoveryDecision
        decision: AIRecoveryDecision = self.ai_engine.evaluate_decision(
            context=context,
            random_seed=random_seed,
            force_mode=force_mode,
        )

        selected_action = decision.selected_action
        trace_id = f"trace_{opportunity_id}_{decision.decision_id[:8]}"

        # 4. Handle NO_ACTION or SAFE_ABSTENTION
        if selected_action == ActionType.NO_ACTION or decision.decision_mode == DecisionMode.SAFE_ABSTENTION:
            # NO_ACTION consumes ZERO contact capacity
            action_req = SandboxActionRequest(
                action_id=f"act_{decision.decision_id[:8]}",
                decision_id=decision.decision_id,
                merchant_id=merch_id,
                customer_id=customer_id,
                opportunity_id=opportunity_id,
                action_type=ActionType.NO_ACTION,
                amount_paise=amount_at_risk_paise,
                requested_at=eval_time,
                idempotency_key=f"idemp_no_action_{opportunity_id}",
            )

            exec_result = self.simulator.execute_action(
                request=action_req,
                force_outcome=force_sandbox_outcome,
                random_seed=random_seed,
            )

            attribution = self.attribution_engine.attribute_recovery(
                decision=decision,
                execution_result=exec_result,
                amount_at_risk_paise=amount_at_risk_paise,
                ledger_entry=None,
                evaluated_at=eval_time,
            )

            observation = self.attribution_engine.create_observation(
                attribution=attribution,
                decision=decision,
                experiment_id=experiment_id,
                arm=arm,
            )

            return EndToEndRecoveryResult(
                opportunity_id=opportunity_id,
                merchant_id=merch_id,
                customer_id=customer_id,
                event_id=context.opportunity.source_event_id,
                decision=decision,
                ledger_entry=None,
                execution_result=exec_result,
                attribution=attribution,
                observation=observation,
                trace_id=trace_id,
            )

        # 5. Handle Action Intervention -> Atomic Reservation
        idempotency_key = f"idemp_{opportunity_id}_{selected_action.value}"

        # D1 seam: with a SHARED ledger, every stream reserves against one per-customer
        # budget, so the cap arbitrates across streams. Without it, each independent agent
        # reserves against its own budget row and nothing arbitrates - which is precisely
        # the behaviour of N agents that cannot see each other.
        budget_key = (
            customer_id if self.shared_ledger_enabled else f"{customer_id}::{opportunity_id}"
        )

        ledger_entry: Optional[ContactLedgerEntry] = ledger_engine.reserve_contact(
            customer_id=budget_key,
            opportunity_id=opportunity_id,
            action_type=selected_action,
            intervention_idempotency_key=idempotency_key,
        )

        # If reservation failed (budget cap exhausted or database constraint violation)
        if ledger_entry is None:
            # Safe Fallback to uncontacted execution
            action_req = SandboxActionRequest(
                action_id=f"act_{decision.decision_id[:8]}",
                decision_id=decision.decision_id,
                merchant_id=merch_id,
                customer_id=customer_id,
                opportunity_id=opportunity_id,
                action_type=ActionType.NO_ACTION,
                amount_paise=amount_at_risk_paise,
                requested_at=eval_time,
                idempotency_key=idempotency_key,
            )

            exec_result = self.simulator.execute_action(
                request=action_req,
                force_outcome=PaymentOutcome.NO_PAYMENT,
                random_seed=random_seed,
            )

            attribution = self.attribution_engine.attribute_recovery(
                decision=decision,
                execution_result=exec_result,
                amount_at_risk_paise=amount_at_risk_paise,
                ledger_entry=None,
                evaluated_at=eval_time,
            )

            observation = self.attribution_engine.create_observation(
                attribution=attribution,
                decision=decision,
                experiment_id=experiment_id,
                arm=arm,
            )

            return EndToEndRecoveryResult(
                opportunity_id=opportunity_id,
                merchant_id=merch_id,
                customer_id=customer_id,
                event_id=context.opportunity.source_event_id,
                decision=decision,
                ledger_entry=None,
                execution_result=exec_result,
                attribution=attribution,
                observation=observation,
                trace_id=trace_id,
            )

        # 6. Record Execution Attempt
        ledger_engine.record_execution_attempt(ledger_id=ledger_entry.ledger_id)

        # 7. Sandbox Execution
        action_req = SandboxActionRequest(
            action_id=f"act_{ledger_entry.ledger_id}",
            decision_id=decision.decision_id,
            merchant_id=merch_id,
            customer_id=customer_id,
            opportunity_id=opportunity_id,
            action_type=selected_action,
            amount_paise=amount_at_risk_paise,
            requested_at=eval_time,
            idempotency_key=idempotency_key,
        )

        exec_result = self.simulator.execute_action(
            request=action_req,
            force_outcome=force_sandbox_outcome,
            force_status=force_sandbox_status,
            random_seed=random_seed,
        )

        # 8. Record Execution Result in Ledger
        if exec_result.execution_status == ExecutionStatus.EXECUTION_UNKNOWN:
            ledger_engine.mark_execution_unknown(
                ledger_id=ledger_entry.ledger_id,
                metadata={"reason": exec_result.failure_reason},
            )
            # Reconcile if explicit reconciliation outcome requested
            if reconcile_unknown_as:
                ledger_engine.reconcile(
                    ledger_id=ledger_entry.ledger_id,
                    outcome=reconcile_unknown_as,
                )

        elif exec_result.execution_status == ExecutionStatus.EXECUTED:
            ledger_engine.record_execution_result(
                ledger_id=ledger_entry.ledger_id,
                success=True,
                metadata={"outcome": exec_result.payment_outcome.value},
            )

        else:
            ledger_engine.record_execution_result(
                ledger_id=ledger_entry.ledger_id,
                success=False,
                metadata={"outcome": exec_result.payment_outcome.value},
            )

        # Retrieve final updated ledger entry state
        updated_ledger = ledger_engine.get_ledger_entry(ledger_entry.ledger_id)

        # 9. Attribute Recovery
        attribution = self.attribution_engine.attribute_recovery(
            decision=decision,
            execution_result=exec_result,
            amount_at_risk_paise=amount_at_risk_paise,
            ledger_entry=updated_ledger,
            evaluated_at=eval_time,
        )

        # 10. Observation Record
        observation = self.attribution_engine.create_observation(
            attribution=attribution,
            decision=decision,
            experiment_id=experiment_id,
            arm=arm,
        )

        return EndToEndRecoveryResult(
            opportunity_id=opportunity_id,
            merchant_id=merch_id,
            customer_id=customer_id,
            event_id=context.opportunity.source_event_id,
            decision=decision,
            ledger_entry=updated_ledger,
            execution_result=exec_result,
            attribution=attribution,
            observation=observation,
            trace_id=trace_id,
        )
