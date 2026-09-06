"""Real-Time Razorpay Webhook Ingestion Server (ADR-0018).

Receives live Razorpay webhooks, verifies them, and runs each event through the Unified
Recovery Engine against DURABLE shared state that the dashboard can observe.

WHAT CHANGED FROM THE FIRST VERSION, AND WHY
    1. SIGNATURE VERIFICATION NOW FAILS CLOSED. It previously skipped verification whenever
       no secret was configured, so an unauthenticated POST to a public URL would run the
       engine and mint Razorpay payment links. Absent configuration is now a refusal, not
       an open door. `ALLOW_UNSIGNED_WEBHOOKS=1` re-opens it for local testing and says so
       loudly on every request.
    2. DURABLE SHARED STATE. The orchestrator used an in-memory database, so the dashboard
       (a different process) could never see a single ingested event and everything was
       lost on restart. One WAL-mode SQLite file is now shared by both.
    3. IDEMPOTENT DELIVERY. Razorpay retries until it gets a 2xx. Without deduplication a
       retry meant a second message to the same customer and a second slot off their
       contact budget. Deliveries are now keyed on Razorpay's own event id.
    4. FAST ACKNOWLEDGEMENT. Full orchestration plus an outbound API call ran inside the
       request, so a slow dependency produced a timeout and therefore a retry - turning one
       failure into duplicate contact attempts. The request now durably records the event,
       acknowledges, and processes in the background.
    5. NO SEED ON THE LIVE PATH. `random_seed=42` was hardcoded, so live exploration was
       deterministic and every decision replayed the same draw. Live traffic gets no seed.
    6. ALL FOUR STREAMS. The old mapping produced only FAILED_PAYMENT or ABANDONED_CHECKOUT,
       making subscriptions and B2B receivables unreachable from real traffic.

SAFETY POSTURE
    Outbound dispatch is OFF by default. The engine decides, records, and builds a full
    audit trail, but sends nothing until RECOVERY_DISPATCH_ENABLED is set - and refuses
    live (non-test) credentials unless separately acknowledged. See app/realtime/config.py.
"""

from __future__ import annotations

import contextlib
import json
import logging
import threading
import time
from typing import Any, Dict, Optional

from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response
from starlette.routing import Route

from app.domain.enums import ActionType, LedgerStatus
from app.integrations.razorpay_client import RazorpayIntegrationClient
from app.orchestration.recovery_orchestrator import RecoveryOrchestrator
from app.cases.repository import CaseRepository
from app.dispatch import voice
from app.realtime import config, followup, ingest, reliability
from app.realtime.downtime_live import LiveRazorpayDowntimeProvider
from app.realtime.event_mapper import (
    DOWNTIME_EVENTS,
    RESOLUTION_EVENTS,
    extract_case_hints,
    extract_entity,
    map_webhook,
)

logger = logging.getLogger("recovery.webhook")

razorpay_client = RazorpayIntegrationClient()

# Actions that put a message in front of a person. RECOMMEND_RETRY is excluded: it is a
# recommendation to the payment infrastructure, not an outbound contact (ADR-0006).
DISPATCHABLE = frozenset({
    ActionType.WHATSAPP_LINK, ActionType.SMS_LINK, ActionType.EMAIL_LINK,
})

# One orchestrator per THREAD, because it holds a SQLite connection and those are
# thread-bound. Starlette acknowledges on the event loop and processes in a worker thread,
# so a process-wide singleton fails on the first background decision — the webhook returns
# 202 and the recovery never happens. Per-thread instances share the same database file.
_LOCAL = threading.local()


