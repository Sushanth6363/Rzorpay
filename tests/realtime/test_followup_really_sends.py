"""A follow-up on a real case must actually send, and record what the dispatcher did.

WHY THIS EXISTS
    The escalation ladder climbed on camera while the phone stayed silent. The ledger
    from that live run, with the writer of each row:

        EMAIL_LINK  EXECUTED  source=ChannelDispatcher   <- real, the first touch
        EMAIL_LINK  EXECUTED  source=simulator           <- nothing was sent
        SMS_LINK    EXECUTED  source=simulator           <- nothing was sent

        dispatch_log: one row. The email. Nothing else.

    Two separate faults in one code path, both in `_process`, which was written for
    webhook traffic and then reused for follow-ups:

    1. It calls `process_and_execute` WITHOUT `defer_execution_result`, so the SANDBOX
       SIMULATOR's imagined outcome is stamped into contact_ledger as a confirmed contact.
       `RecoveryAgent` had already been fixed for exactly this; the follow-up path had not.

    2. Its idea of "dispatch" is creating a payment link. It never calls ChannelDispatcher
       at all, so no email, SMS or WhatsApp is ever sent on a follow-up.

    Together: every escalation after the first touch was fabricated. And because
    `get_customer_ledger_history` drives the escalation ceiling, the contact budget and
    the "already tried" handoff report, every one of those was reading invented history.
    A fabricated contact does not merely fail to send - it spends a real contact slot and
    pushes the customer one rung closer to a phone call.

WHAT MUST NOT CHANGE
    Webhook-born opportunities have no Case row and still belong to `_process`, which is
    what it was written for. Only follow-ups that resolve to a case take the agent path.
"""

import json

import pytest

from app.cases.csv_ingest import create_cases, parse_csv
from app.cases.repository import CaseRepository

CSV = """customer_id,name,email,phone,amount,due_date
Z9,Test Person,z@example.com,9845012345,25000,2026-08-24
"""


