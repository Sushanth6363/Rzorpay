"""Domain models for Unified Recovery Engine.

Defines core business entities (RecoveryOpportunity, CustomerContactBudget, EventLog, CanonicalEvent,
ContactLedgerEntry, Stage0Result, DiagnosisResult, ActionCandidate, RecoveryDecisionContext)
using clean type-annotated dataclasses.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
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
        }