def get_orchestrator() -> RecoveryOrchestrator:
    """Orchestrator for this thread, bound to the durable shared database.

    Wired to the LIVE downtime provider: outages come from Razorpay's own
    `payment.downtime.*` notifications, not from an authored fixture. INV-4 is unchanged —
    only the source of "known outage" is real now.
    """
    orch = getattr(_LOCAL, "orchestrator", None)
    if orch is None:
        # Arm A5's exact configuration, so the live engine is the evaluated engine. A
        # bare RecoveryOrchestrator carries an UNFITTED model and quietly scores from
        # cold-start baselines instead.
        from app.domain.enums import ExperimentArm
        from app.experiment.policies import build_orchestrator_for_arm

        orch = build_orchestrator_for_arm(
            ExperimentArm.A5,
            db_conn=ingest.get_conn(),
            downtime_provider_override=LiveRazorpayDowntimeProvider(),
        )
        _LOCAL.orchestrator = orch
    return orch


def _handle_downtime(payload: Dict[str, Any], event_name: str) -> str:
    """Apply a payment.downtime.* notification to the live outage store."""
    entity = extract_entity(payload) or (payload.get("payload", {}).get("payment.downtime", {}) or {}).get("entity", {})
    downtime_id = str(entity.get("id") or f"{event_name}:{payload.get('created_at')}")
    # Razorpay reports the affected thing as an instrument (an issuing bank, a wallet) or a
    # method (upi / card / netbanking). Both are stored; matching tries both.
    instrument = entity.get("instrument") or {}
    if isinstance(instrument, dict):
        instrument = instrument.get("bank") or instrument.get("wallet") or instrument.get("issuer") or ""
    status = "RESOLVED" if event_name.endswith(".resolved") else "ACTIVE"
    ingest.upsert_downtime(
        downtime_id=downtime_id,
        status=status,
        method=str(entity.get("method") or "") or None,
        instrument=str(instrument or "") or None,
        severity=str(entity.get("severity") or "") or None,
        began_at=str(entity.get("begin") or "") or None,
    )
    return status



def _is_stale(payload: Dict[str, Any]) -> tuple:
    """Return (is_stale, age_seconds). Unparseable timestamps are NOT rejected.

    Razorpay stamps `created_at` as epoch seconds. A missing or unreadable value is
    accepted rather than refused: rejecting on absent evidence would drop legitimate
    traffic, and the HMAC signature is the primary authenticity control. This bounds the
    window in which a captured request stays usable; it is not the authentication itself.
    """
    created = payload.get("created_at")
    if not isinstance(created, (int, float)) or created <= 0:
        return False, None
    age = int(time.time() - float(created))
    return age > config.WEBHOOK_MAX_AGE_SECONDS, age


def _retry_item(item: Dict[str, Any]) -> None:
    """Re-run a previously failed event from the retry queue."""
    try:
        raw_event = json.loads(item["raw_event_json"])
    except Exception:
        return
    _process(raw_event, item["razorpay_event_id"], item.get("razorpay_event") or "", is_retry=True)


def _reconcile_stale(ledger_id: str) -> bool:
    """Close a stale EXECUTION_UNKNOWN entry fail-closed (slot CONSUMED, not released)."""
    from app.ledger.engine import ContactLedgerEngine

    conn = ingest.get_conn()
    row = conn.execute(
        "SELECT merchant_id FROM contact_ledger WHERE ledger_id = ?;", (ledger_id,)
    ).fetchone()
    if not row:
        return False
    engine = ContactLedgerEngine(conn=conn, merchant_id=row[0])
    return engine.reconcile(
        ledger_id=ledger_id,
        outcome=LedgerStatus.RECONCILED_UNRESOLVED,
        metadata={"reason": "reconciliation sweep: unresolved past window"},
    )


def _payments():
    """PaymentLinkService for this thread, bound to the durable shared database."""
    from app.payments.link_service import PaymentLinkService

    svc = getattr(_LOCAL, "payments", None)
    if svc is None:
        svc = PaymentLinkService(ingest.get_conn())
        _LOCAL.payments = svc
    return svc


