"""Point-in-Time Safe Feature Builder for M5 AI Scorer (INV-7).

INVARIANTS:
1. INV-7: observed_at <= decision_timestamp. Any feature observed after decision_timestamp raises PointInTimeLeakageError.
2. INV-1: merchant_id is strictly excluded from model feature vector to prevent tenant bias.
3. No post-decision information (outcomes, delivery timestamps) allowed in feature vectors.
"""

import math
from typing import Any, Dict, List, Optional
from app.domain.enums import ActionType
from app.domain.models import ActionCandidate, RecoveryDecisionContext, RecoveryOpportunity


class PointInTimeLeakageError(ValueError):
    """Raised when a feature or observation violates point-in-time safety (INV-7)."""

    pass


DENYLISTED_LEAKAGE_FIELDS = {
    "outcome",
    "recovered",
    "delivered_at",
    "attribution_status",
    "post_decision_events",
    "recovered_at",
    "actual_recovery",
}


class FeatureBuilder:
    """Constructs point-in-time safe feature vectors for CatBoost S-learner model."""

    @staticmethod
    def validate_point_in_time_safety(
        observed_at: str,
        decision_timestamp: str,
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Validate point-in-time safety invariant (observed_at <= decision_timestamp)."""
        if observed_at and decision_timestamp and observed_at > decision_timestamp:
            raise PointInTimeLeakageError(
                f"Point-in-Time Safety Violation (INV-7): Feature observed_at ('{observed_at}') "
                f"is strictly after decision_timestamp ('{decision_timestamp}'). Future leakage is forbidden."
            )

        if extra_fields:
            for field in DENYLISTED_LEAKAGE_FIELDS:
                if field in extra_fields:
                    raise PointInTimeLeakageError(
                        f"Point-in-Time Safety Violation (INV-7): Denylisted post-decision field "
                        f"'{field}' detected in feature input."
                    )

    @classmethod
    def build_feature_dict(
        self,
        context: RecoveryDecisionContext,
        candidate_action: ActionType,
    ) -> Dict[str, Any]:
        """Construct feature dictionary for (Context, Action) tuple.
        
        S-Learner Design: Action is encoded as an explicit feature alongside context features (X + A).
        """
        # Validate point-in-time safety on snapshot and diagnosis
        self.validate_point_in_time_safety(
            observed_at=context.opportunity.observed_at,
            decision_timestamp=context.decision_timestamp,
            extra_fields=context.opportunity.context_data,
        )

        amount_paise = context.opportunity.amount.amount_paise

        return {
            "event_type": context.opportunity.event_type.value,
            "diagnosis_code": context.diagnosis.diagnosis_code.value,
            "diagnosis_confidence": float(context.diagnosis.confidence),
            "amount_log": round(math.log1p(amount_paise), 4),
            "amount_paise": amount_paise,
            "stage0_decision": context.stage0_result.decision.value,
            "stage0_reason": context.stage0_result.reason_code.value,
            "action_type": candidate_action.value,
            "is_downtime_active": 1 if context.diagnosis.diagnosis_code.value == "GATEWAY_FAILURE" else 0,
        }

    @classmethod
    def get_feature_names(cls) -> List[str]:
        """Return canonical list of feature names used by CatBoost model."""
        return [
            "event_type",
            "diagnosis_code",
            "diagnosis_confidence",
            "amount_log",
            "amount_paise",
            "stage0_decision",
            "stage0_reason",
            "action_type",
            "is_downtime_active",
        ]

    @classmethod
    def get_categorical_feature_names(cls) -> List[str]:
        """Return names of categorical features for CatBoost."""
        return [
            "event_type",
            "diagnosis_code",
            "stage0_decision",
            "stage0_reason",
            "action_type",
        ]
