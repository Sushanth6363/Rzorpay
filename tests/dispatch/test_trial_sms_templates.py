"""SMS on a Twilio trial: a message is delivered, but it is not our message.

WHY THIS EXISTS
    A trial account rejects custom SMS text with 572006, "Trial accounts can only use
    predefined SMS templates". The `Body` parameter must literally BE one of ten fixed
    identifiers. Setting TWILIO_TRIAL_SMS_TEMPLATE does that, and an SMS genuinely arrives
    - verified against a real trial and a real handset.

    But the customer receives TWILIO'S wording. The composed message is discarded, so THE
    PAYMENT LINK IS NOT DELIVERED. The channel is proven; the recovery action is not
    performed.

    Those are different things, and the difference has to survive into the record. A
    dispatch that read plainly "SENT" would light a ladder rung and consume a contact slot
    for a message that cannot recover anything - and the handoff report would later tell a
    collections agent an SMS was already tried. Everything below exists to keep that
    distinction visible.
"""

import json

import pytest

from app.dispatch import channels

TO = "+916363613285"
COMPOSED = "Your invoice of Rs 25,000 is outstanding: https://rzp.io/rzp/X"


class FakeResponse:
    def __init__(self, status_code=201, payload=None):
        self.status_code = status_code
        self._payload = payload or {"sid": "SM123"}
        self.text = json.dumps(self._payload)

    def json(self):
        return self._payload


@pytest.fixture()
def sent(monkeypatch):
    monkeypatch.setenv("TWILIO_SMS_FROM", "+15550001111")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "0123456789abcdef0123456789abcdef")
    monkeypatch.delenv("TWILIO_TRIAL_SMS_TEMPLATE", raising=False)
    captured = {}

    def fake_post(url, auth=None, data=None, timeout=None):
        captured["data"] = data or {}
        return captured.get("response", FakeResponse())

    monkeypatch.setattr(channels.requests, "post", fake_post)
    return captured


# --- paid accounts are untouched ---------------------------------------------------------------


def test_without_the_setting_our_own_message_is_sent(sent):
    channels.send_sms(TO, COMPOSED)

    assert sent["data"]["Body"] == COMPOSED


# --- trial mode --------------------------------------------------------------------------------


def test_the_template_identifier_replaces_the_body(sent, monkeypatch):
    monkeypatch.setenv("TWILIO_TRIAL_SMS_TEMPLATE", "sms_account_alerts")

    channels.send_sms(TO, COMPOSED)

    assert sent["data"]["Body"] == "sms_account_alerts"


def test_the_result_says_our_message_was_not_delivered(sent, monkeypatch):
    """The single most important assertion in this file. Anyone reading the dispatch record
    must be able to see that the payment link never reached the customer."""
    monkeypatch.setenv("TWILIO_TRIAL_SMS_TEMPLATE", "sms_account_alerts")

    result = channels.send_sms(TO, COMPOSED)

    assert result.status == "SENT"
    assert "NOT our message" in result.detail
    assert "payment link was not included" in result.detail


def test_the_substitution_is_recorded_as_structured_data(sent, monkeypatch):
    """Not only prose: the dispatch log stores `extra`, so the substitution stays queryable
    rather than needing a human to read a sentence."""
    monkeypatch.setenv("TWILIO_TRIAL_SMS_TEMPLATE", "sms_appointment_reminders")

    result = channels.send_sms(TO, COMPOSED)

    assert result.extra["template_substituted"] == "sms_appointment_reminders"


def test_an_invalid_template_name_is_refused_before_sending(sent, monkeypatch):
    """Twilio would reject it anyway, with a message that does not list the valid names."""
    monkeypatch.setenv("TWILIO_TRIAL_SMS_TEMPLATE", "sms_debt_recovery")

    result = channels.send_sms(TO, COMPOSED)

    assert result.status == "NOT_CONFIGURED"
    assert "sms_debt_recovery" in result.detail
    assert "sms_account_alerts" in result.detail, "the error must list what IS valid"
    assert "data" not in sent, "nothing should have been sent"


def test_a_failed_send_is_not_dressed_up_as_a_substitution(sent, monkeypatch):
    """The substitution note applies only to messages that actually left."""
    monkeypatch.setenv("TWILIO_TRIAL_SMS_TEMPLATE", "sms_account_alerts")
    sent["response"] = FakeResponse(400, {"code": 21610, "message": "unsubscribed"})

    result = channels.send_sms(TO, COMPOSED)

    assert result.status == "FAILED"
    assert "template_substituted" not in dict(result.extra)


def test_every_documented_trial_template_is_accepted(sent, monkeypatch):
    for name in channels.TRIAL_SMS_TEMPLATES:
        monkeypatch.setenv("TWILIO_TRIAL_SMS_TEMPLATE", name)
        assert channels.send_sms(TO, COMPOSED).status == "SENT", name


def test_the_ten_twilio_documented_templates_are_the_ones_we_accept():
    """Pinned against Twilio's published trial list, so a typo cannot silently narrow it."""
    assert channels.TRIAL_SMS_TEMPLATES == {
        "sms_2fa", "sms_appointment_reminders", "sms_order_confirmation",
        "sms_delivery_updates", "sms_customer_support", "sms_marketing_promotions",
        "sms_event_notifications", "sms_account_alerts", "sms_feedback_surveys",
        "sms_internal_alerts",
    }
