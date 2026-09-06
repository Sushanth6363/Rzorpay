"""The ladder only offers channels that can actually reach the customer (ADR-0015).

WHY THIS EXISTS
    A customer with a valid phone and no email was contacted ZERO times, indefinitely,
    while their debt sat recoverable. Observed, not theorised:

        cycle 1: action=EMAIL_LINK  SKIPPED    "row has no email address"
        cycle 2: action=EMAIL_LINK  DUPLICATE
        cycle 3: action=EMAIL_LINK  DUPLICATE
        contacted: 0 times

    The CSV accepts a phone-only row - a phone is a perfectly good route to a customer.
    But receivables enter the ladder at rung 0, EMAIL_LINK, and nothing checked whether an
    address existed on that channel. The send was skipped, so the contact was never
    confirmed, so the escalation ceiling never rose above rung 0, so the engine offered the
    same impossible action forever.

    Two changes fix it, and both are needed. The safety filter rejects a channel the
    customer has no address on, and the escalation ceiling advances to the next REACHABLE
    rung rather than the next number. With only the second, EMAIL_LINK remained a candidate
    and still won on expected value.

WHAT MUST NOT CHANGE
    Every synthetic event in the experiment carries no contact details at all. Unknown is
    therefore treated as reachable, leaving the evaluated path byte-identical - verified by
    re-running the evaluation and diffing results/.
"""

import pytest

from app.domain.enums import ActionType
from app.pipeline.escalation import (
    ESCALATION_LADDER,
    RUNG_OF,
    EscalationPolicy,
    reachable_rungs,
)

EMAIL = RUNG_OF[ActionType.EMAIL_LINK]
SMS = RUNG_OF[ActionType.SMS_LINK]
WHATSAPP = RUNG_OF[ActionType.WHATSAPP_LINK]
IVR = RUNG_OF[ActionType.IVR_CALL]
AGENT = RUNG_OF[ActionType.AGENT_DIAL]


# --- which rungs are reachable ----------------------------------------------------------


def test_unknown_contact_details_leave_the_whole_ladder_available():
    """The experiment path. Unknown must never mean "assume nothing works"."""
    assert reachable_rungs(None, None) == list(range(len(ESCALATION_LADDER)))


def test_a_phone_only_customer_cannot_be_emailed():
    rungs = reachable_rungs(has_email=False, has_phone=True)

    assert EMAIL not in rungs
    assert rungs == [SMS, WHATSAPP, IVR, AGENT]


def test_an_email_only_customer_cannot_be_messaged_or_called():
    """Every rung above email needs a phone number, including the human call."""
    rungs = reachable_rungs(has_email=True, has_phone=False)

    assert rungs == [EMAIL]


def test_a_customer_with_both_can_use_the_whole_ladder():
    assert reachable_rungs(has_email=True, has_phone=True) == list(range(len(ESCALATION_LADDER)))


# --- the entry rung ----------------------------------------------------------------------


def test_a_phone_only_customer_is_met_at_sms_not_at_an_email_they_cannot_receive():
    """The bug, at the point it starts. Receivables enter at rung 0; this customer cannot
    receive rung 0, so the first touch must be the lowest rung that can reach them."""
    assessment = EscalationPolicy().assess(
        history=[], decision_timestamp="2026-09-01T10:00:00Z",
        event_type_value="OVERDUE_B2B_INVOICE", has_email=False, has_phone=True,
    )

    assert assessment.allowed_max_rung == SMS


def test_an_email_only_customer_still_enters_at_email():
    assessment = EscalationPolicy().assess(
        history=[], decision_timestamp="2026-09-01T10:00:00Z",
        event_type_value="OVERDUE_B2B_INVOICE", has_email=True, has_phone=False,
    )

    assert assessment.allowed_max_rung == EMAIL


def test_the_entry_rung_is_unchanged_when_contacts_are_unknown():
    """Pins the experiment path against drift."""
    known = EscalationPolicy().assess(
        history=[], decision_timestamp="2026-09-01T10:00:00Z",
        event_type_value="OVERDUE_B2B_INVOICE",
    )

    assert known.allowed_max_rung == EMAIL


# --- escalation skips what cannot arrive --------------------------------------------------


