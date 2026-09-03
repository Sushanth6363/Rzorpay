"""Unified Recovery Pipeline Orchestrator for Unified Recovery Engine (M4).

INVARIANTS:
1. INV-1: Tenant isolation strictly enforced on all pipeline inputs/outputs.
2. INV-7: Point-in-time safety on feature snapshots and Stage 0 evidence.
3. DECISION-PREPARATION ONLY: Prepares RecoveryDecisionContext without reserving/consuming contact slots.
"""

from typing import Any, Dict, Optional, Tuple
from app.clock import Clock, SystemClock
from app.db.dal import TenantScopedDB
from app.domain.enums import DataProvenance, EventSource, OpportunityStatus, Stage0Decision
from app.domain.models import (
    CanonicalEvent,
    CustomerContactBudget,
    RecoveryDecisionContext,
    RecoveryOpportunity,
)
from app.pipeline.candidate_generator import CandidateGenerator
from app.pipeline.dataset_adapter import DatasetAdapter
from app.pipeline.downtime import DowntimeProvider, SimulatedDowntimeProvider
from app.pipeline.escalation import EscalationPolicy
from app.pipeline.safety_filter import HardSafetyFilter
from app.pipeline.stage0 import Stage0Evaluator
from app.pipeline.stage1 import Stage1Diagnoser


