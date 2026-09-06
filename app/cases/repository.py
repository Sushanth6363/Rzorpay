"""Case persistence and the payment-to-case resolution the closed loop depends on.

DESIGN NOTES
    Schema is applied additively at first use, matching the pattern `app/realtime/ingest.py`
    already uses, so `app/db/init.py` and the existing five tables are untouched. One
    connection, one file: the webhook server, the scheduler and the dashboard all read the
    same state, which is the whole reason any of this is observable.

    Connections are THREAD-LOCAL. SQLite connections are thread-bound and Starlette runs
    background work on a worker thread; a shared connection raises on the first background
    write, which fails silently behind an already-sent 202.

RESOLUTION IS THE POINT
    `find_case_for_provider_entity` tries every id a payment could arrive under, because
    Razorpay uses a different one depending on how the customer paid:

        payment_link.paid      -> plink_...   matches payment_links.payment_link_id
        payment.captured       -> pay_...     may be a NEW payment against a link,
                                              or the ORIGINAL attempt that opened the case
        order.paid             -> order_...
        any of the above       -> reference_id we set when creating the link

    Trying only one of these is what made a paid customer invisible to the agent.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from typing import Any, Dict, List, Optional

from app.cases.models import (
    Case,
    CaseEvent,
    CaseEventKind,
    CaseStatus,
    Customer,
    PaymentLink,
    PaymentLinkStatus,
    now_iso,
)

CASES_DDL = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT NOT NULL,
    merchant_id TEXT NOT NULL,
    name        TEXT DEFAULT '',
    email       TEXT DEFAULT '',
    phone       TEXT DEFAULT '',
    created_at  TEXT NOT NULL,
    PRIMARY KEY (merchant_id, customer_id)
);

CREATE TABLE IF NOT EXISTS cases (
    case_id         TEXT PRIMARY KEY,
    merchant_id     TEXT NOT NULL,
    customer_id     TEXT NOT NULL,
    amount_paise    INTEGER NOT NULL CHECK (amount_paise >= 0),
    currency        TEXT NOT NULL DEFAULT 'INR',
    due_date        TEXT DEFAULT '',
    description     TEXT DEFAULT '',
    source_event_id TEXT DEFAULT '',
    opportunity_id  TEXT DEFAULT '',
    event_type      TEXT DEFAULT 'OVERDUE_B2B_INVOICE',
    status          TEXT NOT NULL,
    promised_date   TEXT DEFAULT '',
    close_reason    TEXT DEFAULT '',
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    closed_at       TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(merchant_id, status);
CREATE INDEX IF NOT EXISTS idx_cases_source ON cases(source_event_id);
CREATE INDEX IF NOT EXISTS idx_cases_opp    ON cases(opportunity_id);

CREATE TABLE IF NOT EXISTS payment_links (
    payment_link_id TEXT PRIMARY KEY,
    case_id         TEXT NOT NULL,
    merchant_id     TEXT NOT NULL,
    customer_id     TEXT NOT NULL,
    amount_paise    INTEGER NOT NULL,
    short_url       TEXT DEFAULT '',
    reference_id    TEXT DEFAULT '',
    opportunity_id  TEXT DEFAULT '',
    status          TEXT NOT NULL,
    is_test_mode    INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    paid_at         TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_plink_case ON payment_links(case_id, status);
CREATE INDEX IF NOT EXISTS idx_plink_ref  ON payment_links(reference_id);

CREATE TABLE IF NOT EXISTS case_events (
    event_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id    TEXT NOT NULL,
    at         TEXT NOT NULL,
    kind       TEXT NOT NULL,
    actor      TEXT NOT NULL,
    summary    TEXT NOT NULL,
    detail_json TEXT DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_case_events ON case_events(case_id, event_id);
"""

_LOCK = threading.Lock()


