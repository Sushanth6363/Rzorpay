"""Standardized Golden AI Decision Scenarios AI-01 through AI-10 (M5 Verification Gate)."""

import pytest
from app.domain.enums import ActionType, DecisionMode, DiagnosisCode, EligibilityStatus, SafetyRejectReason
from app.domain.models import CustomerContactBudget, RecoveryDecisionContext
from app.pipeline.recovery_pipeline import RecoveryPipeline
from app.scoring.engine import AIRecoveryDecisionEngine
from app.scoring.feature_builder import PointInTimeLeakageError
from app.scoring.s_learner import CatBoostSLearner


def test_ai_01_no_action_wins_when_all_interventions_have_negative_incremental_ev():
    """AI-01: NO_ACTION wins when every intervention candidate has negative incremental EV."""
    pipeline = RecoveryPipeline()
    raw = {"merchant_id": "m1", "customer_id": "c1", "event_id": "e1", "amount_paise": 100000}
    context = pipeline.process_raw_event(raw)

    learner = CatBoostSLearner(random_seed=42)

    # Mock predictions where NO_ACTION baseline = 0.50, interventions = 0.40 (negative uplift delta = -0.10)
    def mock_prob(ctx, act):
        if act == ActionType.NO_ACTION:
            return 0.50
        return 0.40

    learner.predict_action_probability = mock_prob

    engine = AIRecoveryDecisionEngine(learner=learner)
    decision = engine.evaluate_decision(context, force_mode=DecisionMode.EXPLOIT)

    assert decision.selected_action == ActionType.NO_ACTION


def test_ai_02_retry_recommendation_wins_with_positive_incremental_ev():
    """AI-02: A retry recommendation has positive incremental EV and zero action cost, winning selection."""
    pipeline = RecoveryPipeline()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c1",
        "event_id": "e1",
        "amount_paise": 500000,
        "occurred_at": "2026-09-01T10:00:00+00:00",
        "failure_reason": "INSUFFICIENT_FUNDS",
    }
    context = pipeline.process_raw_event(raw)

    learner = CatBoostSLearner(random_seed=42)

    def mock_prob(ctx, act):
        if act == ActionType.NO_ACTION:
            return 0.10
        elif act == ActionType.RECOMMEND_RETRY:
            return 0.60  # +50% uplift, cost 0 paise
        return 0.20

    learner.predict_action_probability = mock_prob

    engine = AIRecoveryDecisionEngine(learner=learner)
    decision = engine.evaluate_decision(context, force_mode=DecisionMode.EXPLOIT)

    assert decision.selected_action == ActionType.RECOMMEND_RETRY


def test_ai_03_customer_message_action_beats_retry_on_incremental_ev():
    """AI-03: WhatsApp payment link beats retry recommendation based on higher incremental EV."""
    pipeline = RecoveryPipeline()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c1",
        "event_id": "e1",
        "amount_paise": 1000000,  # ₹10,000.00
        "occurred_at": "2026-09-01T10:00:00+00:00",
    }
    context = pipeline.process_raw_event(raw)

    learner = CatBoostSLearner(random_seed=42)

    def mock_prob(ctx, act):
        if act == ActionType.NO_ACTION:
            return 0.10
        elif act == ActionType.RECOMMEND_RETRY:
            return 0.20  # +10% uplift -> EV = ₹1,000
        elif act == ActionType.WHATSAPP_LINK:
            return 0.50  # +40% uplift -> EV = ₹4,000 - ₹0.25 = ₹3,999.75
        return 0.15

    learner.predict_action_probability = mock_prob

    engine = AIRecoveryDecisionEngine(learner=learner)
    decision = engine.evaluate_decision(context, force_mode=DecisionMode.EXPLOIT)

    assert decision.selected_action == ActionType.WHATSAPP_LINK


def test_ai_04_raw_probability_favors_action_a_but_incremental_ev_favors_action_b():
    """AI-04: Action A has higher raw probability, but Action B has higher incremental EV and wins."""
    pipeline = RecoveryPipeline()
    raw = {"merchant_id": "m1", "customer_id": "c1", "event_id": "e1", "amount_paise": 100000}
    context = pipeline.process_raw_event(raw)

    learner = CatBoostSLearner(random_seed=42)

    # Agent Dial: raw prob 0.61 (cost 1500 paise -> EV = 51000 - 1500 = 49500 paise)
    # WhatsApp: raw prob 0.60 (cost 25 paise -> EV = 50000 - 25 = 49975 paise)
    def mock_prob(ctx, act):
        if act == ActionType.NO_ACTION:
            return 0.10
        elif act == ActionType.AGENT_DIAL:
            return 0.61  # Higher raw prob (0.61 vs 0.60)
        elif act == ActionType.WHATSAPP_LINK:
            return 0.60  # Slightly lower raw prob, but much lower cost (25 paise vs 1500 paise)
        return 0.15

    learner.predict_action_probability = mock_prob

    engine = AIRecoveryDecisionEngine(learner=learner)
    decision = engine.evaluate_decision(context, force_mode=DecisionMode.EXPLOIT)

    assert decision.selected_action == ActionType.WHATSAPP_LINK


