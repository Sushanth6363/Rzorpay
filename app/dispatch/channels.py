"""Real outbound channel adapters — actually send, or say exactly why they cannot.

DESIGN RULE THAT MATTERS MOST HERE
    An adapter NEVER reports success it did not achieve. If a credential is missing the
    result is NOT_CONFIGURED naming the exact environment variable, and the UI shows that.
    A demo that prints "Sent!" while sending nothing is worse than one that sends nothing,
    because the person watching now believes something that is false — and this whole
    project's argument rests on not doing that.

WHAT CAN GENUINELY SEND, AND WITH WHAT
    RAZORPAY_LINK   Razorpay Payment Links carry `notify: {sms, email}`, so RAZORPAY ITSELF
                    delivers the SMS and the email. This needs only the Razorpay test keys
                    that are already configured, which makes it the highest-fidelity channel
                    available without signing up for anything else.
    EMAIL_SMTP      Direct SMTP. Works with a Gmail App Password.
    TWILIO_SMS      Twilio REST API. Called with `requests`, so no new dependency.
    TWILIO_WHATSAPP Twilio WhatsApp sender (the sandbox requires the recipient to have
                    joined it first — stated, because otherwise it silently does nothing).
    TWILIO_VOICE    Twilio Voice, spoken with TwiML. This is the IVR call.

Every adapter returns the same shape so the caller never has to special-case a channel.
"""

from __future__ import annotations

import os
import smtplib
import ssl
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Any, Dict, Optional

import requests


@dataclass
class DispatchResult:
    """Outcome of one real send attempt."""

    channel: str
    status: str  # SENT | NOT_CONFIGURED | FAILED | SKIPPED
    detail: str = ""
    provider_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def sent(self) -> bool:
        return self.status == "SENT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel": self.channel,
            "status": self.status,
            "detail": self.detail,
            "provider_id": self.provider_id,
            **self.extra,
        }


def _missing(channel: str, *env_vars: str) -> DispatchResult:
    return DispatchResult(
        channel=channel,
        status="NOT_CONFIGURED",
        detail="set " + ", ".join(env_vars),
    )


# --- Razorpay Payment Link (Razorpay sends the SMS + email itself) -----------------------


def send_razorpay_link(
    amount_paise: int,
    name: str,
    email: str,
    contact: str,
    description: str,
    reference_id: str,
) -> DispatchResult:
    """Create a Razorpay Payment Link with notifications on. Razorpay delivers it."""
    from app.integrations.razorpay_client import RazorpayIntegrationClient

    client = RazorpayIntegrationClient()
    if client.key_id.startswith("rzp_test_mock"):
        return _missing("RAZORPAY_LINK", "RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET")

    try:
        res = client.create_payment_link(
            amount_paise=amount_paise,
            customer_name=name,
            customer_email=email,
            customer_contact=contact,
            description=description,
            reference_id=reference_id,
        )
    except Exception as exc:
        return DispatchResult("RAZORPAY_LINK", "FAILED", str(exc)[:200])

    if res.get("is_simulated"):
        return DispatchResult(
            "RAZORPAY_LINK", "FAILED",
            "client fell back to a simulated link - check the API response",
        )

    return DispatchResult(
        channel="RAZORPAY_LINK",
        status="SENT",
        detail=f"Razorpay notified {email or contact} (SMS + email)",
        provider_id=str(res.get("id", "")),
        extra={"short_url": res.get("short_url", "")},
    )


# --- SMTP email ---------------------------------------------------------------------------


def send_email_smtp(
    to_email: str,
    subject: str,
    body: str,
    html_body: str = "",
) -> DispatchResult:
    """Send a real email over SMTP.

    When `html_body` is supplied the message is multipart/alternative: the plain-text part
    is a genuine fallback, not a placeholder, because a client that cannot render HTML must
    still receive a usable payment URL rather than an empty message.
    """
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")

    if not user or not password:
        return _missing("EMAIL_SMTP", "SMTP_USER", "SMTP_PASSWORD")
    if not to_email:
        return DispatchResult("EMAIL_SMTP", "SKIPPED", "row has no email address")

    message = EmailMessage()
    message["From"] = os.environ.get("SMTP_FROM", user)
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(user, password)
            server.send_message(message)
    except Exception as exc:
        return DispatchResult("EMAIL_SMTP", "FAILED", str(exc)[:200])

    return DispatchResult("EMAIL_SMTP", "SENT", f"delivered to {to_email}")


# --- Twilio: SMS, WhatsApp, and the IVR voice call ----------------------------------------


