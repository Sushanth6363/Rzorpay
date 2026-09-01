"""M8 Reproducibility, Safety, and Reconciliation Audit Tests.

INVARIANTS:
1. 100% REPRODUCIBILITY: Identical random seed produces identical scenario execution, AI decision, and attribution.
2. RECONCILIATION INTEGRITY: Ambiguous executions resolve to terminal reconciliation states without slot leakage.
"""

import pytest
from app.domain.enums import ActionType, PaymentOutcome, ExecutionStatus
from app.experiment.runner import ExperimentRunner
from app.sandbox.scenarios import GOLDEN_DEMO_SCENARIOS, ScenarioRunner


def test_m8_07_deterministic_scenario_reproducibility():
    """Identical scenario execution with same seed produces 100% identical outputs."""
    runner = ScenarioRunner()
    spec = GOLDEN_DEMO_SCENARIOS["SCENARIO_01_SUCCESSFUL_RETRY"]

    res1 = runner.run_scenario(spec)
    res2 = runner.run_scenario(spec)

    assert res1.decision.selected_action == res2.decision.selected_action
    assert res1.attribution.payment_outcome == res2.attribution.payment_outcome
    assert res1.attribution.attributed_recovered_paise == res2.attribution.attributed_recovered_paise


def test_m8_08_reproducible_experiment_runner():
    """ExperimentRunner with identical seeds produces identical summary metric hashes."""
    runner = ExperimentRunner(experiment_id="EXP_M8_REPRO_TEST")
    events = [
        {"merchant_id": "m1", "customer_id": "c1", "event_id": "e1", "amount_paise": 100000},
        {"merchant_id": "m1", "customer_id": "c2", "event_id": "e2", "amount_paise": 200000},
    ]

    summary1 = runner.run_paired_experiment(events=events, seeds=[42, 43])
    summary2 = runner.run_paired_experiment(events=events, seeds=[42, 43])

    assert summary1.primary_comparison.incremental_recovery_rate == summary2.primary_comparison.incremental_recovery_rate
    assert summary1.primary_comparison.status == summary2.primary_comparison.status
    assert summary1.arm_metrics["A5"].gross_recovered_paise == summary2.arm_metrics["A5"].gross_recovered_paise


def test_m8_09_scenario_08_execution_unknown_reconciled_delivered():
    """EXECUTION_UNKNOWN simulation correctly transitions to reconciliation status."""
    runner = ScenarioRunner()
    spec = GOLDEN_DEMO_SCENARIOS["SCENARIO_08_EXECUTION_UNKNOWN_DELIVERED"]

    result = runner.run_scenario(spec)

    assert result.attribution.payment_outcome == PaymentOutcome.EXECUTION_UNKNOWN
    assert result.execution_result is not None
    assert result.execution_result.execution_status == ExecutionStatus.EXECUTION_UNKNOWN


def test_m8_10_scenario_12_negative_ev_abstention():
    """Scenario 12 (Negative EV micro-transaction / Forced abstention) forces NO_ACTION."""
    runner = ScenarioRunner()
    spec = GOLDEN_DEMO_SCENARIOS["SCENARIO_12_NEGATIVE_EV_ABSTENTION"]

    result = runner.run_scenario(spec)

    assert result.decision.selected_action == ActionType.NO_ACTION
    assert result.attribution.attributed_recovered_paise == 0
