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


# The ten fixed strings a Twilio TRIAL account accepts in place of a message body. On a
# trial the `Body` parameter must BE one of these identifiers; anything else is rejected
# with 572006 "Trial accounts can only use predefined SMS templates".
TRIAL_SMS_TEMPLATES = frozenset({
    "sms_2fa", "sms_appointment_reminders", "sms_order_confirmation",
    "sms_delivery_updates", "sms_customer_support", "sms_marketing_promotions",
    "sms_event_notifications", "sms_account_alerts", "sms_feedback_surveys",
    "sms_internal_alerts",
})


def send_sms(to_number: str, body: str) -> DispatchResult:
    """Send an SMS, or explain exactly why the customer will not receive our text.

    TRIAL MODE SENDS SOMETHING, BUT NOT OUR MESSAGE
        Setting TWILIO_TRIAL_SMS_TEMPLATE makes this send one of Twilio's fixed template
        identifiers instead of the composed message. That is the only way an SMS leaves a
        trial account at all.

        The customer then receives TWILIO'S wording, which means THE PAYMENT LINK IS NOT
        DELIVERED. The channel is proven; the recovery action is not performed. Those are
        different things and the result says so, because a dispatch that reads plainly
        "SENT" here would light a ladder rung and consume a contact slot for a message
        that cannot recover anything.
    """
    sender = os.environ.get("TWILIO_SMS_FROM", "")
    if not sender:
        return _missing("TWILIO_SMS", "TWILIO_SMS_FROM")
    if not to_number:
        return DispatchResult("TWILIO_SMS", "SKIPPED", "row has no phone number")

    template = os.environ.get("TWILIO_TRIAL_SMS_TEMPLATE", "").strip()
    if not template:
        return _twilio_post(
            "Messages.json", {"To": to_number, "From": sender, "Body": body}, "TWILIO_SMS"
        )

    if template not in TRIAL_SMS_TEMPLATES:
        return DispatchResult(
            "TWILIO_SMS", "NOT_CONFIGURED",
            f"TWILIO_TRIAL_SMS_TEMPLATE={template!r} is not one of Twilio's trial "
            f"templates: {', '.join(sorted(TRIAL_SMS_TEMPLATES))}",
        )

    result = _twilio_post(
        "Messages.json", {"To": to_number, "From": sender, "Body": template}, "TWILIO_SMS"
    )
    if result.status == "SENT":
        return DispatchResult(
            channel=result.channel, status="SENT",
            detail=(f"trial template {template!r} delivered - Twilio's wording, "
                    f"NOT our message, so the payment link was not included"),
            provider_id=result.provider_id,
            extra={**dict(result.extra), "template_substituted": template},
        )
    return result


# --- WhatsApp: Meta Cloud API, or Twilio ---------------------------------------------------
#
# TWO PROVIDERS, BECAUSE ONE OF THEM CANNOT BE TESTED FOR FREE
#     Twilio's WhatsApp requires a paid account for any message the API composes itself: a
#     trial rejects freeform text with `ContentSid Required` and refuses Content Templates
#     with "not available on a Trial account". So on a trial the rung is unreachable, and
#     the only way to see it work is to pay.
#
#     Meta's Cloud API gives a free test business number and up to five verified
#     recipients, and freeform text works. It is also the API Twilio is itself wrapping.
#
#     Meta is preferred when configured. Twilio remains for accounts that already pay for
#     it, so nobody's working setup is taken away by this change.
#
# THE 24-HOUR WINDOW IS NOT OURS TO OPT OUT OF
#     WhatsApp only permits freeform business messages inside 24 hours of the customer's
#     last message. Outside it, only pre-approved templates are delivered. That is a
#     WhatsApp policy, not a provider limitation, and it applies to production accounts
#     exactly as it applies here. Error 131047 is named explicitly below, because "failed"
#     with no explanation would send someone hunting through their credentials for a
#     problem that is really a closed conversation window.

