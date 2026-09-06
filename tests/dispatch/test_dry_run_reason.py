"""A skipped send must name the reason that actually applied.

WHY THIS EXISTS
    Every dry run recorded the same line:

        DRY RUN: RECOVERY_DISPATCH_ENABLED is not set, nothing was sent

    On a server where dispatch IS enabled, and the send was held only because the Live
    test page's dry-run toggle was on, that sentence is false. It was read exactly as
    intended and cost real time: the environment variable was checked, found correct,
    and the actual cause - a toggle on the screen - went unnoticed.

    There are two independent gates. `RECOVERY_DISPATCH_ENABLED` is the deployment level
    one, and the per-run override is the operator saying "decide but do not send". A
    record that collapses them into one message is not an audit trail, it is a guess.
"""

import sqlite3

import pytest

from app.cases.csv_ingest import create_cases, parse_csv
from app.cases.repository import CaseRepository
from app.db.init import init_db
from app.dispatch.dispatcher import ChannelDispatcher
from app.domain.enums import ActionType

CSV = """customer_id,name,email,amount,due_date
U_A,Rahul,rahul@example.com,25000,2026-08-24
"""


@pytest.fixture()
def case_and_conn(tmp_path):
    conn = init_db(str(tmp_path / "dry.db"))
    repo = CaseRepository(conn)
    case = create_cases(repo, parse_csv(CSV).valid, merchant_id="m1")[0]
    return conn, repo, case


def _skip_reason(conn, repo, case, dry_run, monkeypatch, dispatch_enabled=True, key="k1"):
    """One dispatch attempt, returning whatever the gate decided.

    `key` is a parameter because idempotency is real here: reusing one across two calls
    returns DUPLICATE on the second, which would test the de-duplication rather than the
    message under examination.
    """
    from app.realtime import config
    monkeypatch.setattr(config, "DISPATCH_ENABLED", dispatch_enabled, raising=False)
    dispatcher = ChannelDispatcher(conn, repository=repo, dry_run=dry_run)
    return dispatcher.dispatch(
        case_id=case.case_id, action=ActionType.EMAIL_LINK,
        idempotency_key=key, payment_url="https://rzp.io/rzp/X",
    )


def test_the_page_toggle_is_named_when_it_is_the_reason(case_and_conn, monkeypatch):
    """The defect. Dispatch is enabled, so the environment variable is not the cause."""
    conn, repo, case = case_and_conn

    outcome = _skip_reason(conn, repo, case, dry_run=True, monkeypatch=monkeypatch,
                           dispatch_enabled=True)

    assert outcome.status == "SKIPPED"
    assert "dry-run toggle" in outcome.reason
    assert "RECOVERY_DISPATCH_ENABLED" not in outcome.reason


def test_the_environment_variable_is_named_when_it_is_the_reason(case_and_conn, monkeypatch):
    """The other gate still has to be reported accurately, with no override in play."""
    conn, repo, case = case_and_conn

    outcome = _skip_reason(conn, repo, case, dry_run=None, monkeypatch=monkeypatch,
                           dispatch_enabled=False)

    assert outcome.status == "SKIPPED"
    assert "RECOVERY_DISPATCH_ENABLED" in outcome.reason


def test_nothing_is_sent_either_way(case_and_conn, monkeypatch):
    """The wording changed. The safety behaviour must not have."""
    conn, repo, case = case_and_conn

    for n, (dry, enabled) in enumerate(((True, True), (None, False))):
        outcome = _skip_reason(conn, repo, case, dry_run=dry, monkeypatch=monkeypatch,
                               dispatch_enabled=enabled, key=f"k_send_{n}")
        assert outcome.status == "SKIPPED"
        assert not outcome.sent


def test_the_record_still_says_where_it_would_have_gone(case_and_conn, monkeypatch):
    """A dry run is only useful if it shows what the real run would have done."""
    conn, repo, case = case_and_conn

    outcome = _skip_reason(conn, repo, case, dry_run=True, monkeypatch=monkeypatch)

    assert outcome.detail.get("would_send_to") == "rahul@example.com"
