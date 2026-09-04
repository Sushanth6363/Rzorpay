"""Judge test harness: upload a CSV, the engine decides, the message really goes out.

WHAT THIS IS FOR
    Everything else in this project is measured in a sandbox. This is the one path where a
    reviewer can put their own email and phone number into a file, upload it, and have the
    actual decision engine choose an action and a real message arrive on their actual
    device. It closes the gap between "the engine decided SMS_LINK" and seeing the SMS.

WHAT IS RELAXED HERE, PRECISELY
    Two campaign-PACING controls are lifted, and nothing else:
      - the 24h quiet period between escalation rungs (set to zero), and
      - the per-customer contact cap (raised for the demo customer).
    Both exist to protect a MERCHANT'S CUSTOMER BASE during a live campaign - they stop a
    real person being messaged four times in an hour. A reviewer testing on their own
    contact details is not that situation, and waiting 24 hours between rungs would
    demonstrate nothing.

    Everything else runs exactly as in production. Stage 0, diagnosis, candidate
    generation, EV ranking and the hard safety filter are untouched. So is the ONE-RUNG
    escalation ladder: upload three rows with the same email and you will see the engine
    climb EMAIL -> SMS -> WHATSAPP, one rung per confirmed contact, because that ladder is
    a decision rule rather than a pacing rule.

THE ONE GUARD THAT STAYS
    A recipient cap, and an explicit confirmation of the row count before anything sends.
    This is not regulatory box-ticking - it is the difference between a person testing on
    themselves and a list of uninvolved strangers receiving unsolicited messages. It costs
    a reviewer nothing, because a demo is a handful of rows.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.domain.enums import ActionType, DecisionMode
from app.dispatch import channels
from app.orchestration.recovery_orchestrator import RecoveryOrchestrator

# A demo is a handful of rows; a spam run is hundreds. This blocks the second without ever
# touching the first.
MAX_ROWS = 25

REQUIRED_ANY = ("email", "phone")
TEMPLATE_COLUMNS = [
    "customer_name", "email", "phone", "amount_rupees",
    "event_type", "failure_reason", "invoice_status", "amount_received_rupees", "tds_section",
]

SAMPLE_CSV = """customer_name,email,phone,amount_rupees,event_type,failure_reason
Your Name,you@example.com,+919876543210,4500,FAILED_PAYMENT,INSUFFICIENT_FUNDS
Your Name,you@example.com,+919876543210,899,ABANDONED_CHECKOUT,
Your Name,you@example.com,+919876543210,120000,OVERDUE_B2B_INVOICE,
"""


@dataclass
class RowResult:
    """One CSV row: what the engine decided, and what actually happened when it sent."""

    row_number: int
    customer_name: str
    email: str
    phone: str
    amount_paise: int
    event_type: str
    decided_action: str = ""
    decision_mode: str = ""
    reasoning: str = ""
    expected_value_rupees: float = 0.0
    uplift: float = 0.0
    dispatches: List[Dict[str, Any]] = field(default_factory=list)
    error: str = ""

    @property
    def any_sent(self) -> bool:
        return any(d.get("status") == "SENT" for d in self.dispatches)


def parse_csv(raw: bytes | str) -> tuple:
    """Parse an uploaded CSV into rows. Returns (rows, errors)."""
    text = raw.decode("utf-8-sig") if isinstance(raw, bytes) else raw
    reader = csv.DictReader(io.StringIO(text))
    rows: List[Dict[str, str]] = []
    errors: List[str] = []

    for i, raw_row in enumerate(reader, start=2):  # header is line 1
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw_row.items()}
        if not any(row.values()):
            continue
        if not any(row.get(f) for f in REQUIRED_ANY):
            errors.append(f"line {i}: needs an email or a phone number")
            continue
        try:
            rupees = float(row.get("amount_rupees") or 0)
        except ValueError:
            errors.append(f"line {i}: amount_rupees is not a number")
            continue
        if rupees <= 0:
            errors.append(f"line {i}: amount_rupees must be greater than zero")
            continue
        row["_amount_paise"] = str(int(round(rupees * 100)))
        row["_line"] = str(i)
        rows.append(row)

    if len(rows) > MAX_ROWS:
        errors.append(
            f"{len(rows)} rows, limit is {MAX_ROWS}. This harness sends real messages; "
            f"the cap keeps it a test rather than a broadcast."
        )
        rows = rows[:MAX_ROWS]

    return rows, errors


def _build_event(row: Dict[str, str]) -> Dict[str, Any]:
    """Turn a CSV row into an engine event."""
    now = datetime.now(timezone.utc).isoformat()
    key = row.get("email") or row.get("phone") or "csv_customer"
    event: Dict[str, Any] = {
        "merchant_id": "merch_judge_demo",
        "customer_id": f"csv_{abs(hash(key)) % 10**10}",
        "event_id": f"csv_row_{row.get('_line', '0')}_{int(datetime.now().timestamp())}",
        "event_type": (row.get("event_type") or "FAILED_PAYMENT").upper(),
        "amount_paise": int(row["_amount_paise"]),
        "currency": "INR",
        "occurred_at": now,
        "observed_at": now,
        "gateway": "razorpay",
    }
    if row.get("failure_reason"):
        event["failure_reason"] = row["failure_reason"].upper()
    if row.get("invoice_status"):
        event["invoice_status"] = row["invoice_status"].upper()
    if row.get("tds_section"):
        event["tds_section"] = row["tds_section"]
        event["payee_type"] = row.get("payee_type", "COMPANY")
    if row.get("amount_received_rupees"):
        try:
            event["amount_received_paise"] = int(round(float(row["amount_received_rupees"]) * 100))
        except ValueError:
            pass
    return event


def _message_for(
    action: ActionType,
    name: str,
    amount_paise: int,
    link: str = "",
    diagnosis_code: Optional[str] = None,
) -> tuple:
    """Copy whose TONE follows the escalation rung and whose ASK follows the diagnosis.

    Previously every channel sent identical text, so a customer's fourth contact read
    exactly like their first, only louder in medium. See app/dispatch/copy.py.
    """
    from app.dispatch.copy import build_message

    message = build_message(
        action=action,
        amount_paise=amount_paise,
        customer_name=name,
        diagnosis_code=diagnosis_code,
        payment_link=link,
    )
    return message.subject, message.body, message.spoken


def run_csv(
    rows: List[Dict[str, str]],
    orchestrator: Optional[RecoveryOrchestrator] = None,
    dry_run: bool = False,
) -> List[RowResult]:
    """Run each row through the real engine and dispatch the chosen action for real.

    `dry_run=True` runs the full decision path and reports what WOULD be sent, sending
    nothing. That is the default the UI offers first.
    """
    # Campaign PACING off (see module docstring); decision logic entirely unchanged.
    from app.db.dal import TenantScopedDB
    from app.pipeline.escalation import EscalationPolicy

    orch = orchestrator or RecoveryOrchestrator()
    orch.pipeline.escalation_policy = EscalationPolicy(cooldown_hours=0)

    # Raise the contact cap for this harness only. A reviewer will reasonably put their own
    # single email on every row; with the production cap of 3 the fourth row onwards would
    # be budget-suppressed and the demo would look broken rather than careful.
    if rows:
        dal = TenantScopedDB(conn=orch.conn, merchant_id="merch_judge_demo", clock=orch.clock)
        for row in rows:
            key = row.get("email") or row.get("phone") or "csv_customer"
            try:
                dal.init_contact_budget(f"csv_{abs(hash(key)) % 10**10}", cap=MAX_ROWS + 5)
            except Exception:
                pass

    results: List[RowResult] = []

    for row in rows:
        event = _build_event(row)
        result = RowResult(
            row_number=int(row.get("_line", 0)),
            customer_name=row.get("customer_name", ""),
            email=row.get("email", ""),
            phone=row.get("phone", ""),
            amount_paise=event["amount_paise"],
            event_type=event["event_type"],
        )
        try:
            outcome = orch.process_and_execute(raw_event=event, arm="A5", random_seed=None)
        except Exception as exc:
            result.error = str(exc)[:300]
            results.append(result)
            continue

        decision = outcome.decision
        action = decision.selected_action
        result.decided_action = action.value
        result.decision_mode = decision.decision_mode.value
        score = decision.selected_action_score
        if score is not None:
            result.expected_value_rupees = score.expected_value_paise / 100
            result.uplift = score.incremental_effect
        result.reasoning = _explain(outcome, action)

        if action == ActionType.NO_ACTION or decision.decision_mode == DecisionMode.SAFE_ABSTENTION:
            result.dispatches.append({
                "channel": "NONE", "status": "SKIPPED",
                "detail": "engine chose not to contact this customer",
            })
            results.append(result)
            continue

        if dry_run:
            result.dispatches.append({
                "channel": _channel_for(action), "status": "DRY_RUN",
                "detail": "would send; dry run is on",
            })
            results.append(result)
            continue

        result.dispatches = [
            d.to_dict()
            for d in _dispatch(
                action, result, outcome.decision.decision_id,
                diagnosis_code=getattr(outcome, 'diagnosis_code', None)
                or _diagnosis_of(outcome),
            )
        ]
        results.append(result)

    return results


def _channel_for(action: ActionType) -> str:
    return {
        ActionType.EMAIL_LINK: "EMAIL_SMTP + RAZORPAY_LINK",
        ActionType.SMS_LINK: "TWILIO_SMS + RAZORPAY_LINK",
        ActionType.WHATSAPP_LINK: "TWILIO_WHATSAPP",
        ActionType.IVR_CALL: "TWILIO_VOICE",
        ActionType.AGENT_DIAL: "TWILIO_VOICE",
        ActionType.RECOMMEND_RETRY: "NONE (infrastructure recommendation)",
    }.get(action, "NONE")


def _diagnosis_of(outcome: Any) -> Optional[str]:
    """Read the diagnosis off the executed decision so copy matches the real reason."""
    score = getattr(outcome.decision, 'selected_action_score', None)
    features = getattr(outcome.decision, 'decision_features', None) or {}
    if isinstance(features, dict) and features.get('diagnosis_code'):
        return str(features['diagnosis_code'])
    return None


def _dispatch(
    action: ActionType,
    row: RowResult,
    reference_id: str,
    diagnosis_code: Optional[str] = None,
) -> List[channels.DispatchResult]:
    """Send for real. Every attempt is reported, including the ones that could not run."""
    out: List[channels.DispatchResult] = []

    if action == ActionType.RECOMMEND_RETRY:
        # ADR-0006: a recommendation to the payment infrastructure, not a message to a
        # person. Nothing is sent, and that is correct rather than a gap.
        return [channels.DispatchResult(
            "NONE", "SKIPPED",
            "RECOMMEND_RETRY targets the payment infrastructure, not the customer",
        )]

    link = ""
    if action in (ActionType.EMAIL_LINK, ActionType.SMS_LINK, ActionType.WHATSAPP_LINK):
        rz = channels.send_razorpay_link(
            amount_paise=row.amount_paise,
            name=row.customer_name or "Customer",
            email=row.email,
            contact=row.phone,
            description=f"Recovery for {row.event_type}",
            reference_id=reference_id,
        )
        out.append(rz)
        link = rz.extra.get("short_url", "")

    subject, body, spoken = _message_for(
        action, row.customer_name, row.amount_paise, link, diagnosis_code
    )

    if action == ActionType.EMAIL_LINK:
        out.append(channels.send_email_smtp(row.email, subject, body))
    elif action == ActionType.SMS_LINK:
        out.append(channels.send_sms(row.phone, body))
    elif action == ActionType.WHATSAPP_LINK:
        out.append(channels.send_whatsapp(row.phone, body))
    elif action in (ActionType.IVR_CALL, ActionType.AGENT_DIAL):
        out.append(channels.send_ivr_call(row.phone, spoken))

    return out


def _explain(outcome: Any, action: ActionType) -> str:
    """Plain-language reason, read from the executed decision rather than composed."""
    stage0 = outcome.decision
    if action == ActionType.NO_ACTION:
        reason = getattr(stage0, "abstention_reason", None)
        if reason is not None and getattr(reason, "value", "") not in ("", "NONE"):
            return f"Abstained: {reason.value.replace('_', ' ').lower()}."
        return "Abstained: no action had positive expected value over doing nothing."
    score = stage0.selected_action_score
    if score is None:
        return f"Chose {action.value}."
    return (
        f"Chose {action.value}: estimated uplift {score.incremental_effect:+.1%} over no "
        f"action, worth Rs {score.incremental_value_paise / 100:,.0f}, minus Rs "
        f"{score.action_cost_paise / 100:,.2f} cost = EV Rs {score.expected_value_paise / 100:,.0f}."
    )
