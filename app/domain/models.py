"""Domain models for Unified Recovery Engine.

Defines core business entities (RecoveryOpportunity, CustomerContactBudget, EventLog, CanonicalEvent,
ContactLedgerEntry, Stage0Result, DiagnosisResult, ActionCandidate, RecoveryDecisionContext)
using clean type-annotated dataclasses.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from app.domain.enums import (
    EventType,
    OpportunityStatus,
    ActionType,
    ExecutionStatus,
    LedgerStatus,
    AttributionStatus,
    EventSource,
    Stage0Decision,
    Stage0Reason,
    DiagnosisCode,
    EligibilityStatus,
    SafetyRejectReason,
    DataProvenance,
    AbstentionReason,
    DecisionMode,
    PaymentOutcome,
    ExperimentArm,
    StatisticalStatus,
)

from app.domain.money import Money


def current_iso_timestamp() -> str:

    """Return ISO 8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class CanonicalEvent:
    """Provider-neutral event contract (ADR-0012)."""

    event_id: str
    merchant_id: str
    customer_id: str
    source_event_id: str
    event_type: EventType
    amount: Money
    currency: str
    source: EventSource
    idempotency_key: str
    occurred_at: str
    observed_at: str = field(default_factory=current_iso_timestamp)
    raw_payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryOpportunity:
    """Core domain object representing a potentially recoverable revenue event."""

    opportunity_id: str
    merchant_id: str
    customer_id: str
    source_event_id: str
    event_type: EventType
    amount: Money
    currency: str
    status: OpportunityStatus
    source: EventSource
    occurred_at: str
    observed_at: str
    created_at: str = field(default_factory=current_iso_timestamp)
    updated_at: str = field(default_factory=current_iso_timestamp)
    context_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for persistence/serialization."""
        return {
            "opportunity_id": self.opportunity_id,
            "merchant_id": self.merchant_id,
            "customer_id": self.customer_id,
            "source_event_id": self.source_event_id,
            "event_type": self.event_type.value,
            "amount_paise": self.amount.amount_paise,
            "currency": self.currency,
            "status": self.status.value,
            "source": self.source.value,
            "occurred_at": self.occurred_at,
            "observed_at": self.observed_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "context_data": self.context_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecoveryOpportunity":
        """Reconstruct model from dictionary."""
        return cls(
            opportunity_id=data["opportunity_id"],
            merchant_id=data["merchant_id"],
            customer_id=data["customer_id"],
            source_event_id=data["source_event_id"],
            event_type=EventType(data["event_type"]),
            amount=Money(int(data["amount_paise"])),
            currency=data["currency"],
            status=OpportunityStatus(data["status"]),
            source=EventSource(data["source"]),
            occurred_at=data["occurred_at"],
            observed_at=data["observed_at"],
            created_at=data.get("created_at", current_iso_timestamp()),
            updated_at=data.get("updated_at", current_iso_timestamp()),
            context_data=data.get("context_data", {}),
        )


@dataclass
class CustomerContactBudget:
    """Customer-level contact cap and reservation counter state.

    INVARIANT: reserved_count + consumed_count <= cap
    """

    merchant_id: str
    customer_id: str
    cap: int
    reserved_count: int = 0
    consumed_count: int = 0
    updated_at: str = field(default_factory=current_iso_timestamp)

    @property
    def total_active_slots(self) -> int:
        """Return total active + consumed contact slots."""
        return self.reserved_count + self.consumed_count

    @property
    def available_slots(self) -> int:
        """Return remaining contact slots under the monthly cap."""
        return max(0, self.cap - self.total_active_slots)

    def is_cap_exhausted(self) -> bool:
        """Check if contact budget is exhausted."""
        return self.total_active_slots >= self.cap


@dataclass(frozen=True)
class EventLog:
    """Ingested event record."""

    event_id: str
    merchant_id: str
    source_event_id: str
    event_type: EventType
    source: EventSource
    payload_json: str
    idempotency_key: str
    created_at: str = field(default_factory=current_iso_timestamp)


@dataclass
class ContactLedgerEntry:
    """Durable ledger record for an individual contact intervention attempt."""

    ledger_id: str
    merchant_id: str
    customer_id: str
    opportunity_id: str
    action_type: ActionType
    intervention_idempotency_key: str
    status: LedgerStatus
    created_at: str = field(default_factory=current_iso_timestamp)
    updated_at: str = field(default_factory=current_iso_timestamp)
    attempted_at: Optional[str] = None
    resolved_at: Optional[str] = None
    metadata_json: str = "{}"

    def is_terminal(self) -> bool:
        """Return True if entry is in a terminal state."""
        return self.status in (
            LedgerStatus.EXECUTED,
            LedgerStatus.FAILED_CLOSED,
            LedgerStatus.RECONCILED_DELIVERED,
            LedgerStatus.RECONCILED_NOT_SENT,
            LedgerStatus.RECONCILED_UNRESOLVED,
            LedgerStatus.RELEASED,
            LedgerStatus.EXPIRED,
        )


# ------------------------------------------------------------------
# Milestone M4 Models
# ------------------------------------------------------------------


@dataclass(frozen=True)
class Stage0Result:
    """Explicit Stage 0 recoverability evaluation output."""

    decision: Stage0Decision
    reason_code: Stage0Reason
    evidence: Dict[str, Any]
    evaluated_at: str
    # Amount genuinely chaseable, where that is LESS than the opportunity's face amount.
    # Set by the TDS derivation on a B2B receivable whose shortfall is partly statutory
    # withholding: the engine must chase the excess only, never the exchequer's share.
    # None means "no restatement" - the full amount stands.
    recoverable_amount_paise: Optional[int] = None

    @property
    def is_recoverable(self) -> bool:
        """Return True if opportunity is genuinely recoverable."""
        return self.decision == Stage0Decision.VALID_RECOVERY


@dataclass(frozen=True)
class DiagnosisResult:
    """Structured Stage 1 failure context diagnosis."""

    diagnosis_code: DiagnosisCode
    evidence: Dict[str, Any]
    confidence: float
    observed_at: str


@dataclass(frozen=True)
class ActionCandidate:
    """Inspected candidate action with safety eligibility status."""

    action_type: ActionType
    eligibility: EligibilityStatus
    reject_reason: SafetyRejectReason
    reason_explanation: str
    evidence: Dict[str, Any]
    is_counterfactual: bool = False

    @property
    def is_eligible(self) -> bool:
        """Return True if action candidate is eligible for AI evaluation/arbitration."""
        return self.eligibility == EligibilityStatus.ELIGIBLE


@dataclass(frozen=True)
class RecoveryDecisionContext:
    """Clean decision surface contract handed off from M4 to M5 AI Scorer.

    INVARIANT: M4 prepares context but DOES NOT reserve or consume contact slots.
    """

    opportunity: RecoveryOpportunity
    stage0_result: Stage0Result
    diagnosis: DiagnosisResult
    candidates: List[ActionCandidate]
    decision_timestamp: str
    feature_snapshot: Dict[str, Any]
    provenance: DataProvenance
    is_contact_reserved: bool = False
    # Compliant-escalation working: the ladder, the ceiling this decision was allowed to
    # reach, and why. Carried on the context so the audit trail shows the bound that was
    # applied BEFORE scoring, not a rationalisation after it. None where not evaluated.
    escalation: Optional[Any] = None

    def get_eligible_candidates(self) -> List[ActionCandidate]:
        """Return subset of candidates that passed hard safety filter."""
        return [c for c in self.candidates if c.is_eligible]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context deterministically for audit and golden testing."""
        return {
            "opportunity": self.opportunity.to_dict(),
            "stage0_result": {
                "decision": self.stage0_result.decision.value,
                "reason_code": self.stage0_result.reason_code.value,
                "evidence": self.stage0_result.evidence,
                "evaluated_at": self.stage0_result.evaluated_at,
                "recoverable_amount_paise": self.stage0_result.recoverable_amount_paise,
            },
            "diagnosis": {
                "diagnosis_code": self.diagnosis.diagnosis_code.value,
                "evidence": self.diagnosis.evidence,
                "confidence": self.diagnosis.confidence,
                "observed_at": self.diagnosis.observed_at,
            },
            "candidates": [
                {
                    "action_type": c.action_type.value,
                    "eligibility": c.eligibility.value,
                    "reject_reason": c.reject_reason.value,
                    "reason_explanation": c.reason_explanation,
                    "evidence": c.evidence,
                    "is_counterfactual": c.is_counterfactual,
                }
                for c in self.candidates
            ],
            "decision_timestamp": self.decision_timestamp,
            "feature_snapshot": self.feature_snapshot,
            "provenance": self.provenance.value,
            "is_contact_reserved": self.is_contact_reserved,
            "escalation": self.escalation.to_dict() if self.escalation is not None else None,
        }


