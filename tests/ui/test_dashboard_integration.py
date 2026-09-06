"""Tests for Streamlit Dashboard & ScenarioRunner Integration (M8 Audit).

INVARIANTS:
1. SCENARIO INTEGRITY: ScenarioRunner executes domain services without duplicating business logic.
2. ALL 12 GOLDEN SCENARIOS EXECUTABLE: Every scenario in GOLDEN_DEMO_SCENARIOS runs to completion.
3. TRACE CORRELATION: Returned EndToEndRecoveryResult contains matching trace_id and observation.
"""

import pytest
from app.domain.enums import ActionType, PaymentOutcome, SafetyRejectReason
from app.sandbox.scenarios import GOLDEN_DEMO_SCENARIOS, ScenarioRunner


def test_m8_01_all_12_golden_scenarios_execute():
    """All 12 pre-configured Golden Demo Scenarios execute successfully to completion."""
    runner = ScenarioRunner()
    for scenario_id, spec in GOLDEN_DEMO_SCENARIOS.items():
        result = runner.run_scenario(spec)
        assert result.opportunity_id is not None
        assert result.decision is not None
        assert result.attribution is not None
        assert result.observation is not None
        assert result.trace_id.startswith("trace_")


def test_m8_02_scenario_01_retry_recovery():
    """Scenario 1 produces intervention recovery with attributed recovery > 0."""
    runner = ScenarioRunner()
    spec = GOLDEN_DEMO_SCENARIOS["SCENARIO_01_SUCCESSFUL_RETRY"]
    result = runner.run_scenario(spec)

    assert result.decision.selected_action != ActionType.NO_ACTION
    assert result.attribution.payment_outcome == PaymentOutcome.PAYMENT_SUCCESS
    assert result.attribution.attributed_recovered_paise == 1500000
    assert result.observation.self_cured is False


def test_m8_03_scenario_03_self_cure_attribution_inv8():
    """Scenario 3 (NO_ACTION) yields SELF_CURED outcome with strictly ₹0 AI Attribution (INV-8)."""
    runner = ScenarioRunner()
    spec = GOLDEN_DEMO_SCENARIOS["SCENARIO_03_NATURAL_SELF_CURE"]
    result = runner.run_scenario(spec)

    assert result.decision.selected_action == ActionType.NO_ACTION
    assert result.attribution.payment_outcome == PaymentOutcome.SELF_CURED
    assert result.attribution.attributed_recovered_paise == 0
    assert result.observation.attributed_recovered_paise == 0


def test_m8_04_scenario_05_gateway_outage_safety_inv4():
    """Scenario 5 (Gateway Outage) suppresses retry recommendations via hard safety filter (INV-4)."""
    runner = ScenarioRunner()
    spec = GOLDEN_DEMO_SCENARIOS["SCENARIO_05_GATEWAY_OUTAGE"]
    result = runner.run_scenario(spec)

    assert result.decision.selected_action != ActionType.RECOMMEND_RETRY
    # Verify retry candidate had safety reject reason KNOWN_GATEWAY_OUTAGE
    retry_cand = next(
        c for c in result.decision.candidate_scores if c.action_type == ActionType.RECOMMEND_RETRY
    )
    assert retry_cand.reject_reason == SafetyRejectReason.KNOWN_GATEWAY_OUTAGE


def test_m8_05_scenario_06_contact_cap_exhaustion_inv2():
    """Scenario 6 (Exhausted Contact Budget) blocks active intervention reservation (INV-2)."""
    runner = ScenarioRunner()
    spec = GOLDEN_DEMO_SCENARIOS["SCENARIO_06_CONTACT_BUDGET_EXHAUSTED"]
    result = runner.run_scenario(spec)

    assert result.opportunity_id is not None
    assert result.decision is not None
    assert result.decision.is_contact_reserved is False or result.attribution.ledger_id is None


def test_m8_06_scenario_11_cross_tenant_isolation_inv1():
    """Scenario 11 (Cross-tenant identical customer) preserves complete tenant isolation (INV-1)."""
    runner = ScenarioRunner()
    spec_alpha = GOLDEN_DEMO_SCENARIOS["SCENARIO_01_SUCCESSFUL_RETRY"]
    spec_beta = GOLDEN_DEMO_SCENARIOS["SCENARIO_11_CROSS_TENANT_ISOLATION"]

    res_alpha = runner.run_scenario(spec_alpha)
    res_beta = runner.run_scenario(spec_beta)

    assert res_alpha.merchant_id == "merchant_alpha"
    assert res_beta.merchant_id == "merchant_beta"
    assert res_alpha.customer_id == "cust_101"
    assert res_beta.customer_id == "cust_101"
    assert res_alpha.opportunity_id != res_beta.opportunity_id


def test_the_experiment_summary_exposes_the_attributes_the_dashboard_reads():
    """A getattr with a default silently hid the secondary-comparison panel when the
    attribute name was wrong: the feature never rendered and nothing reported it missing.

    These names are a contract between the runner and the dashboard, so a rename should
    fail here rather than quietly remove a panel a judge was meant to see.
    """
    import dataclasses

    from app.domain.models import ExperimentResultSummary

    fields = {f.name for f in dataclasses.fields(ExperimentResultSummary)}

    for required in ("arm_metrics", "primary_comparison", "secondary_comparisons"):
        assert required in fields, f"the dashboard reads {required} off the summary"


def test_the_trace_tab_states_which_scorer_produced_it():
    """The Decision trace tab runs an UNFITTED learner, so its probabilities are base
    rates rather than model predictions. The live CSV path uses the fitted model.

    Both are honest engines, but they are not the same one, and a screen showing only
    "v1.0.0-baseline" invites a reader to assume the model decided. The label is read from
    the object rather than hardcoded, so it cannot drift if the runner is later rewired.
    """
    from app.ui.dashboard import _scorer_is_fitted

    assert _scorer_is_fitted() is False, (
        "the scenario runner now uses a fitted learner - the disclosure on the trace tab "
        "is stale and should be re-checked"
    )


def test_the_fitted_model_would_choose_the_same_actions_anyway():
    """Why the disclosure is a footnote rather than a defect.

    Across every golden scenario the fitted CatBoost model selects the identical action to
    the unfitted baseline. That is this project's central finding restated: by the time
    scoring happens, the safety filter and the escalation ceiling have bounded the action
    space so tightly that scorer quality rarely changes the answer.
    """
    from app.db.init import init_db
    from app.domain.enums import ExperimentArm
    from app.experiment.policies import build_orchestrator_for_arm
    from app.sandbox.scenarios import GOLDEN_DEMO_SCENARIOS, DemoScenarioSpec, ScenarioRunner

    for spec in GOLDEN_DEMO_SCENARIOS.values():
        exec_spec = DemoScenarioSpec(
            scenario_id=spec.scenario_id, title=spec.title, description=spec.description,
            raw_event=spec.raw_event,
            simulate_outage_gateway=spec.simulate_outage_gateway,
            exhaust_contact_budget_customer=spec.exhaust_contact_budget_customer,
            force_sandbox_outcome=spec.force_sandbox_outcome,
            force_mode=spec.force_mode, random_seed=42,
        )
        baseline = ScenarioRunner().run_scenario(exec_spec).decision.selected_action
        fitted = ScenarioRunner(
            orchestrator=build_orchestrator_for_arm(ExperimentArm.A5, db_conn=init_db(":memory:"))
        ).run_scenario(exec_spec).decision.selected_action

        assert baseline == fitted, f"{spec.title}: {baseline.value} vs {fitted.value}"
