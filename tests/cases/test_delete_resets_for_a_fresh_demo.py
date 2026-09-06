"""Delete all has to leave a database the next demo can actually start from.

WHY THIS EXISTS
    "Delete all" removed the cases and looked like it worked. Two things survived it, and
    together they made the next run behave as if the engine were broken.

    1. THE CONTACT BUDGET COUNTER. `contact_budgets` holds reserved/consumed per
       (merchant, customer) in its own table, and nothing in the delete touched it.
       Observed on the demo machine, after deleting everything:

           contact_budgets   CUST001  cap=3  consumed=3   <- still exhausted

       The next upload of that same customer abstained with CONTACT_BUDGET_UNAVAILABLE and
       sent nothing. That is the SAFETY FILTER WORKING CORRECTLY on stale state, which is
       the worst kind of wrong: the reason printed on screen is true, and the cause is
       invisible.

    2. FOLLOW-UP OPPORTUNITY IDS ARE SUFFIXED. A follow-up carries `<opportunity_id>#f1`
       on purpose, so the ladder reads real history rather than colliding with the
       original's idempotency key. The delete matched on equality, so it never saw them.
       333 of 334 queued follow-ups on that machine pointed at deleted cases.

WHAT MUST NOT CHANGE
    The budget is cleared ONLY for customers with no cases left. A customer who still has
    live work keeps their contact history - forgetting it would let the engine contact
    them past the cap, which is the one thing the budget exists to prevent.
"""

import pytest

from app.cases.csv_ingest import create_cases, parse_csv
from app.cases.repository import CaseRepository
from app.domain.enums import ActionType

CSV = """customer_id,name,email,amount,due_date
U_A,Rahul,a@example.com,25000,2026-08-24
U_B,Priya,b@example.com,1200,2026-08-30
"""


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOVERY_DB_PATH", str(tmp_path / "reset.db"))
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


def _exhaust_budget(repo, merchant_id, customer_id, consumed=3, cap=3):
    repo.conn.execute(
        """INSERT OR REPLACE INTO contact_budgets
           (merchant_id, customer_id, cap, reserved_count, consumed_count, updated_at)
           VALUES (?,?,?,0,?,'2026-09-06T00:00:00Z');""",
        (merchant_id, customer_id, cap, consumed))
    repo.conn.commit()


def _budget(repo, merchant_id, customer_id):
    return repo.conn.execute(
        "SELECT consumed_count FROM contact_budgets WHERE merchant_id=? AND customer_id=?;",
        (merchant_id, customer_id)).fetchone()


def _count(repo, table, column, value):
    return repo.conn.execute(
        f"SELECT COUNT(*) FROM {table} WHERE {column}=?;", (value,)).fetchone()[0]


# --- the budget counter -------------------------------------------------------------


def test_a_deleted_customer_starts_the_next_demo_uncapped(repo):
    """The defect. Cases gone, counter still exhausted, next upload silently abstains."""
    case = repo.list_cases("m1")[0]
    _exhaust_budget(repo, "m1", case.customer_id)

    repo.delete_cases([case.case_id])

    assert _budget(repo, "m1", case.customer_id) is None


def test_the_delete_reports_the_counters_it_cleared(repo):
    case = repo.list_cases("m1")[0]
    _exhaust_budget(repo, "m1", case.customer_id)

    removed = repo.delete_cases([case.case_id])

    assert removed["contact_budgets"] == 1


def test_a_customer_with_work_left_keeps_their_contact_history(repo):
    """The line that must not move. Clearing the counter while a case is still live would
    let the engine contact someone past the cap, which is the one thing it exists to stop.

    Both CSV rows are the same customer here, so deleting one leaves the other open.
    """
    from app.cases.models import Case, CaseStatus
    repo.create_case(Case(
        case_id="case_extra", merchant_id="m1", customer_id="U_A",
        amount_paise=500000, due_date="2026-09-30",
        source_event_id="csv_extra", event_type="OVERDUE_B2B_INVOICE",
        status=CaseStatus.OPEN))
    _exhaust_budget(repo, "m1", "U_A")
    first = next(c for c in repo.list_cases("m1") if c.customer_id == "U_A")

    repo.delete_cases([first.case_id])

    assert _budget(repo, "m1", "U_A") is not None, "history dropped while a case is live"