def _diagnosis_code(result: Any) -> Optional[str]:
    """Stage 1's verdict — drives follow-up timing and the message's ASK."""
    return str(getattr(result, "diagnosis_code", "") or "") or None


def _run_followup(item: Dict[str, Any]) -> None:
    """A due follow-up: re-enter the FULL engine as a new opportunity for this customer.

    A NEW event id is essential. Replaying the original would collide with its intervention
    idempotency key and silently send nothing; as a new opportunity the escalation ladder
    reads the customer's real contact history and advances exactly one rung.
    """
    from datetime import datetime, timezone

    attempt = int(item.get("attempt", 0)) + 1
    event = dict(item["event"])
    origin = item.get("origin_event_id") or event.get("event_id", "")
    event["event_id"] = f"{origin}#f{attempt}"
    now = datetime.now(timezone.utc).isoformat()
    event["occurred_at"] = now
    event["observed_at"] = now

    # Money may have arrived since this was scheduled.
    if ingest.is_resolved(origin):
        followup.cancel_for_entity(origin, "payment received before follow-up")
        return

    _process(event, f"followup:{event['event_id']}", "followup", attempt=attempt)


def _verify(body: bytes, signature: str) -> tuple:
    """Return (ok, reason). Fails closed when no secret is configured."""
    if config.WEBHOOK_SECRET:
        if razorpay_client.verify_webhook_signature(body, signature):
            return True, "signature verified"
        return False, "invalid signature"
    if config.ALLOW_UNSIGNED_WEBHOOKS:
        logger.warning(
            "ACCEPTING UNSIGNED WEBHOOK - ALLOW_UNSIGNED_WEBHOOKS is on. "
            "This endpoint will run the engine for anyone who can reach it."
        )
        return True, "UNSIGNED (testing mode)"
    return False, (
        "refused: RAZORPAY_WEBHOOK_SECRET is not configured. Set it, or set "
        "ALLOW_UNSIGNED_WEBHOOKS=1 for local testing only."
    )


def _process(
    raw_event: Dict[str, Any],
    razorpay_event_id: str,
    event_name: str,
    is_retry: bool = False,
    attempt: int = 0,
) -> None:
    """Run the engine and dispatch. Executes AFTER the response is sent."""
    try:
        result = get_orchestrator().process_and_execute(
            raw_event=raw_event,
            arm="A5",
            random_seed=None,  # live traffic is not a replay; no determinism seed
        )
    except Exception as exc:
        logger.exception("engine failed for %s", razorpay_event_id)
        # Razorpay already received its 200, so it will NEVER redeliver this. Without a
        # retry queue the opportunity is silently lost — revenue at risk becoming revenue
        # gone, which is precisely what this product exists to prevent.
        state = reliability.enqueue_retry(
            razorpay_event_id=razorpay_event_id,
            razorpay_event=event_name,
            raw_event_json=json.dumps(raw_event, default=str),
            error=str(exc),
        )
        ingest.record(
            razorpay_event_id=razorpay_event_id, razorpay_event=event_name,
            status=state, raw_event=raw_event,
        )
        return

    decision = result.decision
    action = decision.selected_action
    dispatch_state, dispatch_detail = "NOT_APPLICABLE", None

    if action in DISPATCHABLE:
        allowed, reason = config.dispatch_permitted(razorpay_client.key_id)
        if not allowed:
            dispatch_state, dispatch_detail = "SUPPRESSED", reason
        else:
            try:
                link = razorpay_client.create_payment_link(
                    amount_paise=raw_event["amount_paise"],
                    customer_name="Valued Customer",
                    customer_email=str(raw_event.get("customer_id", "")),
                    customer_contact="",
                    description=f"Recovery for {raw_event['event_id']}",
                    reference_id=decision.decision_id,
                )
                dispatch_state = "DISPATCHED"
                dispatch_detail = str(link.get("short_url") or link.get("id") or "")
            except Exception as exc:
                logger.exception("dispatch failed for %s", razorpay_event_id)
                dispatch_state, dispatch_detail = "DISPATCH_ERROR", str(exc)

    ingest.record(
        razorpay_event_id=razorpay_event_id, razorpay_event=event_name,
        status="PROCESSED", raw_event=raw_event,
        selected_action=action.value, decision_mode=decision.decision_mode.value,
        dispatch_state=dispatch_state, dispatch_detail=dispatch_detail,
        trace_id=result.trace_id,
    )
    if is_retry:
        reliability.mark_retry_succeeded(razorpay_event_id)

    # Schedule the next reconsideration. The engine was purely event-driven: contact a
    # customer once, have them ignore it, and nothing further happened. Recovery is a
    # SEQUENCE over time, so silence plus elapsed time is itself a trigger. The delay is
    # derived from WHY it failed and WHAT we did (app/realtime/followup.py) - chasing an
    # abandoned cart a week late is pointless, and chasing an insufficient-funds failure
    # tomorrow chases money that does not exist yet.
    if action != ActionType.NO_ACTION:
        followup.schedule(
            opportunity_id=result.opportunity_id,
            merchant_id=result.merchant_id,
            customer_id=result.customer_id,
            origin_event_id=str(raw_event.get("event_id", "")).split("#")[0],
            event=raw_event,
            diagnosis_code=_diagnosis_code(result),
            last_action=action,
            attempt=attempt,
        )


