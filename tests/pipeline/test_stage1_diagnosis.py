"""Tests for Stage 1 failure diagnosis and gateway downtime safety (M4-12..14)."""

from app.domain.enums import ActionType, DiagnosisCode, EventSource, EventType
from app.domain.models import RecoveryOpportunity
from app.domain.money import Money
from app.pipeline.downtime import SimulatedDowntimeProvider
from app.pipeline.stage1 import Stage1Diagnoser


def test_m4_12_stage1_diagnosis_categories():
    """M4-12: Verify Stage 1 correctly diagnoses failure categories across streams."""
    diagnoser = Stage1Diagnoser()

    opp_payment = RecoveryOpportunity(
        opportunity_id="opp_01",
        merchant_id="merch_01",
        customer_id="cust_01",
        source_event_id="evt_01",
        event_type=EventType.FAILED_PAYMENT,
        amount=Money.from_rupees(100),
        currency="INR",
        status=EventType.FAILED_PAYMENT,
        source=EventSource.SIMULATED,
        occurred_at="2026-09-01T10:00:00+00:00",
        observed_at="2026-09-01T10:00:00+00:00",
    )
    diag_payment = diagnoser.diagnose(opp_payment, context_state={"failure_reason": "INSUFFICIENT_FUNDS"})
    assert diag_payment.diagnosis_code == DiagnosisCode.INSUFFICIENT_FUNDS
    assert diag_payment.confidence > 0.9

    opp_card = RecoveryOpportunity(
        opportunity_id="opp_02",
        merchant_id="merch_01",
        customer_id="cust_01",
        source_event_id="evt_02",
        event_type=EventType.FAILED_PAYMENT,
        amount=Money.from_rupees(100),
        currency="INR",
        status=EventType.FAILED_PAYMENT,
        source=EventSource.SIMULATED,
        occurred_at="2026-09-01T10:00:00+00:00",
        observed_at="2026-09-01T10:00:00+00:00",
    )
    diag_card = diagnoser.diagnose(opp_card, context_state={"failure_reason": "CARD_LIMIT_EXCEEDED"})
    assert diag_card.diagnosis_code == DiagnosisCode.CARD_DECLINED

    opp_checkout = RecoveryOpportunity(
        opportunity_id="opp_03",
        merchant_id="merch_01",
        customer_id="cust_01",
        source_event_id="evt_03",
        event_type=EventType.ABANDONED_CHECKOUT,
        amount=Money.from_rupees(100),
        currency="INR",
        status=EventType.ABANDONED_CHECKOUT,
        source=EventSource.SIMULATED,
        occurred_at="2026-09-01T10:00:00+00:00",
        observed_at="2026-09-01T10:00:00+00:00",
    )
    diag_checkout = diagnoser.diagnose(opp_checkout)
    assert diag_checkout.diagnosis_code == DiagnosisCode.CUSTOMER_ABANDONMENT


def test_m4_13_gateway_outage_diagnosis():
    """M4-13: Verify active gateway downtime automatically diagnoses as GATEWAY_FAILURE."""
    downtime_provider = SimulatedDowntimeProvider()
    downtime_provider.set_outage("hdfc_bank", is_down=True)

    diagnoser = Stage1Diagnoser(downtime_provider=downtime_provider)

    opp = RecoveryOpportunity(
        opportunity_id="opp_down",
        merchant_id="merch_01",
        customer_id="cust_01",
        source_event_id="evt_down",
        event_type=EventType.FAILED_PAYMENT,
        amount=Money.from_rupees(100),
        currency="INR",
        status=EventType.FAILED_PAYMENT,
        source=EventSource.SIMULATED,
        occurred_at="2026-09-01T10:00:00+00:00",
        observed_at="2026-09-01T10:00:00+00:00",
    )
    diag = diagnoser.diagnose(opp, context_state={"gateway": "hdfc_bank"})
    assert diag.diagnosis_code == DiagnosisCode.GATEWAY_FAILURE
    assert diag.evidence["is_gateway_down"] is True
    assert diag.confidence == 1.0


def test_m4_14_outage_retry_suppression():
    """M4-14: Verify gateway outage suppresses retry and outreach recommendations via pipeline."""
    from app.pipeline.recovery_pipeline import RecoveryPipeline

    downtime_provider = SimulatedDowntimeProvider()
    downtime_provider.set_outage("razorpay", is_down=True)

    pipeline = RecoveryPipeline(downtime_provider=downtime_provider)

    raw_event = {
        "merchant_id": "merch_alpha",
        "customer_id": "cust_100",
        "event_id": "evt_downtime",
        "event_type": EventType.FAILED_PAYMENT.value,
        "amount_paise": 100000,
        "currency": "INR",
        "occurred_at": "2026-09-01T10:00:00+00:00",
        "gateway": "razorpay",
    }

    ctx = pipeline.process_raw_event(raw_event)

    assert ctx.diagnosis.diagnosis_code == DiagnosisCode.GATEWAY_FAILURE

    # Verify NO_ACTION is eligible, but outreach/retry candidates are SAFETY_REJECTED due to KNOWN_GATEWAY_OUTAGE
    eligible_actions = [c.action_type for c in ctx.get_eligible_candidates()]
    assert eligible_actions == [ActionType.NO_ACTION]

    rejected_candidates = [c for c in ctx.candidates if not c.is_eligible]
    assert len(rejected_candidates) > 0
    for c in rejected_candidates:
        assert c.reject_reason.value == "KNOWN_GATEWAY_OUTAGE"
