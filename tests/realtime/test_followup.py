"""Follow-up scheduling and rung-aware copy (ADR-0021).

The engine was purely event-driven: contact a customer once, have them ignore it forever,
and nothing further happened. These tests define the sequence half of the product.
"""

import importlib

import pytest

from app.domain.enums import ActionType, DiagnosisCode
from app.dispatch.copy import build_message
from app.realtime.followup import compute_delay_hours


@pytest.fixture()
def fu(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOVERY_DB_PATH", str(tmp_path / "fu.db"))
    from app.realtime import config as cfg
    importlib.reload(cfg)
    from app.realtime import ingest as ing
    importlib.reload(ing)
    from app.realtime import followup as f
    importlib.reload(f)
    f.ensure_schema()
    return f


# --- Dynamic timing: delay follows the failure reason -------------------------------------


def test_an_abandoned_cart_is_chased_far_sooner_than_an_overdue_invoice():
    """Intent decays in hours; accounts payable runs on weekly cycles. One fixed interval
    would be wrong in both directions."""
    cart = compute_delay_hours(DiagnosisCode.CUSTOMER_ABANDONMENT.value, ActionType.EMAIL_LINK, 0)
    invoice = compute_delay_hours(DiagnosisCode.INVOICE_OVERDUE.value, ActionType.EMAIL_LINK, 0)

    assert cart < invoice / 10


def test_insufficient_funds_waits_for_a_realistic_funding_cycle():
    """Chasing tomorrow chases money that does not exist yet."""
    funds = compute_delay_hours(DiagnosisCode.INSUFFICIENT_FUNDS.value, ActionType.SMS_LINK, 0)
    declined = compute_delay_hours(DiagnosisCode.CARD_DECLINED.value, ActionType.SMS_LINK, 0)

    # A declined card is fixable immediately; absent funds are not.
    assert funds > declined
    assert funds >= 48


def test_a_gateway_outage_is_rechecked_quickly():
    """Infrastructure clears in hours, and the customer did nothing wrong."""
    gateway = compute_delay_hours(DiagnosisCode.GATEWAY_FAILURE.value, ActionType.SMS_LINK, 0)

    assert gateway <= 12


# --- Dynamic timing: delay follows the action taken ---------------------------------------


def test_email_is_given_longer_to_be_read_than_sms():
    """An SMS unanswered after a day is a signal; an email may simply be unread."""
    sms = compute_delay_hours(DiagnosisCode.CARD_DECLINED.value, ActionType.SMS_LINK, 0)
    email = compute_delay_hours(DiagnosisCode.CARD_DECLINED.value, ActionType.EMAIL_LINK, 0)

    assert email > sms


def test_a_phone_call_earns_the_longest_pause():
    """Following a call quickly reads as pressure."""
    call = compute_delay_hours(DiagnosisCode.CARD_DECLINED.value, ActionType.AGENT_DIAL, 0)
    email = compute_delay_hours(DiagnosisCode.CARD_DECLINED.value, ActionType.EMAIL_LINK, 0)

    assert call > email


def test_each_unanswered_touch_widens_the_gap():
    """Someone who ignored three messages will not answer the fourth sooner."""
    delays = [
        compute_delay_hours(DiagnosisCode.CARD_DECLINED.value, ActionType.SMS_LINK, i)
        for i in range(4)
    ]

    assert delays == sorted(delays)
    assert delays[-1] > delays[0]


def test_a_delay_is_never_less_than_an_hour():
    fast = compute_delay_hours(DiagnosisCode.CUSTOMER_ABANDONMENT.value, ActionType.RECOMMEND_RETRY, 0)

    assert fast >= 1.0


# --- Scheduling, stopping, bounding -------------------------------------------------------


def _schedule(fu, attempt=0, opp="opp_1", origin="pay_1"):
    return fu.schedule(
        opportunity_id=opp, merchant_id="m1", customer_id="c1",
        origin_event_id=origin, event={"event_id": origin, "amount_paise": 5000},
        diagnosis_code=DiagnosisCode.CARD_DECLINED.value,
        last_action=ActionType.EMAIL_LINK, attempt=attempt,
    )


def test_a_contact_schedules_the_next_reconsideration(fu):
    due = _schedule(fu)

    assert due is not None
    assert fu.counters().get("SCHEDULED") == 1


def test_payment_arriving_stops_every_scheduled_followup(fu):
    """The engine must never chase money it already has."""
    _schedule(fu)

    stopped = fu.cancel_for_entity("pay_1", "payment received")

    assert stopped == 1
    assert fu.counters().get("SCHEDULED", 0) == 0
    assert fu.counters().get("STOPPED") == 1


def test_followups_are_bounded(fu):
    """A customer cannot be pursued indefinitely."""
    result = _schedule(fu, attempt=fu.MAX_FOLLOWUPS)

    assert result is None
    assert fu.counters().get("SCHEDULED", 0) == 0


def test_nothing_is_due_before_its_delay_has_elapsed(fu):
    _schedule(fu)

    assert fu.due_followups() == []


# --- Rung-aware copy ----------------------------------------------------------------------


def test_tone_escalates_with_the_rung():
    """A fourth contact must not read exactly like the first, only louder in medium."""
    first = build_message(ActionType.EMAIL_LINK, 450000, "Sam", DiagnosisCode.CARD_DECLINED.value)
    later = build_message(ActionType.AGENT_DIAL, 450000, "Sam", DiagnosisCode.CARD_DECLINED.value)

    assert first.subject != later.subject
    assert first.body != later.body
    assert "We noticed" in first.body
    assert "outstanding" in later.body.lower()


def test_the_ask_follows_the_diagnosis_not_the_channel():
    """Telling someone whose card expired to wait for funds misdiagnoses them to their face."""
    declined = build_message(ActionType.EMAIL_LINK, 100000, "", DiagnosisCode.CARD_DECLINED.value)
    funds = build_message(ActionType.EMAIL_LINK, 100000, "", DiagnosisCode.INSUFFICIENT_FUNDS.value)

    assert "card" in declined.body.lower()
    assert "insufficient funds" in funds.body.lower()
    assert declined.body != funds.body


def test_b2b_invoices_get_accounts_payable_language():
    """Consumer phrasing to an AP inbox reads as spam and gets filtered."""
    invoice = build_message(ActionType.EMAIL_LINK, 10_000_000, "", DiagnosisCode.INVOICE_OVERDUE.value)

    assert "invoice" in invoice.subject.lower()
    assert "payment date" in invoice.body.lower()


def test_every_message_identifies_itself_and_offers_an_opt_out():
    for action in (ActionType.EMAIL_LINK, ActionType.SMS_LINK, ActionType.WHATSAPP_LINK):
        message = build_message(action, 50000, "Sam", DiagnosisCode.UNKNOWN.value)

        assert "Unified Recovery Engine" in message.body
        assert "STOP" in message.body


def test_copy_never_invents_a_deadline_or_a_threat():
    """The engine has no authority to threaten anything, and manufacturing urgency to lift
    a recovery rate is the behaviour these controls exist to prevent."""
    forbidden = ("final notice", "legal", "penalty", "suspend", "24 hours", "immediately or")

    for action in ActionType:
        message = build_message(action, 500000, "Sam", DiagnosisCode.INVOICE_OVERDUE.value)
        lowered = message.body.lower()
        for word in forbidden:
            assert word not in lowered, f"{action.value} copy contains '{word}'"


def test_the_spoken_message_never_reads_out_a_url():
    """Nobody can write down a URL from a phone call."""
    message = build_message(ActionType.IVR_CALL, 50000, "Sam", DiagnosisCode.CARD_DECLINED.value,
                            payment_link="https://rzp.io/i/abc123")

    assert "http" not in message.spoken
    assert "rzp.io" not in message.spoken