def test_ai_05_gateway_outage_suppresses_retry_even_if_scored_highly():
    """AI-05: Gateway outage forces retry into SAFETY_REJECTED; AI cannot select retry."""
    pipeline = RecoveryPipeline()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c1",
        "event_id": "e1",
        "amount_paise": 100000,
        "failure_reason": "GATEWAY_FAILURE",
    }
    context = pipeline.process_raw_event(raw)

    learner = CatBoostSLearner(random_seed=42)

    def mock_prob(ctx, act):
        if act == ActionType.RECOMMEND_RETRY:
            return 0.99  # Scored extremely high!
        return 0.15

    learner.predict_action_probability = mock_prob

    engine = AIRecoveryDecisionEngine(learner=learner)
    decision = engine.evaluate_decision(context, force_mode=DecisionMode.EXPLOIT)

    assert decision.selected_action != ActionType.RECOMMEND_RETRY
    retry_score = next(s for s in decision.candidate_scores if s.action_type == ActionType.RECOMMEND_RETRY)
    assert retry_score.eligibility == EligibilityStatus.SAFETY_REJECTED
    assert retry_score.reject_reason == SafetyRejectReason.KNOWN_GATEWAY_OUTAGE


def test_ai_06_safety_rejected_action_cannot_be_selected_by_exploration():
    """AI-06: Exploration (epsilon=1.0) cannot select safety-rejected candidate (INV-3)."""
    pipeline = RecoveryPipeline()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c1",
        "event_id": "e1",
        "amount_paise": 100000,
        "failure_reason": "GATEWAY_FAILURE",
    }
    context = pipeline.process_raw_event(raw)

    engine = AIRecoveryDecisionEngine(epsilon=1.0)  # 100% exploration

    for seed in range(50):
        decision = engine.evaluate_decision(context, random_seed=seed)
        assert decision.selected_action != ActionType.RECOMMEND_RETRY


def test_ai_07_budget_constraints_not_bypassed_by_ai():
    """AI-07: Budget exhaustion forces outreach candidates into SAFETY_REJECTED; AI safely falls back."""
    pipeline = RecoveryPipeline()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c1",
        "event_id": "e1",
        "amount_paise": 100000,
    }
    exhausted_budget = CustomerContactBudget(merchant_id="m1", customer_id="c1", cap=3, reserved_count=3, consumed_count=0)
    context = pipeline.process_raw_event(raw, contact_budget=exhausted_budget)

    engine = AIRecoveryDecisionEngine()
    decision = engine.evaluate_decision(context)

    # Budget exhaustion leaves only NO_ACTION eligible (and RECOMMEND_RETRY if not outage)
    # Outreach channels (WHATSAPP, SMS, etc.) are all SAFETY_REJECTED
    outreach_scores = [
        s for s in decision.candidate_scores
        if s.action_type in (ActionType.WHATSAPP_LINK, ActionType.SMS_LINK, ActionType.EMAIL_LINK)
    ]
    for s in outreach_scores:
        assert s.eligibility == EligibilityStatus.SAFETY_REJECTED
        assert s.reject_reason == SafetyRejectReason.CONTACT_BUDGET_UNAVAILABLE

    assert decision.is_contact_reserved is False


def test_ai_08_future_feature_causes_leakage_failure():
    """AI-08: Future-dated feature observed_at > decision_timestamp raises PointInTimeLeakageError (INV-7)."""
    pipeline = RecoveryPipeline()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c1",
        "event_id": "e1",
        "amount_paise": 100000,
        "occurred_at": "2026-09-01T10:00:00+00:00",
        "observed_at": "2026-09-01T10:00:00+00:00",
    }
    # Create context at t=10:00:00
    context = pipeline.process_raw_event(raw, decision_timestamp="2026-09-01T10:00:00+00:00")

    # Manually simulate a future-dated observation in context opportunity for M5 evaluation
    future_opportunity = context.opportunity
    object.__setattr__(future_opportunity, "observed_at", "2026-09-01T12:00:00+00:00")

    engine = AIRecoveryDecisionEngine()

    with pytest.raises(PointInTimeLeakageError):
        engine.evaluate_decision(context)


def test_ai_09_insufficient_training_data_produces_safe_cold_start():
    """AI-09: Unfitted learner uses safe heuristic baselines and records INSUFFICIENT_TRAINING_DATA."""
    pipeline = RecoveryPipeline()
    raw = {"merchant_id": "m1", "customer_id": "c1", "event_id": "e1", "amount_paise": 100000}
    context = pipeline.process_raw_event(raw)

    unfitted_learner = CatBoostSLearner(random_seed=42)
    assert unfitted_learner.is_fitted is False

    engine = AIRecoveryDecisionEngine(learner=unfitted_learner)
    decision = engine.evaluate_decision(context)

    assert decision.abstention_reason.value == "INSUFFICIENT_TRAINING_DATA"
    assert decision.selected_action is not None


def test_ai_10_identical_inputs_produce_identical_decisions():
    """AI-10: Identical context, model version, and random seed produce 100% identical decisions."""
    pipeline = RecoveryPipeline()
    raw = {
        "merchant_id": "m_det",
        "customer_id": "c_det",
        "event_id": "e_det",
        "amount_paise": 250000,
        "occurred_at": "2026-09-01T10:00:00+00:00",
    }
    context = pipeline.process_raw_event(raw, decision_timestamp="2026-09-01T10:00:00+00:00")

    engine = AIRecoveryDecisionEngine()

    dec1 = engine.evaluate_decision(context, random_seed=123)
    dec2 = engine.evaluate_decision(context, random_seed=123)

    assert dec1.to_dict() == dec2.to_dict()