@pytest.fixture()
def live(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOVERY_DB_PATH", str(tmp_path / "fu.db"))
    monkeypatch.setenv("RECOVERY_DISPATCH_ENABLED", "true")
    monkeypatch.setenv("RECOVERY_ALLOW_SIMULATED_LINKS", "true")
    # Pinned, not inherited. The scripted demo ladder changes which rung a follow-up takes,
    # so leaving this to whatever a previous test file exported makes these pass alone and
    # fail in the suite - which is how it first showed up.
    monkeypatch.setenv("RECOVERY_DEMO_FIXED_LADDER", "false")
    import importlib
    from app.realtime import config as cfg
    importlib.reload(cfg)
    from app.realtime import ingest as ing
    importlib.reload(ing)
    from app.realtime import followup as f
    importlib.reload(f)
    f.ensure_schema()
    from app.api import webhook_listener as wl
    importlib.reload(wl)

    conn = ing.get_conn()
    repo = CaseRepository(conn)
    case = create_cases(repo, parse_csv(CSV).valid, merchant_id="merch_demo")[0]
    return wl, conn, repo, case


@pytest.fixture()
def captured(monkeypatch):
    """Every channel the dispatcher actually reaches for, recorded."""
    from app.dispatch import channels
    seen = []

    def _email(to, *a, **k):
        seen.append(("EMAIL", to))
        return channels.DispatchResult("EMAIL_SMTP", "SENT", "ok", provider_id="M1")

    def _sms(to, *a, **k):
        seen.append(("SMS", to))
        return channels.DispatchResult("TWILIO_SMS", "SENT", "ok", provider_id="M2")

    monkeypatch.setattr(channels, "send_email_smtp", _email)
    monkeypatch.setattr(channels, "send_sms", _sms)
    return seen


def _ledger(conn):
    conn.row_factory = None
    return conn.execute(
        "SELECT action_type, status, metadata_json FROM contact_ledger ORDER BY rowid"
    ).fetchall()


# --- it sends -----------------------------------------------------------------------


def test_a_follow_up_actually_reaches_a_channel(live, captured):
    """The defect. Before this, a follow-up sent nothing and said it had."""
    wl, conn, repo, case = live

    wl._run_case_followup(case.case_id, "followup:test")

    assert captured, "the follow-up dispatched nothing at all"


def test_the_ledger_names_the_dispatcher_not_the_simulator(live, captured):
    """`source=simulator` on a contact row is a fabricated observation."""
    wl, conn, repo, case = live

    wl._run_case_followup(case.case_id, "followup:test")

    blob = " ".join(str(m) for _, _, m in _ledger(conn))
    assert "ChannelDispatcher" in blob
    assert "PAYMENT_SUCCESS" not in blob, "a simulated outcome reached the ledger"


def test_the_dispatch_log_and_the_ledger_agree(live, captured):
    """The invariant the live run broke: a confirmed contact must correspond to a message
    the dispatch log says was really sent."""
    wl, conn, repo, case = live

    wl._run_case_followup(case.case_id, "followup:test")

    conn.row_factory = None
    executed = [s for _, s, _ in _ledger(conn) if s == "EXECUTED"]
    sent = conn.execute(
        "SELECT COUNT(*) FROM dispatch_log WHERE status='SENT'").fetchone()[0]
    assert len(executed) == sent


def test_a_failed_send_is_not_recorded_as_a_confirmed_contact(live, monkeypatch):
    """A fabricated contact does not just fail to send - it spends a contact slot and
    pushes the customer one rung closer to a phone call."""
    from app.dispatch import channels
    monkeypatch.setattr(channels, "send_email_smtp",
                        lambda *a, **k: channels.DispatchResult(
                            "EMAIL_SMTP", "FAILED", "smtp refused"))
    wl, conn, repo, case = live

    wl._run_case_followup(case.case_id, "followup:test")

    assert all(s != "EXECUTED" for _, s, _ in _ledger(conn))


# --- and it goes to the right place --------------------------------------------------


def test_a_follow_up_on_a_case_resolves_to_that_case(live):
    wl, conn, repo, case = live

    assert wl._case_id_for_followup(case.source_event_id) == case.case_id


def test_a_webhook_born_opportunity_has_no_case_and_keeps_the_old_path(live):
    """`_process` was written for webhook traffic and still owns it. Only follow-ups with
    a real Case take the agent path."""
    wl, conn, repo, case = live

    assert wl._case_id_for_followup("pay_SomeRazorpayPaymentId") == ""


def test_an_unresolvable_origin_does_not_raise(live):
    """A lookup failure must never kill the background worker."""
    wl, conn, repo, case = live

    assert wl._case_id_for_followup("") == ""


# --- a provider failure must not abandon the debt --------------------------------------


def test_a_failed_send_still_schedules_the_next_look(live, monkeypatch):
    """The case ended in silence when a provider refused.

    Scheduling used to require SENT or SKIPPED, reasoning that a message which did not go
    out has not started a conversation to follow up on. True of the conversation, wrong
    about the debt. Observed live: WhatsApp cannot send on a Twilio trial, so the ladder
    reached it, failed, and nothing was ever scheduled again. The money stayed owed, the
    engine stopped, and the board still showed the case in progress - which is worse than
    never having tried, because nobody would go looking.
    """
    from app.dispatch import channels
    monkeypatch.setattr(channels, "send_email_smtp",
                        lambda *a, **k: channels.DispatchResult(
                            "EMAIL_SMTP", "FAILED", "provider refused"))
    wl, conn, repo, case = live

    wl._run_case_followup(case.case_id, "followup:test")

    conn.row_factory = None
    scheduled = conn.execute(
        "SELECT COUNT(*) FROM followup_queue WHERE status='SCHEDULED';").fetchone()[0]
    assert scheduled >= 1, "a provider failure ended the case with nothing scheduled"


def test_a_blocked_send_does_not_schedule(live, monkeypatch):
    """BLOCKED is a control refusing, not a provider having a problem: the budget is spent,
    the case is paid, an outage is on. Those are decisions to stop, and retrying them later
    would walk straight back through the control that just said no."""
    from app.dispatch import dispatcher as disp
    wl, conn, repo, case = live
    monkeypatch.setattr(
        disp.ChannelDispatcher, "precheck",
        lambda self, case_id, action: disp.DispatchOutcome(
            False, "BLOCKED", "contact budget exhausted"))

    wl._run_case_followup(case.case_id, "followup:blocked")

    conn.row_factory = None
    scheduled = conn.execute(
        "SELECT COUNT(*) FROM followup_queue WHERE status='SCHEDULED';").fetchone()[0]
    assert scheduled == 0