# ------------------------------------------------------------------
# Milestone M5 Additions
# ------------------------------------------------------------------


@dataclass(frozen=True)
class CandidateScore:
    """Detailed S-learner probability, incremental effect, and EV score for a single candidate."""

    action_type: ActionType
    eligibility: EligibilityStatus
    raw_probability: float  # P(Y=1 | X=x, A=a)
    baseline_probability: float  # P(Y=1 | X=x, A=NO_ACTION)
    incremental_effect: float  # P(Y=1|X,a) - P(Y=1|X,NO_ACTION)
    incremental_value_paise: int  # round(incremental_effect * amount_paise)
    action_cost_paise: int
    expected_value_paise: int  # incremental_value_paise - action_cost_paise
    is_eligible: bool
    reject_reason: SafetyRejectReason = SafetyRejectReason.NONE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "eligibility": self.eligibility.value,
            "raw_probability": round(self.raw_probability, 6),
            "baseline_probability": round(self.baseline_probability, 6),
            "incremental_effect": round(self.incremental_effect, 6),
            "incremental_value_paise": self.incremental_value_paise,
            "action_cost_paise": self.action_cost_paise,
            "expected_value_paise": self.expected_value_paise,
            "is_eligible": self.is_eligible,
            "reject_reason": self.reject_reason.value,
        }


