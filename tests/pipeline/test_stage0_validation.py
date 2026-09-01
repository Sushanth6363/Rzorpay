"""Tests for Stage 0 recoverability validation, phantom-loss rejection, and point-in-time safety (M4-04..11)."""

import pytest
from app.clock import FakeClock
from app.domain.enums import EventSource, EventType, Stage0Decision, Stage0Reason
from app.domain.models import RecoveryOpportunity
from app.domain.money import Money
from app.pipeline.stage0 import PointInTimeLeakageError, Stage0Evaluator


@pytest.fixture
def base_opportunity():
    return RecoveryOpportunity(
        opportunity_id="opp_test_01",
        merchant_id="merch_test",
        customer_id="cust_01",
        source_event_id="evt_01",
        event_type=EventType.FAILED_PAYMENT,
        amount=Money.from_rupees(1000),
        currency="INR",
        status=EventType.FAILED_PAYMENT,
        source=EventSource.SIMULATED,
        occurred_at="2026-09-01T10:00:00+00:00",
        observed_at="2026-09-01T10:00:00+00:00",
    )


def test_m4_04_stage0_valid_recovery(base_opportunity):
    """M4-04: Verify Stage 0 returns VALID_RECOVERY for a genuine failed payment."""
    evaluator = Stage0Evaluator()
    res = evaluator.evaluate(base_opportunity, decision_timestamp="2026-09-01T10:00:00+00:00")
    assert res.decision == Stage0Decision.VALID_RECOVERY
    assert res.reason_code == Stage0Reason.GENUINE_RECOVERABLE
    assert res.is_recoverable is True


def test_m4_05_stage0_phantom_loss_rejection(base_opportunity):
    """M4-05: Verify Stage 0 rejects zero-amount or invalid opportunities."""
    invalid_opp = RecoveryOpportunity(
        opportunity_id="opp_zero",
        merchant_id="merch_test",
        customer_id="cust_01",
        source_event_id="evt_zero",
        event_type=EventType.FAILED_PAYMENT,
        amount=Money(0),
        currency="INR",
        status=EventType.FAILED_PAYMENT,
        source=EventSource.SIMULATED,
        occurred_at="2026-09-01T10:00:00+00:00",
        observed_at="2026-09-01T10:00:00+00:00",
    )
    evaluator = Stage0Evaluator()
    res = evaluator.evaluate(invalid_opp, decision_timestamp="2026-09-01T10:00:00+00:00")
    assert res.decision == Stage0Decision.NOT_RECOVERABLE
    assert res.reason_code == Stage0Reason.INVALID_EVENT


def test_m4_06_self_cure_handling(base_opportunity):
    """M4-06: Verify Stage 0 rejects self-cured/already-paid opportunities."""
    evaluator = Stage0Evaluator()
    context = {"is_paid": True, "paid_at": "2026-09-01T10:05:00+00:00", "payment_status": "SUCCESS"}
    res = evaluator.evaluate(base_opportunity, decision_timestamp="2026-09-01T10:10:00+00:00", context_state=context)
    assert res.decision == Stage0Decision.NOT_RECOVERABLE
    assert res.reason_code == Stage0Reason.SELF_CURED


def test_m4_07_duplicate_event_handling(base_opportunity):
    """M4-07: Verify Stage 0 rejects duplicate webhook events."""
    evaluator = Stage0Evaluator()
    context = {"is_duplicate": True, "duplicate_event_id": "evt_00"}
    res = evaluator.evaluate(base_opportunity, decision_timestamp="2026-09-01T10:10:00+00:00", context_state=context)
    assert res.decision == Stage0Decision.NOT_RECOVERABLE
    assert res.reason_code == Stage0Reason.DUPLICATE_EVENT


def test_m4_08_tds_withholding_handling(base_opportunity):
    """M4-08: Verify Stage 0 rejects TDS withholding exclusions."""
    evaluator = Stage0Evaluator()
    context = {"is_tds_withheld": True, "tds_amount_paise": 10000}
    res = evaluator.evaluate(base_opportunity, decision_timestamp="2026-09-01T10:10:00+00:00", context_state=context)
    assert res.decision == Stage0Decision.NOT_RECOVERABLE
    assert res.reason_code == Stage0Reason.TDS_WITHHOLDING_EXCLUSION


def test_m4_09_completed_state_handling():
    """M4-09: Verify Stage 0 rejects completed checkout and resolved invoice opportunities."""
    evaluator = Stage0Evaluator()

    checkout_opp = RecoveryOpportunity(
        opportunity_id="opp_chk",
        merchant_id="merch_test",
        customer_id="cust_01",
        source_event_id="evt_chk",
        event_type=EventType.ABANDONED_CHECKOUT,
        amount=Money.from_rupees(500),
        currency="INR",
        status=EventType.ABANDONED_CHECKOUT,
        source=EventSource.SIMULATED,
        occurred_at="2026-09-01T10:00:00+00:00",
        observed_at="2026-09-01T10:00:00+00:00",
    )
    res_chk = evaluator.evaluate(checkout_opp, decision_timestamp="2026-09-01T10:10:00+00:00", context_state={"checkout_completed": True})
    assert res_chk.decision == Stage0Decision.NOT_RECOVERABLE
    assert res_chk.reason_code == Stage0Reason.CHECKOUT_COMPLETED

    invoice_opp = RecoveryOpportunity(
        opportunity_id="opp_inv",
        merchant_id="merch_test",
        customer_id="cust_01",
        source_event_id="evt_inv",
        event_type=EventType.OVERDUE_B2B_INVOICE,
        amount=Money.from_rupees(50000),
        currency="INR",
        status=EventType.OVERDUE_B2B_INVOICE,
        source=EventSource.SIMULATED,
        occurred_at="2026-09-01T10:00:00+00:00",
        observed_at="2026-09-01T10:00:00+00:00",
    )
    res_inv = evaluator.evaluate(invoice_opp, decision_timestamp="2026-09-01T10:10:00+00:00", context_state={"invoice_status": "PAID"})
    assert res_inv.decision == Stage0Decision.NOT_RECOVERABLE
    assert res_inv.reason_code == Stage0Reason.INVOICE_RESOLVED


def test_m4_10_point_in_time_enforcement(base_opportunity):
    """M4-10: Verify Stage 0 passes when observed_at <= decision_timestamp."""
    evaluator = Stage0Evaluator()
    res = evaluator.evaluate(base_opportunity, decision_timestamp="2026-09-01T10:00:00+00:00", context_state={"observed_at": "2026-09-01T10:00:00+00:00"})
    assert res.decision == Stage0Decision.VALID_RECOVERY


def test_m4_11_future_event_leakage_rejection(base_opportunity):
    """M4-11: Verify Stage 0 raises PointInTimeLeakageError when evidence observed_at > decision_timestamp (INV-7)."""
    evaluator = Stage0Evaluator()
    future_context = {"observed_at": "2026-09-01T12:00:00+00:00"}  # 2 hours in future!

    with pytest.raises(PointInTimeLeakageError):
        evaluator.evaluate(base_opportunity, decision_timestamp="2026-09-01T10:00:00+00:00", context_state=future_context, strict_point_in_time=True)

    # In non-strict mode, returns POINT_IN_TIME_LEAKAGE reason code
    res = evaluator.evaluate(base_opportunity, decision_timestamp="2026-09-01T10:00:00+00:00", context_state=future_context, strict_point_in_time=False)
    assert res.decision == Stage0Decision.NOT_RECOVERABLE
    assert res.reason_code == Stage0Reason.POINT_IN_TIME_LEAKAGE
