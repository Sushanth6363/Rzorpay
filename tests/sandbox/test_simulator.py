"""Unit and property tests for Sandbox Simulator (M6)."""

import pytest
from app.domain.enums import ActionType, ExecutionStatus, PaymentOutcome
from app.domain.models import SandboxActionRequest
from app.sandbox.simulator import SandboxSimulator


def test_sandbox_simulator_no_action_counterfactual():
    """Verify NO_ACTION produces zero contact dispatch and simulated natural outcome."""
    sim = SandboxSimulator()
    req = SandboxActionRequest(
        action_id="act_1",
        decision_id="dec_1",
        merchant_id="m1",
        customer_id="c1",
        opportunity_id="opp_1",
        action_type=ActionType.NO_ACTION,
        amount_paise=100000,
        requested_at="2026-09-01T10:00:00+00:00",
        idempotency_key="key_1",
    )
    res = sim.execute_action(req)

    assert res.action_type == ActionType.NO_ACTION
    assert res.execution_status == ExecutionStatus.EXECUTED
    assert res.payment_outcome in (PaymentOutcome.SELF_CURED, PaymentOutcome.NO_PAYMENT)


def test_sandbox_simulator_forced_execution_unknown():
    """Verify forced EXECUTION_UNKNOWN status simulation."""
    sim = SandboxSimulator()
    req = SandboxActionRequest(
        action_id="act_2",
        decision_id="dec_2",
        merchant_id="m1",
        customer_id="c1",
        opportunity_id="opp_2",
        action_type=ActionType.WHATSAPP_LINK,
        amount_paise=100000,
        requested_at="2026-09-01T10:00:00+00:00",
        idempotency_key="key_2",
    )
    res = sim.execute_action(req, force_status=ExecutionStatus.EXECUTION_UNKNOWN)

    assert res.execution_status == ExecutionStatus.EXECUTION_UNKNOWN
    assert res.payment_outcome == PaymentOutcome.EXECUTION_UNKNOWN
    assert res.delivered_at is None


def test_sandbox_simulator_deterministic_reproducibility():
    """Verify identical seed produces 100% reproducible sandbox execution outcome."""
    sim = SandboxSimulator()
    req = SandboxActionRequest(
        action_id="act_3",
        decision_id="dec_3",
        merchant_id="m1",
        customer_id="c1",
        opportunity_id="opp_3",
        action_type=ActionType.RECOMMEND_RETRY,
        amount_paise=500000,
        requested_at="2026-09-01T10:00:00+00:00",
        idempotency_key="key_3",
    )
    res1 = sim.execute_action(req, random_seed=12345)
    res2 = sim.execute_action(req, random_seed=12345)

    assert res1.to_dict() == res2.to_dict()
