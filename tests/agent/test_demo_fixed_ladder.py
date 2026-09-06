"""The scripted demo ladder, and the audit that keeps it honest.

WHY THIS EXISTS
    The engine ranks by expected value, and the escalation ceiling is a CAP rather than an
    instruction. After one confirmed email SMS becomes ELIGIBLE, but on a Rs 25,000 invoice
    email still scores higher:

        EMAIL_LINK  ELIGIBLE  EV Rs 7,789
        SMS_LINK    ELIGIBLE  EV Rs 7,530

    So the engine keeps emailing. That is correct and it is impossible to demonstrate: the
    ladder never visibly moves, and an audience concludes escalation does not work.

    RECOVERY_DEMO_FIXED_LADDER makes the climb deterministic by taking the next eligible
    rung instead of the highest-scoring action. That is a SCRIPTED SEQUENCE, not a
    decision, and the danger is obvious: a fixed sequence presented as an engine choosing
    is a lie told to an audience. So every artifact it produces labels itself, and the
    tests below hold that line.

WHAT MUST NOT CHANGE
    Off by default. It never overrides a SAFETY_REJECTED candidate - a demo aid must not
    become a way to send something the engine refused.
"""

import json

import pytest

from app.cases.csv_ingest import create_cases, parse_csv
from app.cases.repository import CaseRepository
from app.domain.enums import ActionType

CSV = """customer_id,name,email,phone,amount,due_date
Z5,Test,z@example.com,9845012345,25000,2026-08-24
"""


@pytest.fixture()
def agent_and_case(tmp_path, monkeypatch, request):
    fixed = getattr(request, "param", True)
    monkeypatch.setenv("RECOVERY_DB_PATH", str(tmp_path / "ladder.db"))
    monkeypatch.setenv("RECOVERY_FOLLOWUP_HOUR_SECONDS", "0.02")
    monkeypatch.setenv("RECOVERY_DISPATCH_ENABLED", "true")
    monkeypatch.setenv("RECOVERY_ALLOW_SIMULATED_LINKS", "true")
    monkeypatch.setenv("RECOVERY_DEMO_FIXED_LADDER", "true" if fixed else "false")
    import importlib
    from app.realtime import config as cfg
    importlib.reload(cfg)
    from app.realtime import ingest as ing
    importlib.reload(ing)
    from app.realtime import followup as f
    importlib.reload(f)
    f.ensure_schema()

    from app.dispatch import channels
    for name, attr in (("EMAIL_SMTP", "send_email_smtp"), ("TWILIO_SMS", "send_sms"),
                       ("WA", "send_whatsapp")):
        monkeypatch.setattr(channels, attr, (lambda n: (
            lambda *a, **k: channels.DispatchResult(n, "SENT", "ok", provider_id="M")))(name))

    from app.agent.loop import RecoveryAgent
    conn = ing.get_conn()
    repo = CaseRepository(conn)
    case = create_cases(repo, parse_csv(CSV).valid, merchant_id="merch_demo")[0]
    return RecoveryAgent(conn, repository=repo), repo, case, conn


# --- it climbs, deterministically -----------------------------------------------------


def test_the_second_touch_moves_up_a_rung(agent_and_case):
    """The whole point: without this the second touch is email again."""
    agent, repo, case, conn = agent_and_case

    first = agent.run_cycle(case.case_id, attempt=0)
    second = agent.run_cycle(case.case_id, attempt=1)

    assert first.action == ActionType.EMAIL_LINK.value
    assert second.action == ActionType.SMS_LINK.value


def test_it_is_deterministic_across_repeats(agent_and_case):
    """A demo that works four times out of five is not demoable."""
    agent, repo, case, conn = agent_and_case

    actions = [agent.run_cycle(case.case_id, attempt=n).action for n in range(3)]

    assert actions[0] == ActionType.EMAIL_LINK.value
    assert actions[1] == actions[2] == ActionType.SMS_LINK.value


# --- and it never hides what it is ------------------------------------------------------


def test_a_scripted_choice_is_labelled_in_the_result(agent_and_case):
    agent, repo, case, conn = agent_and_case
    agent.run_cycle(case.case_id, attempt=0)

    second = agent.run_cycle(case.case_id, attempt=1)

    assert second.decision_mode == "SCRIPTED_LADDER"
    assert "DEMO FIXED LADDER" in second.reasoning


def test_the_timeline_says_it_was_scripted(agent_and_case):
    """The audience reads the timeline, not the return value."""
    agent, repo, case, conn = agent_and_case
    agent.run_cycle(case.case_id, attempt=0)
    agent.run_cycle(case.case_id, attempt=1)

    conn.row_factory = None
    rows = conn.execute(
        "SELECT summary FROM case_events WHERE kind='AGENT_DECIDED' ORDER BY event_id"
    ).fetchall()

    assert "SCRIPTED" in rows[1][0]
    assert "SCRIPTED" not in rows[0][0], "the genuine first decision was mislabelled"


def test_the_full_ranking_is_recorded_on_every_touch(agent_and_case):
    """The audit that makes "email keeps winning" checkable: SMS being ELIGIBLE and
    scoring lower is a different fact from SMS being blocked."""
    agent, repo, case, conn = agent_and_case
    agent.run_cycle(case.case_id, attempt=0)

    conn.row_factory = None
    detail = json.loads(conn.execute(
        "SELECT detail_json FROM case_events WHERE kind='AGENT_DECIDED' "
        "ORDER BY event_id LIMIT 1;").fetchone()[0])
    ranking = detail["ranking"]

    by_action = {r["action"]: r for r in ranking}
    assert by_action["EMAIL_LINK"]["eligibility"] == "ELIGIBLE"
    assert by_action["EMAIL_LINK"]["ev_rupees"] > by_action["SMS_LINK"]["ev_rupees"]
    assert by_action["WHATSAPP_LINK"]["rejected_for"] == "ESCALATION_CEILING"


# --- the line it must not cross -----------------------------------------------------------


def test_it_never_promotes_a_safety_rejected_action(agent_and_case):
    """A demo aid must not become a way to send what the engine refused."""
    agent, repo, case, conn = agent_and_case
    agent.run_cycle(case.case_id, attempt=0)

    second = agent.run_cycle(case.case_id, attempt=1)

    assert second.action != ActionType.AGENT_DIAL.value
    assert second.action != ActionType.WHATSAPP_LINK.value


@pytest.mark.parametrize("agent_and_case", [False], indirect=True)
def test_it_is_off_unless_asked_for(agent_and_case):
    """Default behaviour is the engine deciding, unchanged."""
    agent, repo, case, conn = agent_and_case

    first = agent.run_cycle(case.case_id, attempt=0)
    second = agent.run_cycle(case.case_id, attempt=1)

    assert second.decision_mode != "SCRIPTED_LADDER"
    assert "DEMO FIXED LADDER" not in second.reasoning
    assert first.action == ActionType.EMAIL_LINK.value


def test_the_flag_defaults_to_false():
    import importlib
    import os
    from app.realtime import config as cfg
    os.environ.pop("RECOVERY_DEMO_FIXED_LADDER", None)
    importlib.reload(cfg)

    assert cfg.DEMO_FIXED_LADDER is False
