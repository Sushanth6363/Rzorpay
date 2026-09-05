"""Case board — one row per customer, showing where the agent has got to (ADR-0027).

The board's job is to make one row obvious: the customer who was contacted, has not paid,
and has nothing further scheduled. That row needs a human, and everything else on the
screen exists to make it stand out.
"""

import pytest

from app.cases.board import build_board, summarise
from app.cases.csv_ingest import create_cases, parse_csv
from app.cases.models import CaseStatus
from app.cases.repository import CaseRepository
from app.db.init import init_db

CSV = """customer_id,name,email,amount,due_date
U_A,Rahul,a@example.com,25000,2026-08-24
U_B,Priya,b@example.com,1200,2026-08-30
"""


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOVERY_DB_PATH", str(tmp_path / "board.db"))
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


def _row(rows, name):
    return next(r for r in rows if r.name == name)


# --- Flags ------------------------------------------------------------------------------


def test_a_fresh_case_is_waiting_not_stalled(repo):
    """Nothing has been decided yet, so nothing has gone wrong yet."""
    rows = build_board(repo, "m1")

    assert all(r.flag == "WAITING" for r in rows)
    assert _row(rows, "Rahul").stage == "Awaiting first evaluation"


def test_a_paid_case_is_flagged_paid_and_closed(repo):
    case = repo.list_cases("m1")[0]
    repo.set_status(case.case_id, CaseStatus.PAID, reason="verified by payment_link.paid")

    row = next(r for r in build_board(repo, "m1") if r.case_id == case.case_id)

    assert row.flag == "PAID"
    assert row.paid is True
    assert "closed" in row.stage.lower()


def test_a_settled_case_never_advertises_a_future_contact(repo):
    """"Next review" beside "PAID" reads as though the engine intends to chase someone who
    has already paid - the one thing this product must never appear to do."""
    from app.domain.enums import ActionType
    from app.realtime import followup

    case = repo.list_cases("m1")[0]
    followup.schedule(
        opportunity_id=case.case_id, merchant_id="m1", customer_id=case.customer_id,
        origin_event_id=case.source_event_id, event={}, diagnosis_code=None,
        last_action=ActionType.EMAIL_LINK, attempt=0,
    )
    repo.set_status(case.case_id, CaseStatus.PAID, reason="paid")

    row = next(r for r in build_board(repo, "m1") if r.case_id == case.case_id)

    assert row.next_review == ""


def test_a_closed_unpaid_case_needs_attention(repo):
    case = repo.list_cases("m1")[0]
    repo.set_status(case.case_id, CaseStatus.CLOSED, reason="wrong person")

    row = next(r for r in build_board(repo, "m1") if r.case_id == case.case_id)

    assert row.flag == "STALLED"
    assert row.paid is False


# --- The row that needs a human -----------------------------------------------------------


def test_contacted_unpaid_with_nothing_scheduled_is_the_red_row(repo):
    """This is the whole point of the board."""
    from app.cases.models import CaseEvent, CaseEventKind

    case = repo.list_cases("m1")[0]
    repo.add_event(CaseEvent(case_id=case.case_id, kind=CaseEventKind.AGENT_DECIDED,
                             summary="Agent selected EMAIL_LINK"))
    repo.add_event(CaseEvent(case_id=case.case_id, kind=CaseEventKind.MESSAGE_SENT,
                             summary="EMAIL_LINK sent via EMAIL_SMTP",
                             detail={"channel": "EMAIL_SMTP"}))

    row = next(r for r in build_board(repo, "m1") if r.case_id == case.case_id)

    assert row.flag == "STALLED"
    assert row.contacts_made == 1
    assert "nothing scheduled" in row.stage


def test_contacted_with_a_review_scheduled_is_active_not_stalled(repo):
    """A sequence still in progress is not a problem to escalate to a human."""
    from app.cases.models import CaseEvent, CaseEventKind
    from app.domain.enums import ActionType
    from app.realtime import followup

    case = repo.list_cases("m1")[0]
    repo.add_event(CaseEvent(case_id=case.case_id, kind=CaseEventKind.AGENT_DECIDED,
                             summary="Agent selected EMAIL_LINK"))
    repo.add_event(CaseEvent(case_id=case.case_id, kind=CaseEventKind.MESSAGE_SENT,
                             summary="sent", detail={"channel": "EMAIL_SMTP"}))
    followup.schedule(
        opportunity_id=case.case_id, merchant_id="m1", customer_id=case.customer_id,
        origin_event_id=case.source_event_id, event={}, diagnosis_code=None,
        last_action=ActionType.EMAIL_LINK, attempt=0,
    )

    row = next(r for r in build_board(repo, "m1") if r.case_id == case.case_id)

    assert row.flag == "ACTIVE"
    assert row.next_review


