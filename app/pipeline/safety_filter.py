"""Hard Safety Eligibility Filter for Unified Recovery Engine.

INVARIANTS:
1. INV-4: Gateway downtime suppresses retries and customer outreach.
2. ADR-0003: Exhausted contact budget suppresses contact interventions.
3. ADR-0006: Retry ownership stays outside engine (RECOMMEND_RETRY only, never execute).
4. SAFETY ABSTENTION: Candidates marked SAFETY_REJECTED cannot be overridden by AI exploration.
"""

from typing import List, Optional
from app.domain.enums import ActionType, DiagnosisCode, EligibilityStatus, SafetyRejectReason
from app.domain.models import ActionCandidate, CustomerContactBudget, DiagnosisResult, RecoveryOpportunity
from app.pipeline.downtime import DowntimeProvider


class HardSafetyFilter:
    """Evaluates candidate action set against hard safety constraints."""

    def filter_candidates(
        self,
        opportunity: RecoveryOpportunity,
        diagnosis: DiagnosisResult,
        candidates: List[ActionCandidate],
        contact_budget: Optional[CustomerContactBudget] = None,
        downtime_provider: Optional[DowntimeProvider] = None,
    ) -> List[ActionCandidate]:
        """Apply non-negotiable safety rules to mark candidates ELIGIBLE or SAFETY_REJECTED."""
        filtered: List[ActionCandidate] = []

        # Check downtime status
        gateway_name = opportunity.context_data.get("gateway", "razorpay")
        method = opportunity.context_data.get("method")
        # INV-4 SAFETY FLOOR: a GATEWAY_FAILURE diagnosis suppresses on its own. This is a
        # safety property and is NEVER relaxed to make an experiment measurable.
        is_downtime = diagnosis.diagnosis_code == DiagnosisCode.GATEWAY_FAILURE

        # ADDITIONAL CAPABILITY (D2, ADR-0011): the downtime SIGNAL reveals outages the error
        # code does not. Its value shows on failures reported with an ordinary code that
        # nonetheless occur inside an outage window - an arm without the signal is blind to
        # those and acts; an arm with it suppresses. That difference is the A3 vs A2 measurement.
        if downtime_provider and downtime_provider.is_gateway_down(gateway_name, method, diagnosis.observed_at):
            is_downtime = True

        # Check budget status
        is_budget_exhausted = contact_budget.is_cap_exhausted() if contact_budget else False

        for candidate in candidates:
            # 1. NO_ACTION is ALWAYS ELIGIBLE (Counterfactual Safety Anchor)
            if candidate.action_type == ActionType.NO_ACTION:
                filtered.append(
                    ActionCandidate(
                        action_type=ActionType.NO_ACTION,
                        eligibility=EligibilityStatus.ELIGIBLE,
                        reject_reason=SafetyRejectReason.NONE,
                        reason_explanation="Counterfactual baseline is always safe and eligible.",
                        evidence=candidate.evidence,
                        is_counterfactual=True,
                    )
                )
                continue

            # 2. Rule 1: Gateway Downtime Outage Suppression (INV-4)
            if is_downtime and candidate.action_type in (
                ActionType.RECOMMEND_RETRY,
                ActionType.WHATSAPP_LINK,
                ActionType.SMS_LINK,
                ActionType.EMAIL_LINK,
                ActionType.IVR_CALL,
                ActionType.AGENT_DIAL,
            ):
                filtered.append(
                    ActionCandidate(
                        action_type=candidate.action_type,
                        eligibility=EligibilityStatus.SAFETY_REJECTED,
                        reject_reason=SafetyRejectReason.KNOWN_GATEWAY_OUTAGE,
                        reason_explanation=f"Action '{candidate.action_type.value}' rejected due to active gateway downtime outage.",
                        evidence={"gateway": gateway_name, "is_downtime": True},
                        is_counterfactual=False,
                    )
                )
                continue

            # 3. Rule 2: Contact Budget Cap Exhaustion (ADR-0003)
            # Outbound customer contact channels require available contact slot
            if is_budget_exhausted and candidate.action_type in (
                ActionType.WHATSAPP_LINK,
                ActionType.SMS_LINK,
                ActionType.EMAIL_LINK,
                ActionType.IVR_CALL,
                ActionType.AGENT_DIAL,
            ):
                filtered.append(
                    ActionCandidate(
                        action_type=candidate.action_type,
                        eligibility=EligibilityStatus.SAFETY_REJECTED,
                        reject_reason=SafetyRejectReason.CONTACT_BUDGET_UNAVAILABLE,
                        reason_explanation=f"Action '{candidate.action_type.value}' rejected because customer contact budget cap is exhausted.",
                        evidence={"reserved": contact_budget.reserved_count, "consumed": contact_budget.consumed_count, "cap": contact_budget.cap},
                        is_counterfactual=False,
                    )
                )
                continue

            # 4. Action Passed Hard Safety Filter
            filtered.append(
                ActionCandidate(
                    action_type=candidate.action_type,
                    eligibility=EligibilityStatus.ELIGIBLE,
                    reject_reason=SafetyRejectReason.NONE,
                    reason_explanation=f"Action '{candidate.action_type.value}' passed all hard safety checks.",
                    evidence=candidate.evidence,
                    is_counterfactual=False,
                )
            )

        return filtered
