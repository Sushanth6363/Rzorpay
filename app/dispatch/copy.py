"""Rung-aware message copy (ADR-0021).

THE PROBLEM
    Every channel sent identical text. A customer's fourth contact — an escalation earned
    over days — read exactly like their first gentle email, only by SMS. That is worse than
    it sounds in both directions: the first touch arrives with more urgency than a single
    failed payment warrants, and the fourth arrives with none at all, so the escalation the
    engine worked to justify lands as a shrug.

    Escalation has to change the MESSAGE, not just the medium. Otherwise the ladder is
    theatre.

TWO AXES
    RUNG      sets TONE.     Informational -> reminder -> direct -> urgent -> final.
    DIAGNOSIS sets the ASK.  A declined card needs "update your card"; insufficient funds
              needs "when you're ready"; an overdue invoice needs accounts-payable
              language, not consumer language.

    Getting the ask wrong is the more expensive error. Telling someone whose card expired
    to "try again when funds are available" is not merely unhelpful — it misdiagnoses them
    to their face and reads as automated indifference.

INVARIANTS:
1. NEVER FABRICATE URGENCY. No invented deadlines, no threatened consequences, no fake
   scarcity. The engine has no authority to threaten anything, and inventing pressure to
   lift a recovery rate is exactly the behaviour these controls exist to prevent.
2. TONE RISES WITH EARNED RUNG, never with the amount. A large balance does not license
   opening at the loudest register.
3. ALWAYS IDENTIFIABLE AND DECLINABLE. Every message says who it is from and how to stop.
"""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Dict, Optional

from app.domain.enums import ActionType, DiagnosisCode

# Rung -> tone. Index matches ESCALATION_LADDER position; RECOMMEND_RETRY is off-ladder.
TONE_BY_RUNG = {
    0: "informational",   # EMAIL_LINK    — we noticed, here is the link
    1: "reminder",        # SMS_LINK      — still outstanding
    2: "direct",          # WHATSAPP_LINK — can we help you finish this?
    3: "urgent",          # IVR_CALL      — we have tried a few times
    4: "final",           # AGENT_DIAL    — a person is calling
}

# Diagnosis -> the ASK. What the customer must actually DO for this to resolve.
ASK_BY_DIAGNOSIS: Dict[str, str] = {
    DiagnosisCode.CARD_DECLINED.value:
        "Your card was declined, so it will need updating before this can go through.",
    DiagnosisCode.INSUFFICIENT_FUNDS.value:
        "The payment could not be completed due to insufficient funds. "
        "You can complete it whenever you are ready.",
    DiagnosisCode.GATEWAY_FAILURE.value:
        "This failed because of a temporary issue with the payment gateway, not anything "
        "you did. It should work now.",
    DiagnosisCode.CUSTOMER_ABANDONMENT.value:
        "Your order is still saved and you can pick up where you left off.",
    DiagnosisCode.SUBSCRIPTION_RENEWAL_FAILURE.value:
        "Your subscription renewal did not go through, so access may be interrupted.",
    DiagnosisCode.INVOICE_OVERDUE.value:
        "This invoice is showing as outstanding on our ledger.",
    DiagnosisCode.CUSTOMER_UNRESPONSIVE.value:
        "We have not been able to reach you about this payment.",
    DiagnosisCode.UNKNOWN.value:
        "The payment did not complete.",
}

OPENER_BY_TONE = {
    "informational": "We noticed a payment of {amount} did not go through.",
    "reminder": "A payment of {amount} is still outstanding.",
    # Plain ASCII punctuation throughout: an em-dash can transcode badly on SMS gateways
    # and push a message over the GSM-7 boundary, silently doubling its cost.
    "direct": "Your payment of {amount} is still pending. Can we help you complete it?",
    "urgent": "We have tried to reach you a few times about {amount}.",
    "final": "We are calling about an outstanding payment of {amount}.",
}

CLOSER_BY_TONE = {
    "informational": "No action is needed if you have already paid.",
    "reminder": "If you have already paid, please ignore this.",
    "direct": "If something is blocking the payment, reply and we will help.",
    "urgent": "If there is a problem with this payment, please let us know.",
    "final": "Please get in touch so we can resolve this with you.",
}

