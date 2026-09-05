"""The case board renders as designed cards, not a spreadsheet (ADR-0027).

WHY THIS TEST EXISTS
    The board began life as `st.dataframe`. A grid is honest but unreadable: a merchant
    scanning fifty rows of wrapped text cannot see which customer needs a human, which is
    the entire reason the board exists. The card layout carries real claims - a lit ladder
    rung means a message was CONFIRMED SENT, a badge means a verified status - so the
    claims are tested here rather than left to the eye.
"""

import pytest

pytest.importorskip("streamlit")

from app.cases.board import BoardRow  # noqa: E402
from app.ui.dashboard import (  # noqa: E402
    FLAG_ORDER,
    _case_card,
    _due_line,
    _ladder,
)


def row(**kw) -> BoardRow:
    base = dict(
        case_id="c1", customer_id="U_A", name="Aarti", contact="a@example.com",
        amount_paise=2_500_000, stage="EMAIL_LINK sent, awaiting payment",
        last_action="EMAIL_LINK", contacts_made=1, channels_tried="EMAIL",
        delivered=True, paid=False, payment_note="no payment since contact",
        flag="ACTIVE", due_date="2026-08-01",
    )
    base.update(kw)
    return BoardRow(**base)


# --- the escalation ladder -----------------------------------------------------------------


def test_only_channels_actually_used_are_lit():
    """A lit rung is a claim that a message was confirmed sent on that channel."""
    html = _ladder(row(channels_tried="EMAIL, SMS"))

    assert html.count("r done") == 2
    assert ">EMAIL<" in html and ">SMS<" in html


def test_a_decided_but_undispatched_action_is_dashed_never_lit():
    """The one mistake this widget must not make: showing a decision as a delivery."""
    html = _ladder(row(channels_tried="", contacts_made=0, last_action="EMAIL_LINK"))

    assert "r done" not in html
    assert "r next" in html


def test_a_paid_case_advertises_no_next_rung():
    """Nothing further is planned for someone who has paid, so nothing may be drawn as
    planned - the same rule that keeps 'next review' off a settled row."""
    html = _ladder(row(paid=True, channels_tried="EMAIL", last_action="SMS_LINK"))

    assert "r next" not in html


def test_every_rung_of_the_ladder_is_always_visible():
    """The unused rungs are what make an escalation ladder legible as a ladder."""
    html = _ladder(row(channels_tried=""))

    for rung in ("EMAIL", "SMS", "WHATSAPP", "CALL"):
        assert f">{rung}<" in html


# --- ageing --------------------------------------------------------------------------------


def test_a_settled_case_is_never_shown_as_overdue():
    """A debt stops ageing when the payment is verified. "17d overdue" beside a PAID badge
    is wrong, and one visibly wrong number discredits every other figure on the screen."""
    line = _due_line(row(paid=True, due_date="2020-01-01"))

    assert "overdue" not in line
    assert "settled" in line


def test_an_unpaid_case_is_aged_from_the_merchants_own_due_date():
    line = _due_line(row(paid=False, due_date="2020-01-01"))

    assert "overdue" in line
    assert "2020-01-01" in line


def test_a_missing_due_date_is_stated_not_invented():
    assert _due_line(row(due_date="")) == "no due date supplied"


def test_an_unreadable_due_date_does_not_crash_the_board():
    assert "not-a-date" in _due_line(row(due_date="not-a-date"))


# --- the card ------------------------------------------------------------------------------


def test_the_card_carries_the_facts_a_merchant_scans_for():
    html = _case_card(row(amount_paise=2_500_000))

    assert "Aarti" in html
    assert "a@example.com" in html
    assert "25,000.00" in html
    assert "IN PROGRESS" in html


def test_the_card_never_claims_to_know_what_the_customer_did():
    """Carried over from the board: there is no open/click tracking anywhere, so no card
    may imply readership. We cannot tell "ignored" from "never saw it"."""
    html = _case_card(row(contacts_made=3, payment_note="no payment since contact 6d ago")).lower()

    for inference in ("opened", "read ", "ignored", "declined", "refused", "seen"):
        assert inference not in html


def test_an_uncontacted_case_says_so_rather_than_showing_a_blank():
    html = _case_card(row(contacts_made=0, channels_tried="", next_review=""))

    assert "0 confirmed contacts" in html
    assert "nothing scheduled" in html


def test_a_case_with_no_contact_details_says_so():
    html = _case_card(row(contact=""))

    assert "no contact on file" in html


# --- ordering ------------------------------------------------------------------------------


def test_the_row_that_needs_a_human_sorts_to_the_top():
    """The board is ordered by urgency, not upload order. A merchant must never scroll to
    find the stalled case."""
    rows = [row(flag=f, case_id=f) for f in ("PAID", "WAITING", "ACTIVE", "STALLED")]

    ordered = sorted(rows, key=lambda r: (FLAG_ORDER.get(r.flag, 9), -r.amount_paise))

    assert [r.flag for r in ordered] == ["STALLED", "ACTIVE", "WAITING", "PAID"]


def test_within_a_flag_the_largest_exposure_comes_first():
    rows = [row(case_id="small", flag="STALLED", amount_paise=100),
            row(case_id="big", flag="STALLED", amount_paise=9_000_000)]

    ordered = sorted(rows, key=lambda r: (FLAG_ORDER.get(r.flag, 9), -r.amount_paise))

    assert [r.case_id for r in ordered] == ["big", "small"]
