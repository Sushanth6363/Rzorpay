"""The decision trace must actually change when you change the scenario.

WHY THIS EXISTS
    Working the scenario selector on the trace tab barely moved the page. The cause was
    two things at once, and either alone would have been enough to hide it:

    1. All twelve golden scenarios were FAILED_PAYMENT. The stream decides the candidate
       set, so eight of the twelve produced the IDENTICAL decision - RECOMMEND_RETRY,
       four eligible, three suppressed. Only the rupee figure moved.

    2. The trace's own prose was hardcoded. Step 3 said "Cause identified" without ever
       naming the cause, and step 4 asserted "a merchant-uploaded debt has no stored
       instrument" on every scenario including the ones that were not merchant-uploaded
       debt. A reader could not tell the scenarios apart because the page did not say
       what was different about them.

    A trace that reads the same whatever you feed it is not evidence of anything, which
    is the one job this tab has.

WHAT MUST NOT CHANGE
    These scenarios are demo fixtures only - nothing in results/ reads them, so adding
    to them cannot move the evaluation. The test at the bottom pins that separation.
"""

import re

import pytest

from app.domain.enums import ActionType, EligibilityStatus, EventType
from app.sandbox.scenarios import GOLDEN_DEMO_SCENARIOS, ScenarioRunner
from app.ui.dashboard import (
    _action_list,
    _diagnosis_source,
    _pretty,
    _ranking_note,
    _reject_breakdown,
    _retry_note,
)


def _run(key):
    return ScenarioRunner().run_scenario(GOLDEN_DEMO_SCENARIOS[key])


def _trace_prose(key):
    """The scenario-dependent sentences of the pipeline, as the page renders them."""
    spec = GOLDEN_DEMO_SCENARIOS[key]
    result = _run(key)
    d = result.decision
    eligible = [c for c in d.candidate_scores if c.eligibility == EligibilityStatus.ELIGIBLE]
    rejected = [c for c in d.candidate_scores if c.eligibility != EligibilityStatus.ELIGIBLE]
    chosen = next((c for c in d.candidate_scores if c.action_type == d.selected_action), None)
    return " | ".join([
        f"{result.merchant_id}/{result.customer_id}",
        _pretty(result.event_type),
        _pretty(result.diagnosis_code) + _diagnosis_source(spec.raw_event),
        _action_list(d.candidate_scores) + _retry_note(result, d),
        f"{len(eligible)}/{len(rejected)}" + _reject_breakdown(rejected),
        _ranking_note(d, eligible, chosen),
    ])


# --- the catalogue covers more than one stream ---------------------------------------


def test_every_track_3_stream_is_represented():
    """Track 3 names payment failures, checkout abandonment and overdue receivables. A
    trace tab that can only show one of them cannot demonstrate a unified engine."""
    streams = {_run(k).event_type for k in GOLDEN_DEMO_SCENARIOS}

    assert EventType.FAILED_PAYMENT in streams
    assert EventType.ABANDONED_CHECKOUT in streams
    assert EventType.OVERDUE_B2B_INVOICE in streams


def test_the_catalogue_produces_more_than_one_selected_action():
    actions = {_run(k).decision.selected_action for k in GOLDEN_DEMO_SCENARIOS}

    assert len(actions) >= 3, f"only {actions} across the whole catalogue"


# --- and the page says what is different about each one -------------------------------


def test_a_stream_without_a_stored_instrument_is_never_offered_a_retry():
    """The single clearest thing the stream changes, and what step 4 used to claim on
    every scenario regardless."""
    checkout = _run("SCENARIO_13_ABANDONED_CHECKOUT").decision

    offered = {c.action_type for c in checkout.candidate_scores}

    assert ActionType.RECOMMEND_RETRY not in offered