def test_another_customer_budget_is_untouched(repo):
    a, b = repo.list_cases("m1")[:2]
    _exhaust_budget(repo, "m1", a.customer_id)
    _exhaust_budget(repo, "m1", b.customer_id)

    repo.delete_cases([a.case_id])

    assert _budget(repo, "m1", b.customer_id) is not None


def test_another_merchants_budget_for_the_same_customer_id_is_untouched(repo):
    """Tenant isolation. The same customer id at two merchants is two different people."""
    case = repo.list_cases("m1")[0]
    _exhaust_budget(repo, "m1", case.customer_id)
    _exhaust_budget(repo, "m2", case.customer_id)

    repo.delete_cases([case.case_id])

    assert _budget(repo, "m2", case.customer_id) is not None


# --- the suffixed follow-up chain ---------------------------------------------------


def test_a_follow_up_scheduled_under_a_suffixed_id_does_not_survive(repo):
    """`#f1` is added on purpose so the ladder reads real history. Matching on equality
    meant the delete never saw a single follow-up."""
    from app.realtime import followup

    case = repo.list_cases("m1")[0]
    followup.schedule(
        opportunity_id=f"{case.case_id}#f1", merchant_id="m1",
        customer_id=case.customer_id, origin_event_id=case.source_event_id,
        event={}, diagnosis_code=None, last_action=ActionType.EMAIL_LINK, attempt=1,
    )
    assert _count(repo, "followup_queue", "opportunity_id", f"{case.case_id}#f1") == 1

    repo.delete_cases([case.case_id])

    assert _count(repo, "followup_queue", "opportunity_id", f"{case.case_id}#f1") == 0


def test_a_deep_follow_up_chain_goes_too(repo):
    """Attempt four is `#f4`, and it is no more attached to a live case than `#f1`."""
    from app.realtime import followup

    case = repo.list_cases("m1")[0]
    for n in (1, 2, 3, 4):
        followup.schedule(
            opportunity_id=f"{case.case_id}#f{n}", merchant_id="m1",
            customer_id=case.customer_id, origin_event_id=case.source_event_id,
            event={}, diagnosis_code=None, last_action=ActionType.EMAIL_LINK, attempt=n,
        )

    repo.delete_cases([case.case_id])

    left = repo.conn.execute(
        "SELECT COUNT(*) FROM followup_queue WHERE opportunity_id LIKE ?;",
        (f"{case.case_id}%",)).fetchone()[0]
    assert left == 0


def test_a_similarly_named_case_is_not_swept_up_by_the_prefix_match(repo):
    """The risk the LIKE introduces. `case_x` must not delete `case_x_2`'s follow-up."""
    from app.realtime import followup

    a, b = repo.list_cases("m1")[:2]
    followup.schedule(
        opportunity_id=b.case_id, merchant_id="m1", customer_id=b.customer_id,
        origin_event_id=b.source_event_id, event={}, diagnosis_code=None,
        last_action=ActionType.EMAIL_LINK, attempt=0,
    )

    repo.delete_cases([a.case_id])

    assert _count(repo, "followup_queue", "opportunity_id", b.case_id) == 1


def test_the_board_is_empty_and_nothing_is_left_pointing_at_it(repo):
    """The whole point, stated once: after Delete all, a fresh demo starts clean."""
    from app.cases.board import build_board
    from app.realtime import followup

    for case in repo.list_cases("m1"):
        _exhaust_budget(repo, "m1", case.customer_id)
        followup.schedule(
            opportunity_id=f"{case.case_id}#f1", merchant_id="m1",
            customer_id=case.customer_id, origin_event_id=case.source_event_id,
            event={}, diagnosis_code=None, last_action=ActionType.EMAIL_LINK, attempt=1,
        )

    repo.delete_cases([c.case_id for c in repo.list_cases("m1")])

    assert build_board(repo, "m1") == []
    assert repo.conn.execute("SELECT COUNT(*) FROM followup_queue;").fetchone()[0] == 0
    assert repo.conn.execute("SELECT COUNT(*) FROM contact_budgets;").fetchone()[0] == 0
