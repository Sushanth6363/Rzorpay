"""Merchant CSV -> validated Customers and Cases (ADR-0025).

WHY VALIDATION IS THE POINT
    A merchant's receivables export is messy: blank phones, dates in three formats, the
    same customer twice, an amount typed as "25,000.00". The temptation is to skip what
    does not parse and process the rest. That is the wrong default here, because a silently
    dropped row is revenue the merchant believes is being chased and which nothing is
    chasing. Every rejected row is returned WITH ITS REASON and shown, never discarded.

    The opposite error matters too. A malformed email address that is accepted becomes a
    contact attempt that hard-bounces, which damages the sending domain's reputation for
    every subsequent customer. Rejecting it up front is cheaper than a bounce.

THE CSV IS THE SINGLE SOURCE
    A Case and Customer are created from the row and everything downstream - the amount in
    the email subject, the name in the greeting, the payment link's value - is read back
    from those records. The email cannot drift from the file, because nothing downstream
    re-enters the numbers by hand.

INVARIANTS:
1. INTEGER PAISE. `amount` arrives as rupees and is converted once, here.
2. NOTHING IS SILENTLY DROPPED. Rejected rows are returned with a line number and reason.
3. NO ROW WITHOUT A ROUTE TO THE CUSTOMER. An email or a phone is required; a case that
   can never be contacted is not a recovery opportunity, it is a data-quality ticket.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.cases.models import Case, CaseStatus, Customer, now_iso

# Canonical column names, with the aliases a real export tends to use.
COLUMN_ALIASES: Dict[str, Tuple[str, ...]] = {
    "customer_id": ("customer_id", "customerid", "id", "customer"),
    "name": ("name", "customer_name", "customername", "full_name"),
    "email": ("email", "email_address", "e-mail", "mail"),
    "phone": ("phone", "mobile", "contact", "phone_number", "msisdn"),
    "amount": ("amount", "amount_rupees", "amount_due", "outstanding", "value"),
    "due_date": ("due_date", "duedate", "due", "date"),
    # Optional extras the engine understands; absent is fine.
    "event_type": ("event_type", "stream", "type"),
    "failure_reason": ("failure_reason", "reason", "error_code"),
}

REQUIRED = ("amount",)          # plus at least one of email / phone, checked per row

# Deliberately permissive but not meaningless: it rejects the mistakes that actually occur
# in exports (missing @, no domain dot, stray spaces) without trying to be RFC 5322.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d %b %Y", "%d %B %Y")

MAX_ROWS = 500


@dataclass
class RejectedRow:
    line: int
    reason: str
    raw: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"Line": self.line, "Reason": self.reason, **self.raw}


@dataclass
class ValidRow:
    line: int
    customer_id: str
    name: str
    email: str
    phone: str
    amount_paise: int
    due_date: str
    event_type: str = "OVERDUE_B2B_INVOICE"
    failure_reason: str = ""

    @property
    def days_overdue(self) -> int:
        if not self.due_date:
            return 0
        try:
            due = datetime.strptime(self.due_date, "%Y-%m-%d").date()
        except ValueError:
            return 0
        return max(0, (datetime.now(timezone.utc).date() - due).days)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Line": self.line, "Customer": self.customer_id, "Name": self.name,
            "Email": self.email, "Phone": self.phone,
            "Amount": self.amount_paise / 100, "Due": self.due_date or "-",
            "Days overdue": self.days_overdue, "Stream": self.event_type,
        }


@dataclass
class IngestReport:
    valid: List[ValidRow] = field(default_factory=list)
    rejected: List[RejectedRow] = field(default_factory=list)
    missing_columns: List[str] = field(default_factory=list)

    @property
    def total_seen(self) -> int:
        return len(self.valid) + len(self.rejected)

    @property
    def total_paise(self) -> int:
        return sum(r.amount_paise for r in self.valid)

    @property
    def ok(self) -> bool:
        return bool(self.valid) and not self.missing_columns


# --- field parsers -----------------------------------------------------------------------


def _normalise_header(fieldnames: Optional[List[str]]) -> Dict[str, str]:
    """Map whatever the merchant called a column onto our canonical name."""
    mapping: Dict[str, str] = {}
    for raw in fieldnames or []:
        key = (raw or "").strip().lower().replace(" ", "_")
        for canonical, aliases in COLUMN_ALIASES.items():
            if key in aliases:
                mapping[raw] = canonical
                break
    return mapping


def parse_amount(raw: str) -> Optional[int]:
    """Rupees -> integer paise. Accepts '25,000.00', 'Rs 25000', '₹25000'."""
    if raw is None:
        return None
    cleaned = str(raw).strip().replace(",", "").replace("₹", "").replace("Rs", "")
    cleaned = cleaned.replace("rs", "").replace("INR", "").replace("inr", "").strip()
    if not cleaned:
        return None
    try:
        rupees = float(cleaned)
    except ValueError:
        return None
    if rupees <= 0:
        return None
    # round() not int(): int() truncates, so 0.1+0.2 style float error would silently
    # shave a paisa off every amount.
    return int(round(rupees * 100))


def parse_due_date(raw: str) -> Tuple[Optional[str], bool]:
    """Return (iso_date, was_supplied). A blank date is allowed; a malformed one is not."""
    value = (raw or "").strip()
    if not value:
        return None, False
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date().isoformat(), True
        except ValueError:
            continue
    return None, True  # supplied but unparseable


def normalise_phone(raw: str) -> Optional[str]:
    """Normalise to E.164 for India, or None if it cannot be one.

    A wrong number is worse than a blank one: it is a message to a stranger, and it burns
    a contact slot that belonged to the real customer.
    """
    value = re.sub(r"[\s\-()]", "", (raw or "").strip())
    if not value:
        return None
    if value.startswith("+"):
        digits = value[1:]
        return f"+{digits}" if digits.isdigit() and 10 <= len(digits) <= 15 else None
    if not value.isdigit():
        return None
    if len(value) == 10:
        return f"+91{value}"
    if len(value) == 12 and value.startswith("91"):
        return f"+{value}"
    if len(value) == 11 and value.startswith("0"):
        return f"+91{value[1:]}"
    return None


def valid_email(raw: str) -> bool:
    return bool(EMAIL_RE.match((raw or "").strip()))


# --- ingestion ---------------------------------------------------------------------------


def parse_csv(raw: bytes | str) -> IngestReport:
    """Validate a merchant CSV. Every rejection carries a line number and a reason."""
    text = raw.decode("utf-8-sig", errors="replace") if isinstance(raw, bytes) else raw
    reader = csv.DictReader(io.StringIO(text))
    header_map = _normalise_header(reader.fieldnames)
    canonical_present = set(header_map.values())

    report = IngestReport()
    report.missing_columns = [c for c in REQUIRED if c not in canonical_present]
    if "email" not in canonical_present and "phone" not in canonical_present:
        report.missing_columns.append("email or phone")
    if report.missing_columns:
        return report

    seen_keys: Dict[str, int] = {}

    for i, raw_row in enumerate(reader, start=2):  # header is line 1
        row = {
            header_map[k]: (v or "").strip()
            for k, v in raw_row.items()
            if k in header_map
        }
        original = {k: (v or "").strip() for k, v in raw_row.items() if k}

        if not any(row.values()):
            continue
        if len(report.valid) + len(report.rejected) >= MAX_ROWS:
            report.rejected.append(RejectedRow(i, f"beyond the {MAX_ROWS}-row limit", original))
            continue

        email = row.get("email", "")
        phone_raw = row.get("phone", "")

        if not email and not phone_raw:
            report.rejected.append(RejectedRow(
                i, "no email and no phone - there is no way to contact this customer", original))
            continue
        if email and not valid_email(email):
            report.rejected.append(RejectedRow(
                i, f"malformed email '{email}' - sending to it would hard-bounce", original))
            continue

        phone = normalise_phone(phone_raw) if phone_raw else None
        if phone_raw and phone is None:
            report.rejected.append(RejectedRow(
                i, f"unusable phone '{phone_raw}' - a wrong number messages a stranger", original))
            continue

        amount_paise = parse_amount(row.get("amount", ""))
        if amount_paise is None:
            report.rejected.append(RejectedRow(
                i, f"invalid amount '{row.get('amount', '')}' - must be a positive number",
                original))
            continue

        due_iso, supplied = parse_due_date(row.get("due_date", ""))
        if supplied and due_iso is None:
            report.rejected.append(RejectedRow(
                i, f"unreadable due date '{row.get('due_date')}' - "
                   f"use YYYY-MM-DD or DD/MM/YYYY", original))
            continue

        customer_id = row.get("customer_id", "") or (email or phone or f"row_{i}")
        dedupe_key = f"{customer_id}|{amount_paise}"
        if dedupe_key in seen_keys:
            report.rejected.append(RejectedRow(
                i, f"duplicate of line {seen_keys[dedupe_key]} "
                   f"(same customer and amount) - would contact them twice", original))
            continue
        seen_keys[dedupe_key] = i

        report.valid.append(ValidRow(
            line=i, customer_id=customer_id, name=row.get("name", ""),
            email=email, phone=phone or "", amount_paise=amount_paise,
            due_date=due_iso or "",
            # A merchant uploading outstanding amounts is describing RECEIVABLES, not
            # failed charges. There was no payment attempt, so there is no stored
            # instrument to retry - and typing it as FAILED_PAYMENT makes the engine
            # recommend retrying a charge that never happened. A row may override this.
            event_type=(row.get("event_type") or "OVERDUE_B2B_INVOICE").upper(),
            failure_reason=(row.get("failure_reason") or "").upper(),
        ))

    return report


def create_cases(
    repo: Any,
    rows: List[ValidRow],
    merchant_id: str = "merch_demo",
) -> List[Case]:
    """Persist validated rows as Customers and Cases. The CSV is the source of truth."""
    created: List[Case] = []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    for row in rows:
        repo.upsert_customer(Customer(
            customer_id=row.customer_id, merchant_id=merchant_id,
            name=row.name, email=row.email, phone=row.phone,
        ))
        case = Case(
            case_id=f"case_{merchant_id}_{row.customer_id}_{stamp}_{row.line}",
            merchant_id=merchant_id,
            customer_id=row.customer_id,
            amount_paise=row.amount_paise,
            due_date=row.due_date,
            source_event_id=f"csv_{merchant_id}_{row.customer_id}_{stamp}_{row.line}",
            event_type=row.event_type,
            status=CaseStatus.OPEN,
        )
        repo.create_case(case)
        created.append(case)
    return created