class RecoveryPipeline:
    """Orchestrates Stage 0 validation, Stage 1 failure diagnosis, candidate generation, and safety filtering."""

    def __init__(
        self,
        db: Optional[TenantScopedDB] = None,
        clock: Optional[Clock] = None,
        downtime_provider: Optional[DowntimeProvider] = None,
        stage0_enabled: bool = True,
        shared_ledger_enabled: bool = True,
        escalation_policy: Optional[EscalationPolicy] = None,
    ) -> None:
        self.db = db
        self.clock = clock or SystemClock()
        # stage0_enabled=False makes the pipeline skip the validation GATE, so the
        # A2 vs A2ns comparison isolates the Stage 0 contribution (ADR-0011).
        # Stage 0 still RUNS and is still recorded; only its power to reject is removed.
        self.stage0_enabled = stage0_enabled
        # When False, the shared per-customer budget is not consulted: independent agents
        # have no cross-stream view, so the shared cap cannot suppress a candidate (D1 seam).
        self.shared_ledger_enabled = shared_ledger_enabled
        self.downtime_provider = downtime_provider or SimulatedDowntimeProvider()
        self.stage0_evaluator = Stage0Evaluator(clock=self.clock)
        self.stage1_diagnoser = Stage1Diagnoser(downtime_provider=self.downtime_provider, clock=self.clock)
        self.candidate_generator = CandidateGenerator()
        self.safety_filter = HardSafetyFilter()
        # Compliant escalation runs AFTER the hard safety filter and only ever subtracts,
        # so a SAFETY_REJECTED candidate can never be revived by the escalation ceiling.
        self.escalation_policy = escalation_policy or EscalationPolicy()

    def process_canonical_event(
        self,
        event: CanonicalEvent,
        decision_timestamp: Optional[str] = None,
        provenance: DataProvenance = DataProvenance.SIMULATED_EXTERNAL_STATE,
        contact_budget: Optional[CustomerContactBudget] = None,
    ) -> RecoveryDecisionContext:
        """Process a provider-neutral CanonicalEvent through the M4 pipeline."""
        eval_time = decision_timestamp or self.clock.now_iso()

        # 1. Opportunity Construction (Idempotent per merchant_id + source_event_id)
        opportunity_id = f"opp_{event.merchant_id}_{event.source_event_id}"
        opportunity = RecoveryOpportunity(
            opportunity_id=opportunity_id,
            merchant_id=event.merchant_id,
            customer_id=event.customer_id,
            source_event_id=event.source_event_id,
            event_type=event.event_type,
            amount=event.amount,
            currency=event.currency,
            status=OpportunityStatus.NEW,
            source=event.source,
            occurred_at=event.occurred_at,
            observed_at=event.observed_at,
            created_at=eval_time,
            updated_at=eval_time,
            context_data=event.raw_payload,
        )

        # Persist opportunity idempotently if DB is provided
        if self.db and self.db.merchant_id == event.merchant_id:
            existing = self.db.get_opportunity(opportunity_id)
            if existing:
                opportunity = existing
            else:
                self.db.create_opportunity(opportunity)

        return self.process_opportunity(
            opportunity=opportunity,
            decision_timestamp=eval_time,
            provenance=provenance,
            contact_budget=contact_budget,
        )

    def process_opportunity(
        self,
        opportunity: RecoveryOpportunity,
        decision_timestamp: Optional[str] = None,
        provenance: DataProvenance = DataProvenance.SIMULATED_EXTERNAL_STATE,
        contact_budget: Optional[CustomerContactBudget] = None,
    ) -> RecoveryDecisionContext:
        """Process an existing RecoveryOpportunity through Stage 0, Stage 1, Generator, and Safety Filter."""
        eval_time = decision_timestamp or self.clock.now_iso()
        context_data = opportunity.context_data or {}

        # Fetch contact budget from DB if available and not passed
        if (
            self.shared_ledger_enabled
            and contact_budget is None
            and self.db
            and self.db.merchant_id == opportunity.merchant_id
        ):
            contact_budget = self.db.get_contact_budget(opportunity.customer_id)

        # If context_data specifies explicit simulated budget exhaustion
        if context_data.get("is_budget_exhausted", False) and contact_budget is None:
            contact_budget = CustomerContactBudget(
                merchant_id=opportunity.merchant_id,
                customer_id=opportunity.customer_id,
                cap=3,
                reserved_count=3,
                consumed_count=0,
            )

        # 2. Stage 0 — Validate Genuine Recoverability
        stage0_result = self.stage0_evaluator.evaluate(
            opportunity=opportunity,
            decision_timestamp=eval_time,
            context_state=context_data,
        )

        # 3. Stage 1 — Diagnose Failure Context
        diagnosis = self.stage1_diagnoser.diagnose(
            opportunity=opportunity,
            decision_timestamp=eval_time,
            context_state=context_data,
        )

        # 4. Candidate Generation
        raw_candidates = self.candidate_generator.generate_candidates(
            opportunity=opportunity,
            diagnosis=diagnosis,
        )

        # 5. Hard Safety Eligibility Filtering
        # If Stage 0 declared opportunity NOT_RECOVERABLE, all non-counterfactual candidates are SAFETY_REJECTED
        if self.stage0_enabled and not stage0_result.is_recoverable:
            filtered_candidates = []
            for c in raw_candidates:
                if c.is_counterfactual:
                    filtered_candidates.append(c)
                else:
                    filtered_candidates.append(
                        c.__class__(
                            action_type=c.action_type,
                            eligibility=c.eligibility.SAFETY_REJECTED,
                            reject_reason=c.reject_reason.INVALID_OPPORTUNITY,
                            reason_explanation=f"Action '{c.action_type.value}' rejected because Stage 0 evaluated opportunity as NOT_RECOVERABLE ({stage0_result.reason_code.value}).",
                            evidence={"stage0_reason": stage0_result.reason_code.value},
                            is_counterfactual=False,
                        )
                    )
        else:
            filtered_candidates = self.safety_filter.filter_candidates(
                opportunity=opportunity,
                diagnosis=diagnosis,
                candidates=raw_candidates,
                contact_budget=contact_budget,
                downtime_provider=self.downtime_provider,
            )

        # 5b. Compliant Escalation Ceiling (ADR-0015)
        # Intensity may rise at most ONE rung above the last CONFIRMED contact, and never
        # inside the quiet period. Applied here - after hard safety, before scoring - so
        # the model chooses among what policy permits rather than the reverse.
        #
        # The history key mirrors the reservation key exactly: with a shared ledger the
        # ladder is per customer, so a second stream inherits the first stream's rung.
        # Without one, independent agents have no shared memory and each starts at the
        # quietest rung - which is the honest depiction of N uncoordinated agents, and is
        # precisely how a customer ends up receiving four first-touch messages.
        escalation_assessment = None
        if self.db and self.db.merchant_id == opportunity.merchant_id:
            history_key = (
                opportunity.customer_id
                if self.shared_ledger_enabled
                else f"{opportunity.customer_id}::{opportunity.opportunity_id}"
            )
            try:
                history = self.db.get_customer_ledger_history(history_key)
            except Exception:
                history = []
            filtered_candidates, escalation_assessment = self.escalation_policy.apply(
                candidates=filtered_candidates,
                history=history,
                decision_timestamp=eval_time,
                event_type_value=opportunity.event_type.value,
            )

        # 6. Feature Snapshot Construction (Point-in-Time Safe)
        feature_snapshot = {
            "merchant_id": opportunity.merchant_id,
            "customer_id": opportunity.customer_id,
            "opportunity_id": opportunity.opportunity_id,
            "event_type": opportunity.event_type.value,
            "amount_paise": opportunity.amount.amount_paise,
            "amount_rupees": float(opportunity.amount.to_rupees_decimal()),
            "currency": opportunity.currency,
            "diagnosis_code": diagnosis.diagnosis_code.value,
            "diagnosis_confidence": diagnosis.confidence,
            "stage0_decision": stage0_result.decision.value,
            "stage0_reason": stage0_result.reason_code.value,
            "observed_at": opportunity.observed_at,
            "decision_timestamp": eval_time,
            "is_downtime_active": diagnosis.diagnosis_code.value == "GATEWAY_FAILURE",
        }

        # Return explicit RecoveryDecisionContext without reserving contact budget
        return RecoveryDecisionContext(
            opportunity=opportunity,
            stage0_result=stage0_result,
            diagnosis=diagnosis,
            candidates=filtered_candidates,
            decision_timestamp=eval_time,
            feature_snapshot=feature_snapshot,
            provenance=provenance,
            is_contact_reserved=False,  # EXPLICIT INVARIANT CHECK
            escalation=escalation_assessment,
        )

    def process_raw_event(
        self,
        raw_data: Dict[str, Any],
        decision_timestamp: Optional[str] = None,
        provenance: DataProvenance = DataProvenance.SIMULATED_EXTERNAL_STATE,
        contact_budget: Optional[CustomerContactBudget] = None,
    ) -> RecoveryDecisionContext:
        """Helper to process raw input dictionary via DatasetAdapter."""
        canonical_event, prov = DatasetAdapter.adapt_raw_event(raw_data, provenance=provenance)
        return self.process_canonical_event(
            event=canonical_event,
            decision_timestamp=decision_timestamp,
            provenance=prov,
            contact_budget=contact_budget,
        )

