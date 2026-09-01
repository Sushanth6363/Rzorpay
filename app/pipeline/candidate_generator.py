"""Action Candidate Generator for Unified Recovery Engine.

INVARIANT: NO_ACTION is a mandatory first-class counterfactual candidate,
always present in every generated candidate set.
"""

from typing import List, Optional
from app.domain.enums import ActionType, DiagnosisCode, EligibilityStatus, EventType, SafetyRejectReason
from app.domain.models import ActionCandidate, DiagnosisResult, RecoveryOpportunity


class CandidateGenerator:
    """Generates the pool of potential recovery intervention candidates for an opportunity."""

    def generate_candidates(
        self,
        opportunity: RecoveryOpportunity,
        diagnosis: DiagnosisResult,
    ) -> List[ActionCandidate]:
        """Generate full candidate action set based on opportunity stream and diagnosis.

        Returns list of ActionCandidate objects. NO_ACTION is always included as candidate #1.
        """
        candidates: List[ActionCandidate] = []

        # 1. Mandatory Counterfactual Baseline candidate (NO_ACTION)
        candidates.append(
            ActionCandidate(
                action_type=ActionType.NO_ACTION,
                eligibility=EligibilityStatus.ELIGIBLE,
                reject_reason=SafetyRejectReason.NONE,
                reason_explanation="Counterfactual baseline (do nothing).",
                evidence={"is_counterfactual": True},
                is_counterfactual=True,
            )
        )

        # 2. Payment Retry Recommendation candidate
        # Suitable for payment failures, renewal failures, or gateway outage resolution
        if opportunity.event_type in (
            EventType.FAILED_PAYMENT,
            EventType.FAILED_SUBSCRIPTION_RENEWAL,
            EventType.AUTOPAY_FAILURE,
        ):
            candidates.append(
                ActionCandidate(
                    action_type=ActionType.RECOMMEND_RETRY,
                    eligibility=EligibilityStatus.ELIGIBLE,
                    reject_reason=SafetyRejectReason.NONE,
                    reason_explanation="Recommend passive payment retry.",
                    evidence={"diagnosis": diagnosis.diagnosis_code.value},
                    is_counterfactual=False,
                )
            )

        # 3. Direct Customer Communication Link candidates (WhatsApp, SMS, Email)
        candidates.append(
            ActionCandidate(
                action_type=ActionType.WHATSAPP_LINK,
                eligibility=EligibilityStatus.ELIGIBLE,
                reject_reason=SafetyRejectReason.NONE,
                reason_explanation="Send interactive WhatsApp recovery link.",
                evidence={"channel": "WHATSAPP"},
                is_counterfactual=False,
            )
        )

        candidates.append(
            ActionCandidate(
                action_type=ActionType.SMS_LINK,
                eligibility=EligibilityStatus.ELIGIBLE,
                reject_reason=SafetyRejectReason.NONE,
                reason_explanation="Send SMS recovery payment link.",
                evidence={"channel": "SMS"},
                is_counterfactual=False,
            )
        )

        candidates.append(
            ActionCandidate(
                action_type=ActionType.EMAIL_LINK,
                eligibility=EligibilityStatus.ELIGIBLE,
                reject_reason=SafetyRejectReason.NONE,
                reason_explanation="Send email payment reminder with invoice link.",
                evidence={"channel": "EMAIL"},
                is_counterfactual=False,
            )
        )

        # 4. High-Touch Assisted Channel candidates (IVR Call, Agent Dial)
        # Generated for high-value or overdue B2B invoice opportunities
        if opportunity.amount.amount_paise >= 500000 or opportunity.event_type == EventType.OVERDUE_B2B_INVOICE:
            candidates.append(
                ActionCandidate(
                    action_type=ActionType.IVR_CALL,
                    eligibility=EligibilityStatus.ELIGIBLE,
                    reject_reason=SafetyRejectReason.NONE,
                    reason_explanation="Trigger automated IVR payment outbound call.",
                    evidence={"channel": "IVR"},
                    is_counterfactual=False,
                )
            )
            candidates.append(
                ActionCandidate(
                    action_type=ActionType.AGENT_DIAL,
                    eligibility=EligibilityStatus.ELIGIBLE,
                    reject_reason=SafetyRejectReason.NONE,
                    reason_explanation="Queue for high-touch human agent outreach call.",
                    evidence={"channel": "AGENT"},
                    is_counterfactual=False,
                )
            )

        return candidates
