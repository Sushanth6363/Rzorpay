"""Deleting a case removes everything that hangs off it, and nothing that does not.

WHY THIS EXISTS
    Resetting the board between demo runs meant hand-editing SQLite. A delete button is
    the obvious fix and the obvious way to leave orphans behind: a follow-up still
    scheduled against a case that no longer exists, a ledger row propping up an escalation
    ceiling for a customer whose history was erased, or a live payment link a customer can
    still pay with nothing left to record it against.

    So the tests below check the second half - what is left over - rather than only that
    the case is gone.
"""

import pytest

from app.cases.csv_ingest import create_cases, parse_csv
from app.cases.models import CaseEvent, CaseEventKind, CaseStatus, PaymentLink
from app.cases.repository import CaseRepository
from app.domain.enums import ActionType

CSV = """customer_id,name,email,amount,due_date
U_A,Rahul,a@example.com,25000,2026-08-24
U_B,Priya,b@example.com,1200,2026-08-30
"""


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOVERY_DB_PATH", str(tmp_path / "del.db"))
    import importlib
    from app.realtime import config as cfg
    importlib.reload(cfg)
    from app.realtime import ingest as ing
    importlib.reload(ing)
    from app.realtime import followup as f
    importlib.reload(f)
    f.ensure_schema()
    r = CaseRepository(ing.get_conn())
    create_cases(r, parse_csv(CSV).valid, merchant_id="m1")
    return r


def _count(repo, table, column, value):
    return repo.conn.execute(
        f"SELECT COUNT(*) FROM {table} WHERE {column}=?;", (value,)
    ).fetchone()[0]


# --- the case and its trail ------------------------------------------------------------


def test_the_case_is_gone(repo):
    case = repo.list_cases("m1")[0]

    repo.delete_cases([case.case_id])

    assert repo.get_case(case.case_id) is None


def test_its_timeline_goes_with_it(repo):
    """An orphaned timeline is unreadable - there is no case to attach it to."""
    case = repo.list_cases("m1")[0]
    repo.add_event(CaseEvent(case_id=case.case_id, kind=CaseEventKind.AGENT_DECIDED,
                             summary="Agent selected EMAIL_LINK"))

    repo.delete_cases([case.case_id])

    assert _count(repo, "case_events", "case_id", case.case_id) == 0


def test_its_payment_links_go_with_it(repo):
    case = repo.list_cases("m1")[0]
    repo.save_payment_link(PaymentLink(
        payment_link_id="plink_x", case_id=case.case_id, merchant_id="m1",
        customer_id=case.customer_id, amount_paise=case.amount_paise,
        reference_id="ref_x", short_url="https://rzp.io/rzp/X"))

    repo.delete_cases([case.case_id])

    assert _count(repo, "payment_links", "case_id", case.case_id) == 0


def test_a_scheduled_follow_up_does_not_survive_its_case(repo):
    """The orphan that actually bites: the worker would wake, find a due follow-up, and
    try to act on a case that no longer exists."""
    from app.realtime import followup

    case = repo.list_cases("m1")[0]
    followup.schedule(
        opportunity_id=case.case_id, merchant_id="m1", customer_id=case.customer_id,
        origin_event_id=case.source_event_id, event={}, diagnosis_code=None,
        last_action=ActionType.EMAIL_LINK, attempt=0,
    )
    assert _count(repo, "followup_queue", "opportunity_id", case.case_id) == 1

    repo.delete_cases([case.case_id])

    assert _count(repo, "followup_queue", "opportunity_id", case.case_id) == 0


# --- and nothing else ------------------------------------------------------------------


def test_other_cases_are_untouched(repo):
    """"Clear unpaid" must not take the paid case with it."""
    first, second = repo.list_cases("m1")[:2]

    repo.delete_cases([first.case_id])

    assert repo.get_case(second.case_id) is not None


def test_deleting_nothing_is_a_no_op(repo):
    before = len(repo.list_cases("m1"))

    assert repo.delete_cases([]) == {}
    assert len(repo.list_cases("m1")) == before


def test_deleting_an_unknown_case_does_not_raise(repo):
    """A double-click on the button must not produce a stack trace."""
    repo.delete_cases(["case_that_never_existed"])

    assert len(repo.list_cases("m1")) == 2


def test_it_reports_what_it_removed(repo):
    """The UI states the counts, so they have to be real rather than assumed."""
    case = repo.list_cases("m1")[0]
    repo.add_event(CaseEvent(case_id=case.case_id, kind=CaseEventKind.AGENT_DECIDED,
                             summary="decided"))

    removed = repo.delete_cases([case.case_id])

    assert removed["cases"] == 1
    assert removed["case_events"] >= 1


def test_deleting_every_case_leaves_an_empty_board(repo):
    from app.cases.board import build_board

    repo.delete_cases([c.case_id for c in repo.list_cases("m1")])

    assert build_board(repo, "m1") == []


def test_a_paid_case_can_be_deleted_when_explicitly_asked(repo):
    """"Delete all" means all. It must not silently protect the paid rows - a control that
    quietly does less than it says is worse than one that refuses."""
    case = repo.list_cases("m1")[0]
    repo.set_status(case.case_id, CaseStatus.PAID, reason="paid")

    repo.delete_cases([case.case_id])

    assert repo.get_case(case.case_id) is None