async def handle_razorpay_webhook(request: Request) -> JSONResponse:
    """Verify, deduplicate, acknowledge, then process in the background."""
    body = await request.body()
    ok, reason = _verify(body, request.headers.get("X-Razorpay-Signature", ""))
    if not ok:
        return JSONResponse({"error": reason}, status_code=401)

    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as exc:
        return JSONResponse({"error": f"invalid JSON: {exc}"}, status_code=400)

    # REPLAY PROTECTION. config advertised WEBHOOK_MAX_AGE_SECONDS and reported it on
    # /health, but nothing enforced it — a captured body and its still-valid signature
    # could be replayed indefinitely. A documented-but-absent control is worse than a
    # missing one, because everything downstream assumes it is there.
    stale, age = _is_stale(payload)
    if stale:
        return JSONResponse(
            {"error": f"stale webhook: {age}s old, max {config.WEBHOOK_MAX_AGE_SECONDS}s"},
            status_code=401,
        )

    # Razorpay's own delivery id. Retries of the same event carry the same value, which is
    # what makes acknowledging early safe.
    razorpay_event_id = (
        request.headers.get("X-Razorpay-Event-Id")
        or str(payload.get("id") or "")
        or f"{payload.get('event')}:{payload.get('created_at')}"
    )
    event_name = str(payload.get("event", ""))

    if ingest.already_seen(razorpay_event_id):
        # A retry. Acknowledge so Razorpay stops resending; do NOT act twice.
        return JSONResponse(
            {"status": "DUPLICATE_IGNORED", "razorpay_event_id": razorpay_event_id},
            status_code=200,
        )

    # --- Gateway health, not customer debt ----------------------------------------------
    # Feeds the live downtime provider (INV-4). Never becomes a recovery opportunity: an
    # infrastructure notice is not a failed payment.
    if event_name in DOWNTIME_EVENTS:
        state = _handle_downtime(payload, event_name)
        ingest.record(
            razorpay_event_id=razorpay_event_id, razorpay_event=event_name,
            status=f"DOWNTIME_{state}", payload=payload,
        )
        return JSONResponse({"status": f"DOWNTIME_{state}"}, status_code=200)

    # --- Money arrived ------------------------------------------------------------------
    # Recorded so Stage 0 can refuse to chase this entity later. In live traffic the
    # resolution is its OWN webhook, arriving separately from the failure, so without
    # persisting it the engine has no way to learn the customer already paid.
    if event_name in RESOLUTION_EVENTS:
        entity = extract_entity(payload)
        entity_id = str(entity.get("id") or "")
        amount = entity.get("amount")
        ingest.record_resolution(entity_id, event_name, amount if isinstance(amount, int) else None)
        # Stop chasing immediately. The engine must never pursue money it already has.
        followup.cancel_for_entity(entity_id, f"resolved by {event_name}")

        # Close the CASE. This is the step that makes the loop close: a payment made
        # through a recovery link arrives as plink_..., and only the case layer can map
        # that back to the case opened from the original failure (ADR-0023). Without it
        # the payment is recorded and the customer keeps being contacted.
        # Not just the entity id and a top-level reference_id: `payment.captured` and
        # `order.paid` carry our reference inside `notes` and the payment link inside
        # `description`, and reading only the top level is what left a paid case open
        # with a follow-up still scheduled against it.
        case_id = _payments().mark_paid_from_provider_event(
            entity_id=entity_id,
            event_name=event_name,
            amount_paise=amount if isinstance(amount, int) else None,
            reference_id=str(entity.get("reference_id") or ""),
            hints=extract_case_hints(payload),
        )
        if case_id:
            followup.cancel_for_entity(case_id, f"case closed by {event_name}")
        ingest.record(
            razorpay_event_id=razorpay_event_id, razorpay_event=event_name,
            status="RESOLVED_PAID", payload=payload,
        )
        return JSONResponse(
            {"status": "RESOLVED_PAID", "entity_id": entity_id}, status_code=200
        )

    raw_event = map_webhook(payload)
    if raw_event is None:
        ingest.record(
            razorpay_event_id=razorpay_event_id, razorpay_event=event_name,
            status="NOT_RECOVERABLE", payload=payload,
        )
        return JSONResponse(
            {"status": "IGNORED", "reason": "event does not represent revenue at risk"},
            status_code=200,
        )

    # If a paid-confirmation for this entity already arrived, hand Stage 0 the evidence.
    # Webhooks are not ordered: a `payment.captured` can land before the `payment.failed`
    # for an earlier attempt on the same entity. Chasing someone who has already paid is
    # the phantom recovery Stage 0 exists to prevent, so the check happens here rather than
    # relying on the failure payload to somehow know.
    if ingest.is_resolved(raw_event["event_id"]):
        raw_event["is_paid"] = True
        raw_event["payment_status"] = "SUCCESS"

    ingest.record(
        razorpay_event_id=razorpay_event_id, razorpay_event=event_name,
        status="ACCEPTED", raw_event=raw_event,
    )

    return JSONResponse(
        {
            "status": "ACCEPTED",
            "razorpay_event_id": razorpay_event_id,
            "event_type": raw_event["event_type"],
            "verification": reason,
        },
        status_code=202,
        background=BackgroundTask(_process, raw_event, razorpay_event_id, event_name),
    )


