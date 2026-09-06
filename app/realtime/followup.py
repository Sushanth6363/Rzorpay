"""Follow-up scheduling — the missing half of a recovery product (ADR-0021).

THE GAP THIS CLOSES
    The engine was purely event-driven: something had to arrive for it to think. Contact a
    customer once, have them ignore it forever, and nothing further happened. No second
    touch, no timer, no sequence. But recovery is fundamentally a SEQUENCE OVER TIME —
    one message is not a campaign, and a decision engine that only ever makes one move per
    event is half a product.

    Note what the engine can and cannot observe. There is no open, click or read signal
    anywhere in the system. The engine cannot distinguish "read and ignored" from "never
    saw it". It knows exactly two things: whether the contact was CONFIRMED DELIVERED, and
    whether the money ARRIVED. A follow-up is therefore triggered by *silence plus elapsed
    time*, never by an inferred customer intent — and this module does not pretend
    otherwise.

DYNAMIC TIMING: DELAY IS A FUNCTION OF WHY IT FAILED AND WHAT WE DID
    A single fixed interval is wrong in both directions. Chasing an abandoned cart a week
    later is pointless; chasing an insufficient-funds failure the next morning is chasing
    money that does not exist yet. So the delay is derived:

        delay = base_hours(diagnosis) x multiplier(last_action) x backoff(attempt)

    The diagnosis sets the base because it determines WHEN the blocker realistically
    clears. The action adjusts it because channels have very different read latencies — an
    SMS is read in minutes, an email may sit for two days, and a phone call earns a longer
    pause before the next approach.

INVARIANTS:
1. STOPS ON RESOLUTION. Payment arriving cancels every scheduled follow-up for that
   opportunity immediately. The engine must never chase money it already has.
2. BOUNDED. MAX_FOLLOWUPS per opportunity, and a hard recovery window after which the
   opportunity is closed regardless. A customer cannot be pursued indefinitely.
3. A FOLLOW-UP IS A NEW OPPORTUNITY, not a replay. It carries a suffixed event id so the
   escalation ladder reads the customer's real contact history and advances one rung —
   rather than colliding with the original's idempotency key and silently sending nothing.
4. POLICY STILL APPLIES. Follow-ups re-enter the full engine: Stage 0, safety filter,
   contact budget, quiet period and escalation ceiling all bind exactly as they do on a
   first touch. This schedules a RECONSIDERATION, never a guaranteed send.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.domain.enums import ActionType, DiagnosisCode
from app.realtime import ingest

logger = logging.getLogger("recovery.followup")

# --- Base delay per diagnosis: when does the blocker realistically clear? -----------------
#
#   CUSTOMER_ABANDONMENT   intent decays within hours; the classic cart sequence is
#                          ~1h / 24h / 72h. Shortest first touch of any stream.
#   GATEWAY_FAILURE        infrastructure. The outage clears in hours, and until it does a
#                          follow-up is noise, so this is short but deliberately not
#                          instant.
#   CARD_DECLINED          the customer must update an instrument — an action they can take
#                          immediately once they see the message.
#   SUBSCRIPTION_RENEWAL_FAILURE  a mandate exists; standard dunning is ~1/3/5/7 days.
#   INSUFFICIENT_FUNDS     the money genuinely is not there. Chasing tomorrow chases
#                          nothing; this waits for a realistic funding cycle.
#   INVOICE_OVERDUE        B2B accounts-payable runs on weekly or fortnightly cycles. A
#                          two-day nudge to an AP team is simply ignored.
#   CUSTOMER_UNRESPONSIVE  repeated non-response is itself evidence. Back off hard.
BASE_DELAY_HOURS: Dict[str, float] = {
    DiagnosisCode.CUSTOMER_ABANDONMENT.value: 6,
    DiagnosisCode.GATEWAY_FAILURE.value: 8,
    DiagnosisCode.CARD_DECLINED.value: 24,
    DiagnosisCode.SUBSCRIPTION_RENEWAL_FAILURE.value: 48,
    DiagnosisCode.INSUFFICIENT_FUNDS.value: 72,
    DiagnosisCode.INVOICE_OVERDUE.value: 168,      # one week
    DiagnosisCode.CUSTOMER_UNRESPONSIVE.value: 120,
    DiagnosisCode.UNKNOWN.value: 48,
}
DEFAULT_DELAY_HOURS = 48.0

# --- Action multiplier: how long until we can fairly call it silence? --------------------
#
# Read latency differs enormously by channel. An SMS unanswered after a day is a real
# signal; an email unanswered after a day may simply be unread. A voice call earns the
# longest pause — following a call quickly reads as pressure.
ACTION_DELAY_MULTIPLIER: Dict[ActionType, float] = {
    ActionType.RECOMMEND_RETRY: 0.5,   # no human involved; re-check sooner
    ActionType.SMS_LINK: 0.8,
    ActionType.WHATSAPP_LINK: 0.9,
    ActionType.EMAIL_LINK: 1.2,        # long read latency
    ActionType.IVR_CALL: 1.5,
    ActionType.AGENT_DIAL: 2.0,        # a person called; do not crowd them
}

# Each successive unanswered touch widens the gap. Diminishing returns are real: someone
# who ignored three messages is unlikely to answer the fourth sooner.
ATTEMPT_BACKOFF = (1.0, 1.5, 2.5, 4.0)

MAX_FOLLOWUPS = 4
RECOVERY_WINDOW_DAYS = 30
MIN_DELAY_HOURS = 1.0

FOLLOWUP_DDL = """
CREATE TABLE IF NOT EXISTS followup_queue (
    opportunity_id   TEXT PRIMARY KEY,
    merchant_id      TEXT,
    customer_id      TEXT,
    origin_event_id  TEXT,
    event_json       TEXT NOT NULL,
    diagnosis_code   TEXT,
    last_action      TEXT,
    attempt          INTEGER NOT NULL DEFAULT 0,
    next_touch_at    TEXT NOT NULL,
    first_seen_at    TEXT NOT NULL,
    status           TEXT NOT NULL,
    stop_reason      TEXT,
    updated_at       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_followup_due ON followup_queue(status, next_touch_at);
"""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_schema() -> None:
    conn = ingest.get_conn()
    conn.executescript(FOLLOWUP_DDL)
    conn.commit()


def compute_delay_hours(
    diagnosis_code: Optional[str],
    last_action: Optional[ActionType],
    attempt: int,
) -> float:
    """delay = base(diagnosis) x multiplier(action) x backoff(attempt). Never below an hour."""
    base = BASE_DELAY_HOURS.get(str(diagnosis_code or ""), DEFAULT_DELAY_HOURS)
    multiplier = ACTION_DELAY_MULTIPLIER.get(last_action, 1.0) if last_action else 1.0
    backoff = ATTEMPT_BACKOFF[min(max(attempt, 0), len(ATTEMPT_BACKOFF) - 1)]
    return max(MIN_DELAY_HOURS, base * multiplier * backoff)


def schedule(
    opportunity_id: str,
    merchant_id: str,
    customer_id: str,
    origin_event_id: str,
    event: Dict[str, Any],
    diagnosis_code: Optional[str],
    last_action: Optional[ActionType],
    attempt: int = 0,
) -> Optional[str]:
    """Schedule the next reconsideration. Returns the ISO due time, or None if stopped."""
    ensure_schema()
    if attempt >= MAX_FOLLOWUPS:
        _stop(opportunity_id, "MAX_FOLLOWUPS reached")
        return None

    delay = compute_delay_hours(diagnosis_code, last_action, attempt)
    # Scale hours to real seconds. At the default (3600) this is exactly `hours=delay`;
    # at demo speed the same policy plays out in seconds with every ratio intact.
    from app.realtime import config as _cfg
    due = _now() + timedelta(seconds=delay * _cfg.FOLLOWUP_HOUR_SECONDS)
    now_iso = _now().isoformat()

    conn = ingest.get_conn()
    conn.execute(
        """
        INSERT INTO followup_queue (
            opportunity_id, merchant_id, customer_id, origin_event_id, event_json,
            diagnosis_code, last_action, attempt, next_touch_at, first_seen_at,
            status, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,'SCHEDULED',?)
        ON CONFLICT(opportunity_id) DO UPDATE SET
            attempt        = excluded.attempt,
            last_action    = excluded.last_action,
            diagnosis_code = excluded.diagnosis_code,
            next_touch_at  = excluded.next_touch_at,
            status         = 'SCHEDULED',
            stop_reason    = NULL,
            updated_at     = excluded.updated_at;
        """,
        (
            opportunity_id, merchant_id, customer_id, origin_event_id,
            json.dumps(event, default=str), diagnosis_code,
            last_action.value if last_action else None, attempt,
            due.isoformat(), now_iso, now_iso,
        ),
    )
    conn.commit()
    logger.info(
        "follow-up %d for %s in %.1fh (%s / %s)",
        attempt + 1, opportunity_id, delay, diagnosis_code,
        last_action.value if last_action else "none",
    )
    return due.isoformat()


def _stop(opportunity_id: str, reason: str) -> None:
    ensure_schema()
    conn = ingest.get_conn()
    conn.execute(
        """UPDATE followup_queue SET status='STOPPED', stop_reason=?, updated_at=?
           WHERE opportunity_id=?;""",
        (reason, _now().isoformat(), opportunity_id),
    )
    conn.commit()


def mark_handled(opportunity_id: str, reason: str = "handled",
                 only_if_due_at: Optional[str] = None) -> None:
    """Retire a row the worker has just run.

    WHY THIS HAS TO EXIST
        `due_followups` selected rows and nothing ever changed their status. The only
        transitions were `_stop` for the recovery window and `cancel_for_entity` for a
        payment. So a row that came due stayed SCHEDULED and was re-run on EVERY worker
        tick, forever.

        That is the cause of nearly every strange thing seen during a demo: a log line
        repeating hundreds of times, nineteen "overdue" rows accumulating from a single
        case, and a payment provider returning 429 because the worker was asking it for a
        new link every two seconds. Waiting never helped, because the loop never stopped.

        The chain is not broken by retiring the row. A follow-up schedules its successor
        under a NEW opportunity id (`<origin>#f2`), which is its own row. This one has
        done its job.

    HANDLED, NOT DELETED: the row stays as a record of what the engine did and when.
    """
    ensure_schema()
    conn = ingest.get_conn()
    if only_if_due_at:
        # ONLY RETIRE THE ROW WE ACTUALLY RAN.
        #
        # The handler reschedules the NEXT touch by upserting the same opportunity id with
        # a new due time. Retiring unconditionally afterwards overwrote that fresh
        # SCHEDULED row with HANDLED, so the chain died after exactly one follow-up: the
        # ladder reached SMS and then nothing further ever fired.
        #
        # Matching on the due time we were handed distinguishes the two: unchanged means
        # this is still the row we ran, changed means the handler has already moved it on.
        conn.execute(
            """UPDATE followup_queue SET status='HANDLED', stop_reason=?, updated_at=?
               WHERE opportunity_id=? AND status='SCHEDULED' AND next_touch_at=?;""",
            (reason[:200], _now().isoformat(), opportunity_id, only_if_due_at),
        )
    else:
        conn.execute(
            """UPDATE followup_queue SET status='HANDLED', stop_reason=?, updated_at=?
               WHERE opportunity_id=? AND status='SCHEDULED';""",
            (reason[:200], _now().isoformat(), opportunity_id),
        )
    conn.commit()


def cancel_for_entity(entity_id: str, reason: str = "payment received") -> int:
    """Stop chasing an entity the money has arrived for. Returns rows stopped.

    Matches EITHER identifier a queue row carries. Callers legitimately hold different
    ones: the webhook path resolves a payment to a `case_id`, the ingest path holds the
    `origin_event_id` of the failure that opened the opportunity. Matching only
    origin_event_id meant a real paid case kept a live follow-up scheduled against it -
    the update matched nothing, returned 0, and nobody looked at the return value.

    Nothing was sent to that customer, because ChannelDispatcher re-reads case state
    before dispatching and would have refused. But relying on the last line of defence
    for something the first line was supposed to handle is not a design, it is luck.
    """
    ensure_schema()
    conn = ingest.get_conn()
    cur = conn.execute(
        """UPDATE followup_queue SET status='STOPPED', stop_reason=?, updated_at=?
           WHERE (origin_event_id=? OR opportunity_id=?) AND status='SCHEDULED';""",
        (reason, _now().isoformat(), entity_id, entity_id),
    )
    conn.commit()
    if cur.rowcount:
        logger.info("cancelled %d follow-up(s) for %s: %s", cur.rowcount, entity_id, reason)
    return cur.rowcount


def due_followups(limit: int = 50) -> List[Dict[str, Any]]:
    """Opportunities whose next touch is due, excluding any past the recovery window."""
    ensure_schema()
    conn = ingest.get_conn()
    now = _now()
    window_start = (now - timedelta(days=RECOVERY_WINDOW_DAYS)).isoformat()
    rows = conn.execute(
        """
        SELECT opportunity_id, merchant_id, customer_id, origin_event_id, event_json,
               diagnosis_code, last_action, attempt, first_seen_at, next_touch_at
        FROM followup_queue
        WHERE status='SCHEDULED' AND next_touch_at <= ?
        ORDER BY next_touch_at LIMIT ?;
        """,
        (now.isoformat(), int(limit)),
    ).fetchall()

    due: List[Dict[str, Any]] = []
    for r in rows:
        if r[8] and r[8] < window_start:
            _stop(r[0], f"outside the {RECOVERY_WINDOW_DAYS}-day recovery window")
            continue
        due.append({
            "opportunity_id": r[0], "merchant_id": r[1], "customer_id": r[2],
            "origin_event_id": r[3], "event": json.loads(r[4]),
            "diagnosis_code": r[5], "last_action": r[6], "attempt": r[7],
            "next_touch_at": r[9],
        })
    return due


def counters() -> Dict[str, int]:
    ensure_schema()
    conn = ingest.get_conn()
    return {
        str(s): int(c)
        for s, c in conn.execute(
            "SELECT status, COUNT(*) FROM followup_queue GROUP BY status;"
        ).fetchall()
    }