@dataclass(frozen=True)
class AIRecoveryDecision:
    """Structured AI recovery decision produced by M5 AI Decision Engine.

    INVARIANT: M5 produces this decision record, but DOES NOT reserve contact slots or execute payments (M6 responsibility).
    """

    decision_id: str
    merchant_id: str
    opportunity_id: str
    customer_id: str
    selected_action: ActionType
    decision_mode: DecisionMode  # EXPLOIT | EXPLORE | SAFE_ABSTENTION
    model_version: str
    decision_timestamp: str
    baseline_probability: float
    selected_action_score: Optional[CandidateScore]
    candidate_scores: List[CandidateScore]
    abstention_reason: AbstentionReason = AbstentionReason.NONE
    provenance: DataProvenance = DataProvenance.SIMULATED_EXTERNAL_STATE
    exploration_epsilon: float = 0.05
    random_seed: Optional[int] = None
    is_contact_reserved: bool = False  # Always False in M5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "merchant_id": self.merchant_id,
            "opportunity_id": self.opportunity_id,
            "customer_id": self.customer_id,
            "selected_action": self.selected_action.value,
            "decision_mode": self.decision_mode.value,
            "model_version": self.model_version,
            "decision_timestamp": self.decision_timestamp,
            "baseline_probability": round(self.baseline_probability, 6),
            "selected_action_score": (
                self.selected_action_score.to_dict() if self.selected_action_score else None
            ),
            "candidate_scores": [cs.to_dict() for cs in self.candidate_scores],
            "abstention_reason": self.abstention_reason.value,
            "provenance": self.provenance.value,
            "exploration_epsilon": self.exploration_epsilon,
            "random_seed": self.random_seed,
            "is_contact_reserved": self.is_contact_reserved,
        }


