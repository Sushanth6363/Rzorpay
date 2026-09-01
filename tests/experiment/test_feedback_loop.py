"""Tests for Feedback Loop Engine & Point-in-Time Safety (INV-7)."""

import pytest
from app.domain.enums import ActionType, DataProvenance, ExperimentArm, PaymentOutcome
from app.domain.models import RecoveryObservation
from app.experiment.feedback_loop import FeedbackLoopEngine
from app.scoring.feature_builder import PointInTimeLeakageError


def test_feedback_loop_valid_record_creation():
    """Valid observation and point-in-time decision features create clean TrainingRecord."""
    engine = FeedbackLoopEngine()
    obs = RecoveryObservation(
        observation_id="obs_1",
        experiment_id="EXP_TEST",
        arm="A5",
        opportunity_id="opp_1",
        merchant_id="m1",
        customer_id="c1",
        decision_id="dec_1",
        selected_action=ActionType.RECOMMEND_RETRY,
        outcome=PaymentOutcome.PAYMENT_SUCCESS,
        amount_at_risk_paise=100000,
        gross_recovered_paise=100000,
        attributed_recovered_paise=100000,
        self_cured=False,
        decision_timestamp="2026-09-01T10:00:00+00:00",
        outcome_timestamp="2026-09-01T10:05:00+00:00",
        model_version="v1.0.0",
    )

    valid_features = {
        "amount_paise": 100000,
        "historical_failure_count": 2,
        "is_downtime_active": False,
    }

    record = engine.create_training_record(observation=obs, decision_features=valid_features)

    assert record.opportunity_id == "opp_1"
    assert record.arm == ExperimentArm.A5
    assert record.selected_action == ActionType.RECOMMEND_RETRY
    assert record.observed_outcome == PaymentOutcome.PAYMENT_SUCCESS
    assert record.features["amount_paise"] == 100000


def test_feedback_loop_post_decision_leakage_rejection_inv7():
    """Feature vector X containing post-decision outcome fields raises PointInTimeLeakageError (INV-7)."""
    engine = FeedbackLoopEngine()
    obs = RecoveryObservation(
        observation_id="obs_1",
        experiment_id="EXP_TEST",
        arm="A5",
        opportunity_id="opp_1",
        merchant_id="m1",
        customer_id="c1",
        decision_id="dec_1",
        selected_action=ActionType.RECOMMEND_RETRY,
        outcome=PaymentOutcome.PAYMENT_SUCCESS,
        amount_at_risk_paise=100000,
        gross_recovered_paise=100000,
        attributed_recovered_paise=100000,
        self_cured=False,
        decision_timestamp="2026-09-01T10:00:00+00:00",
        outcome_timestamp="2026-09-01T10:05:00+00:00",
        model_version="v1.0.0",
    )

    leaked_features = {
        "amount_paise": 100000,
        "gross_recovered_paise": 100000,  # POST-DECISION LEAKAGE!
    }

    with pytest.raises(PointInTimeLeakageError, match="Post-decision feature leakage detected"):
        engine.create_training_record(observation=obs, decision_features=leaked_features)
