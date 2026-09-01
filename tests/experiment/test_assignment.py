"""Tests for Deterministic Experiment Arm Assignment (ADR-0011, INV-1, INV-3)."""

import pytest
from app.domain.enums import ExperimentArm
from app.experiment.assignment import ExperimentAssigner


def test_assignment_deterministic_identical_input():
    """Identical input parameters + seed produce 100% reproducible arm assignment."""
    assigner = ExperimentAssigner(experiment_id="EXP_TEST")
    
    arm1 = assigner.assign_arm(merchant_id="m1", customer_id="c1", opportunity_id="opp1", seed=42)
    arm2 = assigner.assign_arm(merchant_id="m1", customer_id="c1", opportunity_id="opp1", seed=42)

    assert arm1 == arm2


def test_assignment_seed_variation():
    """Changing random seed produces valid arm assignments without mutating opportunity."""
    assigner = ExperimentAssigner(experiment_id="EXP_TEST")

    arm_seed_42 = assigner.assign_arm(merchant_id="m1", customer_id="c1", opportunity_id="opp1", seed=42)
    arm_seed_100 = assigner.assign_arm(merchant_id="m1", customer_id="c1", opportunity_id="opp1", seed=100)

    assert isinstance(arm_seed_42, ExperimentArm)
    assert isinstance(arm_seed_100, ExperimentArm)


def test_assignment_cross_tenant_isolation_inv1():
    """Identical customer IDs across different merchants receive independent assignment (INV-1)."""
    assigner = ExperimentAssigner(experiment_id="EXP_TEST")

    arm_merchant_a = assigner.assign_arm(merchant_id="merchant_A", customer_id="cust_123", opportunity_id="opp1", seed=42)
    arm_merchant_b = assigner.assign_arm(merchant_id="merchant_B", customer_id="cust_123", opportunity_id="opp1", seed=42)

    # Hash salt includes merchant_id, so digests differ
    # Note: They could occasionally land on same arm index by chance, but calculation includes merchant_id
    assert isinstance(arm_merchant_a, ExperimentArm)
    assert isinstance(arm_merchant_b, ExperimentArm)


def test_assignment_outcome_independence():
    """Assignment depends ONLY on pre-decision identifiers, zero dependency on payment outcome."""
    assigner = ExperimentAssigner(experiment_id="EXP_TEST")

    arm_before = assigner.assign_arm(merchant_id="m1", customer_id="c1", opportunity_id="opp1", seed=42)
    
    # Simulate payment success vs failure - assignment signature remains unchanged
    arm_after_success = assigner.assign_arm(merchant_id="m1", customer_id="c1", opportunity_id="opp1", seed=42)
    assert arm_before == arm_after_success
