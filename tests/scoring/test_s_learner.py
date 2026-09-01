"""Tests for CatBoost S-Learner Model & Model Registry (M5-01..06)."""

import os
import tempfile
import pytest
from app.scoring.dataset_generator import SyntheticDatasetGenerator
from app.scoring.registry import FileBasedModelRegistry
from app.scoring.s_learner import CatBoostSLearner


def test_m5_01_s_learner_fit_and_predict():
    """M5-01: Verify CatBoost S-Learner fits on synthetic data and predicts probabilities."""
    training_data = SyntheticDatasetGenerator.generate_training_data(num_samples=100, random_seed=42)
    learner = CatBoostSLearner(random_seed=42, iterations=20)

    fitted = learner.fit(training_data, target_key="recovered")
    assert fitted is True
    assert learner.is_fitted is True

    # Predict on sample feature record
    sample_feature = training_data[0]
    prob = learner.predict_probability(sample_feature)

    assert 0.0 <= prob <= 1.0


def test_m5_02_s_learner_deterministic_predictions():
    """M5-02: Verify identical models with identical seed produce identical predictions."""
    training_data = SyntheticDatasetGenerator.generate_training_data(num_samples=100, random_seed=42)

    learner1 = CatBoostSLearner(random_seed=42, iterations=20)
    learner1.fit(training_data)

    learner2 = CatBoostSLearner(random_seed=42, iterations=20)
    learner2.fit(training_data)

    sample = training_data[5]
    assert learner1.predict_probability(sample) == learner2.predict_probability(sample)


def test_m5_03_insufficient_training_data_fallback():
    """M5-03: Verify model handles insufficient training data gracefully without crashing."""
    learner = CatBoostSLearner(random_seed=42)
    small_data = [{"event_type": "FAILED_PAYMENT", "recovered": 1}]

    fitted = learner.fit(small_data)
    assert fitted is False
    assert learner.is_fitted is False

    # Standard prediction falls back to baseline heuristic
    sample = {"action_type": "WHATSAPP_LINK", "diagnosis_code": "CUSTOMER_ABANDONMENT"}
    prob = learner.predict_probability(sample)
    assert prob > 0.0


def test_m5_04_file_based_registry():
    """M5-04: Verify FileBasedModelRegistry registers, saves, and loads CatBoost model artifacts (ADR-0008)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry = FileBasedModelRegistry(base_dir=tmpdir)

        training_data = SyntheticDatasetGenerator.generate_training_data(num_samples=50, random_seed=42)
        learner = CatBoostSLearner(random_seed=42, iterations=10)
        learner.fit(training_data)

        meta = registry.register_model(
            version="v1.0.0-test",
            learner=learner,
            metrics={"auc": 0.85},
            notes="Test baseline model",
        )

        assert meta["model_version"] == "v1.0.0-test"
        assert os.path.exists(meta["artifact_path"])
        assert len(meta["artifact_hash"]) > 0

        # Load back
        loaded_learner = registry.load_model("v1.0.0-test")
        assert loaded_learner is not None
        assert loaded_learner.is_fitted is True

        sample = training_data[0]
        assert round(learner.predict_probability(sample), 4) == round(loaded_learner.predict_probability(sample), 4)
