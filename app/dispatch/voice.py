"""TwiML for the IVR rung, served from our own endpoint (ADR-0012, ADR-0021).

WHY THIS EXISTS
    Twilio accepts a spoken message two ways: inline as a `Twiml` parameter, or as a `Url`
    pointing at TwiML the caller hosts. A TRIAL ACCOUNT REJECTS THE INLINE FORM:

        400 "Invalid or disallowed parameters provided - trial accounts have
             limited parameter access, upgrade your account to unlock full
             functionality"

    while the `Url` form is accepted and the call connects. Observed against a real trial:
    a call placed with a hosted TwiML URL completed in 5 seconds and rang the handset.

    So the IVR rung is reachable without paying, provided the engine serves its own TwiML.
    That is what this module is for.

WHY THE URL IS SIGNED
    The endpoint must be publicly reachable, because Twilio fetches it. A plain
    `?case=<id>` would let anyone who guessed a case id hear a customer's name and the
    amount they owe read aloud - a disclosure endpoint wearing a phone system's clothes.

    So the URL carries an HMAC over the case id. Only something holding the webhook secret
    can mint a valid one, which means only this engine can.

WHY NOT PUT THE MESSAGE IN THE URL
    Passing the spoken text as a query parameter would be simpler and worse: the message
    would appear in Twilio's request logs, in any proxy in between, and in our own access
    log, and anyone able to call the endpoint could make our number read out text of their
    choosing. The URL names a case; the message is built here, from stored state.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Optional
from xml.sax.saxutils import escape

# Distinct from the webhook signing context. The same secret is used, so the two purposes
# are separated by a domain prefix rather than by hoping their message shapes never collide.
_SIGNING_CONTEXT = b"twiml-recovery-v1:"

# Twilio's `alice` voice reads Indian English numerals acceptably and needs no extra
# configuration. Anything better is a paid feature.
VOICE = "alice"


def _secret() -> bytes:
    return os.environ.get("RAZORPAY_WEBHOOK_SECRET", "").encode("utf-8")


def sign_case(case_id: str) -> str:
    """A signature only this engine can produce for this case id."""
    return hmac.new(_secret(), _SIGNING_CONTEXT + case_id.encode("utf-8"),
                    hashlib.sha256).hexdigest()


def verify_case(case_id: str, signature: str) -> bool:
    """Constant-time check. Fails closed when no secret is configured."""
    if not case_id or not signature or not _secret():
        return False
    return hmac.compare_digest(sign_case(case_id), signature)


def public_base_url() -> str:
    """Where Twilio can reach this engine, or empty if it cannot reach it at all."""
    explicit = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if explicit:
        return explicit
    domain = os.environ.get("NGROK_DOMAIN", "").strip().rstrip("/")
    if domain:
        return domain if domain.startswith("http") else f"https://{domain}"
    return ""


def twiml_url(case_id: str) -> Optional[str]:
    """The URL Twilio should fetch, or None when this engine is not publicly reachable.

    None is a legitimate answer, not an error: without a public URL the trial path is
    unavailable, and the adapter falls back to inline TwiML, which works on paid accounts.
    """
    base = public_base_url()
    if not base or not case_id or not _secret():
        return None
    return f"{base}/twiml/recovery?case={case_id}&sig={sign_case(case_id)}"


def spoken_message(name: str, amount_paise: int, due_date: str = "") -> str:
    """What the customer actually hears.

    Written for the ear, not the eye: rupees spoken in full rather than a symbol, no URL
    (nobody writes one down from a call - that is what the companion SMS is for), and short
    enough to finish before an answering machine cuts in.
    """
    greeting = f"Hello {name}. " if name else "Hello. "
    rupees = amount_paise / 100
    due = f" It was due on {due_date}." if due_date else ""
    return (
        f"{greeting}This is a call from the accounts team about an outstanding payment "
        f"of {rupees:,.0f} rupees.{due} "
        f"We have also sent you the payment link by text message. "
        f"Thank you."
    )


def twiml_for(message: str) -> str:
    """Wrap a spoken message as TwiML.

    The message is XML-escaped even though it is built from our own records: an apostrophe
    in a customer's name would otherwise produce malformed XML, and Twilio's failure mode
    for that is a silent hang-up rather than an error we would see.
    """
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response><Say voice="{VOICE}">{escape(message)}</Say></Response>'
    )
