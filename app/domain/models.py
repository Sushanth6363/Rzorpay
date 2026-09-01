"""Domain models for Unified Recovery Engine.

Defines core business entities (RecoveryOpportunity, CustomerContactBudget, EventLog, CanonicalEvent)
using clean type-annotated dataclasses.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from app.domain.enums import EventType, OpportunityStatus, ActionType, ExecutionStatus, AttributionStatus, EventSource
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
