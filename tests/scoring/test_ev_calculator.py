"""Tests for Expected Value (EV) Calculator & Counterfactual Baseline (M5-07..12)."""

import pytest
from app.domain.enums import ActionType, EligibilityStatus, SafetyRejectReason
from app.domain.models import ActionCandidate, CanonicalEvent, EventType, Money
from app.pipeline.recovery_pipeline import RecoveryPipeline
from app.scoring.ev_calculator import EVCalculator
from app.scoring.s_learner import CatBoostSLearner


def test_m5_07_no_action_counterfactual_baseline():
    """M5-07: Verify NO_ACTION is always evaluated as baseline P(Y=1 | X, NO_ACTION)."""
    pipeline = RecoveryPipeline()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c1",
        "event_id": "e1",
        "amount_paise": 100000,
        "occurred_at": "2026-09-01T10:00:00+00:00",
    }
    context = pipeline.process_raw_event(raw)

    learner = CatBoostSLearner(random_seed=42)
    ev_calc = EVCalculator(model=learner)

    baseline_prob, scores = ev_calc.calculate_scores(context)
    assert baseline_prob > 0.0

    no_action_score = next(s for s in scores if s.action_type == ActionType.NO_ACTION)
    assert no_action_score.baseline_probability == baseline_prob
    assert no_action_score.incremental_effect == 0.0
    assert no_action_score.expected_value_paise == 0


def test_m5_08_incremental_effect_calculation():
    """M5-08: Verify incremental effect delta_hat = p(x,a) - p(x, NO_ACTION) is calculated correctly."""
    pipeline = RecoveryPipeline()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c1",
        "event_id": "e1",
        "amount_paise": 100000,  # ₹1,000.00
        "occurred_at": "2026-09-01T10:00:00+00:00",
    }
    context = pipeline.process_raw_event(raw)

    learner = CatBoostSLearner(random_seed=42)
    ev_calc = EVCalculator(model=learner)

    baseline_prob, scores = ev_calc.calculate_scores(context)

    for score in scores:
        if score.action_type != ActionType.NO_ACTION:
            expected_delta = score.raw_probability - baseline_prob
            assert pytest.approx(score.incremental_effect, abs=1e-5) == expected_delta


def test_m5_09_negative_uplift_produces_negative_ev():
    """M5-09: Verify negative incremental effect produces negative EV even if raw probability is high."""
    pipeline = RecoveryPipeline()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c1",
        "event_id": "e1",
        "amount_paise": 100000,
        "occurred_at": "2026-09-01T10:00:00+00:00",
    }
    context = pipeline.process_raw_event(raw)

    learner = CatBoostSLearner(random_seed=42)

    # Mock custom prediction: P(NO_ACTION)=0.70, P(WHATSAPP)=0.60 (Negative uplift delta = -0.10)
    def mock_predict_action_prob(ctx, act):
        if act == ActionType.NO_ACTION:
            return 0.70
        elif act == ActionType.WHATSAPP_LINK:
            return 0.60
        return 0.20

    learner.predict_action_probability = mock_predict_action_prob

    ev_calc = EVCalculator(model=learner)
    baseline_prob, scores = ev_calc.calculate_scores(context)

    wa_score = next(s for s in scores if s.action_type == ActionType.WHATSAPP_LINK)
    assert wa_score.raw_probability == 0.60
    assert wa_score.baseline_probability == 0.70
    assert pytest.approx(wa_score.incremental_effect, abs=1e-5) == -0.10
    assert wa_score.expected_value_paise < 0  # Negative EV


def test_m5_10_integer_paise_ev_precision():
    """M5-10: Verify Expected Value is strictly calculated in integer paise without floating point money storage."""
    pipeline = RecoveryPipeline()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c1",
        "event_id": "e1",
        "amount_paise": 50050,  # ₹500.50
        "occurred_at": "2026-09-01T10:00:00+00:00",
    }
    context = pipeline.process_raw_event(raw)

    learner = CatBoostSLearner(random_seed=42)
    ev_calc = EVCalculator(model=learner)

    _, scores = ev_calc.calculate_scores(context)

    for s in scores:
        assert isinstance(s.incremental_value_paise, int)
        assert isinstance(s.action_cost_paise, int)
        assert isinstance(s.expected_value_paise, int)
        assert s.expected_value_paise == s.incremental_value_paise - s.action_cost_paise