META_GRAPH_VERSION = "v23.0"


def _meta_whatsapp_creds() -> Optional[tuple]:
    phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    token = os.environ.get("WHATSAPP_ACCESS_TOKEN", "").strip()
    return (phone_id, token) if phone_id and token else None


def send_whatsapp_meta(to_number: str, body: str) -> DispatchResult:
    """Send via Meta's WhatsApp Cloud API."""
    creds = _meta_whatsapp_creds()
    if not creds:
        return _missing("META_WHATSAPP", "WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_ACCESS_TOKEN")
    if not to_number:
        return DispatchResult("META_WHATSAPP", "SKIPPED", "row has no phone number")

    phone_id, token = creds
    # Meta wants the number without a leading '+'.
    recipient = to_number.lstrip("+")
    try:
        res = requests.post(
            f"https://graph.facebook.com/{META_GRAPH_VERSION}/{phone_id}/messages",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
            json={"messaging_product": "whatsapp", "recipient_type": "individual",
                  "to": recipient, "type": "text", "text": {"body": body}},
            timeout=20,
        )
    except Exception as exc:
        return DispatchResult("META_WHATSAPP", "FAILED", str(exc)[:200])

    if res.status_code not in (200, 201):
        detail = res.text[:200]
        try:
            error = res.json().get("error", {})
            code = error.get("code")
            if code == 131047:
                detail = ("outside WhatsApp's 24-hour window - the customer must message "
                          "first, or the message must use an approved template")
            elif code == 190:
                detail = "access token expired or invalid (temporary tokens last 24 hours)"
            elif code == 131030:
                detail = f"{recipient} is not in the test number's allow-list"
            else:
                detail = f"{code}: {str(error.get('message'))[:150]}"
        except ValueError:
            pass
        return DispatchResult("META_WHATSAPP", "FAILED", f"{res.status_code}: {detail}")

    try:
        message_id = (res.json().get("messages") or [{}])[0].get("id", "")
    except (ValueError, IndexError):
        message_id = ""
    return DispatchResult(
        "META_WHATSAPP", "SENT", f"accepted by Meta for {to_number}",
        provider_id=str(message_id),
    )


def send_whatsapp_twilio(to_number: str, body: str) -> DispatchResult:
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


def send_whatsapp(to_number: str, body: str) -> DispatchResult:
    """Meta if it is configured, Twilio otherwise. The caller never has to know which."""
    if _meta_whatsapp_creds():
        return send_whatsapp_meta(to_number, body)
    return send_whatsapp_twilio(to_number, body)


def send_ivr_call(
    to_number: str,
    spoken_message: str,
    twiml_url: str = "",
) -> DispatchResult:
    """Place a real voice call that speaks the recovery message. This is the IVR channel.

    TWO FORMS, BECAUSE A TRIAL ACCOUNT ONLY ACCEPTS ONE
        Inline `Twiml` is rejected on a trial: "trial accounts have limited parameter
        access". A hosted `Url` is accepted and the call connects - verified against a real
        trial, 5 seconds, handset rang.

        So a URL is used when the engine is publicly reachable, and inline TwiML otherwise,
        which keeps paid accounts working with no configuration at all.
    """
    sender = os.environ.get("TWILIO_VOICE_FROM", os.environ.get("TWILIO_SMS_FROM", ""))
    if not sender:
        return _missing("TWILIO_VOICE", "TWILIO_VOICE_FROM")
    if not to_number:
        return DispatchResult("TWILIO_VOICE", "SKIPPED", "row has no phone number")

    payload = {"To": to_number, "From": sender}
    if twiml_url:
        payload["Url"] = twiml_url
    else:
        payload["Twiml"] = f'<Response><Say voice="alice">{spoken_message}</Say></Response>'
    return _twilio_post("Calls.json", payload, "TWILIO_VOICE")


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
