"""Property-based testing and deterministic behavior checks for M4 Recovery Pipeline (M4-22..28)."""

import json
from hypothesis import given, strategies as st
from app.domain.enums import ActionType, DataProvenance, EventSource, EventType, Stage0Decision, Stage0Reason
from app.domain.models import CanonicalEvent, RecoveryDecisionContext, RecoveryOpportunity
from app.domain.money import Money
from app.pipeline.dataset_adapter import DatasetAdapter
from app.pipeline.recovery_pipeline import RecoveryPipeline


def test_m4_22_deterministic_identical_input():
    """M4-22: Verify identical inputs produce identical RecoveryDecisionContext outputs."""
    pipeline = RecoveryPipeline()

    raw_event = {
        "merchant_id": "merch_det",
        "customer_id": "cust_det",
        "event_id": "evt_det",
        "event_type": EventType.FAILED_PAYMENT.value,
        "amount_paise": 45000,
        "currency": "INR",
        "occurred_at": "2026-09-01T10:00:00+00:00",
        "failure_reason": "INSUFFICIENT_FUNDS",
    }

    ctx1 = pipeline.process_raw_event(raw_event, decision_timestamp="2026-09-01T10:00:00+00:00")
    ctx2 = pipeline.process_raw_event(raw_event, decision_timestamp="2026-09-01T10:00:00+00:00")

    assert ctx1.to_dict() == ctx2.to_dict()


def test_m4_23_cross_tenant_identical_customer():
    """M4-23: Verify identical customer_id under different merchants are evaluated with full tenant isolation."""
    pipeline = RecoveryPipeline()

    raw_a = {
        "merchant_id": "merch_A",
        "customer_id": "cust_shared",
        "event_id": "evt_A",
        "event_type": EventType.FAILED_PAYMENT.value,
        "amount_paise": 100000,
        "currency": "INR",
        "occurred_at": "2026-09-01T10:00:00+00:00",
    }
    raw_b = {
        "merchant_id": "merch_B",
        "customer_id": "cust_shared",
        "event_id": "evt_B",
        "event_type": EventType.FAILED_PAYMENT.value,
        "amount_paise": 200000,
        "currency": "INR",
        "occurred_at": "2026-09-01T10:00:00+00:00",
    }

    ctx_a = pipeline.process_raw_event(raw_a)
    ctx_b = pipeline.process_raw_event(raw_b)

    assert ctx_a.opportunity.merchant_id == "merch_A"
    assert ctx_b.opportunity.merchant_id == "merch_B"
    assert ctx_a.feature_snapshot["merchant_id"] != ctx_b.feature_snapshot["merchant_id"]


def test_m4_24_feature_snapshot_point_in_time():
    """M4-24: Verify feature snapshot fields match decision timestamp and observed_at."""
    pipeline = RecoveryPipeline()
    raw_event = {
        "merchant_id": "merch_alpha",
        "customer_id": "cust_100",
        "event_id": "evt_snapshot",
        "event_type": EventType.FAILED_PAYMENT.value,
        "amount_paise": 50000,
        "currency": "INR",
        "occurred_at": "2026-09-01T10:00:00+00:00",
        "observed_at": "2026-09-01T10:00:00+00:00",
    }
    ctx = pipeline.process_raw_event(raw_event, decision_timestamp="2026-09-01T10:00:00+00:00")

    snap = ctx.feature_snapshot
    assert snap["decision_timestamp"] == "2026-09-01T10:00:00+00:00"
    assert snap["observed_at"] == "2026-09-01T10:00:00+00:00"