def _confirmed(action, at="2026-09-01T00:00:00Z"):
    from app.domain.enums import LedgerStatus
    from app.domain.models import ContactLedgerEntry

    return ContactLedgerEntry(
        ledger_id="l1", merchant_id="m1", customer_id="c1", opportunity_id="o1",
        action_type=action, intervention_idempotency_key="k1",
        status=LedgerStatus.EXECUTED, created_at=at, updated_at=at,
        attempted_at=at, resolved_at=at,
    )


def test_an_email_only_customer_never_escalates_to_a_channel_they_lack():
    """There is no phone, so SMS, WhatsApp, IVR and the human call are all unreachable.
    The ceiling must stay at email rather than advancing into a void."""
    assessment = EscalationPolicy().assess(
        history=[_confirmed(ActionType.EMAIL_LINK)],
        decision_timestamp="2026-09-20T10:00:00Z",   # well past the quiet period
        event_type_value="OVERDUE_B2B_INVOICE", has_email=True, has_phone=False,
    )

    assert assessment.allowed_max_rung == EMAIL


def test_a_phone_only_customer_climbs_sms_then_whatsapp():
    assessment = EscalationPolicy().assess(
        history=[_confirmed(ActionType.SMS_LINK)],
        decision_timestamp="2026-09-20T10:00:00Z",
        event_type_value="OVERDUE_B2B_INVOICE", has_email=False, has_phone=True,
    )

    assert assessment.allowed_max_rung == WHATSAPP


def test_a_phone_only_customer_eventually_reaches_the_human_call():
    """The end of the ladder the merchant asked for: SMS, WhatsApp, IVR, then a person."""
    assessment = EscalationPolicy().assess(
        history=[_confirmed(ActionType.IVR_CALL)],
        decision_timestamp="2026-09-20T10:00:00Z",
        event_type_value="OVERDUE_B2B_INVOICE", has_email=False, has_phone=True,
    )

    assert assessment.allowed_max_rung == AGENT


def test_skipping_an_unreachable_rung_is_not_escalating_by_two():
    """A phone-only customer confirmed at SMS goes to WhatsApp, not straight to IVR. The
    one-rung rule still binds; only rungs that could never deliver are skipped."""
    assessment = EscalationPolicy().assess(
        history=[_confirmed(ActionType.SMS_LINK)],
        decision_timestamp="2026-09-20T10:00:00Z",
        event_type_value="OVERDUE_B2B_INVOICE", has_email=False, has_phone=True,
    )

    assert assessment.allowed_max_rung == WHATSAPP
    assert assessment.allowed_max_rung != IVR


# --- end to end, through the real agent ----------------------------------------------------


@pytest.mark.parametrize("email,phone,expected", [
    ("",                "9845012345", "SMS_LINK"),
    ("arjun@example.com", "",         "EMAIL_LINK"),
    ("k@example.com",   "9845099999", "EMAIL_LINK"),
])
def test_the_first_action_matches_how_the_customer_can_be_reached(
        tmp_path, monkeypatch, email, phone, expected):
    monkeypatch.setenv("RECOVERY_DB_PATH", str(tmp_path / "reach.db"))
    monkeypatch.setenv("RECOVERY_DISPATCH_ENABLED", "false")

    from app.agent.loop import RecoveryAgent
    from app.cases.csv_ingest import create_cases, parse_csv
    from app.cases.repository import CaseRepository
    from app.db.init import init_db
    from app.dispatch.dispatcher import ChannelDispatcher
    from app.payments.link_service import PaymentLinkService

    class FakeRZP:
        key_id = "rzp_test_REAL"

        def create_payment_link(self, **kwargs):
            return {"id": "p1", "short_url": "https://rzp.io/rzp/P", "is_simulated": False}

        def cancel_payment_link(self, payment_link_id):
            return {"id": payment_link_id, "status": "cancelled"}

    conn = init_db(str(tmp_path / "reach.db"))
    repo = CaseRepository(conn)
    row = (f"customer_id,name,email,phone,amount,due_date\n"
           f"C1,Test,{email},{phone},18000,2026-07-15\n")
    case = create_cases(repo, parse_csv(row).valid, merchant_id="m1")[0]
    agent = RecoveryAgent(
        conn, repository=repo,
        payments=PaymentLinkService(conn, client=FakeRZP(), repository=repo),
        dispatcher=ChannelDispatcher(conn, repository=repo, dry_run=True),
    )

    assert agent.run_cycle(case.case_id, random_seed=7).action == expected