def test_an_abstention_is_waiting_not_a_failure(repo):
    """The engine choosing not to contact is a decision, not a breakdown."""
    from app.cases.models import CaseEvent, CaseEventKind

    case = repo.list_cases("m1")[0]
    repo.add_event(CaseEvent(case_id=case.case_id, kind=CaseEventKind.AGENT_DECIDED,
                             summary="Agent selected NO_ACTION"))

    row = next(r for r in build_board(repo, "m1") if r.case_id == case.case_id)

    assert row.flag == "WAITING"
    assert "not to contact" in row.stage


# --- Honesty about what we can observe ------------------------------------------------------


def test_the_board_reports_delivery_not_readership(repo):
    """There is no open or click tracking anywhere, so the board must not imply any."""
    from app.cases.models import CaseEvent, CaseEventKind

    case = repo.list_cases("m1")[0]
    repo.add_event(CaseEvent(case_id=case.case_id, kind=CaseEventKind.AGENT_DECIDED,
                             summary="Agent selected EMAIL_LINK"))
    repo.add_event(CaseEvent(case_id=case.case_id, kind=CaseEventKind.MESSAGE_SENT,
                             summary="sent", detail={"channel": "EMAIL_SMTP"}))

    row = next(r for r in build_board(repo, "m1") if r.case_id == case.case_id)
    columns = row.to_row()

    assert row.delivered is True
    for forbidden in ("Opened", "Read", "Response", "Ignored"):
        assert forbidden not in columns
    # The note may never claim to know what the customer did with the message. We cannot
    # tell "ignored" from "never saw it", so every note must be a fact about US.
    for inference in ("ignored", "read", "opened", "declined", "refused"):
        assert inference not in row.payment_note.lower()


# --- Summary --------------------------------------------------------------------------------


def test_the_summary_counts_only_verified_recovery(repo):
    cases = repo.list_cases("m1")
    repo.set_status(cases[0].case_id, CaseStatus.PAID, reason="paid")

    s = summarise(build_board(repo, "m1"))

    assert s["cases"] == 2
    assert s["recovered_paise"] == cases[0].amount_paise
    assert s["outstanding_paise"] == s["total_paise"] - s["recovered_paise"]


def test_needs_attention_counts_the_red_rows(repo):
    case = repo.list_cases("m1")[0]
    repo.set_status(case.case_id, CaseStatus.CLOSED, reason="gave up")

    assert summarise(build_board(repo, "m1"))["needs_attention"] == 1


def test_the_biggest_exposure_is_visible_in_the_row(repo):
    rows = build_board(repo, "m1")

    assert _row(rows, "Rahul").amount_paise == 2_500_000
    assert _row(rows, "Priya").amount_paise == 120_000


# --- Does the stage actually change when payment lands? -------------------------------------


def test_the_board_flips_from_active_to_paid_when_a_payment_is_verified(repo):
    """The whole loop, observed through the board: a verified payment must change the row,
    cancel the next review, and close the case - without anyone refreshing anything."""
    from app.cases.models import CaseEvent, CaseEventKind
    from app.domain.enums import ActionType
    from app.realtime import followup

    case = repo.list_cases("m1")[0]
    repo.add_event(CaseEvent(case_id=case.case_id, kind=CaseEventKind.AGENT_DECIDED,
                             summary="Agent selected EMAIL_LINK"))
    repo.add_event(CaseEvent(case_id=case.case_id, kind=CaseEventKind.MESSAGE_SENT,
                             summary="sent", detail={"channel": "EMAIL_SMTP"}))
    followup.schedule(
        opportunity_id=case.case_id, merchant_id="m1", customer_id=case.customer_id,
        origin_event_id=case.source_event_id, event={}, diagnosis_code=None,
        last_action=ActionType.EMAIL_LINK, attempt=0,
    )

    before = next(r for r in build_board(repo, "m1") if r.case_id == case.case_id)
    assert before.flag == "ACTIVE"
    assert before.next_review

    repo.set_status(case.case_id, CaseStatus.PAID, reason="verified by payment_link.paid")
    followup.cancel_for_entity(case.source_event_id, "case closed")

    after = next(r for r in build_board(repo, "m1") if r.case_id == case.case_id)
    assert after.flag == "PAID"
    assert after.paid is True
    assert after.next_review == ""
    assert "closed" in after.stage.lower()


def test_a_row_carries_everything_needed_to_open_it(repo):
    """Clicking a row opens its detail, so the row must carry the case id and link."""
    from app.cases.models import PaymentLink

    case = repo.list_cases("m1")[0]
    repo.save_payment_link(PaymentLink(
        payment_link_id="plink_row", case_id=case.case_id, merchant_id="m1",
        customer_id=case.customer_id, amount_paise=case.amount_paise,
        short_url="https://rzp.io/rzp/ROW", reference_id="ref_row",
    ))

    row = next(r for r in build_board(repo, "m1") if r.case_id == case.case_id)

    assert row.case_id == case.case_id
    assert row.payment_url == "https://rzp.io/rzp/ROW"
