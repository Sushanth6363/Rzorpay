"""Domain enumerations for Unified Recovery Engine.

INVARIANT: All enum values use stable uppercase string representations.
Ordinal integer database persistence is strictly forbidden.
"""

from enum import Enum


class EventType(str, Enum):
    """Source event type."""

    FAILED_PAYMENT = "FAILED_PAYMENT"
    PAYMENT_DOWNTIME = "PAYMENT_DOWNTIME"
    AUTOPAY_FAILURE = "AUTOPAY_FAILURE"
    SIMULATED_FAILURE = "SIMULATED_FAILURE"


class OpportunityStatus(str, Enum):
    """Lifecycle status of a RecoveryOpportunity."""

    NEW = "NEW"
    PENDING_STAGE_0 = "PENDING_STAGE_0"
    STAGE_0_ABSTAINED = "STAGE_0_ABSTAINED"
    STAGE_1_DIAGNOSED = "STAGE_1_DIAGNOSED"
    CANDIDATES_GENERATED = "CANDIDATES_GENERATED"
    ARBITRATED = "ARBITRATED"
    RESERVED = "RESERVED"
    EXECUTED = "EXECUTED"
    EXPIRED = "EXPIRED"
    ATTRIBUTED_RECOVERED = "ATTRIBUTED_RECOVERED"
    ATTRIBUTED_SELF_CURED = "ATTRIBUTED_SELF_CURED"
    ATTRIBUTED_LOST = "ATTRIBUTED_LOST"


class ActionType(str, Enum):
    """Recovery action types (including NO_ACTION counterfactual)."""

    NO_ACTION = "NO_ACTION"
    WHATSAPP_LINK = "WHATSAPP_LINK"
    SMS_LINK = "SMS_LINK"
    EMAIL_LINK = "EMAIL_LINK"
    IVR_CALL = "IVR_CALL"
    AGENT_DIAL = "AGENT_DIAL"


class ExecutionStatus(str, Enum):
    """Execution status for contact slots and transactions."""

    RESERVED = "RESERVED"
    EXECUTED = "EXECUTED"
    EXPIRED = "EXPIRED"
    FAILED_CLOSED = "FAILED_CLOSED"
    RELEASED = "RELEASED"


class AttributionStatus(str, Enum):
    """Final recovery attribution classification."""

    PENDING = "PENDING"
    SELF_CURED = "SELF_CURED"
    RECOVERED = "RECOVERED"
    FAILED_UNRECOVERED = "FAILED_UNRECOVERED"
    EXPIRED_UNRECOVERED = "EXPIRED_UNRECOVERED"


class EventSource(str, Enum):
    """Dual-path ingestion source mode."""

    RAZORPAY_TEST = "RAZORPAY_TEST"
    SIMULATED = "SIMULATED"
