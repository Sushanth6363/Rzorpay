"""ChannelDispatcher — the single boundary between a decision and the outside world.

WHAT THIS IS, AND IS NOT
    It is NOT a second policy engine. Safety, contact budget, escalation ceiling and
    expected-value ranking all ran inside the Recovery Engine before anything reached here,
    and none of it is re-litigated. The dispatcher does not decide WHETHER a customer
    should be contacted.

    It checks FACTS the engine cannot know, at the only moment they matter: immediately
    before the message leaves the process. The engine decided at 17:00. The customer paid
    at 17:30. The scheduler wakes at 18:00. Only something reading case state at 18:00 can
    stop that message, and this is that something.

THE RACE THIS EXISTS TO LOSE SAFELY
        17:00  engine decides WHATSAPP, follow-up scheduled
        17:30  customer pays -> verified webhook -> case = PAID
        18:00  scheduler wakes
        18:00  dispatcher RE-READS the case from the database
        18:00  case.may_contact is False -> BLOCKED, nothing sent

    The re-read is the entire point. A `Case` object passed in from an earlier decision is
    by definition stale, so `dispatch()` deliberately ignores any case state it is handed
    and loads it fresh. Trusting the caller's copy would reintroduce exactly the bug.

INVARIANTS:
1. PAYMENT ALWAYS WINS. A PAID or CLOSED case can never produce an outbound contact,
   whatever was scheduled earlier.
2. IDEMPOTENT AT THE BOUNDARY. A provider timeout that is retried with the same key sends
   once. The ledger guards this upstream; this guards the adapter itself, because the CSV
   and scheduler paths can reach an adapter without passing through a reservation.
3. NEVER REPORTS A SEND IT DID NOT MAKE. A missing credential is NOT_CONFIGURED naming the
   variable; a blocked send says which check blocked it.
4. NO POLICY OF ITS OWN. Every rejection here is a FACT (paid, closed, already sent,
   unconfigured), never a judgement about whether contacting this person is wise.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.cases.models import Case, CaseEvent, CaseEventKind, CaseStatus, now_iso
from app.cases.repository import CaseRepository
from app.dispatch import channels
from app.domain.enums import ActionType

logger = logging.getLogger("recovery.dispatcher")

# Actions that put a message in front of a person. RECOMMEND_RETRY is absent by design:
# it is a recommendation to the payment infrastructure, not an outbound contact (ADR-0006).
CONTACT_ACTIONS = frozenset({
    ActionType.EMAIL_LINK,
    ActionType.SMS_LINK,
    ActionType.WHATSAPP_LINK,
    ActionType.IVR_CALL,
    ActionType.AGENT_DIAL,
})

DISPATCH_DDL = """
CREATE TABLE IF NOT EXISTS dispatch_log (
    idempotency_key TEXT PRIMARY KEY,
    case_id         TEXT NOT NULL,
    action_type     TEXT NOT NULL,
    channel         TEXT,
    status          TEXT NOT NULL,
    detail          TEXT,
    provider_id     TEXT,
    dispatched_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_dispatch_case ON dispatch_log(case_id, dispatched_at);
"""

_LOCK = threading.Lock()


@dataclass
class DispatchOutcome:
    """What happened, and if nothing happened, exactly which check stopped it."""

    allowed: bool
    status: str          # SENT | BLOCKED | NOT_CONFIGURED | FAILED | DUPLICATE | SKIPPED
    reason: str = ""
    channel: str = ""
    provider_id: Optional[str] = None
    detail: Dict[str, Any] = field(default_factory=dict)

    @property
    def sent(self) -> bool:
        return self.status == "SENT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed, "status": self.status, "reason": self.reason,
            "channel": self.channel, "provider_id": self.provider_id, **self.detail,
        }


# Razorpay's `notify` covers exactly two channels for a payment link: email and SMS. It
# does not place voice calls, so IVR and agent dial remain the engine's own to send even
# when the provider owns link delivery.
PROVIDER_DELIVERED_ACTIONS = frozenset({ActionType.EMAIL_LINK, ActionType.SMS_LINK})

# A call is the only rung that leaves nothing behind. These get an SMS alongside carrying
# the payment link, so the most intrusive action the engine can take also produces
# something the customer can act on afterwards. See RECOVERY_VOICE_COMPANION_SMS.
VOICE_ACTIONS = frozenset({ActionType.IVR_CALL, ActionType.AGENT_DIAL})


class ChannelDispatcher:
    """Routes an already-decided action to a channel, after re-checking case facts."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        repository: Optional[CaseRepository] = None,
        dry_run: Optional[bool] = None,
    ) -> None:
        self.conn = conn
        self.repo = repository or CaseRepository(conn)
        self._dry_run_override = dry_run
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with _LOCK:
            self.conn.executescript(DISPATCH_DDL)
            self.conn.commit()

    @property
    def dry_run(self) -> bool:
        """Dry run unless dispatch is explicitly enabled. Default is always safe."""
        if self._dry_run_override is not None:
            return self._dry_run_override
        from app.realtime import config

        return not config.DISPATCH_ENABLED

    # --- the gate -------------------------------------------------------------------

    def precheck(self, case_id: str, action: ActionType) -> DispatchOutcome:
        """Re-read the case and decide whether this send may still proceed.

        Every rejection is a fact, not an opinion.
        """
        if action == ActionType.NO_ACTION:
            return DispatchOutcome(False, "SKIPPED", "engine chose not to contact")

        if action not in CONTACT_ACTIONS:
            return DispatchOutcome(
                False, "SKIPPED",
                f"{action.value} targets the payment infrastructure, not the customer",
            )

        # THE RE-READ. Any case object held by the caller is stale by construction.
        case = self.repo.get_case(case_id)
        if case is None:
            return DispatchOutcome(False, "BLOCKED", f"unknown case {case_id}")

        if case.status == CaseStatus.PAID:
            return DispatchOutcome(
                False, "BLOCKED",
                "case is PAID - payment always wins over a scheduled action",
            )
        if case.status == CaseStatus.CLOSED:
            return DispatchOutcome(
                False, "BLOCKED", f"case is CLOSED ({case.close_reason or 'no reason given'})",
            )

        return DispatchOutcome(True, "ALLOWED", "case is open for contact")

    def already_dispatched(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        self.conn.row_factory = sqlite3.Row
        row = self.conn.execute(
            "SELECT * FROM dispatch_log WHERE idempotency_key=?;", (idempotency_key,)
        ).fetchone()
        return dict(row) if row else None

    def _record(
        self, key: str, case_id: str, action: ActionType, outcome: DispatchOutcome
    ) -> None:
        self.conn.execute(
            """INSERT OR IGNORE INTO dispatch_log (
                   idempotency_key, case_id, action_type, channel, status, detail,
                   provider_id, dispatched_at
               ) VALUES (?,?,?,?,?,?,?,?);""",
            (key, case_id, action.value, outcome.channel, outcome.status,
             outcome.reason[:400], outcome.provider_id, now_iso()),
        )
        self.conn.commit()

    # --- dispatch -------------------------------------------------------------------

    def _send_voice_companion_sms(
        self,
        case_id: str,
        action: ActionType,
        phone: str,
        idempotency_key: str,
        payment_url: str,
    ) -> None:
        """Follow a placed call with the link, so the call leaves something behind.

        Only ever runs AFTER a call was actually placed. If the call itself did not go out,
        sending an SMS instead would be the dispatcher substituting one channel for another
        - a policy decision that belongs to the engine, not to the thing that carries out
        its instructions.

        Failure here is deliberately not fatal. The call succeeded and the contact is real;
        a companion that could not be delivered is recorded and moves on rather than
        turning a successful contact into a failed one.
        """
        if not phone or not payment_url:
            return

        # The call happened moments ago, but "moments" is exactly when a payment lands. The
        # cheapest possible re-read closes the window rather than assuming it away.
        case = self.repo.get_case(case_id)
        if case is None or not case.may_contact:
            return

        companion_key = f"{idempotency_key}:companion_sms"
        if self.already_dispatched(companion_key) is not None:
            return

        body = (
            f"We just tried to call you about your outstanding payment. "
            f"You can settle it here: {payment_url}"
        )
        result = channels.send_sms(phone, body)
        outcome = DispatchOutcome(
            allowed=True, status=result.status, reason=result.detail,
            channel=result.channel, provider_id=result.provider_id,
            detail={**dict(result.extra), "companion_to": action.value},
        )
        self._record(companion_key, case_id, ActionType.SMS_LINK, outcome)

        if outcome.sent:
            self.repo.add_event(CaseEvent(
                case_id=case_id, kind=CaseEventKind.MESSAGE_SENT, actor="agent",
                summary=f"Payment link sent by SMS alongside {action.value}",
                detail={"channel": result.channel, "provider_id": result.provider_id,
                        "companion_to": action.value},
            ))
        else:
            logger.info("companion SMS for %s not sent: %s", case_id, result.detail)

    def dispatch(
        self,
        case_id: str,
        action: ActionType,
        idempotency_key: str,
        subject: str = "",
        body: str = "",
        html_body: str = "",
        spoken: str = "",
        payment_url: str = "",
    ) -> DispatchOutcome:
        """Send, or explain precisely why not. Never both, never neither."""
        gate = self.precheck(case_id, action)
        if not gate.allowed:
            if gate.status == "BLOCKED":
                self.repo.add_event(CaseEvent(
                    case_id=case_id, kind=CaseEventKind.ACTION_CANCELLED, actor="agent",
                    summary=f"{action.value} cancelled: {gate.reason}",
                    detail={"action": action.value},
                ))
                logger.info("dispatch blocked for %s: %s", case_id, gate.reason)
            return gate

        prior = self.already_dispatched(idempotency_key)
        if prior is not None:
            return DispatchOutcome(
                False, "DUPLICATE",
                f"already dispatched at {prior['dispatched_at']}",
                channel=str(prior.get("channel") or ""),
                provider_id=prior.get("provider_id"),
            )

        case = self.repo.get_case(case_id)
        customer = self.repo.get_customer(case.merchant_id, case.customer_id)
        email = customer.email if customer else ""
        phone = customer.phone if customer else ""
        name = customer.name if customer else ""

        if self.dry_run:
            outcome = DispatchOutcome(
                True, "SKIPPED",
                "DRY RUN: RECOVERY_DISPATCH_ENABLED is not set, nothing was sent",
                channel=self._channel_name(action),
                detail={"would_send_to": email or phone, "payment_url": payment_url},
            )
            self._record(idempotency_key, case_id, action, outcome)
            return outcome

        # RECOVERY_LINK_NOTIFY=razorpay hands delivery of the link's email and SMS to
        # Razorpay itself. Sending here as well would put two messages in front of the
        # customer for one rung the engine decided on, which is the exact double-contact
        # this setting exists to prevent. The record still lands in dispatch_log and the
        # timeline, attributed to the provider that actually delivered it, so the ladder
        # and the contact budget still count the rung.
        from app.realtime import config as realtime_config  # late, so tests can reload it

        if realtime_config.PROVIDER_NOTIFIES and action in PROVIDER_DELIVERED_ACTIONS:
            outcome = DispatchOutcome(
                True, "SENT",
                "delivered by Razorpay (RECOVERY_LINK_NOTIFY=razorpay), not re-sent here",
                channel="RAZORPAY_LINK",
                detail={"delivered_to": email or phone, "payment_url": payment_url},
            )
            self._record(idempotency_key, case_id, action, outcome)
            self.repo.add_event(CaseEvent(
                case_id=case_id, kind=CaseEventKind.MESSAGE_SENT, actor="provider",
                summary=f"{action.value} sent via RAZORPAY_LINK",
                detail={"channel": "RAZORPAY_LINK", "provider_id": None},
            ))
            if self.repo.get_case(case_id).status == CaseStatus.OPEN:
                self.repo.set_status(case_id, CaseStatus.IN_PROGRESS, reason="contacted")
            return outcome

        result = self._send(action, name, email, phone, subject, body, html_body, spoken)
        outcome = DispatchOutcome(
            allowed=True,
            status=result.status,
            reason=result.detail,
            channel=result.channel,
            provider_id=result.provider_id,
            detail=dict(result.extra),
        )
        self._record(idempotency_key, case_id, action, outcome)

        if outcome.sent:
            self.repo.add_event(CaseEvent(
                case_id=case_id, kind=CaseEventKind.MESSAGE_SENT, actor="agent",
                summary=f"{action.value} sent via {result.channel}",
                detail={"provider_id": result.provider_id, "channel": result.channel},
            ))
            if self.repo.get_case(case_id).status == CaseStatus.OPEN:
                self.repo.set_status(case_id, CaseStatus.IN_PROGRESS, reason="contacted")

            if action in VOICE_ACTIONS and realtime_config.VOICE_COMPANION_SMS:
                self._send_voice_companion_sms(
                    case_id=case_id, action=action, phone=phone,
                    idempotency_key=idempotency_key, payment_url=payment_url,
                )
        else:
            self.repo.add_event(CaseEvent(
                case_id=case_id, kind=CaseEventKind.MESSAGE_FAILED, actor="provider",
                summary=f"{action.value} not sent: {result.status}",
                detail={"channel": result.channel, "detail": result.detail},
            ))
        return outcome

    @staticmethod
    def _channel_name(action: ActionType) -> str:
        return {
            ActionType.EMAIL_LINK: "EMAIL_SMTP",
            ActionType.SMS_LINK: "TWILIO_SMS",
            ActionType.WHATSAPP_LINK: "TWILIO_WHATSAPP",
            ActionType.IVR_CALL: "TWILIO_VOICE",
            ActionType.AGENT_DIAL: "TWILIO_VOICE",
        }.get(action, "NONE")

    def _send(
        self,
        action: ActionType,
        name: str,
        email: str,
        phone: str,
        subject: str,
        body: str,
        html_body: str,
        spoken: str,
    ) -> channels.DispatchResult:
        """Route to the adapter. Adapters own all provider-specific detail."""
        if action == ActionType.EMAIL_LINK:
            return channels.send_email_smtp(email, subject, body, html_body=html_body)
        if action == ActionType.SMS_LINK:
            return channels.send_sms(phone, body)
        if action == ActionType.WHATSAPP_LINK:
            return channels.send_whatsapp(phone, body)
        if action in (ActionType.IVR_CALL, ActionType.AGENT_DIAL):
            return channels.send_ivr_call(phone, spoken or body)
        return channels.DispatchResult("NONE", "SKIPPED", "no adapter for this action")
