"""Transparent Heuristic Scorer — the non-ML baseline for the A3 vs A5 comparison (ADR-0011).

This is the honest comparison the AI must beat. It answers: "what would a simple,
readable, non-ML decision engine choose?"

INVARIANTS:
1. NO MACHINE LEARNING. Fixed, hand-written rules only. No fitting, no training data.
2. DROP-IN INTERFACE: exposes `is_fitted` and `predict_action_probability(context, action)`,
   the complete surface EVCalculator consumes, so A3 and A5 differ ONLY in the scorer.
3. DETERMINISTIC: identical context and action always produce an identical probability.
   No randomness, no state.
4. READABLE BY DESIGN: every adjustment below is a stated rule a reviewer can audit.
   If this beats CatBoost, that result is reported honestly (ADR-0005).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.domain.enums import ActionType, DiagnosisCode
from app.domain.models import RecoveryDecisionContext
from app.scoring.feature_builder import FeatureBuilder

# Base recovery probability per action, before any context adjustment.
# Chosen to mirror plausible channel effectiveness ordering, not fitted to data.
HEURISTIC_ACTION_BASELINES: Dict[ActionType, float] = {
    ActionType.NO_ACTION: 0.15,
    ActionType.EMAIL_LINK: 0.25,
    ActionType.SMS_LINK: 0.35,
    ActionType.IVR_CALL: 0.40,
    ActionType.WHATSAPP_LINK: 0.45,
    ActionType.RECOMMEND_RETRY: 0.50,
    ActionType.AGENT_DIAL: 0.55,
}

# Multiplicative adjustment by diagnosis. A flat table, deliberately simple:
# the heuristic knows the failure reason matters, but not how it interacts with
# the specific action. That interaction is what the model may or may not capture.
DIAGNOSIS_MULTIPLIER: Dict[str, float] = {
    DiagnosisCode.GATEWAY_FAILURE.value: 0.15,             # outage: acting now rarely works
    DiagnosisCode.INSUFFICIENT_FUNDS.value: 1.10,          # liquidity returns; nudging helps
    DiagnosisCode.CARD_DECLINED.value: 0.80,               # needs a method update, not a nudge
    DiagnosisCode.CUSTOMER_ABANDONMENT.value: 0.90,
    DiagnosisCode.SUBSCRIPTION_RENEWAL_FAILURE.value: 1.00,
    DiagnosisCode.INVOICE_OVERDUE.value: 0.95,
    DiagnosisCode.CUSTOMER_UNRESPONSIVE.value: 0.60,       # repeated non-response
    DiagnosisCode.UNKNOWN.value: 0.85,                     # unexplained: act cautiously
}

# Larger amounts are marginally harder to recover in a single touch.
LARGE_AMOUNT_THRESHOLD_PAISE = 2_000_000  # Rs 20,000
LARGE_AMOUNT_MULTIPLIER = 0.85


class HeuristicScorer:
    """Rule-based recovery-probability estimator. Drop-in replacement for CatBoostSLearner."""

    def __init__(self, model_version: str = "v1.0.0-heuristic") -> None:
        self.model_version = model_version
        # Always "fitted": there is nothing to fit. Declared True so the decision engine
        # does not report INSUFFICIENT_TRAINING_DATA for a scorer that needs none.
        self.is_fitted = True

    # -- Interface consumed by EVCalculator ------------------------------------------------

    def predict_action_probability(
        self,
        context: RecoveryDecisionContext,
        action_type: ActionType,
    ) -> float:
        """Estimate P(recovery | context, action) from fixed rules."""
        feature_dict = FeatureBuilder.build_feature_dict(context, action_type)
        return self.predict_probability(feature_dict)

    def predict_probability(self, feature_dict: Dict[str, Any]) -> float:
        """Apply the rule stack to a feature dictionary. Deterministic and bounded."""
        action = self._coerce_action(feature_dict.get("action_type"))
        prob = HEURISTIC_ACTION_BASELINES.get(action, 0.15)

        # NO_ACTION is the counterfactual baseline; context does not move it.
        if action == ActionType.NO_ACTION:
            return prob

        diagnosis = feature_dict.get("diagnosis_code", "")
        prob *= DIAGNOSIS_MULTIPLIER.get(diagnosis, 1.0)

        amount_paise = feature_dict.get("amount_paise", 0)
        if isinstance(amount_paise, (int, float)) and amount_paise >= LARGE_AMOUNT_THRESHOLD_PAISE:
            prob *= LARGE_AMOUNT_MULTIPLIER

        return max(0.0, min(1.0, prob))

    # -- Parity with CatBoostSLearner's surface ---------------------------------------------

    def fit(self, training_data: Any, target_key: str = "recovered") -> bool:
        """No-op. A heuristic has nothing to learn; returns True so callers stay uniform."""
        return True

    def to_config_dict(self) -> Dict[str, Any]:
        return {
            "scorer_type": "HEURISTIC",
            "model_version": self.model_version,
            "is_fitted": True,
            "action_baselines": {a.value: p for a, p in HEURISTIC_ACTION_BASELINES.items()},
            "diagnosis_multipliers": dict(DIAGNOSIS_MULTIPLIER),
            "large_amount_threshold_paise": LARGE_AMOUNT_THRESHOLD_PAISE,
            "large_amount_multiplier": LARGE_AMOUNT_MULTIPLIER,
        }

    @staticmethod
    def _coerce_action(raw: Optional[Any]) -> ActionType:
        if isinstance(raw, ActionType):
            return raw
        try:
            return ActionType(raw)
        except (ValueError, TypeError):
            return ActionType.NO_ACTION
