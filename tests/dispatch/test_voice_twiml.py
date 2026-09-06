"""The IVR rung on a trial account, and the endpoint that makes it possible.

WHY THIS EXISTS
    Twilio rejects inline TwiML on a trial account:

        400 "Invalid or disallowed parameters provided - trial accounts have
             limited parameter access"

    but accepts a `Url` pointing at TwiML we host. Verified against a real trial: the call
    completed in 5 seconds and rang the handset. So the voice rung IS reachable without
    paying, provided the engine serves its own TwiML.

    That endpoint has to be publicly reachable, because Twilio fetches it with no
    credentials. Which makes the signature the only thing standing between a phone system
    and an endpoint that reads a customer's name and debt aloud to anyone who guesses a
    case id. Most of this file is about that.
"""

import pytest

from app.dispatch import voice

SECRET = "test-webhook-secret"
CASE = "case_merch_demo_CUST001_1"


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", SECRET)
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.setenv("NGROK_DOMAIN", "example.ngrok-free.dev")


# --- the signature is the access control ------------------------------------------------------


def test_a_valid_signature_verifies():
    assert voice.verify_case(CASE, voice.sign_case(CASE)) is True


def test_a_signature_for_one_case_does_not_open_another():
    """Otherwise one leaked URL would expose every customer."""
    assert voice.verify_case("case_other", voice.sign_case(CASE)) is False


def test_an_absent_signature_is_refused():
    assert voice.verify_case(CASE, "") is False


def test_a_tampered_signature_is_refused():
    signature = voice.sign_case(CASE)
    tampered = ("0" if signature[0] != "0" else "1") + signature[1:]

    assert voice.verify_case(CASE, tampered) is False


def test_it_fails_closed_when_no_secret_is_configured(monkeypatch):
    """A missing secret must not mean "no checking required"."""
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "")

    assert voice.verify_case(CASE, "anything") is False
    assert voice.twiml_url(CASE) is None


def test_the_signing_context_differs_from_webhook_signing():
    """The same secret signs both. A domain prefix keeps a signature minted for one
    purpose from being replayable as the other."""
    import hashlib
    import hmac

    raw = hmac.new(SECRET.encode(), CASE.encode(), hashlib.sha256).hexdigest()

    assert voice.sign_case(CASE) != raw


# --- the URL ------------------------------------------------------------------------------------


def test_the_url_carries_the_case_and_its_signature():
    url = voice.twiml_url(CASE)

    assert url.startswith("https://example.ngrok-free.dev/twiml/recovery?")
    assert f"case={CASE}" in url
    assert f"sig={voice.sign_case(CASE)}" in url


def test_an_explicit_public_url_wins_over_the_tunnel(monkeypatch):
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://recovery.example.com")

    assert voice.twiml_url(CASE).startswith("https://recovery.example.com/")


def test_no_public_url_means_no_hosted_twiml(monkeypatch):
    """A legitimate answer, not an error: the adapter falls back to inline TwiML, which
    works on a paid account."""
    monkeypatch.delenv("NGROK_DOMAIN", raising=False)

    assert voice.twiml_url(CASE) is None


# --- what the customer hears ---------------------------------------------------------------------


def test_the_message_speaks_rupees_rather_than_showing_a_symbol():
    message = voice.spoken_message("Aarti", 2_500_000)

    assert "25,000 rupees" in message
    assert "Rs" not in message and "₹" not in message


def test_the_message_carries_no_url():
    """Nobody writes a URL down from a phone call. That is what the companion SMS is for."""
    message = voice.spoken_message("Aarti", 2_500_000, "2026-08-24")

    assert "http" not in message
    assert "text message" in message


def test_a_missing_name_does_not_produce_hello_none():
    assert "None" not in voice.spoken_message("", 100_000)


def test_the_twiml_is_well_formed_and_escaped():
    """An apostrophe in a customer's name would otherwise produce malformed XML, and
    Twilio's failure mode for that is a silent hang-up rather than a visible error."""
    from xml.etree import ElementTree

    xml = voice.twiml_for(voice.spoken_message("D'Souza & Co", 100_000))

    root = ElementTree.fromstring(xml)
    assert root.tag == "Response"
    assert "D'Souza & Co" in root.find("Say").text
