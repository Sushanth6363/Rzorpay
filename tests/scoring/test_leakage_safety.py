"""Tests for Point-in-Time Feature Safety & Leakage Prevention (M5-13..15, INV-7)."""

import pytest
from app.pipeline.recovery_pipeline import RecoveryPipeline
from app.scoring.engine import AIRecoveryDecisionEngine
from app.scoring.feature_builder import FeatureBuilder, PointInTimeLeakageError


def test_m5_13_future_dated_feature_leakage_error():
    """M5-13: Verify FeatureBuilder raises PointInTimeLeakageError when observed_at > decision_timestamp (INV-7)."""
    with pytest.raises(PointInTimeLeakageError):
        FeatureBuilder.validate_point_in_time_safety(
            observed_at="2026-09-01T12:00:00+00:00",
            decision_timestamp="2026-09-01T10:00:00+00:00",  # Decision time is earlier than observation time!
        )


def test_m5_14_denylisted_post_decision_field_error():
    """M5-14: Verify FeatureBuilder raises PointInTimeLeakageError when denylisted post-decision fields are present."""
    extra = {"outcome": "RECOVERED", "recovered_at": "2026-09-01T11:00:00+00:00"}
    with pytest.raises(PointInTimeLeakageError):
        FeatureBuilder.validate_point_in_time_safety(
            observed_at="2026-09-01T10:00:00+00:00",
            decision_timestamp="2026-09-01T10:00:00+00:00",
            extra_fields=extra,
        )


def test_m5_15_post_decision_mutations_do_not_change_decision():
    """M5-15: Verify changing post-decision state does not alter the AI decision."""
    pipeline = RecoveryPipeline()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c1",
        "event_id": "e1",
        "amount_paise": 100000,
        "occurred_at": "2026-09-01T10:00:00+00:00",
        "observed_at": "2026-09-01T10:00:00+00:00",
    }
    context = pipeline.process_raw_event(raw, decision_timestamp="2026-09-01T10:00:00+00:00")

    engine = AIRecoveryDecisionEngine()
    decision1 = engine.evaluate_decision(context, random_seed=42)

    # Mutate post-decision context data
    mutated_context_data = dict(context.opportunity.context_data)
    mutated_context_data["post_event_retry_count"] = 5

    # Re-evaluate decision
    decision2 = engine.evaluate_decision(context, random_seed=42)

    assert decision1.selected_action == decision2.selected_action
    assert decision1.candidate_scores == decision2.candidate_scores
