"""Real-time ingestion service — durable, idempotent, observable (ADR-0018).

WHAT WAS BROKEN
    The webhook handler built `RecoveryOrchestrator()` at module import, which defaults to
    `init_db(":memory:")`. The server and the dashboard are separate processes, so each held
    a private database: nothing the server ingested could ever appear in the UI, and every
    decision vanished on restart. A "real-time system" whose output nobody can observe and
    which forgets everything on deploy is a demo script, not a system.

    Nothing deduplicated deliveries either. Razorpay retries a webhook until it gets a 2xx,
    so a slow response or a transient error meant the same failed payment was recovered
    twice — two messages to one customer, two slots off one contact budget.

WHAT THIS PROVIDES
    - ONE durable SQLite database (WAL) shared by the server and the dashboard.
    - Idempotent ingestion keyed on Razorpay's own event id, so retries are free.
    - A persisted decision feed the UI tails.
    - Dispatch that is OFF by default, so the engine can run live traffic end to end
      without contacting anybody until that is switched on deliberately.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.db.init import init_db
from app.realtime import config

# THREAD-LOCAL CONNECTIONS.
#
# A SQLite connection may only be used by the thread that created it. The webhook server
# acknowledges on the event loop and then processes in a worker thread, so a single shared
# connection raises `SQLite objects created in a thread can only be used in that same
# thread` on the first background decision — the request succeeds, the recovery silently
# does not. Each thread therefore gets its own connection to the SAME database file, which
# WAL mode is built for: concurrent readers alongside one writer.
_LOCK = threading.Lock()
_LOCAL = threading.local()
_INITIALISED = False

# The live decision feed. Kept as its own table rather than reconstructed by joining the
# engine's internal tables, so the UI has one cheap, append-only thing to tail and the
# read path can never slow the ingest path down.
FEED_DDL = """
CREATE TABLE IF NOT EXISTS live_feed (
    feed_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    received_at        TEXT NOT NULL,
    razorpay_event     TEXT,
    razorpay_event_id  TEXT UNIQUE,
    merchant_id        TEXT,
    customer_id        TEXT,
    event_id           TEXT,
    event_type         TEXT,
    amount_paise       INTEGER,
    status             TEXT NOT NULL,
    selected_action    TEXT,
    decision_mode      TEXT,
    dispatch_state     TEXT,
    dispatch_detail    TEXT,
    trace_id           TEXT,
    payload_json       TEXT
);
CREATE INDEX IF NOT EXISTS idx_live_feed_received ON live_feed(received_at DESC);

-- Live gateway outages, driven by payment.downtime.* webhooks. Persisted rather than held
-- in memory because the webhook thread WRITES and the decision path READS, and because an
-- outage must survive a restart: forgetting an active outage means the engine resumes
-- contacting customers about a gateway that is still down (INV-4).
CREATE TABLE IF NOT EXISTS live_downtime (
    downtime_id  TEXT PRIMARY KEY,
    method       TEXT,
    instrument   TEXT,
    severity     TEXT,
    status       TEXT NOT NULL,
    began_at     TEXT,
    resolved_at  TEXT,
    updated_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_live_downtime_status ON live_downtime(status);

-- Entities Razorpay has told us were PAID. Stage 0's phantom-recovery check needs to know
-- this, and in live traffic the resolution arrives as its OWN webhook, separately from the
-- failure. Without persisting it the engine has no way to learn a customer already paid.
CREATE TABLE IF NOT EXISTS live_resolutions (
    entity_id    TEXT PRIMARY KEY,
    event        TEXT,
    amount_paise INTEGER,
    resolved_at  TEXT NOT NULL
);
"""


def get_conn() -> sqlite3.Connection:
    """Return THIS thread's connection to the durable database, creating it on first use."""
    global _INITIALISED
    conn = getattr(_LOCAL, "conn", None)
    if conn is not None:
        return conn

    with _LOCK:
        config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        # init_db applies the schema idempotently, so every thread may safely call it.
        conn = init_db(config.DB_PATH)
        # WAL lets the dashboard read while the server writes, which is the whole point of
        # a shared file-backed database.
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.executescript(FEED_DDL)
        conn.commit()
        _INITIALISED = True

    _LOCAL.conn = conn
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def already_seen(razorpay_event_id: str) -> bool:
    """True if this exact Razorpay delivery has been recorded before."""
    if not razorpay_event_id:
        return False
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM live_feed WHERE razorpay_event_id = ? LIMIT 1;",
        (razorpay_event_id,),
    ).fetchone()
    return row is not None


