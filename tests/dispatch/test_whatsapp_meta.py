"""WhatsApp via Meta's Cloud API, and why there are two providers (ADR-0012).

WHY META WAS ADDED
    Twilio's WhatsApp cannot be exercised on a trial account at all. Freeform text is
    rejected with `ContentSid Required`, and Content Templates return "not available on a
    Trial account". Both were observed against a real Twilio trial. So the rung was
    unreachable without paying, which makes it undemonstrable and, worse, untestable
    against the real provider.

    Meta's Cloud API gives a free test business number, up to five verified recipients, and
    freeform text - and is the API Twilio itself wraps. Meta is preferred when configured;
    Twilio stays for accounts that already pay for it.

THE ERROR CODES ARE THE POINT
    Every failure below is a real WhatsApp condition with a specific cause, and each is
    translated into a sentence naming that cause. "FAILED: 400" would send someone hunting
    through their credentials for a problem that is really a closed conversation window.
"""

import json

import pytest

from app.dispatch import channels

TO = "+916363613285"


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    for name in ("WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_ACCESS_TOKEN",
                 "TWILIO_WHATSAPP_FROM", "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture()
def meta(monkeypatch):
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123456789")
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "EAAG...")
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers or {}
        captured["body"] = json or {}
        return captured.get("response", FakeResponse(200, {"messages": [{"id": "wamid.X"}]}))

    monkeypatch.setattr(channels.requests, "post", fake_post)
    return captured


# --- routing ---------------------------------------------------------------------------------


def test_meta_is_used_when_configured(meta):
    result = channels.send_whatsapp(TO, "hello")

    assert result.channel == "META_WHATSAPP"
    assert result.status == "SENT"


def test_twilio_is_used_when_meta_is_not_configured(monkeypatch):
    """Adding Meta must not break an account that already pays for Twilio."""
    monkeypatch.setenv("TWILIO_WHATSAPP_FROM", "+15550001111")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "0123456789abcdef0123456789abcdef")
    monkeypatch.setattr(channels.requests, "post",
                        lambda *a, **k: FakeResponse(201, {"sid": "SM1"}))

    assert channels.send_whatsapp(TO, "hello").channel == "TWILIO_WHATSAPP"


def test_neither_configured_names_both_missing_meta_variables(monkeypatch):
    result = channels.send_whatsapp_meta(TO, "hello")

    assert result.status == "NOT_CONFIGURED"
    assert "WHATSAPP_PHONE_NUMBER_ID" in result.detail
    assert "WHATSAPP_ACCESS_TOKEN" in result.detail


# --- the request Meta actually receives -------------------------------------------------------


def test_the_number_is_sent_without_a_leading_plus(meta):
    """Meta rejects the E.164 '+'. The CSV stores it with one, so it is stripped here
    rather than making every caller remember."""
    channels.send_whatsapp(TO, "hello")

    assert meta["body"]["to"] == "916363613285"


def test_the_request_is_shaped_the_way_meta_expects(meta):
    channels.send_whatsapp(TO, "pay here")

    assert "graph.facebook.com" in meta["url"]
    assert meta["url"].endswith("/123456789/messages")
    assert meta["headers"]["Authorization"].startswith("Bearer ")
    assert meta["body"]["messaging_product"] == "whatsapp"
    assert meta["body"]["text"]["body"] == "pay here"


def test_the_provider_message_id_is_recorded(meta):
    """Without it there is no way to trace a delivery back to a WhatsApp message."""
    assert channels.send_whatsapp(TO, "hello").provider_id == "wamid.X"


# --- failures explained rather than reported --------------------------------------------------


def test_a_closed_24_hour_window_says_so(meta):
    meta["response"] = FakeResponse(400, {"error": {"code": 131047, "message": "Re-engagement"}})

    detail = channels.send_whatsapp(TO, "hello").detail

    assert "24-hour" in detail
    assert "template" in detail


def test_an_expired_token_says_so(meta):
    """Temporary Meta tokens last 24 hours, so this is the most likely failure the morning
    after a setup."""
    meta["response"] = FakeResponse(401, {"error": {"code": 190, "message": "expired"}})

    assert "expired" in channels.send_whatsapp(TO, "hello").detail


def test_an_unverified_recipient_says_so(meta):
    """The test number only delivers to numbers added to its allow-list."""
    meta["response"] = FakeResponse(400, {"error": {"code": 131030, "message": "not allowed"}})

    detail = channels.send_whatsapp(TO, "hello").detail

    assert "allow-list" in detail
    assert "916363613285" in detail


def test_an_unknown_error_still_carries_its_code(meta):
    meta["response"] = FakeResponse(400, {"error": {"code": 99999, "message": "surprise"}})

    detail = channels.send_whatsapp(TO, "hello").detail

    assert "99999" in detail
    assert "surprise" in detail


def test_a_non_json_error_body_does_not_crash(meta):
    class Weird:
        status_code = 500
        text = "<html>gateway error</html>"

        def json(self):
            raise ValueError("not json")

    meta["response"] = Weird()

    result = channels.send_whatsapp(TO, "hello")

    assert result.status == "FAILED"
    assert "500" in result.detail


def test_no_phone_number_is_skipped_not_failed(meta):
    """A missing number is a data-quality fact, not a provider error."""
    assert channels.send_whatsapp_meta("", "hello").status == "SKIPPED"