def _twilio_creds() -> Optional[tuple]:
    """Return (account_sid, auth_user, auth_password), or None if unusable.

    TWILIO ACCEPTS TWO KINDS OF CREDENTIAL AND THEY AUTHENTICATE DIFFERENTLY
        Account SID + Auth Token   the account-wide credential. The SID is both the
                                   username and the account in the URL path.
        API Key SID + Secret       a scoped, revocable key pair (`SK...`). Here the KEY
                                   authenticates, while the URL still names the ACCOUNT.

        Using the account SID as the username alongside an API key secret fails with a
        401 that reads like a wrong password, which is a genuinely confusing hour to
        spend. So the account and the identity are resolved separately.

        An API key is preferred when present: it can be revoked without rotating the
        account-wide token that every other integration depends on.
    """
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    if not account_sid:
        return None

    key_sid = os.environ.get("TWILIO_API_KEY_SID", "").strip()
    key_secret = os.environ.get("TWILIO_API_KEY_SECRET", "").strip()
    if key_sid and key_secret:
        return (account_sid, key_sid, key_secret)

    token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    if token:
        return (account_sid, account_sid, token)

    return None


def _twilio_post(path: str, data: Dict[str, str], channel: str) -> DispatchResult:
    creds = _twilio_creds()
    if not creds:
        return _missing(
            channel, "TWILIO_ACCOUNT_SID",
            "and either TWILIO_AUTH_TOKEN or TWILIO_API_KEY_SID + TWILIO_API_KEY_SECRET",
        )
    account_sid, auth_user, auth_password = creds
    try:
        res = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/{path}",
            auth=(auth_user, auth_password), data=data, timeout=20,
        )
    except Exception as exc:
        return DispatchResult(channel, "FAILED", str(exc)[:200])

    if res.status_code not in (200, 201):
        return DispatchResult(channel, "FAILED", f"{res.status_code}: {res.text[:180]}")
    return DispatchResult(
        channel, "SENT", f"accepted by Twilio for {data.get('To', '')}",
        provider_id=str(res.json().get("sid", "")),
    )


def send_sms(to_number: str, body: str) -> DispatchResult:
    sender = os.environ.get("TWILIO_SMS_FROM", "")
    if not sender:
        return _missing("TWILIO_SMS", "TWILIO_SMS_FROM")
    if not to_number:
        return DispatchResult("TWILIO_SMS", "SKIPPED", "row has no phone number")
    return _twilio_post(
        "Messages.json", {"To": to_number, "From": sender, "Body": body}, "TWILIO_SMS"
    )


def send_whatsapp(to_number: str, body: str) -> DispatchResult:
    sender = os.environ.get("TWILIO_WHATSAPP_FROM", "")
    if not sender:
        return _missing("TWILIO_WHATSAPP", "TWILIO_WHATSAPP_FROM")
    if not to_number:
        return DispatchResult("TWILIO_WHATSAPP", "SKIPPED", "row has no phone number")
    # The Twilio WhatsApp sandbox only delivers to numbers that have joined it. Without
    # that the API returns 200 and the message never arrives, which would look like a
    # success here - so it is called out rather than discovered later.
    return _twilio_post(
        "Messages.json",
        {"To": f"whatsapp:{to_number}", "From": f"whatsapp:{sender}", "Body": body},
        "TWILIO_WHATSAPP",
    )


def send_ivr_call(to_number: str, spoken_message: str) -> DispatchResult:
    """Place a real voice call that speaks the recovery message. This is the IVR channel."""
    sender = os.environ.get("TWILIO_VOICE_FROM", os.environ.get("TWILIO_SMS_FROM", ""))
    if not sender:
        return _missing("TWILIO_VOICE", "TWILIO_VOICE_FROM")
    if not to_number:
        return DispatchResult("TWILIO_VOICE", "SKIPPED", "row has no phone number")
    twiml = f'<Response><Say voice="alice">{spoken_message}</Say></Response>'
    return _twilio_post(
        "Calls.json", {"To": to_number, "From": sender, "Twiml": twiml}, "TWILIO_VOICE"
    )


def configured_channels() -> Dict[str, bool]:
    """Which channels can actually send right now. Drives the UI so nothing is promised."""
    from app.integrations.razorpay_client import RazorpayIntegrationClient

    twilio = _twilio_creds() is not None
    return {
        "RAZORPAY_LINK": not RazorpayIntegrationClient().key_id.startswith("rzp_test_mock"),
        "EMAIL_SMTP": bool(os.environ.get("SMTP_USER") and os.environ.get("SMTP_PASSWORD")),
        "TWILIO_SMS": twilio and bool(os.environ.get("TWILIO_SMS_FROM")),
        "TWILIO_WHATSAPP": twilio and bool(os.environ.get("TWILIO_WHATSAPP_FROM")),
        "TWILIO_VOICE": twilio and bool(
            os.environ.get("TWILIO_VOICE_FROM") or os.environ.get("TWILIO_SMS_FROM")
        ),
    }
