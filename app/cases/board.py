"""Case board — one row per customer, showing where the agent has got to (ADR-0027).

WHAT THIS IS FOR
    A merchant uploads fifty rows and needs one screen that answers, per person: what did
    the agent decide, did it reach them, have they paid, and if not, is anything still
    going to happen. Everything needed for that already exists - it is just spread across
    `cases`, `case_events`, `payment_links` and `followup_queue`. This assembles it.

HONESTY ABOUT "RESPONSE"
    There is no open, click, or read tracking anywhere in this system. The engine knows
    exactly two things about a customer: whether a contact was CONFIRMED DELIVERED, and
    whether MONEY ARRIVED. So this board reports delivery and payment, and says "no reply
    signal" rather than inventing an Opened column that would always be empty or, worse,
    a Response column that guesses.

    A row flagged red means "contacted, and no payment since" - NOT "the customer ignored
    us". We cannot distinguish ignored from never-saw-it, and the column name should not
    pretend otherwise.

FLAGS
    PAID     money verified by a provider webhook
    ACTIVE   contacted, still within the follow-up sequence
    WAITING  not yet contacted, or the engine chose not to
    STALLED  contacted, no payment, and NOTHING further is scheduled - this is the row a
             human has to look at, and the reason the board exists
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.cases.models import CaseEventKind, CaseStatus
from app.cases.repository import CaseRepository


def _age_days(iso: str) -> Optional[int]:
    if not iso:
        return None
    try:
        then = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return max(0, (datetime.now(timezone.utc) - then).days)


@dataclass
class BoardRow:
    """One customer's position in the recovery loop."""

    case_id: str
    customer_id: str
    name: str
    contact: str
    amount_paise: int
    stage: str                  # plain-English "what is happening now"
    last_action: str = ""       # EMAIL_LINK / SMS_LINK / NO_ACTION ...
    contacts_made: int = 0
    channels_tried: str = ""
    delivered: bool = False
    paid: bool = False
    payment_note: str = ""      # why we believe paid / not paid
    next_review: str = ""
    days_since_contact: Optional[int] = None
    flag: str = "WAITING"       # PAID | ACTIVE | WAITING | STALLED
    payment_url: str = ""
    due_date: str = ""          # from the merchant's own CSV, so the card can age it
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_row(self) -> Dict[str, Any]:
        """Flat shape for a table."""
        return {
            "Flag": self.flag,
            "Customer": self.name or self.customer_id,
            "Contact": self.contact,
            "Amount": self.amount_paise / 100,
            "Stage": self.stage,
            "Decision": self.last_action or "-",
            "Channels tried": self.channels_tried or "-",
            "Contacts": self.contacts_made,
            "Paid": "YES" if self.paid else "NO",
            "Why": self.payment_note,
            "Last contact": (
                f"{self.days_since_contact}d ago"
                if self.days_since_contact is not None else "never"
            ),
            "Next review": self.next_review[:16].replace("T", " ") if self.next_review else "-",
        }


def _next_review(conn: sqlite3.Connection, case_id: str) -> str:
    """When the agent will look at this case again, if ever."""
    try:
        row = conn.execute(
            """SELECT next_touch_at FROM followup_queue
               WHERE opportunity_id=? AND status='SCHEDULED' LIMIT 1;""",
            (case_id,),
        ).fetchone()
    except sqlite3.OperationalError:
        return ""
    return str(row[0]) if row else ""