# ------------------------------------------------------------------
# Milestone M6 Additions
# ------------------------------------------------------------------


@dataclass(frozen=True)
class SandboxActionRequest:
    """Request contract for executing a candidate recovery action in the M6 sandbox."""

    action_id: str
    decision_id: str
    merchant_id: str
    customer_id: str
    opportunity_id: str
    action_type: ActionType
    amount_paise: int
    requested_at: str
    idempotency_key: str
    # Failure context, so the sandbox outcome model can express diagnosis x channel
    # interaction. None reproduces the previous context-free behaviour exactly.
    diagnosis_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "decision_id": self.decision_id,
            "merchant_id": self.merchant_id,
            "customer_id": self.customer_id,
            "opportunity_id": self.opportunity_id,
            "action_type": self.action_type.value,
            "amount_paise": self.amount_paise,
            "requested_at": self.requested_at,
            "idempotency_key": self.idempotency_key,
        }


@dataclass(frozen=True)
class SandboxExecutionResult:
    """Result of sandbox intervention execution."""

    execution_id: str
    action_id: str
    decision_id: str
    opportunity_id: str
    merchant_id: str
    customer_id: str
    action_type: ActionType
    execution_status: ExecutionStatus  # EXECUTED | FAILED_CLOSED | EXECUTION_UNKNOWN
    payment_outcome: PaymentOutcome  # PAYMENT_SUCCESS | PAYMENT_FAILED | NO_PAYMENT | EXECUTION_UNKNOWN | SELF_CURED
    executed_at: str
    delivered_at: Optional[str] = None
    failure_reason: Optional[str] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)
    provenance: DataProvenance = DataProvenance.SIMULATED_EXTERNAL_STATE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "action_id": self.action_id,
            "decision_id": self.decision_id,
            "opportunity_id": self.opportunity_id,
            "merchant_id": self.merchant_id,
            "customer_id": self.customer_id,
            "action_type": self.action_type.value,
            "execution_status": self.execution_status.value,
            "payment_outcome": self.payment_outcome.value,
            "executed_at": self.executed_at,
            "delivered_at": self.delivered_at,
            "failure_reason": self.failure_reason,
            "raw_response": self.raw_response,
            "provenance": self.provenance.value,
        }


@dataclass(frozen=True)
class RecoveryAttribution:
    """Structured attribution record linking payment recovery to intervention causality."""

    attribution_id: str
    opportunity_id: str
    merchant_id: str
    customer_id: str
    decision_id: str
    ledger_id: Optional[str]
    execution_id: Optional[str]
    selected_action: ActionType
    attribution_status: AttributionStatus  # SELF_CURED | RECOVERED | FAILED_UNRECOVERED | PENDING
    payment_outcome: PaymentOutcome
    gross_recovered_paise: int  # Actual simulated payment amount recovered
    attributed_recovered_paise: int  # ₹0 for SELF_CURED, equal to gross if attributed intervention
    amount_at_risk_paise: int
    evaluated_at: str
    delivered_at: Optional[str] = None
    payment_at: Optional[str] = None
    explanation: str = ""

    @property
    def is_self_cured(self) -> bool:
        return self.attribution_status == AttributionStatus.SELF_CURED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attribution_id": self.attribution_id,
            "opportunity_id": self.opportunity_id,
            "merchant_id": self.merchant_id,
            "customer_id": self.customer_id,
            "decision_id": self.decision_id,
            "ledger_id": self.ledger_id,
            "execution_id": self.execution_id,
            "selected_action": self.selected_action.value,
            "attribution_status": self.attribution_status.value,
            "payment_outcome": self.payment_outcome.value,
            "gross_recovered_paise": self.gross_recovered_paise,
            "attributed_recovered_paise": self.attributed_recovered_paise,
            "amount_at_risk_paise": self.amount_at_risk_paise,
            "evaluated_at": self.evaluated_at,
            "delivered_at": self.delivered_at,
            "payment_at": self.payment_at,
            "explanation": self.explanation,
            "is_self_cured": self.is_self_cured,
        }