def record(
    *,
    razorpay_event_id: str,
    razorpay_event: str,
    status: str,
    raw_event: Optional[Dict[str, Any]] = None,
    selected_action: Optional[str] = None,
    decision_mode: Optional[str] = None,
    dispatch_state: Optional[str] = None,
    dispatch_detail: Optional[str] = None,
    trace_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """Upsert ONE row per delivery, advancing it in place as processing progresses.

    A delivery moves ACCEPTED -> PROCESSED (or ENGINE_ERROR) as the background worker
    finishes. Inserting a second row would duplicate the event in the feed; `INSERT OR
    IGNORE` would silently DROP the completion and the UI would show every event stuck at
    ACCEPTED forever. So this upserts, and COALESCE keeps any field the caller did not
    supply on this pass rather than nulling out what the first pass recorded.
    """
    conn = get_conn()
    raw = raw_event or {}
    conn.execute(
        """
        INSERT INTO live_feed (
            received_at, razorpay_event, razorpay_event_id, merchant_id, customer_id,
            event_id, event_type, amount_paise, status, selected_action, decision_mode,
            dispatch_state, dispatch_detail, trace_id, payload_json
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(razorpay_event_id) DO UPDATE SET
            status          = excluded.status,
            merchant_id     = COALESCE(excluded.merchant_id,     live_feed.merchant_id),
            customer_id     = COALESCE(excluded.customer_id,     live_feed.customer_id),
            event_id        = COALESCE(excluded.event_id,        live_feed.event_id),
            event_type      = COALESCE(excluded.event_type,      live_feed.event_type),
            amount_paise    = COALESCE(excluded.amount_paise,    live_feed.amount_paise),
            selected_action = COALESCE(excluded.selected_action, live_feed.selected_action),
            decision_mode   = COALESCE(excluded.decision_mode,   live_feed.decision_mode),
            dispatch_state  = COALESCE(excluded.dispatch_state,  live_feed.dispatch_state),
            dispatch_detail = COALESCE(excluded.dispatch_detail, live_feed.dispatch_detail),
            trace_id        = COALESCE(excluded.trace_id,        live_feed.trace_id),
            payload_json    = COALESCE(excluded.payload_json,    live_feed.payload_json);
        """,
        (
            _now(), razorpay_event, razorpay_event_id or None,
            raw.get("merchant_id"), raw.get("customer_id"), raw.get("event_id"),
            raw.get("event_type"), raw.get("amount_paise"), status,
            selected_action, decision_mode, dispatch_state, dispatch_detail, trace_id,
            json.dumps(payload, default=str) if payload else None,
        ),
    )
    conn.commit()


def recent(limit: int = 50) -> list:
    """Most recent feed rows, newest first. Read by the dashboard's Live tab."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM live_feed ORDER BY feed_id DESC LIMIT ?;", (int(limit),)
    ).fetchall()
    return [dict(r) for r in rows]


def counters() -> Dict[str, int]:
    """Aggregate counts for the Live tab header."""
    conn = get_conn()
    out: Dict[str, int] = {}
    for status, count in conn.execute(
        "SELECT status, COUNT(*) FROM live_feed GROUP BY status;"
    ).fetchall():
        out[str(status)] = int(count)
    return out


# --- Live downtime signal (payment.downtime.*) -------------------------------------------


def upsert_downtime(
    *,
    downtime_id: str,
    status: str,
    method: Optional[str] = None,
    instrument: Optional[str] = None,
    severity: Optional[str] = None,
    began_at: Optional[str] = None,
) -> None:
    """Record or advance one gateway outage. `status` is ACTIVE or RESOLVED."""
    conn = get_conn()
    now = _now()
    resolved_at = now if status == "RESOLVED" else None
    conn.execute(
        """
        INSERT INTO live_downtime (
            downtime_id, method, instrument, severity, status, began_at, resolved_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?)
        ON CONFLICT(downtime_id) DO UPDATE SET
            status      = excluded.status,
            method      = COALESCE(excluded.method,     live_downtime.method),
            instrument  = COALESCE(excluded.instrument, live_downtime.instrument),
            severity    = COALESCE(excluded.severity,   live_downtime.severity),
            began_at    = COALESCE(live_downtime.began_at, excluded.began_at),
            resolved_at = excluded.resolved_at,
            updated_at  = excluded.updated_at;
        """,
        (downtime_id, method, instrument, severity, status, began_at, resolved_at, now),
    )
    conn.commit()


def active_outages() -> list:
    """Every outage Razorpay has told us is currently in progress."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM live_downtime WHERE status = 'ACTIVE' ORDER BY updated_at DESC;"
    ).fetchall()
    return [dict(r) for r in rows]


def is_down(gateway_name: str, method: Optional[str] = None) -> bool:
    """True if any ACTIVE outage matches this gateway/instrument or payment method.

    Matching is deliberately broad: Razorpay reports downtime against an instrument (an
    issuing bank, a wallet) or a method (upi, card, netbanking), and the engine's event
    carries whichever of those the payment used. A missed match means contacting customers
    during a known outage, so ambiguity resolves toward suppression (INV-4).
    """
    rows = active_outages()
    if not rows:
        return False
    g = (gateway_name or "").lower().strip()
    m = (method or "").lower().strip()
    for row in rows:
        inst = (row.get("instrument") or "").lower().strip()
        meth = (row.get("method") or "").lower().strip()
        if g and inst and (g == inst or g in inst or inst in g):
            return True
        if m and meth and m == meth:
            return True
    return False


# --- Resolutions (payment.captured, order.paid, invoice.paid, payment_link.paid) ----------


def record_resolution(entity_id: str, event: str, amount_paise: Optional[int] = None) -> None:
    """Remember that Razorpay reported this entity as paid."""
    if not entity_id:
        return
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO live_resolutions (entity_id, event, amount_paise, resolved_at)
        VALUES (?,?,?,?)
        ON CONFLICT(entity_id) DO UPDATE SET
            event = excluded.event, resolved_at = excluded.resolved_at;
        """,
        (entity_id, event, amount_paise, _now()),
    )
    conn.commit()


def is_resolved(entity_id: str) -> bool:
    """True if a paid-confirmation has been received for this entity."""
    if not entity_id:
        return False
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM live_resolutions WHERE entity_id = ? LIMIT 1;", (entity_id,)
    ).fetchone()
    return row is not None