def build_board(
    repo: CaseRepository,
    merchant_id: Optional[str] = None,
    limit: int = 200,
) -> List[BoardRow]:
    """Assemble one row per case, newest first."""
    conn = repo.conn
    rows: List[BoardRow] = []

    for case in repo.list_cases(merchant_id, limit=limit):
        customer = repo.get_customer(case.merchant_id, case.customer_id)
        events = repo.timeline(case.case_id)

        decided = [e for e in events if e.kind == CaseEventKind.AGENT_DECIDED]
        sent = [e for e in events if e.kind == CaseEventKind.MESSAGE_SENT]
        failed = [e for e in events if e.kind == CaseEventKind.MESSAGE_FAILED]
        cancelled = [e for e in events if e.kind == CaseEventKind.ACTION_CANCELLED]

        last_action = ""
        if decided:
            last_action = str(decided[-1].summary).replace("Agent selected ", "")

        channels = sorted({
            str(e.detail.get("channel", "")) for e in sent if e.detail.get("channel")
        })
        last_contact_at = sent[-1].at if sent else ""
        days = _age_days(last_contact_at)
        next_review = _next_review(conn, case.case_id)

        link = repo.find_reusable_link_any_amount(case.case_id)
        paid = case.status == CaseStatus.PAID

        # A settled case must never advertise a future contact. The live path cancels
        # follow-ups on payment, but a stale row from an interrupted run would otherwise
        # put "next review" beside "PAID" - which reads as though the engine intends to
        # chase someone who has already paid, and is the one thing this product must never
        # appear to do.
        if case.status.is_terminal_for_contact:
            next_review = ""

        # --- stage + flag, in the order a human would reason about them -----------------
        if paid:
            stage, flag = "Paid - case closed", "PAID"
            note = case.close_reason or "verified by provider webhook"
        elif case.status == CaseStatus.CLOSED:
            stage, flag = f"Closed - {case.close_reason or 'no reason given'}", "STALLED"
            note = "closed without payment"
        elif not decided:
            stage, flag = "Awaiting first evaluation", "WAITING"
            note = "not yet processed"
        elif not sent and last_action == "NO_ACTION":
            stage, flag = "Agent chose not to contact", "WAITING"
            note = "no action had positive expected value"
        elif not sent and failed:
            stage, flag = f"Send failed - {failed[-1].summary}", "STALLED"
            note = "message could not be sent"
        elif not sent:
            stage, flag = f"Decided {last_action}, not yet sent", "WAITING"
            note = "awaiting dispatch"
        elif next_review:
            stage = f"{last_action} sent, awaiting payment"
            flag = "ACTIVE"
            note = f"no payment since contact{f' {days}d ago' if days is not None else ''}"
        else:
            # Contacted, unpaid, and nothing scheduled. This is the row that needs a human,
            # which is the entire reason for a board rather than a log.
            stage = f"{last_action} sent, no payment, nothing scheduled"
            flag = "STALLED"
            note = "follow-ups exhausted or not scheduled - needs review"

        if cancelled and not paid:
            stage += f" (an action was cancelled: {cancelled[-1].summary.split(': ')[-1]})"

        rows.append(BoardRow(
            case_id=case.case_id,
            customer_id=case.customer_id,
            name=customer.name if customer else "",
            contact=(customer.email or customer.phone) if customer else "",
            amount_paise=case.amount_paise,
            stage=stage,
            last_action=last_action,
            contacts_made=len(sent),
            channels_tried=", ".join(c.replace("_SMTP", "").replace("TWILIO_", "")
                                     for c in channels),
            delivered=bool(sent),
            paid=paid,
            payment_note=note,
            next_review=next_review,
            days_since_contact=days,
            flag=flag,
            payment_url=link.short_url if link else "",
            due_date=case.due_date or "",
        ))

    return rows


def summarise(rows: List[BoardRow]) -> Dict[str, Any]:
    """Headline counts for the board header."""
    total = sum(r.amount_paise for r in rows)
    recovered = sum(r.amount_paise for r in rows if r.paid)
    by_flag: Dict[str, int] = {}
    for r in rows:
        by_flag[r.flag] = by_flag.get(r.flag, 0) + 1
    return {
        "cases": len(rows),
        "total_paise": total,
        "recovered_paise": recovered,
        "outstanding_paise": total - recovered,
        "recovery_rate": (recovered / total) if total else 0.0,
        "contacts_made": sum(r.contacts_made for r in rows),
        "by_flag": by_flag,
        "needs_attention": by_flag.get("STALLED", 0),
    }
