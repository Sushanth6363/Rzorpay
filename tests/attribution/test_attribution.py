"""Unit tests for Recovery Attribution Engine (M6)."""

import pytest
from app.attribution.attribution_engine import AttributionEngine
from app.domain.enums import (
    ActionType,
    AttributionStatus,
    DecisionMode,
    ExecutionStatus,
    PaymentOutcome,
)
from app.domain.models import AIRecoveryDecision, SandboxExecutionResult


def test_self_cure_receives_zero_ai_attribution():
    """Verify SELF_CURED payments strictly receive ₹0 AI attribution (INV-1)."""
    engine = AttributionEngine()
    decision = AIRecoveryDecision(
        decision_id="dec_1",
        merchant_id="m1",
        opportunity_id="opp_1",
        customer_id="c1",
        selected_action=ActionType.WHATSAPP_LINK,
        decision_mode=DecisionMode.EXPLOIT,
        model_version="v1.0",
        decision_timestamp="2026-09-01T10:00:00+00:00",
        baseline_probability=0.20,
        selected_action_score=None,
        candidate_scores=[],
    )
    exec_res = SandboxExecutionResult(
        execution_id="exec_1",
        action_id="act_1",
        decision_id="dec_1",
        opportunity_id="opp_1",
        merchant_id="m1",
        customer_id="c1",
        action_type=ActionType.WHATSAPP_LINK,
        execution_status=ExecutionStatus.EXECUTED,
        payment_outcome=PaymentOutcome.SELF_CURED,
        executed_at="2026-09-01T10:01:00+00:00",
        delivered_at="2026-09-01T10:01:00+00:00",
    )

    attr = engine.attribute_recovery(
        decision=decision,
        execution_result=exec_res,
        amount_at_risk_paise=1000000,
    )

    assert attr.attribution_status == AttributionStatus.SELF_CURED
    assert attr.gross_recovered_paise == 1000000
    assert attr.attributed_recovered_paise == 0  # CRITICAL INVARIANT: ₹0 AI ATTRIBUTION FOR SELF-CURE
    assert attr.is_self_cured is True


def test_delivered_intervention_recovery_attribution():
    """Verify delivered intervention payment receives 100% attributed recovery."""
    engine = AttributionEngine()
    decision = AIRecoveryDecision(
        decision_id="dec_2",
        merchant_id="m1",
        opportunity_id="opp_2",
        customer_id="c2",
        selected_action=ActionType.RECOMMEND_RETRY,
        decision_mode=DecisionMode.EXPLOIT,
        model_version="v1.0",
        decision_timestamp="2026-09-01T10:00:00+00:00",
        baseline_probability=0.20,
        selected_action_score=None,
        candidate_scores=[],
    )
    exec_res = SandboxExecutionResult(
        execution_id="exec_2",
        action_id="act_2",
        decision_id="dec_2",
        opportunity_id="opp_2",
        merchant_id="m1",
        customer_id="c2",
        action_type=ActionType.RECOMMEND_RETRY,
        execution_status=ExecutionStatus.EXECUTED,
        payment_outcome=PaymentOutcome.PAYMENT_SUCCESS,
        executed_at="2026-09-01T10:01:00+00:00",
        delivered_at="2026-09-01T10:01:00+00:00",
    )

    attr = engine.attribute_recovery(
        decision=decision,
        execution_result=exec_res,
        amount_at_risk_paise=500000,
    )

    assert attr.attribution_status == AttributionStatus.RECOVERED
    assert attr.gross_recovered_paise == 500000
    assert attr.attributed_recovered_paise == 500000
    assert attr.is_self_cured is False
