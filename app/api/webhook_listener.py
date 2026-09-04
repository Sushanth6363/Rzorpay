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

import json
import logging
import threading
from typing import Any, Dict, Optional

from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.domain.enums import ActionType
from app.integrations.razorpay_client import RazorpayIntegrationClient
from app.orchestration.recovery_orchestrator import RecoveryOrchestrator
from app.realtime import config, ingest
from app.realtime.event_mapper import map_webhook

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
    """Orchestrator for this thread, bound to the durable shared database."""
    orch = getattr(_LOCAL, "orchestrator", None)
    if orch is None:
        orch = RecoveryOrchestrator(db_conn=ingest.get_conn())
        _LOCAL.orchestrator = orch
    return orch


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


def _process(raw_event: Dict[str, Any], razorpay_event_id: str, event_name: str) -> None:
    """Run the engine and dispatch. Executes AFTER the response is sent."""
    try:
        result = get_orchestrator().process_and_execute(
            raw_event=raw_event,
            arm="A5",
            random_seed=None,  # live traffic is not a replay; no determinism seed
        )
    except Exception:
        logger.exception("engine failed for %s", razorpay_event_id)
        ingest.record(
            razorpay_event_id=razorpay_event_id, razorpay_event=event_name,
            status="ENGINE_ERROR", raw_event=raw_event,
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


routes = [
    Route("/health", endpoint=health_check, methods=["GET"]),
    Route("/feed", endpoint=live_feed, methods=["GET"]),
    Route("/webhooks/razorpay", endpoint=handle_razorpay_webhook, methods=["POST"]),
]

app = Starlette(debug=False, routes=routes)


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