# B2B receivables are read by an accounts-payable team, not a consumer. Consumer phrasing
# to an AP inbox reads as spam and gets filtered.
B2B_OPENER = "Invoice for {amount} is showing as outstanding."
B2B_CLOSER = "If this is already scheduled for payment, please share the payment date."

SIGNATURE = (
    "Sent by the Unified Recovery Engine on behalf of the merchant.\n"
    "Reply STOP to opt out of payment reminders."
)


@dataclass(frozen=True)
class Message:
    subject: str
    body: str
    spoken: str        # for IVR / voice
    html: str = ""     # email only; empty means send plain text alone


def rung_of(action: ActionType) -> int:
    from app.pipeline.escalation import RUNG_OF

    return RUNG_OF.get(action, 0)


def first_name(full_name: str) -> str:
    """Greet with the first name. "Hi Rahul Sharma," reads like a form letter."""
    return (full_name or "").strip().split(" ")[0]


def due_context(due_date: str) -> str:
    """One sentence of factual overdue context, or nothing.

    Stated as a fact the merchant's ledger already holds, never as pressure - "12 days
    overdue" is information; "overdue - act immediately" is manufactured urgency.
    """
    if not due_date:
        return ""
    try:
        due = datetime.strptime(due_date, "%Y-%m-%d").date()
    except ValueError:
        return ""
    days = (datetime.now(timezone.utc).date() - due).days
    if days > 0:
        return f"It was due on {due.strftime('%d %B %Y')}, {days} day{'s' if days != 1 else ''} ago."
    if days == 0:
        return f"It is due today, {due.strftime('%d %B %Y')}."
    return f"It is due on {due.strftime('%d %B %Y')}."


def build_message(
    action: ActionType,
    amount_paise: int,
    customer_name: str = "",
    diagnosis_code: Optional[str] = None,
    payment_link: str = "",
    attempt: int = 0,
    due_date: str = "",
) -> Message:
    """Compose copy whose TONE follows the earned rung and whose ASK follows the diagnosis."""
    amount = f"Rs {amount_paise / 100:,.2f}"
    tone = TONE_BY_RUNG.get(rung_of(action), "informational")
    is_b2b = diagnosis_code == DiagnosisCode.INVOICE_OVERDUE.value

    opener = (B2B_OPENER if is_b2b else OPENER_BY_TONE[tone]).format(amount=amount)
    closer = B2B_CLOSER if is_b2b else CLOSER_BY_TONE[tone]
    ask = ASK_BY_DIAGNOSIS.get(str(diagnosis_code or ""), ASK_BY_DIAGNOSIS[DiagnosisCode.UNKNOWN.value])

    greeting = f"Hi {first_name(customer_name)}," if customer_name else "Hello,"
    link_line = f"You can complete it here: {payment_link}" if payment_link else ""

    subject = {
        "informational": f"Complete your payment of {amount}",
        "reminder": f"Reminder: {amount} still outstanding",
        "direct": f"Can we help you complete {amount}?",
        "urgent": f"Outstanding payment of {amount}",
        "final": f"Regarding your outstanding payment of {amount}",
    }[tone]
    if is_b2b:
        subject = f"Outstanding invoice — {amount}"

    overdue = due_context(due_date)
    ask_block = f"{ask} {overdue}".strip() if overdue else ask

    body_parts = [greeting, "", opener, ask_block]
    if link_line:
        body_parts += ["", link_line]
    body_parts += ["", closer, "", SIGNATURE]
    body = "\n".join(body_parts)

    # Voice is heard once and cannot be re-read, so it stays short and states the ask
    # plainly. It never speaks a URL — nobody can write one down from a phone call.
    spoken = (
        f"Hello. This is an automated call regarding an outstanding payment of "
        f"{amount_paise // 100} rupees. "
        f"{ask} "
        f"Please check your email or messages for a secure payment link. Thank you."
    )

    # HTML is rendered from the SAME opener / ask / closer as the plain text, so the two
    # parts of a multipart message can never drift into saying different things.
    html = ""
    if action == ActionType.EMAIL_LINK:
        from app.dispatch.email_template import render_payment_email

        html = render_payment_email(
            greeting=greeting,
            opener=opener,
            ask=ask_block,
            closer=closer,
            amount_paise=amount_paise,
            payment_url=payment_link,
            signature=SIGNATURE,
        )

    return Message(subject=subject, body=body, spoken=spoken, html=html)