@dataclass(frozen=True)
class RecoveryObservation:
    """Structured observation record captured for future experiment analysis (M7 preparation)."""

    observation_id: str
    experiment_id: str
    arm: str
    opportunity_id: str
    merchant_id: str
    customer_id: str
    decision_id: str
    selected_action: ActionType
    outcome: PaymentOutcome
    amount_at_risk_paise: int
    gross_recovered_paise: int
    attributed_recovered_paise: int
    self_cured: bool
    decision_timestamp: str
    outcome_timestamp: str
    model_version: str
    provenance: DataProvenance = DataProvenance.SIMULATED_EXTERNAL_STATE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "experiment_id": self.experiment_id,
            "arm": self.arm,
            "opportunity_id": self.opportunity_id,
            "merchant_id": self.merchant_id,
            "customer_id": self.customer_id,
            "decision_id": self.decision_id,
            "selected_action": self.selected_action.value,
            "outcome": self.outcome.value,
            "amount_at_risk_paise": self.amount_at_risk_paise,
            "gross_recovered_paise": self.gross_recovered_paise,
            "attributed_recovered_paise": self.attributed_recovered_paise,
            "self_cured": self.self_cured,
            "decision_timestamp": self.decision_timestamp,
            "outcome_timestamp": self.outcome_timestamp,
            "model_version": self.model_version,
            "provenance": self.provenance.value,
        }


@dataclass(frozen=True)
class EndToEndRecoveryResult:
    """Complete closed-loop recovery result containing full correlation trace."""

    opportunity_id: str
    merchant_id: str
    customer_id: str
    event_id: str
    decision: AIRecoveryDecision
    ledger_entry: Optional[ContactLedgerEntry]
    execution_result: Optional[SandboxExecutionResult]
    attribution: RecoveryAttribution
    observation: RecoveryObservation
    trace_id: str
    # Which of the four unified streams this opportunity came from. Carried on the
    # result so a batch can prove stream coverage rather than assert it.
    event_type: EventType = EventType.FAILED_PAYMENT
    # The escalation ceiling that bound this decision, and what it removed. Carried so a
    # batch can report how often compliant escalation actually held intensity down -
    # a control nobody can count is not an auditable control.
    escalation: Optional[Any] = None

    @property
    def event_type_value(self) -> str:
        return self.event_type.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "opportunity_id": self.opportunity_id,
            "merchant_id": self.merchant_id,
            "customer_id": self.customer_id,
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "escalation": self.escalation.to_dict() if self.escalation is not None else None,
            "decision": self.decision.to_dict(),
            "ledger_entry": self.ledger_entry.to_dict() if self.ledger_entry else None,
            "execution_result": self.execution_result.to_dict() if self.execution_result else None,
            "attribution": self.attribution.to_dict(),
            "observation": self.observation.to_dict(),
        }


# ------------------------------------------------------------------
# Milestone M7 Additions
# ------------------------------------------------------------------


