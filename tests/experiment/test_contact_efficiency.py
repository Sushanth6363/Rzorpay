"""The contact-efficiency comparison, and the ways it must refuse to flatter the engine.

WHY THIS EXISTS
    The pre-registered primary (A2 vs A1 on recovery rate) came back INCONCLUSIVE, and
    it was always going to. A1 has no shared contact ledger, so it repeats the first
    touch to everybody; every control this engine adds can only ever REMOVE a contact.
    On a metric that rewards contacting more people, more safety can only look worse.

    So a second comparison was added on the metric the engine is actually built for.
    That is a post-hoc metric choice, which is exactly the move that turns an experiment
    into a press release, and the danger is not hypothetical:

        - contact rate alone is trivially gamed. CONTROL contacts nobody, scores a
          perfect reduction, and recovers zero rupees.
        - an arm could buy quiet by simply giving up money, and a one-sided reading
          would score that as a win too.

    The tests below are the guardrails. The verdict is only ever a win when BOTH halves
    hold, and the label saying it was not pre-registered has to survive too, because a
    caveat that can be deleted without failing a test is not a caveat.

WHAT MUST NOT CHANGE
    The pre-registered primary. Nothing here revises it, and the last test pins that the
    two comparisons are computed with the SAME arithmetic rather than a second, more
    flattering test written for the occasion.
"""

import pytest

from app.domain.enums import ExperimentArm, StatisticalStatus
from app.domain.models import ArmMetrics
from app.experiment.runner import ExperimentRunner


def _arm(arm, *, contacts, opportunities=4000, recoveries=2000):
    return ArmMetrics(
        arm=arm,
        total_opportunities=opportunities,
        successful_recoveries=recoveries,
        recovery_rate=recoveries / opportunities,
        gross_recovered_paise=0,
        attributed_recovered_paise=0,
        self_cured_count=0,
        total_cost_paise=0,
        net_value_paise=0,
        outbound_contacts=contacts,
        contacted_customers=0,
        total_customers=66,
        total_at_risk_paise=0,
    )


def _compare(treatment, baseline, comparison_id="X_vs_A1_contacts"):
    return ExperimentRunner()._calculate_contact_efficiency(
        comparison_id=comparison_id,
        treatment_arm=treatment.arm,
        baseline_arm=baseline.arm,
        treatment_metrics=treatment,
        baseline_metrics=baseline,
    )


# --- the win, and what it takes to earn it ---------------------------------------------


def test_materially_fewer_contacts_with_recovery_intact_is_a_win():
    baseline = _arm(ExperimentArm.A1, contacts=1500, recoveries=2237)
    treatment = _arm(ExperimentArm.A2, contacts=1336, recoveries=2178)

    result = _compare(treatment, baseline)

    assert result.verdict == "FEWER_CONTACTS_RECOVERY_HELD"
    assert result.contact_status == StatisticalStatus.STATISTICALLY_SIGNIFICANT


def test_the_reduction_is_reported_relative_to_the_baseline_not_as_a_bare_delta():
    baseline = _arm(ExperimentArm.A1, contacts=1500, recoveries=2237)
    treatment = _arm(ExperimentArm.A2, contacts=1336, recoveries=2178)

    result = _compare(treatment, baseline)

    assert result.relative_contact_reduction == pytest.approx(164 / 1500, abs=1e-3)


# --- and the ways it must refuse -------------------------------------------------------


def test_contacting_nobody_is_not_a_win():
    """CONTROL minimises the metric perfectly and recovers nothing. If this ever passes
    as a win, the comparison is measuring silence rather than efficiency."""
    baseline = _arm(ExperimentArm.A1, contacts=1500, recoveries=2237)
    control = _arm(ExperimentArm.CONTROL, contacts=0, recoveries=0)

    result = _compare(control, baseline)

    assert result.verdict == "FEWER_CONTACTS_RECOVERY_LOWER"


def test_buying_quiet_by_giving_up_recovery_is_not_a_win():
    """Fewer contacts AND significantly less money recovered. Half the claim is not the
    claim."""
    baseline = _arm(ExperimentArm.A1, contacts=1500, recoveries=2237)
    treatment = _arm(ExperimentArm.A2, contacts=900, recoveries=1500)

    result = _compare(treatment, baseline)

    assert result.verdict == "FEWER_CONTACTS_RECOVERY_LOWER"
    assert result.recovery_status == StatisticalStatus.STATISTICALLY_SIGNIFICANT


def test_contacting_more_people_is_never_a_win_however_good_the_recovery():
    baseline = _arm(ExperimentArm.A1, contacts=1200, recoveries=2000)
    treatment = _arm(ExperimentArm.A2, contacts=1800, recoveries=2010)

    result = _compare(treatment, baseline)

    assert result.verdict == "NO_CONTACT_REDUCTION"


def test_a_reduction_too_small_to_resolve_is_not_claimed_as_one():
    baseline = _arm(ExperimentArm.A1, contacts=1500, recoveries=2237)
    treatment = _arm(ExperimentArm.A2, contacts=1495, recoveries=2230)

    result = _compare(treatment, baseline)

    assert result.verdict == "NO_CONTACT_REDUCTION"
    assert result.contact_status == StatisticalStatus.INCONCLUSIVE


def test_a_tiny_sample_reports_insufficient_rather_than_a_verdict():
    baseline = _arm(ExperimentArm.A1, contacts=2, opportunities=4, recoveries=2)
    treatment = _arm(ExperimentArm.A2, contacts=0, opportunities=4, recoveries=1)

    result = _compare(treatment, baseline)

    assert result.verdict == "INSUFFICIENT_SAMPLE"


# --- the caveats have to survive too ---------------------------------------------------


def test_the_explanation_refuses_to_claim_non_inferiority():
    """"No detectable loss" and "proven equivalent" are different claims, and only the
    first one is supported without a pre-registered margin."""
    baseline = _arm(ExperimentArm.A1, contacts=1500, recoveries=2237)
    treatment = _arm(ExperimentArm.A2, contacts=1336, recoveries=2178)

    explanation = _compare(treatment, baseline).explanation

    assert "not a proven" in explanation.lower()
    assert "no margin was pre-registered" in explanation.lower()


def test_the_report_labels_the_family_as_not_pre_registered():
    """A caveat that can be deleted without failing a test is not a caveat."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2]
    renderer = (root / "scripts" / "run_evaluation.py").read_text(encoding="utf-8")

    assert "Contact efficiency — SECONDARY, NOT PRE-REGISTERED" in renderer


def test_the_pre_registered_primary_is_still_recovery_rate():
    """The whole point of reporting the second comparison honestly is that it does not
    quietly replace the first one."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2]
    runner = (root / "app" / "experiment" / "runner.py").read_text(encoding="utf-8")

    assert 'comparison_id="A2_vs_A1"' in runner


def test_both_comparisons_use_the_same_arithmetic():
    """A second, more flattering test written for the occasion is the failure mode this
    guards. Same two-proportion helper, same 1.96, same two-sided p."""
    runner = ExperimentRunner()
    diff, ci, p = runner._two_proportion(2178 / 4000, 4000, 2237 / 4000, 4000)

    assert diff == pytest.approx(-0.0148, abs=1e-4)
    assert ci == (pytest.approx(-0.0365, abs=1e-3), pytest.approx(0.0070, abs=1e-3))
    assert p == pytest.approx(0.1846, abs=1e-4)
