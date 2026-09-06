"""Twilio's two credential types authenticate differently (ADR-0012 adapter boundary).

WHY THIS EXISTS
    Twilio accepts either an Account SID + Auth Token, or an API Key SID + Secret. They are
    not interchangeable in the way they look like they should be:

        Auth Token   the ACCOUNT SID is both the username and the account in the URL path
        API Key      the KEY authenticates, while the URL still names the ACCOUNT

    Using the account SID as the username alongside an API key secret returns a 401 that
    reads "auth token is not valid for account" - which points at the password when the
    problem is the username. That cost real time to diagnose, so the resolution is pinned
    here rather than left to be rediscovered.
"""

import pytest

from app.dispatch import channels

ACCOUNT = "ACaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
KEY_SID = "SKbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN",
                 "TWILIO_API_KEY_SID", "TWILIO_API_KEY_SECRET"):
        monkeypatch.delenv(name, raising=False)


def test_an_auth_token_authenticates_as_the_account(monkeypatch):
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", ACCOUNT)
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "0123456789abcdef0123456789abcdef")

    account, user, password = channels._twilio_creds()

    assert account == ACCOUNT
    assert user == ACCOUNT, "the account sid is the username for token auth"
    assert password == "0123456789abcdef0123456789abcdef"


def test_an_api_key_authenticates_as_itself_against_the_same_account(monkeypatch):
    """The distinction the 401 does not explain: the URL still names the ACCOUNT."""
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", ACCOUNT)
    monkeypatch.setenv("TWILIO_API_KEY_SID", KEY_SID)
    monkeypatch.setenv("TWILIO_API_KEY_SECRET", "s3cret")

    account, user, password = channels._twilio_creds()

    assert account == ACCOUNT, "the API path is still the account, never the key"
    assert user == KEY_SID
    assert password == "s3cret"


def test_an_api_key_is_preferred_over_the_account_token(monkeypatch):
    """A key can be revoked on its own; the account token cannot without breaking every
    other integration that shares it."""
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", ACCOUNT)
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "0123456789abcdef0123456789abcdef")
    monkeypatch.setenv("TWILIO_API_KEY_SID", KEY_SID)
    monkeypatch.setenv("TWILIO_API_KEY_SECRET", "s3cret")

    _, user, _ = channels._twilio_creds()

    assert user == KEY_SID


def test_a_half_configured_api_key_falls_back_rather_than_failing(monkeypatch):
    """A key sid with no secret is a half-finished edit, not an instruction to break."""
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", ACCOUNT)
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "0123456789abcdef0123456789abcdef")
    monkeypatch.setenv("TWILIO_API_KEY_SID", KEY_SID)

    _, user, _ = channels._twilio_creds()

    assert user == ACCOUNT


def test_no_account_sid_means_no_credentials(monkeypatch):
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "0123456789abcdef0123456789abcdef")

    assert channels._twilio_creds() is None


def test_nothing_configured_is_reported_not_guessed(monkeypatch):
    monkeypatch.setenv("TWILIO_SMS_FROM", "+15550001111")

    result = channels.send_sms("+919999999999", "hello")

    assert result.status == "NOT_CONFIGURED"
    assert "TWILIO_ACCOUNT_SID" in result.detail


def test_whitespace_around_a_pasted_credential_is_stripped(monkeypatch):
    """Credentials arrive by copy-paste, and a trailing space produces a 401 that looks
    exactly like a wrong secret."""
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", f"  {ACCOUNT} ")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", " 0123456789abcdef0123456789abcdef  ")

    account, user, password = channels._twilio_creds()

    assert account == ACCOUNT
    assert password == "0123456789abcdef0123456789abcdef"
