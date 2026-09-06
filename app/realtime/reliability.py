"""Production reliability: retry, dead-letter, and reconciliation sweeps (ADR-0019).

THREE WAYS THE LIVE SYSTEM SILENTLY LOST MONEY OR STATE
    1. A background decision that threw was marked ENGINE_ERROR and then forgotten.
       Razorpay had already received its 200, so it would never redeliver. One transient
       database lock or model hiccup and that customer is simply never recovered — no
       retry, no alert, no trace beyond a row nobody reads. Revenue at risk became revenue
       lost, quietly, which is the exact failure this product exists to prevent.

    2. The contact ledger has a reconciliation ladder for EXECUTION_UNKNOWN — the state
       where the engine cannot tell whether a message reached the customer — but NOTHING
       EVER RAN IT. Entries sat in EXECUTION_UNKNOWN forever, holding reserved budget slots
       that were never consumed or released. A customer's contact budget silently leaked
       until they could not be contacted at all.

    3. Replay protection was declared in config, reported on /health, and never enforced.
       A captured webhook body plus its signature could be replayed indefinitely. A control
       that is documented but absent is worse than one that is missing, because everyone
       downstream believes it is there.

WHAT THIS PROVIDES
    - A durable retry queue with bounded exponential backoff, and a dead-letter state that
      is visible rather than silent.
    - A periodic reconciliation sweep that resolves stale EXECUTION_UNKNOWN entries
      fail-closed, so budget slots stop leaking.
    - Both driven by one background scheduler that shuts down cleanly.

INVARIANTS:
1. FAIL CLOSED ON AMBIGUITY. An unresolvable contact reconciles to RECONCILED_UNRESOLVED,
   which CONSUMES the slot. Releasing it would risk contacting a customer who may already
   have received the message. Capacity is cheaper than a duplicate contact.
2. BOUNDED RETRY. Attempts are capped. An event that exhausts them is DEAD_LETTER and is
   surfaced for a human, never retried forever.
3. NO DUPLICATE SIDE EFFECTS. Retries re-enter the same idempotent engine path, keyed on
   the same intervention idempotency key, so a retry cannot double-contact anyone.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from app.realtime import ingest

logger = logging.getLogger("recovery.reliability")

# Bounded exponential backoff, in seconds. Length of this list IS the attempt cap.
RETRY_BACKOFF_SECONDS = (30, 120, 600, 1800)
MAX_ATTEMPTS = len(RETRY_BACKOFF_SECONDS)

# How long an EXECUTION_UNKNOWN entry may stay unresolved before the sweep closes it.
# Short enough that budget does not leak for long; long enough that a slow delivery
# receipt still has a chance to arrive and resolve it properly.
RECONCILE_AFTER_MINUTES = 30

SWEEP_INTERVAL_SECONDS = 60  # overridden by config.WORKER_INTERVAL_SECONDS

RETRY_DDL = """
CREATE TABLE IF NOT EXISTS retry_queue (
    razorpay_event_id TEXT PRIMARY KEY,
    razorpay_event    TEXT,
    raw_event_json    TEXT NOT NULL,
    attempts          INTEGER NOT NULL DEFAULT 0,
    next_attempt_at   TEXT NOT NULL,
    last_error        TEXT,
    status            TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_retry_due ON retry_queue(status, next_attempt_at);
"""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def ensure_schema() -> None:
    conn = ingest.get_conn()
    conn.executescript(RETRY_DDL)
    conn.commit()


# --- Retry queue -------------------------------------------------------------------------


def enqueue_retry(
    razorpay_event_id: str,
    razorpay_event: str,
    raw_event_json: str,
    error: str,
) -> str:
    """Schedule a failed event for another attempt, or dead-letter it if attempts are spent.

    Returns the resulting status: RETRY_SCHEDULED or DEAD_LETTER.
    """
    ensure_schema()
    conn = ingest.get_conn()
    row = conn.execute(
        "SELECT attempts FROM retry_queue WHERE razorpay_event_id = ?;",
        (razorpay_event_id,),
    ).fetchone()
    attempts = (row[0] if row else 0) + 1

    if attempts > MAX_ATTEMPTS:
        status = "DEAD_LETTER"
        next_at = _now()
        logger.error(
            "DEAD LETTER after %d attempts: %s (%s). This opportunity will NOT be "
            "recovered without human action.",
            attempts - 1, razorpay_event_id, error,
        )
    else:
        status = "RETRY_SCHEDULED"
        next_at = _now() + timedelta(seconds=RETRY_BACKOFF_SECONDS[attempts - 1])

    now = _iso(_now())
    conn.execute(
        """
        INSERT INTO retry_queue (
            razorpay_event_id, razorpay_event, raw_event_json, attempts,
            next_attempt_at, last_error, status, created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(razorpay_event_id) DO UPDATE SET
            attempts        = excluded.attempts,
            next_attempt_at = excluded.next_attempt_at,
            last_error      = excluded.last_error,
            status          = excluded.status,
            updated_at      = excluded.updated_at;
        """,
        (
            razorpay_event_id, razorpay_event, raw_event_json, attempts,
            _iso(next_at), error[:500], status, now, now,
        ),
    )
    conn.commit()
    return status


def due_retries(limit: int = 20) -> List[Dict[str, Any]]:
    """Events whose backoff has elapsed and which are still retryable."""
    ensure_schema()
    conn = ingest.get_conn()
    rows = conn.execute(
        """
        SELECT razorpay_event_id, razorpay_event, raw_event_json, attempts
        FROM retry_queue
        WHERE status = 'RETRY_SCHEDULED' AND next_attempt_at <= ?
        ORDER BY next_attempt_at LIMIT ?;
        """,
        (_iso(_now()), int(limit)),
    ).fetchall()
    return [
        {"razorpay_event_id": r[0], "razorpay_event": r[1], "raw_event_json": r[2], "attempts": r[3]}
        for r in rows
    ]


def mark_retry_succeeded(razorpay_event_id: str) -> None:
    ensure_schema()
    conn = ingest.get_conn()
    conn.execute(
        "UPDATE retry_queue SET status='SUCCEEDED', updated_at=? WHERE razorpay_event_id=?;",
        (_iso(_now()), razorpay_event_id),
    )
    conn.commit()


def retry_counters() -> Dict[str, int]:
    ensure_schema()
    conn = ingest.get_conn()
    return {
        str(s): int(c)
        for s, c in conn.execute(
            "SELECT status, COUNT(*) FROM retry_queue GROUP BY status;"
        ).fetchall()
    }


# --- Reconciliation sweep -----------------------------------------------------------------


def stale_unknown_entries(older_than_minutes: int = RECONCILE_AFTER_MINUTES) -> List[str]:
    """Ledger entries stuck in EXECUTION_UNKNOWN past the resolution window."""
    conn = ingest.get_conn()
    cutoff = _iso(_now() - timedelta(minutes=older_than_minutes))
    rows = conn.execute(
        """
        SELECT ledger_id FROM contact_ledger
        WHERE status = 'EXECUTION_UNKNOWN' AND updated_at <= ?
        LIMIT 200;
        """,
        (cutoff,),
    ).fetchall()
    return [r[0] for r in rows]


def sweep_reconciliation(reconcile_fn: Callable[[str], bool]) -> int:
    """Close stale EXECUTION_UNKNOWN entries fail-closed. Returns how many were closed.

    FAIL CLOSED: unresolved entries become RECONCILED_UNRESOLVED, which CONSUMES the
    reserved slot rather than returning it. Releasing capacity would risk contacting a
    customer who may already have received the first message; a slightly tighter budget is
    the cheaper error.
    """
    closed = 0
    for ledger_id in stale_unknown_entries():
        try:
            if reconcile_fn(ledger_id):
                closed += 1
        except Exception:
            logger.exception("reconciliation failed for %s", ledger_id)
    if closed:
        logger.info("reconciliation sweep closed %d stale entries", closed)
    return closed


# --- Background scheduler ------------------------------------------------------------------


class BackgroundWorker:
    """Runs the retry drain and reconciliation sweep on an interval, and stops cleanly."""

    def __init__(
        self,
        process_fn: Callable[[Dict[str, Any]], None],
        reconcile_fn: Optional[Callable[[str], bool]] = None,
        followup_fn: Optional[Callable[[Dict[str, Any]], None]] = None,
        interval_seconds: int = SWEEP_INTERVAL_SECONDS,
    ) -> None:
        self.process_fn = process_fn
        self.reconcile_fn = reconcile_fn
        # Follow-ups are the sequence half of recovery: an opportunity contacted N hours
        # ago with no resolution re-enters the engine. Without this the system only ever
        # makes one move per event and silence is never acted on.
        self.followup_fn = followup_fn
        self.interval = interval_seconds
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, daemon=True, name="recovery-worker")
        self._thread.start()
        logger.info("background worker started (interval %ss)", self.interval)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                for item in due_retries():
                    self.process_fn(item)
                if self.reconcile_fn is not None:
                    sweep_reconciliation(self.reconcile_fn)
                if self.followup_fn is not None:
                    from app.realtime import followup as _followup

                    for due in _followup.due_followups():
                        opp = due.get("opportunity_id", "")
                        reason = "handled"
                        try:
                            self.followup_fn(due)
                        except Exception as exc:  # noqa: BLE001
                            reason = f"failed: {exc}"
                            logger.exception("follow-up failed for %s", opp)
                        finally:
                            # RETIRE IT EITHER WAY.
                            #
                            # Nothing used to change this row's status, so a due follow-up
                            # was re-run on every tick forever. That produced the log line
                            # repeating hundreds of times, nineteen overdue rows from one
                            # case, and a payment provider 429 from a new link request
                            # every two seconds.
                            #
                            # A failure is retired too, deliberately. Retrying the same
                            # row every two seconds is not resilience, it is the loop that
                            # caused the outage - and a genuine retry already exists in
                            # the next scheduled follow-up.
                            _followup.mark_handled(opp, reason)
            except Exception:
                logger.exception("background worker iteration failed")
            self._stop.wait(self.interval)