def test_the_retry_note_matches_whether_a_retry_was_actually_generated():
    for key in GOLDEN_DEMO_SCENARIOS:
        result = _run(key)
        d = result.decision
        offered = any(c.action_type == ActionType.RECOMMEND_RETRY for c in d.candidate_scores)

        note = _retry_note(result, d)

        assert ("No retry is offered" in note) is not offered, key


def test_the_diagnosis_is_named_rather_than_merely_asserted():
    """Step 3 used to say "Cause identified" and stop there."""
    invoice = _run("SCENARIO_14_OVERDUE_B2B_INVOICE")

    assert _pretty(invoice.diagnosis_code) == "Invoice Overdue"


def test_a_diagnosis_read_from_a_gateway_code_is_not_presented_like_a_stream_default():
    """Evidence and assumption must not render identically - the second is much weaker."""
    from_code = _diagnosis_source({"error_code": "INSUFFICIENT_FUNDS"})
    from_stream = _diagnosis_source({})

    assert "INSUFFICIENT_FUNDS" in from_code
    assert "no failure code" in from_stream
    assert from_code != from_stream


def test_the_suppression_count_says_what_suppressed_them():
    """A bare "6 suppressed" reads the same on every scenario. The reason does not."""
    outage = _run("SCENARIO_05_GATEWAY_OUTAGE").decision
    rejected = [c for c in outage.candidate_scores
                if c.eligibility != EligibilityStatus.ELIGIBLE]

    breakdown = _reject_breakdown(rejected)

    assert "Known Gateway Outage" in breakdown


def test_the_ranking_names_the_runner_up_it_beat():
    key = "SCENARIO_15_SUBSCRIPTION_RENEWAL"
    result = _run(key)
    d = result.decision
    eligible = [c for c in d.candidate_scores if c.eligibility == EligibilityStatus.ELIGIBLE]
    chosen = next(c for c in d.candidate_scores if c.action_type == d.selected_action)

    note = _ranking_note(d, eligible, chosen)

    assert "Recommend Retry" in note and "SMS Link" in note


def test_an_unopposed_winner_is_described_as_unopposed_not_as_a_contest():
    """When the safety filter leaves one survivor there is no margin to report, and
    inventing one would misrepresent where the decision was made."""
    result = _run("SCENARIO_05_GATEWAY_OUTAGE")
    d = result.decision
    eligible = [c for c in d.candidate_scores if c.eligibility == EligibilityStatus.ELIGIBLE]
    chosen = next(c for c in d.candidate_scores if c.action_type == d.selected_action)

    assert "unopposed" in _ranking_note(d, eligible, chosen)


# --- the defect, stated directly ------------------------------------------------------


def test_no_two_scenarios_render_an_identical_trace():
    """The bug as an invariant. Before the fix, eight of twelve collided here."""
    seen = {}
    for key in GOLDEN_DEMO_SCENARIOS:
        prose = _trace_prose(key)
        assert prose not in seen, (
            f"{key} renders the same trace as {seen.get(prose)}:\n  {prose}"
        )
        seen[prose] = key


def test_acronyms_are_not_mangled_into_something_that_looks_like_a_typo():
    assert _pretty(ActionType.SMS_LINK) == "SMS Link"
    assert _pretty(ActionType.IVR_CALL) == "IVR Call"
    assert _pretty(ActionType.WHATSAPP_LINK) == "WhatsApp Link"


# --- the evaluation cannot see any of this --------------------------------------------


def test_the_demo_catalogue_is_not_wired_into_the_evaluation():
    """Adding demo scenarios must not be able to move a number in results/. If this ever
    fails, the reproducibility hash is no longer independent of the demo fixtures."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2]
    readers = [
        path for path in (root / "app").rglob("*.py")
        if "GOLDEN_DEMO_SCENARIOS" in path.read_text(encoding="utf-8")
    ]
    offenders = [p for p in readers if p.parts[-2] in {"experiment", "sandbox"}
                 and p.name != "scenarios.py"]

    assert not offenders, f"the evaluation path now reads the demo catalogue: {offenders}"