def test_m4_25_data_labeling_provenance():
    """M4-25: Verify clean data provenance tagging across REAL_DATA, SYNTHETIC_DATA, and SIMULATED_EXTERNAL_STATE."""
    pipeline = RecoveryPipeline()

    raw_sim = {"merchant_id": "m1", "customer_id": "c1", "event_id": "e1", "amount_paise": 100}
    ctx_sim = pipeline.process_raw_event(raw_sim, provenance=DataProvenance.SIMULATED_EXTERNAL_STATE)
    assert ctx_sim.provenance == DataProvenance.SIMULATED_EXTERNAL_STATE

    ctx_real = pipeline.process_raw_event(raw_sim, provenance=DataProvenance.REAL_DATA)
    assert ctx_real.provenance == DataProvenance.REAL_DATA


def test_m4_26_dataset_adapter_compatibility():
    """M4-26: Verify DatasetAdapter converts external raw dictionary into normalized CanonicalEvent."""
    raw_external = {
        "user_id": "usr_999",
        "payment_id": "pay_999",
        "amount": "250.50",
        "type": "FAILED_PAYMENT",
        "timestamp": "2026-09-01T12:00:00+00:00",
    }
    event, prov = DatasetAdapter.adapt_raw_event(raw_external, provenance=DataProvenance.SYNTHETIC_DATA)

    assert event.customer_id == "usr_999"
    assert event.source_event_id == "pay_999"
    assert event.amount.amount_paise == 25050
    assert prov == DataProvenance.SYNTHETIC_DATA


def test_m4_27_failure_path_behavior():
    """M4-27: Verify failure path behavior on malformed raw payload returns safe defaults or handles errors."""
    pipeline = RecoveryPipeline()
    malformed = {"merchant_id": "m1"}  # Missing customer_id, event_id, and amount (0 paise)
    ctx = pipeline.process_raw_event(malformed)

    assert ctx.opportunity.merchant_id == "m1"
    assert ctx.opportunity.customer_id == "cust_default"
    assert ctx.stage0_result.decision == Stage0Decision.NOT_RECOVERABLE
    assert ctx.stage0_result.reason_code == Stage0Reason.INVALID_EVENT


def test_m4_28_candidate_serialization_round_trip():
    """M4-28: Verify RecoveryDecisionContext serializes to JSON dict round-trip cleanly."""
    pipeline = RecoveryPipeline()
    raw = {"merchant_id": "m1", "customer_id": "c1", "event_id": "e1", "amount_paise": 1000}
    ctx = pipeline.process_raw_event(raw)

    serialized = ctx.to_dict()
    json_str = json.dumps(serialized)
    deserialized = json.loads(json_str)

    assert deserialized["opportunity"]["merchant_id"] == "m1"
    assert deserialized["stage0_result"]["decision"] == "VALID_RECOVERY"
    assert len(deserialized["candidates"]) > 0


# ------------------------------------------------------------------
# Hypothesis Property-Based Testing
# ------------------------------------------------------------------


@given(
    amount_paise=st.integers(min_value=1, max_value=10000000),
    event_type_str=st.sampled_from(["FAILED_PAYMENT", "ABANDONED_CHECKOUT", "FAILED_SUBSCRIPTION_RENEWAL", "OVERDUE_B2B_INVOICE"]),
)
def test_hypothesis_m4_no_action_always_eligible(amount_paise, event_type_str):
    """M4-36 Property Test: For all valid amounts and stream types, NO_ACTION is ALWAYS present and ELIGIBLE."""
    pipeline = RecoveryPipeline()
    raw = {
        "merchant_id": "merch_prop",
        "customer_id": "cust_prop",
        "event_id": f"evt_prop_{amount_paise}",
        "event_type": event_type_str,
        "amount_paise": amount_paise,
        "occurred_at": "2026-09-01T10:00:00+00:00",
    }
    ctx = pipeline.process_raw_event(raw)

    eligible_types = [c.action_type for c in ctx.get_eligible_candidates()]
    assert ActionType.NO_ACTION in eligible_types

    # Invariant: SAFETY_REJECTED ∩ ELIGIBLE == empty set
    rejected_types = set(c.action_type for c in ctx.candidates if not c.is_eligible)
    eligible_types_set = set(eligible_types)
    assert rejected_types.intersection(eligible_types_set) == set()