async def health_check(request: Request) -> JSONResponse:
    """Health plus the live safety posture, so it is never a guess what this server will do."""
    return JSONResponse({
        "status": "HEALTHY",
        "engine": "Unified Recovery Engine v1.0.0",
        "posture": config.describe(),
        "feed_counts": ingest.counters(),
    })


async def live_feed(request: Request) -> JSONResponse:
    """Recent decisions, for the dashboard and for eyeballing a live demo."""
    try:
        limit = min(int(request.query_params.get("limit", 50)), 500)
    except ValueError:
        limit = 50
    return JSONResponse({"events": ingest.recent(limit)})



async def metrics(request: Request) -> JSONResponse:
    """Operational counters. What an on-call engineer needs to answer "is it working?".

    Deliberately includes the numbers that reveal SILENT failure — dead letters and stale
    unresolved contacts — because those are the states where the system looks healthy while
    losing money.
    """
    feed = ingest.counters()
    retries = reliability.retry_counters()
    stale = len(reliability.stale_unknown_entries())
    return JSONResponse({
        "feed": feed,
        "retry_queue": retries,
        "dead_letters": retries.get("DEAD_LETTER", 0),
        "stale_unresolved_contacts": stale,
        "active_outages": len(ingest.active_outages()),
        "posture": config.describe(),
        "alerts": [
            a for a in [
                f"{retries.get('DEAD_LETTER', 0)} dead-lettered events need human action"
                if retries.get("DEAD_LETTER") else None,
                f"{stale} contacts unresolved past the reconciliation window"
                if stale else None,
                "DISPATCH IS LIVE" if config.DISPATCH_ENABLED else None,
                "UNSIGNED WEBHOOKS ACCEPTED" if config.ALLOW_UNSIGNED_WEBHOOKS
                and not config.WEBHOOK_SECRET else None,
            ] if a
        ],
    })