class CaseRepository:
    """Durable customers, cases, payment links and timeline events."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with _LOCK:
            self.conn.executescript(CASES_DDL)
            # Additive migration for databases created before event_type existed.
            try:
                self.conn.execute(
                    "ALTER TABLE cases ADD COLUMN event_type TEXT "
                    "DEFAULT 'OVERDUE_B2B_INVOICE';"
                )
            except sqlite3.OperationalError:
                pass  # already present
            # Additive migration for databases created before description existed.
            try:
                self.conn.execute("ALTER TABLE cases ADD COLUMN description TEXT DEFAULT '';")
            except sqlite3.OperationalError:
                pass  # already present
            self.conn.commit()

    # --- customers -----------------------------------------------------------------

    def upsert_customer(self, customer: Customer) -> Customer:
        self.conn.execute(
            """INSERT INTO customers (customer_id, merchant_id, name, email, phone, created_at)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(merchant_id, customer_id) DO UPDATE SET
                   name  = COALESCE(NULLIF(excluded.name, ''),  customers.name),
                   email = COALESCE(NULLIF(excluded.email, ''), customers.email),
                   phone = COALESCE(NULLIF(excluded.phone, ''), customers.phone);""",
            (customer.customer_id, customer.merchant_id, customer.name,
             customer.email, customer.phone, customer.created_at),
        )
        self.conn.commit()
        return customer

    def get_customer(self, merchant_id: str, customer_id: str) -> Optional[Customer]:
        self.conn.row_factory = sqlite3.Row
        row = self.conn.execute(
            "SELECT * FROM customers WHERE merchant_id=? AND customer_id=?;",
            (merchant_id, customer_id),
        ).fetchone()
        if not row:
            return None
        return Customer(
            customer_id=row["customer_id"], merchant_id=row["merchant_id"],
            name=row["name"] or "", email=row["email"] or "", phone=row["phone"] or "",
            created_at=row["created_at"],
        )

    # --- cases ---------------------------------------------------------------------

    def create_case(self, case: Case) -> Case:
        self.conn.execute(
            """INSERT OR REPLACE INTO cases (
                   case_id, merchant_id, customer_id, amount_paise, currency, due_date,
                   source_event_id, opportunity_id, event_type, status, promised_date,
                   description,
                   close_reason, created_at, updated_at, closed_at
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);""",
            (case.case_id, case.merchant_id, case.customer_id, case.amount_paise,
             case.currency, case.due_date, case.source_event_id, case.opportunity_id,
             case.event_type, case.status.value, case.promised_date, case.description,
             case.close_reason,
             case.created_at, case.updated_at, case.closed_at),
        )
        self.conn.commit()
        self.add_event(CaseEvent(
            case_id=case.case_id, kind=CaseEventKind.CASE_CREATED, actor="merchant",
            summary=f"Case opened for Rs {case.amount_paise / 100:,.2f}",
            detail={"amount_paise": case.amount_paise, "due_date": case.due_date},
        ))
        return case

    def _row_to_case(self, row: sqlite3.Row) -> Case:
        return Case(
            case_id=row["case_id"], merchant_id=row["merchant_id"],
            customer_id=row["customer_id"], amount_paise=int(row["amount_paise"]),
            currency=row["currency"], due_date=row["due_date"] or "",
            source_event_id=row["source_event_id"] or "",
            opportunity_id=row["opportunity_id"] or "",
            event_type=(row["event_type"] if "event_type" in row.keys() else None)
                       or "OVERDUE_B2B_INVOICE",
            status=CaseStatus(row["status"]), promised_date=row["promised_date"] or "",
            description=(row["description"] if "description" in row.keys() else "") or "",
            close_reason=row["close_reason"] or "", created_at=row["created_at"],
            updated_at=row["updated_at"], closed_at=row["closed_at"] or "",
        )

    def get_case(self, case_id: str) -> Optional[Case]:
        self.conn.row_factory = sqlite3.Row
        row = self.conn.execute("SELECT * FROM cases WHERE case_id=?;", (case_id,)).fetchone()
        return self._row_to_case(row) if row else None

    def list_cases(self, merchant_id: Optional[str] = None, limit: int = 200) -> List[Case]:
        self.conn.row_factory = sqlite3.Row
        if merchant_id:
            rows = self.conn.execute(
                "SELECT * FROM cases WHERE merchant_id=? ORDER BY created_at DESC LIMIT ?;",
                (merchant_id, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM cases ORDER BY created_at DESC LIMIT ?;", (limit,)
            ).fetchall()
        return [self._row_to_case(r) for r in rows]

    def set_status(
        self,
        case_id: str,
        status: CaseStatus,
        reason: str = "",
        promised_date: str = "",
    ) -> bool:
        """Advance a case. PAID is terminal for contact and is never walked back here."""
        case = self.get_case(case_id)
        if case is None:
            return False
        # Guard the invariant at the only place it can be violated: a later, weaker event
        # must never un-pay a case. Payment is verified and final.
        if case.status == CaseStatus.PAID and status != CaseStatus.PAID:
            return False

        closed_at = now_iso() if status.is_terminal_for_contact else ""
        self.conn.execute(
            """UPDATE cases SET status=?, close_reason=?, promised_date=COALESCE(NULLIF(?,''), promised_date),
                   updated_at=?, closed_at=? WHERE case_id=?;""",
            (status.value, reason, promised_date, now_iso(), closed_at, case_id),
        )
        self.conn.commit()
        return True

    def attach_opportunity(self, case_id: str, opportunity_id: str) -> None:
        self.conn.execute(
            "UPDATE cases SET opportunity_id=?, updated_at=? WHERE case_id=?;",
            (opportunity_id, now_iso(), case_id),
        )
        self.conn.commit()

    # --- payment links -------------------------------------------------------------

    def save_payment_link(self, link: PaymentLink) -> PaymentLink:
        self.conn.execute(
            """INSERT INTO payment_links (
                   payment_link_id, case_id, merchant_id, customer_id, amount_paise,
                   short_url, reference_id, opportunity_id, status, is_test_mode,
                   created_at, updated_at, paid_at
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(payment_link_id) DO UPDATE SET
                   status=excluded.status, short_url=excluded.short_url,
                   updated_at=excluded.updated_at, paid_at=excluded.paid_at;""",
            (link.payment_link_id, link.case_id, link.merchant_id, link.customer_id,
             link.amount_paise, link.short_url, link.reference_id, link.opportunity_id,
             link.status.value, 1 if link.is_test_mode else 0,
             link.created_at, link.updated_at, link.paid_at),
        )
        self.conn.commit()
        return link

    def _row_to_link(self, row: sqlite3.Row) -> PaymentLink:
        return PaymentLink(
            payment_link_id=row["payment_link_id"], case_id=row["case_id"],
            merchant_id=row["merchant_id"], customer_id=row["customer_id"],
            amount_paise=int(row["amount_paise"]), short_url=row["short_url"] or "",
            reference_id=row["reference_id"] or "",
            opportunity_id=row["opportunity_id"] or "",
            status=PaymentLinkStatus(row["status"]),
            is_test_mode=bool(row["is_test_mode"]),
            created_at=row["created_at"], updated_at=row["updated_at"],
            paid_at=row["paid_at"] or "",
        )

    def get_payment_link(self, payment_link_id: str) -> Optional[PaymentLink]:
        self.conn.row_factory = sqlite3.Row
        row = self.conn.execute(
            "SELECT * FROM payment_links WHERE payment_link_id=?;", (payment_link_id,)
        ).fetchone()
        return self._row_to_link(row) if row else None

    def find_reusable_link(self, case_id: str, amount_paise: int) -> Optional[PaymentLink]:
        """An existing live link for the same case and amount. Prevents duplicates."""
        self.conn.row_factory = sqlite3.Row
        row = self.conn.execute(
            """SELECT * FROM payment_links
               WHERE case_id=? AND amount_paise=? AND status=?
               ORDER BY created_at DESC LIMIT 1;""",
            (case_id, amount_paise, PaymentLinkStatus.CREATED.value),
        ).fetchone()
        return self._row_to_link(row) if row else None

    def find_reusable_link_any_amount(self, case_id: str) -> Optional[PaymentLink]:
        """Any live link on this case, regardless of amount. Used when closing a case."""
        self.conn.row_factory = sqlite3.Row
        row = self.conn.execute(
            "SELECT * FROM payment_links WHERE case_id=? AND status=? LIMIT 1;",
            (case_id, PaymentLinkStatus.CREATED.value),
        ).fetchone()
        return self._row_to_link(row) if row else None

    def mark_link_cancelled(self, payment_link_id: str, reason: str = "") -> None:
        self.conn.execute(
            "UPDATE payment_links SET status=?, updated_at=? WHERE payment_link_id=?;",
            (PaymentLinkStatus.CANCELLED.value, now_iso(), payment_link_id),
        )
        self.conn.commit()

    def mark_link_paid(self, payment_link_id: str) -> Optional[str]:
        """Mark a link paid. Returns its case_id, or None if unknown."""
        link = self.get_payment_link(payment_link_id)
        if link is None:
            return None
        self.conn.execute(
            "UPDATE payment_links SET status=?, paid_at=?, updated_at=? WHERE payment_link_id=?;",
            (PaymentLinkStatus.PAID.value, now_iso(), now_iso(), payment_link_id),
        )
        self.conn.commit()
        return link.case_id

    # --- THE RESOLUTION THAT FIXES THE BLOCKER --------------------------------------

    def find_case_for_provider_entity(
        self,
        entity_id: str,
        reference_id: str = "",
    ) -> Optional[str]:
        """Map any provider entity id back to a case_id, or None.

        Razorpay uses a different id depending on how the money arrived. Checking only one
        of them is what let a paid customer keep receiving reminders.
        """
        if not entity_id and not reference_id:
            return None
        self.conn.row_factory = sqlite3.Row

        # 1. payment_link.paid -> plink_...
        if entity_id:
            row = self.conn.execute(
                "SELECT case_id FROM payment_links WHERE payment_link_id=?;", (entity_id,)
            ).fetchone()
            if row:
                return row["case_id"]

        # 2. our own reference, echoed back by the provider
        for candidate in (reference_id, entity_id):
            if not candidate:
                continue
            row = self.conn.execute(
                "SELECT case_id FROM payment_links WHERE reference_id=?;", (candidate,)
            ).fetchone()
            if row:
                return row["case_id"]

        # 3. payment.captured on the ORIGINAL failed attempt that opened the case
        if entity_id:
            row = self.conn.execute(
                "SELECT case_id FROM cases WHERE source_event_id=?;", (entity_id,)
            ).fetchone()
            if row:
                return row["case_id"]

            # 4. the engine's own opportunity id
            row = self.conn.execute(
                "SELECT case_id FROM cases WHERE opportunity_id=?;", (entity_id,)
            ).fetchone()
            if row:
                return row["case_id"]

        return None

    # --- timeline ------------------------------------------------------------------

    def add_event(self, event: CaseEvent) -> None:
        self.conn.execute(
            """INSERT INTO case_events (case_id, at, kind, actor, summary, detail_json)
               VALUES (?,?,?,?,?,?);""",
            (event.case_id, event.at, event.kind.value, event.actor, event.summary,
             json.dumps(event.detail, default=str)),
        )
        self.conn.commit()

    def timeline(self, case_id: str, limit: int = 200) -> List[CaseEvent]:
        self.conn.row_factory = sqlite3.Row
        rows = self.conn.execute(
            "SELECT * FROM case_events WHERE case_id=? ORDER BY event_id LIMIT ?;",
            (case_id, limit),
        ).fetchall()
        out: List[CaseEvent] = []
        for r in rows:
            try:
                detail: Dict[str, Any] = json.loads(r["detail_json"] or "{}")
            except Exception:
                detail = {}
            out.append(CaseEvent(
                case_id=r["case_id"], kind=CaseEventKind(r["kind"]), summary=r["summary"],
                at=r["at"], actor=r["actor"], detail=detail, event_id=int(r["event_id"]),
            ))
        return out
