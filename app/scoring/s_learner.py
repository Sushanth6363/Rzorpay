"""CatBoost S-Learner Implementation for Unified Recovery Engine (M5).

INVARIANTS:
1. S-Learner Architecture (ADR-0005): Single CatBoost model with action as a feature.
2. Predicts P(Y=1 | X=x, A=a) for context X and action A.
3. Fixed random seed (default 42) for 100% deterministic model predictions.
4. Cold-start safety: Graceful fallback when training data is missing or insufficient (<10 samples).
"""

import os
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from catboost import CatBoostClassifier

from app.domain.enums import ActionType
from app.domain.models import RecoveryDecisionContext
from app.scoring.feature_builder import FeatureBuilder


# Baseline heuristic probabilities for cold start / insufficient training data
HEURISTIC_BASELINES = {
    ActionType.NO_ACTION: 0.15,
    ActionType.WHATSAPP_LINK: 0.45,
    ActionType.SMS_LINK: 0.35,
    ActionType.EMAIL_LINK: 0.25,
    ActionType.IVR_CALL: 0.40,
    ActionType.AGENT_DIAL: 0.55,
    ActionType.RECOMMEND_RETRY: 0.50,
}


class CatBoostSLearner:
    """S-Learner CatBoost model wrapper for predicting recovery probability P(Y=1 | X=x, A=a)."""

    def __init__(
        self,
        random_seed: int = 42,
        iterations: int = 50,
        depth: int = 4,
        learning_rate: float = 0.1,
    ) -> None:
        self.random_seed = random_seed
        self.iterations = iterations
        self.depth = depth
        self.learning_rate = learning_rate
        self.model: Optional[CatBoostClassifier] = None
        self.is_fitted: bool = False
        self.feature_names = FeatureBuilder.get_feature_names()
        self.cat_features = FeatureBuilder.get_categorical_feature_names()

    def fit(self, training_data: List[Dict[str, Any]], target_key: str = "recovered") -> bool:
        """Fit CatBoost S-learner on training records (List of feature dicts + target)."""
        if not training_data or len(training_data) < 10:
            # Insufficient samples for reliable fitting — maintain safe fallback
            self.is_fitted = False
            return False

        df = pd.DataFrame(training_data)
        if target_key not in df.columns or df[target_key].nunique() < 2:
            # Missing target or single class — maintain safe fallback
            self.is_fitted = False
            return False

        X = df[self.feature_names]
        y = df[target_key].astype(int)

        self.model = CatBoostClassifier(
            iterations=self.iterations,
            depth=self.depth,
            learning_rate=self.learning_rate,
            random_seed=self.random_seed,
            cat_features=self.cat_features,
            verbose=0,
        )
        self.model.fit(X, y)
        self.is_fitted = True
        return True

    def predict_probability(self, feature_dict: Dict[str, Any]) -> float:
        """Predict recovery probability P(Y=1 | X=x, A=a) for a single feature dictionary."""
        if not self.is_fitted or self.model is None:
            # Heuristic cold-start prediction
            action_str = feature_dict.get("action_type", ActionType.NO_ACTION.value)
            try:
                action_enum = ActionType(action_str)
            except ValueError:
                action_enum = ActionType.NO_ACTION
            
            base_p = HEURISTIC_BASELINES.get(action_enum, 0.15)
            # Adjust slightly based on diagnosis if available
            diag = feature_dict.get("diagnosis_code", "")
            if diag == "GATEWAY_FAILURE" and action_enum != ActionType.NO_ACTION:
                base_p = 0.05  # Outage drastically reduces recovery probability
            elif diag == "INSUFFICIENT_FUNDS" and action_enum == ActionType.AGENT_DIAL:
                base_p = 0.60
            return base_p

        df_single = pd.DataFrame([feature_dict])[self.feature_names]
        probs = self.model.predict_proba(df_single)[0]
        # CatBoost returns [p_class_0, p_class_1]
        p_recovered = float(probs[1]) if len(probs) > 1 else float(probs[0])
        return max(0.0, min(1.0, p_recovered))

    def predict_action_probability(
        self,
        context: RecoveryDecisionContext,
        action_type: ActionType,
    ) -> float:
        """Helper to construct features and predict probability for a context and action."""
        f_dict = FeatureBuilder.build_feature_dict(context, action_type)
        return self.predict_probability(f_dict)

    def save_model(self, filepath: str) -> None:
        """Save fitted model to file."""
        if self.is_fitted and self.model:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            self.model.save_model(filepath)

    def load_model(self, filepath: str) -> None:
        """Load model from file."""
        if os.path.exists(filepath):
            self.model = CatBoostClassifier()
            self.model.load_model(filepath)
            self.is_fitted = True

    def to_config_dict(self) -> Dict[str, Any]:
        """Return model metadata dictionary."""
        return {
            "random_seed": self.random_seed,
            "iterations": self.iterations,
            "depth": self.depth,
            "learning_rate": self.learning_rate,
            "is_fitted": self.is_fitted,
            "feature_names": self.feature_names,
            "cat_features": self.cat_features,
        }
