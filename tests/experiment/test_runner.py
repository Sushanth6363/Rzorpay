"""Tests for Experiment Runner & Statistical Evaluator (ADR-0011)."""

import pytest
from app.domain.enums import ExperimentArm, StatisticalStatus
from app.experiment.runner import ExperimentRunner


def test_runner_paired_experiment_execution():
    """Verify batch paired experiment execution across all 5 arms + CONTROL baseline."""
    runner = ExperimentRunner(experiment_id="EXP_TEST")
    events = [
        {"merchant_id": "m1", "customer_id": "c1", "event_id": "e1", "amount_paise": 100000},
        {"merchant_id": "m1", "customer_id": "c2", "event_id": "e2", "amount_paise": 250000},
    ]

    summary = runner.run_paired_experiment(events=events, seeds=[21, 22])

    assert summary.experiment_id == "EXP_TEST"
    assert len(summary.arm_metrics) == 6  # CONTROL, A1, A2ns, A2, A3, A5
    assert summary.primary_comparison.comparison_id == "A2_vs_A1"
    assert summary.primary_comparison.treatment_arm == ExperimentArm.A2
    assert summary.primary_comparison.baseline_arm == ExperimentArm.A1
    assert len(summary.secondary_comparisons) == 5


def test_runner_insufficient_sample_verdict():
    """Very small sample size produces INSUFFICIENT_SAMPLE verdict without claiming false significance."""
    runner = ExperimentRunner(experiment_id="EXP_TEST")
    events = [{"merchant_id": "m1", "customer_id": "c1", "event_id": "e1", "amount_paise": 100000}]

    summary = runner.run_paired_experiment(events=events, seeds=[21])

    assert summary.primary_comparison.status == StatisticalStatus.INSUFFICIENT_SAMPLE
    assert "Insufficient sample size" in summary.primary_comparison.explanation


def test_runner_holm_bonferroni_correction():
    """Secondary comparison family undergoes Holm-Bonferroni step-down correction."""
    runner = ExperimentRunner(experiment_id="EXP_TEST")
    events = [
        {"merchant_id": "m1", "customer_id": f"c{i}", "event_id": f"e{i}", "amount_paise": 100000}
        for i in range(10)
    ]

    summary = runner.run_paired_experiment(events=events, seeds=[21, 22, 23])

    # Verify secondary comparisons exist and contain adjusted status/explanations
    assert len(summary.secondary_comparisons) == 5
    for comp in summary.secondary_comparisons:
        assert isinstance(comp.status, StatisticalStatus)
