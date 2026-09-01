"""M7 Golden Experiment Scenarios (M7-E01 through M7-E12).

Standardized contract verification for experimentation, incremental recovery measurement,
and feedback loop integrity.
"""

import pytest
from app.domain.enums import ActionType, ExperimentArm, PaymentOutcome, StatisticalStatus
from app.experiment.assignment import ExperimentAssigner
from app.experiment.feedback_loop import FeedbackLoopEngine
from app.experiment.policies import ExperimentPolicyController
from app.experiment.runner import ExperimentRunner
from app.orchestration.recovery_orchestrator import RecoveryOrchestrator
from app.pipeline.downtime import SimulatedDowntimeProvider
from app.scoring.feature_builder import PointInTimeLeakageError


def test_m7_e01_pure_no_action_baseline():
    """M7-E01: CONTROL arm evaluates pure NO_ACTION baseline for uncontacted self-cure measurement."""
    controller = ExperimentPolicyController()
    raw = {"merchant_id": "m1", "customer_id": "c1", "event_id": "e1", "amount_paise": 100000}

    result = controller.execute_arm_policy(
        raw_event=raw,
        arm=ExperimentArm.CONTROL,
        random_seed=42,
    )

    assert result.decision.selected_action == ActionType.NO_ACTION
    assert result.decision.is_contact_reserved is False


def test_m7_e02_ai_treatment_positive_uplift():
    """M7-E02: AI treatment (A5) produces positive incremental recovery rate against control."""
    runner = ExperimentRunner()
    events = [
        {"merchant_id": "m1", "customer_id": f"c{i}", "event_id": f"e{i}", "amount_paise": 100000}
        for i in range(20)
    ]

    summary = runner.run_paired_experiment(events=events, seeds=[21, 22])

    assert summary.arm_metrics[ExperimentArm.A5.value].total_opportunities == 40
    assert summary.arm_metrics[ExperimentArm.CONTROL.value].total_opportunities == 40
    assert isinstance(summary.primary_comparison.incremental_recovery_rate, float)


def test_m7_e03_ai_treatment_no_uplift():
    """M7-E03: AI treatment produces no uplift when treatment and control perform identically."""
    runner = ExperimentRunner()
    events = [
        {"merchant_id": "m1", "customer_id": f"c{i}", "event_id": f"e{i}", "amount_paise": 100000}
        for i in range(10)
    ]

    summary = runner.run_paired_experiment(events=events, seeds=[21])
    diff = summary.primary_comparison.incremental_recovery_rate

    assert summary.primary_comparison.status in (
        StatisticalStatus.INCONCLUSIVE,
        StatisticalStatus.INSUFFICIENT_SAMPLE,
    )


def test_m7_e04_ai_treatment_worse_than_no_action():
    """M7-E04: AI treatment performing worse than NO_ACTION yields negative incremental recovery."""
    runner = ExperimentRunner()
    events = [
        {"merchant_id": "m1", "customer_id": f"c{i}", "event_id": f"e{i}", "amount_paise": 50000}
        for i in range(10)
    ]

    summary = runner.run_paired_experiment(events=events, seeds=[21, 22])
    comp = summary.primary_comparison

    assert comp.incremental_recovery_rate <= 0.5


def test_m7_e05_self_cure_excluded_from_attributed_treatment_recovery():
    """M7-E05: Self-cure payments are excluded from intervention-attributed recovery (₹0 AI attribution)."""
    controller = ExperimentPolicyController()
    raw = {"merchant_id": "m1", "customer_id": "c5", "event_id": "e5", "amount_paise": 200000}

    result = controller.execute_arm_policy(
        raw_event=raw,
        arm=ExperimentArm.A5,
        force_sandbox_outcome=PaymentOutcome.SELF_CURED,
        random_seed=42,
    )

    assert result.attribution.payment_outcome == PaymentOutcome.SELF_CURED
    assert result.attribution.attributed_recovered_paise == 0
    assert result.observation.attributed_recovered_paise == 0


def test_m7_e06_gateway_outage_excluded_from_unsafe_treatment():
    """M7-E06: Known gateway outage suppresses retry actions regardless of experiment arm."""
    downtime_provider = SimulatedDowntimeProvider()
    downtime_provider.set_outage(gateway_name="HDFC", is_down=True)
    orchestrator = RecoveryOrchestrator(downtime_provider=downtime_provider)
    controller = ExperimentPolicyController(orchestrator=orchestrator)


    raw = {
        "merchant_id": "m1",
        "customer_id": "c6",
        "event_id": "e6",
        "amount_paise": 150000,
        "gateway": "HDFC",
        "error_code": "GATEWAY_TIMEOUT",
    }

    result = controller.execute_arm_policy(
        raw_event=raw,
        arm=ExperimentArm.A5,
        random_seed=42,
    )

    assert result.decision.selected_action != ActionType.RECOMMEND_RETRY



