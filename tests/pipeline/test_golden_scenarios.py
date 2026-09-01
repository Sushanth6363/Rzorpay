"""Golden Scenario Regression Fixture Tests (S001..S010) for M4 Recovery Pipeline."""

from app.domain.enums import ActionType, DiagnosisCode, Stage0Decision, Stage0Reason
from app.pipeline.downtime import SimulatedDowntimeProvider
from app.pipeline.recovery_pipeline import RecoveryPipeline
from app.pipeline.scenarios import get_golden_scenarios


def test_golden_scenarios_s001_to_s010():
    """Verify all 10 golden scenarios (S001..S010) produce expected Stage 0, Stage 1, and Candidate filter outputs."""
    scenarios = get_golden_scenarios()

    for sc_id, sc in scenarios.items():
        raw_event = sc["raw_event"]

        # Setup downtime provider if scenario specifies outage
        downtime_provider = SimulatedDowntimeProvider()
        if raw_event.get("is_downtime", False):
            downtime_provider.set_outage(raw_event.get("gateway", "razorpay"), is_down=True)

        pipeline = RecoveryPipeline(downtime_provider=downtime_provider)
        ctx = pipeline.process_raw_event(raw_event, decision_timestamp="2026-09-01T10:00:00+00:00")

        # 1. Verify Stage 0 Decision
        assert ctx.stage0_result.decision.value == sc["expected_stage0"], f"{sc_id} Stage 0 decision mismatch!"

        if "expected_stage0_reason" in sc:
            assert ctx.stage0_result.reason_code.value == sc["expected_stage0_reason"], f"{sc_id} Stage 0 reason code mismatch!"

        # 2. Verify Stage 1 Diagnosis if specified
        if "expected_diagnosis" in sc:
            assert ctx.diagnosis.diagnosis_code.value == sc["expected_diagnosis"], f"{sc_id} Stage 1 diagnosis mismatch!"

        # 3. Verify Candidate Safety Filter outcomes if specified
        if "expected_eligible_actions" in sc:
            eligible_types = [c.action_type.value for c in ctx.get_eligible_candidates()]
            for expected_action in sc["expected_eligible_actions"]:
                assert expected_action in eligible_types, f"{sc_id} expected eligible action '{expected_action}' missing!"

        if "expected_safety_rejected_actions" in sc:
            rejected_types = [c.action_type.value for c in ctx.candidates if not c.is_eligible]
            for expected_rejected in sc["expected_safety_rejected_actions"]:
                assert expected_rejected in rejected_types, f"{sc_id} expected rejected action '{expected_rejected}' missing!"

        if "expected_safety_reject_reason" in sc:
            for c in ctx.candidates:
                if not c.is_eligible:
                    assert c.reject_reason.value == sc["expected_safety_reject_reason"], f"{sc_id} reject reason mismatch!"

        if sc.get("expected_has_assisted_channels", False):
            candidate_types = [c.action_type for c in ctx.candidates]
            assert ActionType.IVR_CALL in candidate_types
            assert ActionType.AGENT_DIAL in candidate_types

        if sc.get("expected_multiple_eligible", False):
            assert len(ctx.get_eligible_candidates()) >= 3

        # 4. Verify Contact Slot Reservation Invariant
        assert ctx.is_contact_reserved is False, f"{sc_id} violated M4 contact slot reservation invariant!"
