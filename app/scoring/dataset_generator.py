"""Deterministic Synthetic Training Dataset Generator for S-Learner (M5).

INVARIANTS:
1. Provenance tagged: DataProvenance.SYNTHETIC_DATA.
2. Fixed random seed guarantees 100% reproducible synthetic dataset generation.
3. Realistic recovery probability patterns based on failure diagnosis and recovery actions.
"""

import random
from typing import Any, Dict, List
from app.domain.enums import ActionType, DataProvenance, DiagnosisCode, EventType, Stage0Decision, Stage0Reason
from app.scoring.costs import ACTION_COSTS_PAISE
from app.scoring.feature_builder import FeatureBuilder


class SyntheticDatasetGenerator:
    """Generates synthetic historical training data for CatBoost S-Learner fitting."""

    @staticmethod
    def generate_training_data(
        num_samples: int = 200,
        random_seed: int = 42,
    ) -> List[Dict[str, Any]]:
        """Generate deterministic synthetic feature records with binary recovery outcomes."""
        rng = random.Random(random_seed)

        event_types = [
            EventType.FAILED_PAYMENT,
            EventType.ABANDONED_CHECKOUT,
            EventType.FAILED_SUBSCRIPTION_RENEWAL,
            EventType.OVERDUE_B2B_INVOICE,
        ]
        diagnoses = [
            DiagnosisCode.INSUFFICIENT_FUNDS,
            DiagnosisCode.CARD_DECLINED,
            DiagnosisCode.CUSTOMER_ABANDONMENT,
            DiagnosisCode.SUBSCRIPTION_RENEWAL_FAILURE,
            DiagnosisCode.INVOICE_OVERDUE,
        ]
        actions = list(ActionType)

        dataset: List[Dict[str, Any]] = []

        for i in range(num_samples):
            ev_type = rng.choice(event_types)
            diag = rng.choice(diagnoses)
            act = rng.choice(actions)

            amount_paise = rng.randint(1000, 500000)  # ₹10 to ₹5000

            # Determine synthetic ground truth probability
            # Base rate for NO_ACTION
            base_prob = 0.12

            if act == ActionType.NO_ACTION:
                prob = base_prob
            elif act == ActionType.WHATSAPP_LINK:
                prob = base_prob + (0.35 if diag == DiagnosisCode.CUSTOMER_ABANDONMENT else 0.20)
            elif act == ActionType.SMS_LINK:
                prob = base_prob + 0.18
            elif act == ActionType.EMAIL_LINK:
                prob = base_prob + 0.10
            elif act == ActionType.IVR_CALL:
                prob = base_prob + (0.30 if diag == DiagnosisCode.INVOICE_OVERDUE else 0.15)
            elif act == ActionType.AGENT_DIAL:
                prob = base_prob + (0.45 if amount_paise > 100000 else 0.25)
            elif act == ActionType.RECOMMEND_RETRY:
                prob = base_prob + (0.35 if diag == DiagnosisCode.INSUFFICIENT_FUNDS else 0.15)
            else:
                prob = base_prob

            # Cap probability
            prob = max(0.01, min(0.95, prob))

            # Sample binary target Y ∈ {0, 1}
            recovered = 1 if rng.random() < prob else 0

            import math
            record = {
                "event_type": ev_type.value,
                "diagnosis_code": diag.value,
                "diagnosis_confidence": round(rng.uniform(0.7, 0.99), 2),
                "amount_log": round(math.log1p(amount_paise), 4),
                "amount_paise": amount_paise,
                "stage0_decision": Stage0Decision.VALID_RECOVERY.value,
                "stage0_reason": Stage0Reason.GENUINE_RECOVERABLE.value,
                "action_type": act.value,
                "is_downtime_active": 0,
                "recovered": recovered,
                "provenance": DataProvenance.SYNTHETIC_DATA.value,
            }
            dataset.append(record)

        return dataset