async def twiml_recovery(request: Request) -> Response:
    """TwiML for one case, fetched by Twilio when it places the call (ADR-0021).

    PUBLIC BUT NOT OPEN
        Twilio has to reach this without credentials, so it is unauthenticated by
        necessity. The case id alone would therefore let anyone who guessed one hear a
        customer's name and the amount they owe read aloud. The HMAC in the URL is what
        keeps it a phone system rather than a disclosure endpoint.

        A wrong or missing signature returns 403 with no detail. Saying which part failed
        would help an attacker enumerate; the engine that minted the URL never gets it
        wrong.
    """
    case_id = request.query_params.get("case", "")
    signature = request.query_params.get("sig", "")

    if not voice.verify_case(case_id, signature):
        logger.warning("rejected unsigned TwiML request for %r", case_id[:40])
        return PlainTextResponse("forbidden", status_code=403)

    repo = CaseRepository(ingest.get_conn())
    case = repo.get_case(case_id)
    if case is None:
        return PlainTextResponse("not found", status_code=404)

    customer = repo.get_customer(case.merchant_id, case.customer_id)
    message = voice.spoken_message(
        name=(customer.name if customer else ""),
        amount_paise=case.amount_paise,
        due_date=case.due_date,
    )
    return Response(voice.twiml_for(message), media_type="application/xml")


routes = [
    Route("/health", endpoint=health_check, methods=["GET"]),
    Route("/feed", endpoint=live_feed, methods=["GET"]),
    Route("/metrics", endpoint=metrics, methods=["GET"]),
    Route("/webhooks/razorpay", endpoint=handle_razorpay_webhook, methods=["POST"]),
    Route("/twiml/recovery", endpoint=twiml_recovery, methods=["GET", "POST"]),
]

_worker: Optional[reliability.BackgroundWorker] = None


@contextlib.asynccontextmanager
async def _lifespan(app_: Starlette):
    """Run the retry drain and reconciliation sweep for the life of the server."""
    global _worker
    reliability.ensure_schema()
    followup.ensure_schema()
    _worker = reliability.BackgroundWorker(
        process_fn=_retry_item,
        reconcile_fn=_reconcile_stale,
        followup_fn=_run_followup,
        # At demo speed a review falling due in ten seconds must not wait a full minute to
        # be noticed. The default is unchanged at 60s.
        interval_seconds=config.WORKER_INTERVAL_SECONDS,
    )
    _worker.start()
    try:
        yield
    finally:
        _worker.stop()


app = Starlette(debug=False, routes=routes, lifespan=_lifespan)


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    posture = config.describe()
    logger.info("Real-time recovery server starting")
    logger.info("  database        : %s", posture["db_path"])
    logger.info("  signature req'd : %s", posture["signature_required"])
    logger.info("  dispatch enabled: %s", posture["dispatch_enabled"])
    if not posture["dispatch_enabled"]:
        logger.info("  DRY RUN - decisions are recorded, nothing is sent to anyone.")
    uvicorn.run(app, host="127.0.0.1", port=8000)
