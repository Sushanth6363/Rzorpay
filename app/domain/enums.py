"""Domain enumerations for Unified Recovery Engine.

INVARIANT: All enum values use stable uppercase string representations.
Ordinal integer database persistence is strictly forbidden.
"""

from enum import Enum


class EventType(str, Enum):
    """Source event type covering all four unified recovery streams."""

    FAILED_PAYMENT = "FAILED_PAYMENT"
    ABANDONED_CHECKOUT = "ABANDONED_CHECKOUT"
    FAILED_SUBSCRIPTION_RENEWAL = "FAILED_SUBSCRIPTION_RENEWAL"
    OVERDUE_B2B_INVOICE = "OVERDUE_B2B_INVOICE"
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
    RECOMMEND_RETRY = "RECOMMEND_RETRY"


class ExecutionStatus(str, Enum):
    """Execution status for contact slots and transactions."""

    RESERVED = "RESERVED"
    EXECUTION_ATTEMPTED = "EXECUTION_ATTEMPTED"
    EXECUTED = "EXECUTED"
    FAILED_CLOSED = "FAILED_CLOSED"
    EXECUTION_UNKNOWN = "EXECUTION_UNKNOWN"
    RECONCILED_DELIVERED = "RECONCILED_DELIVERED"
    RECONCILED_NOT_SENT = "RECONCILED_NOT_SENT"
    RECONCILED_UNRESOLVED = "RECONCILED_UNRESOLVED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class LedgerStatus(str, Enum):
    """Detailed contact ledger entry status."""

    RESERVED = "RESERVED"
    EXECUTION_ATTEMPTED = "EXECUTION_ATTEMPTED"
    EXECUTED = "EXECUTED"
    FAILED_CLOSED = "FAILED_CLOSED"
    EXECUTION_UNKNOWN = "EXECUTION_UNKNOWN"
    RECONCILED_DELIVERED = "RECONCILED_DELIVERED"
    RECONCILED_NOT_SENT = "RECONCILED_NOT_SENT"
    RECONCILED_UNRESOLVED = "RECONCILED_UNRESOLVED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


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


# ------------------------------------------------------------------
# Milestone M4 Additions
# ------------------------------------------------------------------


class Stage0Decision(str, Enum):
    """Explicit Stage 0 recoverability validation outcome."""

    VALID_RECOVERY = "VALID_RECOVERY"
    NOT_RECOVERABLE = "NOT_RECOVERABLE"


class Stage0Reason(str, Enum):
    """Explainable reason codes for Stage 0 recoverability evaluation."""

    GENUINE_RECOVERABLE = "GENUINE_RECOVERABLE"
    ALREADY_PAID = "ALREADY_PAID"
    SELF_CURED = "SELF_CURED"
    TDS_WITHHOLDING_EXCLUSION = "TDS_WITHHOLDING_EXCLUSION"
    CHECKOUT_COMPLETED = "CHECKOUT_COMPLETED"
    INVOICE_RESOLVED = "INVOICE_RESOLVED"
    OUTSIDE_RECOVERY_WINDOW = "OUTSIDE_RECOVERY_WINDOW"
    KNOWN_NON_RECOVERABLE = "KNOWN_NON_RECOVERABLE"
    INVALID_EVENT = "INVALID_EVENT"
    DUPLICATE_EVENT = "DUPLICATE_EVENT"
    POINT_IN_TIME_LEAKAGE = "POINT_IN_TIME_LEAKAGE"


class DiagnosisCode(str, Enum):
    """Structured failure context diagnosis categories (Stage 1)."""

    GATEWAY_FAILURE = "GATEWAY_FAILURE"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    CARD_DECLINED = "CARD_DECLINED"
    CUSTOMER_ABANDONMENT = "CUSTOMER_ABANDONMENT"
    SUBSCRIPTION_RENEWAL_FAILURE = "SUBSCRIPTION_RENEWAL_FAILURE"
    INVOICE_OVERDUE = "INVOICE_OVERDUE"
    CUSTOMER_UNRESPONSIVE = "CUSTOMER_UNRESPONSIVE"
    UNKNOWN = "UNKNOWN"


class EligibilityStatus(str, Enum):
    """Hard safety eligibility status for candidate recovery actions."""

    ELIGIBLE = "ELIGIBLE"
    SAFETY_REJECTED = "SAFETY_REJECTED"


class SafetyRejectReason(str, Enum):
    """Explicit reasons for hard safety rejection."""

    NONE = "NONE"
    KNOWN_GATEWAY_OUTAGE = "KNOWN_GATEWAY_OUTAGE"
    CONTACT_BUDGET_UNAVAILABLE = "CONTACT_BUDGET_UNAVAILABLE"
    INVALID_OPPORTUNITY = "INVALID_OPPORTUNITY"
    UNSUPPORTED_ACTION = "UNSUPPORTED_ACTION"
    POLICY_PROHIBITION = "POLICY_PROHIBITION"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    EXECUTION_OWNERSHIP_VIOLATION = "EXECUTION_OWNERSHIP_VIOLATION"


class DataProvenance(str, Enum):
    """Provenance classification for evaluation integrity."""

    REAL_DATA = "REAL_DATA"
    SYNTHETIC_DATA = "SYNTHETIC_DATA"
    SIMULATED_EXTERNAL_STATE = "SIMULATED_EXTERNAL_STATE"
