"""Stage 1 — Failure Context Diagnoser for Unified Recovery Engine.

Evaluates failure symptoms and evidence to produce structured, evidence-backed diagnoses.
"""

from typing import Any, Dict, Optional
from app.clock import Clock, SystemClock
from app.domain.enums import DiagnosisCode, EventType
from app.domain.models import DiagnosisResult, RecoveryOpportunity
from app.pipeline.downtime import DowntimeProvider


class Stage1Diagnoser:
    """Diagnoses root cause failure category from opportunity event context and downtime signals."""

    def __init__(self, downtime_provider: Optional[DowntimeProvider] = None, clock: Optional[Clock] = None) -> None:
        self.downtime_provider = downtime_provider
        self.clock = clock or SystemClock()

    def diagnose(
        self,
        opportunity: RecoveryOpportunity,
        decision_timestamp: Optional[str] = None,
        context_state: Optional[Dict[str, Any]] = None,
    ) -> DiagnosisResult:
        """Diagnose failure context for a RecoveryOpportunity.

        Returns DiagnosisResult with diagnosis_code, evidence, confidence, and observed_at.
        """
        obs_time = decision_timestamp or self.clock.now_iso()
        context = context_state or opportunity.context_data or {}

        gateway_name = context.get("gateway", context.get("bank", "razorpay"))
        method = context.get("method", context.get("payment_method"))
        raw_reason = str(context.get("failure_reason", context.get("error_code", ""))).upper()

        # 1. Gateway Downtime Outage Detection (Mandatory Safety Check)
        if self.downtime_provider and self.downtime_provider.is_gateway_down(gateway_name, method, obs_time):
            return DiagnosisResult(
                diagnosis_code=DiagnosisCode.GATEWAY_FAILURE,
                evidence={
                    "gateway": gateway_name,
                    "method": method,
                    "is_gateway_down": True,
                    "raw_reason": raw_reason or "GATEWAY_OUTAGE",
                },
                confidence=1.0,
                observed_at=obs_time,
            )

        # 2. Stream-Specific or Reason-Specific Rule Evaluation

        # Check explicit error codes
        if "INSUFFICIENT" in raw_reason or "LOW_BALANCE" in raw_reason or raw_reason == "BAD_REQUEST_PAYMENT_LESS_THAN_MIN_AMOUNT":
            return DiagnosisResult(
                diagnosis_code=DiagnosisCode.INSUFFICIENT_FUNDS,
                evidence={"raw_reason": raw_reason},
                confidence=0.95,
                observed_at=obs_time,
            )

        if "DECLINED" in raw_reason or "EXPIRED" in raw_reason or "CARD" in raw_reason or "LIMIT_EXCEEDED" in raw_reason:
            return DiagnosisResult(
                diagnosis_code=DiagnosisCode.CARD_DECLINED,
                evidence={"raw_reason": raw_reason},
                confidence=0.90,
                observed_at=obs_time,
            )

        if "GATEWAY" in raw_reason or "TIMEOUT" in raw_reason or "BANK_DOWN" in raw_reason:
            return DiagnosisResult(
                diagnosis_code=DiagnosisCode.GATEWAY_FAILURE,
                evidence={"raw_reason": raw_reason},
                confidence=0.90,
                observed_at=obs_time,
            )

        # Stream defaults if error code is missing or generic
        if opportunity.event_type == EventType.ABANDONED_CHECKOUT:
            return DiagnosisResult(
                diagnosis_code=DiagnosisCode.CUSTOMER_ABANDONMENT,
                evidence={"event_type": opportunity.event_type.value},
                confidence=0.85,
                observed_at=obs_time,
            )

        if opportunity.event_type in (EventType.FAILED_SUBSCRIPTION_RENEWAL, EventType.AUTOPAY_FAILURE):
            return DiagnosisResult(
                diagnosis_code=DiagnosisCode.SUBSCRIPTION_RENEWAL_FAILURE,
                evidence={"event_type": opportunity.event_type.value, "raw_reason": raw_reason},
                confidence=0.85,
                observed_at=obs_time,
            )

        if opportunity.event_type == EventType.OVERDUE_B2B_INVOICE:
            return DiagnosisResult(
                diagnosis_code=DiagnosisCode.INVOICE_OVERDUE,
                evidence={"event_type": opportunity.event_type.value},
                confidence=0.90,
                observed_at=obs_time,
            )

        # Default fallback
        return DiagnosisResult(
            diagnosis_code=DiagnosisCode.UNKNOWN,
            evidence={"raw_reason": raw_reason or "UNSPECIFIED"},
            confidence=0.50,
            observed_at=obs_time,
        )