@dataclass(frozen=True)
class TrainingRecord:
    """Feedback dataset training tuple (X=features, A=action, Y=observed outcome).
    
    INVARIANT (INV-7): Feature vector X contains ONLY point-in-time features prior to decision_timestamp.
    """

    record_id: str
    experiment_id: str
    arm: ExperimentArm
    merchant_id: str
    customer_id: str
    opportunity_id: str
    decision_timestamp: str
    features: Dict[str, Any]  # X: Point-in-time features
    selected_action: ActionType  # A: Action
    observed_outcome: PaymentOutcome  # Y: Observed outcome label
    gross_recovered_paise: int
    attributed_recovered_paise: int
    self_cured: bool
    model_version: str
    provenance: DataProvenance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "experiment_id": self.experiment_id,
            "arm": self.arm.value,
            "merchant_id": self.merchant_id,
            "customer_id": self.customer_id,
            "opportunity_id": self.opportunity_id,
            "decision_timestamp": self.decision_timestamp,
            "features": self.features,
            "selected_action": self.selected_action.value,
            "observed_outcome": self.observed_outcome.value,
            "gross_recovered_paise": self.gross_recovered_paise,
            "attributed_recovered_paise": self.attributed_recovered_paise,
            "self_cured": self.self_cured,
            "model_version": self.model_version,
            "provenance": self.provenance.value,
        }


@dataclass(frozen=True)
class ArmMetrics:
    """Aggregated evaluation metrics for a specific experiment arm."""

    arm: ExperimentArm
    total_opportunities: int
    successful_recoveries: int
    recovery_rate: float
    gross_recovered_paise: int
    attributed_recovered_paise: int
    self_cured_count: int
    total_cost_paise: int
    net_value_paise: int
    contact_cap_breaches: int = 0
    abstention_count: int = 0

    # --- CONTACT EFFICIENCY -------------------------------------------------
    # The engine's thesis is "one customer, one message" - comparable recovery
    # for materially fewer customer contacts. Measured on recovery rate ALONE,
    # every safety feature can only ever look worse, because each one suppresses
    # a contact. These fields are what make the trade-off visible.
    outbound_contacts: int = 0          # customer-facing messages actually sent
    contacted_customers: int = 0        # distinct customers contacted at least once
    total_customers: int = 0            # distinct customers in the arm

    # --- MONEY AT RISK ------------------------------------------------------
    # Track 3 requires the batch to be reported as "Rs recovered vs Rs at risk,
    # recovery rate, and cost per recovery". Rupees recovered without the
    # denominator it was recovered FROM is not a recovery claim, it is a number.
    total_at_risk_paise: int = 0        # sum of amount_at_risk over every opportunity

    # --- COMPLIANT ESCALATION (ADR-0015) ------------------------------------
    # "Compliant escalation" is named in the Track 3 bar. These are the counts that
    # make it auditable rather than merely claimed.
    escalation_suppressed_count: int = 0   # decisions where the ceiling removed a candidate
    earned_escalations: int = 0            # contacts sent ABOVE their stream's entry rung

    # --- STREAM COVERAGE ----------------------------------------------------
    # Opportunity count per EventType. The engine claims to unify four streams;
    # this is the evidence that a batch actually exercised more than one.
    stream_counts: Dict[str, int] = field(default_factory=dict)

    @property
    def value_recovery_rate(self) -> float:
        """Share of rupees AT RISK that were recovered and attributed to an intervention.

        Distinct from `recovery_rate`, which counts opportunities. A batch can recover
        most cases while recovering little money, or the reverse; both are reported.
        """
        return self.attributed_recovered_paise / self.total_at_risk_paise if self.total_at_risk_paise else 0.0

    @property
    def cost_per_recovery_paise(self) -> float:
        """Intervention spend per successful recovery. Lower is better.

        Denominator is successful recoveries, not opportunities: this answers "what did
        each recovery cost us", which is the figure the Track 3 floor names.
        """
        return self.total_cost_paise / self.successful_recoveries if self.successful_recoveries else 0.0

    @property
    def contacts_per_customer(self) -> float:
        """Average outbound contacts per distinct customer. Lower is better."""
        return self.outbound_contacts / self.total_customers if self.total_customers else 0.0

    @property
    def recovery_per_contact_paise(self) -> float:
        """Attributed recovery earned per outbound contact. Higher is better."""
        return self.attributed_recovered_paise / self.outbound_contacts if self.outbound_contacts else 0.0

    @property
    def contact_rate(self) -> float:
        """Share of opportunities that resulted in an outbound contact."""
        return self.outbound_contacts / self.total_opportunities if self.total_opportunities else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arm": self.arm.value,
            "total_opportunities": self.total_opportunities,
            "successful_recoveries": self.successful_recoveries,
            "recovery_rate": self.recovery_rate,
            "gross_recovered_paise": self.gross_recovered_paise,
            "attributed_recovered_paise": self.attributed_recovered_paise,
            "self_cured_count": self.self_cured_count,
            "total_cost_paise": self.total_cost_paise,
            "net_value_paise": self.net_value_paise,
            "contact_cap_breaches": self.contact_cap_breaches,
            "abstention_count": self.abstention_count,
            "outbound_contacts": self.outbound_contacts,
            "contacted_customers": self.contacted_customers,
            "total_customers": self.total_customers,
            "contacts_per_customer": round(self.contacts_per_customer, 4),
            "recovery_per_contact_paise": round(self.recovery_per_contact_paise, 2),
            "contact_rate": round(self.contact_rate, 4),
            "total_at_risk_paise": self.total_at_risk_paise,
            "escalation_suppressed_count": self.escalation_suppressed_count,
            "earned_escalations": self.earned_escalations,
            "value_recovery_rate": round(self.value_recovery_rate, 6),
            "cost_per_recovery_paise": round(self.cost_per_recovery_paise, 2),
            "stream_counts": dict(self.stream_counts),
        }