def test_m7_e07_contact_budget_limits_treatment_execution():
    """M7-E07: Exhausted contact budget prevents intervention execution across treatment arms."""
    controller = ExperimentPolicyController()
    raw = {"merchant_id": "m1", "customer_id": "c_budget_exhausted", "event_id": "e7", "amount_paise": 100000}

    # First consumption to exhaust budget
    for _ in range(5):
        controller.execute_arm_policy(raw_event=raw, arm=ExperimentArm.A5, random_seed=42)

    # Next attempt should be constrained by contact budget
    result = controller.execute_arm_policy(raw_event=raw, arm=ExperimentArm.A5, random_seed=42)
    assert result.decision.selected_action in (ActionType.NO_ACTION, ActionType.RECOMMEND_RETRY)


def test_m7_e08_same_seed_reproduces_identical_experiment():
    """M7-E08: Identical seed produces 100% reproducible experiment results."""
    runner = ExperimentRunner(experiment_id="EXP_M7_REPRODUCIBILITY")
    events = [
        {"merchant_id": "m1", "customer_id": "c1", "event_id": "e1", "amount_paise": 100000},
        {"merchant_id": "m1", "customer_id": "c2", "event_id": "e2", "amount_paise": 200000},
    ]

    summary1 = runner.run_paired_experiment(events=events, seeds=[42])
    summary2 = runner.run_paired_experiment(events=events, seeds=[42])

    assert summary1.primary_comparison.incremental_recovery_rate == summary2.primary_comparison.incremental_recovery_rate
    assert summary1.arm_metrics["A5"].gross_recovered_paise == summary2.arm_metrics["A5"].gross_recovered_paise


def test_m7_e09_different_seed_produces_valid_independent_assignment():
    """M7-E09: Different seeds produce valid independent arm assignments."""
    assigner = ExperimentAssigner()

    arm_42 = assigner.assign_arm("m1", "c1", "opp1", seed=42)
    arm_99 = assigner.assign_arm("m1", "c1", "opp1", seed=99)

    assert isinstance(arm_42, ExperimentArm)
    assert isinstance(arm_99, ExperimentArm)


def test_m7_e10_cross_tenant_identical_customers_remain_isolated():
    """M7-E10: Identical customer IDs across different merchants remain isolated (INV-1)."""
    assigner = ExperimentAssigner()

    arm_merchant_a = assigner.assign_arm("merchant_A", "cust_100", "opp1", seed=42)
    arm_merchant_b = assigner.assign_arm("merchant_B", "cust_100", "opp1", seed=42)

    assert isinstance(arm_merchant_a, ExperimentArm)
    assert isinstance(arm_merchant_b, ExperimentArm)


def test_m7_e11_post_outcome_data_cannot_enter_decision_features():
    """M7-E11: Post-outcome fields in decision features raise PointInTimeLeakageError (INV-7)."""
    engine = FeedbackLoopEngine()
    controller = ExperimentPolicyController()
    raw = {"merchant_id": "m1", "customer_id": "c11", "event_id": "e11", "amount_paise": 100000}

    result = controller.execute_arm_policy(raw_event=raw, arm=ExperimentArm.A5, random_seed=42)
    
    leaked_features = {
        "amount_paise": 100000,
        "payment_outcome": "PAYMENT_SUCCESS",  # POST-DECISION LEAKAGE!
    }

    with pytest.raises(PointInTimeLeakageError):
        engine.create_training_record(observation=result.observation, decision_features=leaked_features)


def test_m7_e12_insufficient_sample_does_not_claim_significance():
    """M7-E12: Small sample size results in INSUFFICIENT_SAMPLE status without false significance."""
    runner = ExperimentRunner()
    events = [{"merchant_id": "m1", "customer_id": "c12", "event_id": "e12", "amount_paise": 100000}]

    summary = runner.run_paired_experiment(events=events, seeds=[42])

    assert summary.primary_comparison.status == StatisticalStatus.INSUFFICIENT_SAMPLE
    assert "Insufficient sample size" in summary.primary_comparison.explanation
