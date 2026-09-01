"""Feedback Loop & Retraining Dataset Transformation Engine (ADR-0011, 07_EXPERIMENT_METHODOLOGY).

INVARIANTS:
1. POINT-IN-TIME FEATURE SAFETY (INV-7): Feature vector X contains strictly decision-time features prior to decision_timestamp.
2. POST-DECISION SEPARATION: Outcomes (Y, gross_recovered_paise, self_cured) are stored exclusively as training targets/labels, NEVER inside feature vector X.
3. AUDITABLE PROVENANCE: Every TrainingRecord preserves experiment_id, arm, model_version, and SHA256 record hash.
"""

import hashlib
from typing import Dict, List, Any, Optional
from app.domain.enums import DataProvenance, ExperimentArm, PaymentOutcome

from app.domain.models import RecoveryObservation, TrainingRecord
from app.scoring.feature_builder import PointInTimeLeakageError, FeatureBuilder


class FeedbackLoopEngine:
    """Transforms RecoveryObservation logs into clean point-in-time TrainingRecord datasets."""

    def __init__(self, feature_builder: Optional[FeatureBuilder] = None) -> None:
        self.feature_builder = feature_builder or FeatureBuilder()

    def create_training_record(
        self,
        observation: RecoveryObservation,
        decision_features: Dict[str, Any],
        experiment_id: str = "EXP_M7_CANONICAL_V1",
    ) -> TrainingRecord:
        """Transform observation and decision features into a validated TrainingRecord."""
        # 1. Enforce Point-in-Time Safety (INV-7)
        denylisted_fields = {
            "gross_recovered_paise",
            "attributed_recovered_paise",
            "self_cured",
            "payment_outcome",
            "outcome",
            "delivered_at",
            "outcome_timestamp",
        }
        leaked_keys = set(decision_features.keys()).intersection(denylisted_fields)
        if leaked_keys:
            raise PointInTimeLeakageError(
                f"Post-decision feature leakage detected in training record feature vector X: {leaked_keys}"
            )

        # 2. Generate deterministic record_id
        raw = f"{experiment_id}_{observation.observation_id}_{observation.decision_timestamp}"
        record_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
        record_id = f"tr_{observation.opportunity_id}_{record_hash}"

        arm_enum = observation.arm if isinstance(observation.arm, ExperimentArm) else ExperimentArm(str(observation.arm))

        return TrainingRecord(
            record_id=record_id,
            experiment_id=experiment_id,
            arm=arm_enum,
            merchant_id=observation.merchant_id,
            customer_id=observation.customer_id,
            opportunity_id=observation.opportunity_id,
            decision_timestamp=observation.decision_timestamp,
            features=decision_features,
            selected_action=observation.selected_action,
            observed_outcome=observation.outcome,
            gross_recovered_paise=observation.gross_recovered_paise,
            attributed_recovered_paise=observation.attributed_recovered_paise,
            self_cured=observation.self_cured,
            model_version=observation.model_version,
            provenance=observation.provenance,
        )


    def extract_dataset(
        self,
        observations: List[RecoveryObservation],
        feature_lookup: Dict[str, Dict[str, Any]],
        experiment_id: str = "EXP_M7_CANONICAL_V1",
    ) -> List[TrainingRecord]:
        """Convert a batch of RecoveryObservation logs into a clean TrainingRecord dataset."""
        records: List[TrainingRecord] = []
        for obs in observations:
            feats = feature_lookup.get(obs.opportunity_id, {})
            record = self.create_training_record(
                observation=obs,
                decision_features=feats,
                experiment_id=experiment_id,
            )
            records.append(record)
        return records