@dataclass(frozen=True)
class StatisticalComparison:
    """Statistical comparison between a treatment arm and control/baseline arm."""

    comparison_id: str
    treatment_arm: ExperimentArm
    baseline_arm: ExperimentArm
    treatment_recovery_rate: float
    baseline_recovery_rate: float
    incremental_recovery_rate: float  # Treatment rate - Baseline rate
    relative_lift: float  # (Treatment rate - Baseline rate) / Baseline rate
    gross_incremental_revenue_paise: int
    net_incremental_value_paise: int
    confidence_interval_95: Tuple[float, float]
    p_value: float
    status: StatisticalStatus
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "treatment_arm": self.treatment_arm.value,
            "baseline_arm": self.baseline_arm.value,
            "treatment_recovery_rate": self.treatment_recovery_rate,
            "baseline_recovery_rate": self.baseline_recovery_rate,
            "incremental_recovery_rate": self.incremental_recovery_rate,
            "relative_lift": self.relative_lift,
            "gross_incremental_revenue_paise": self.gross_incremental_revenue_paise,
            "net_incremental_value_paise": self.net_incremental_value_paise,
            "confidence_interval_95": list(self.confidence_interval_95),
            "p_value": self.p_value,
            "status": self.status.value,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class ExperimentResultSummary:
    """Full machine-readable and human-readable result of an executed experiment."""

    experiment_id: str
    timestamp: str
    commit_hash: str
    dataset_version: str
    model_version: str
    simulator_version: str
    random_seed: int
    sample_size: int
    arm_metrics: Dict[str, ArmMetrics]
    primary_comparison: StatisticalComparison
    secondary_comparisons: List[StatisticalComparison]
    provenance: DataProvenance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "timestamp": self.timestamp,
            "commit_hash": self.commit_hash,
            "dataset_version": self.dataset_version,
            "model_version": self.model_version,
            "simulator_version": self.simulator_version,
            "random_seed": self.random_seed,
            "sample_size": self.sample_size,
            "arm_metrics": {k: v.to_dict() for k, v in self.arm_metrics.items()},
            "primary_comparison": self.primary_comparison.to_dict(),
            "secondary_comparisons": [c.to_dict() for c in self.secondary_comparisons],
            "provenance": self.provenance.value,
        }



