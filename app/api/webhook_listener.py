"""Real-Time Razorpay Webhook Ingestion API Server for Unified Recovery Engine.

Provides an HTTP webhook listener (Starlette/Uvicorn) to receive live Razorpay webhooks,
verify HMAC signatures, process events through the 5-stage CatBoost AI engine, and trigger
real Razorpay payment recovery actions.
"""

import json
from typing import Any, Dict
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.domain.enums import ActionType, DataProvenance
from app.integrations.razorpay_client import RazorpayIntegrationClient
from app.orchestration.recovery_orchestrator import RecoveryOrchestrator


razorpay_client = RazorpayIntegrationClient()
orchestrator = RecoveryOrchestrator()


async def handle_razorpay_webhook(request: Request) -> JSONResponse:
    """HTTP POST Webhook Handler for Razorpay Event Notifications."""
    body_bytes = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # Verification check if webhook secret is active
    if razorpay_client.webhook_secret and razorpay_client.webhook_secret != "mock_webhook_secret":
        if not razorpay_client.verify_webhook_signature(body_bytes, signature):
            return JSONResponse({"error": "Invalid Razorpay Webhook Signature"}, status_code=400)

    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception as err:
        return JSONResponse({"error": f"Invalid JSON payload: {str(err)}"}, status_code=400)

    event_name = payload.get("event", "payment.failed")
    event_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    
    # Map Razorpay webhook payload into raw engine format
    merchant_id = payload.get("account_id", event_entity.get("merchant_id", "merch_razorpay_live"))
    customer_id = event_entity.get("customer_id", event_entity.get("email", "cust_live_user"))
    payment_id = event_entity.get("id", "pay_live_001")
    amount_paise = event_entity.get("amount", 1500000)
    failure_reason = event_entity.get("error_code", event_entity.get("error_description", "INSUFFICIENT_FUNDS"))
    gateway = event_entity.get("bank", event_entity.get("wallet", "razorpay"))

    raw_event = {
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "event_id": payment_id,
        "event_type": "FAILED_PAYMENT" if "payment" in event_name else "ABANDONED_CHECKOUT",
        "amount_paise": amount_paise,
        "currency": event_entity.get("currency", "INR"),
        "occurred_at": event_entity.get("created_at", "2026-09-01T10:00:00+00:00"),
        "failure_reason": str(failure_reason).upper(),
        "gateway": str(gateway).lower(),
    }

    # Process through Unified Recovery Engine (5-Stage Pipeline + CatBoost S-Learner)
    recovery_result = orchestrator.process_and_execute(
        raw_event=raw_event,
        arm="A5",
        random_seed=42,
    )

    decision = recovery_result.decision
    selected_action = decision.selected_action

    # Generate Razorpay Payment Link for any active recovery intervention
    payment_link_result: Dict[str, Any] = {}
    if selected_action in (ActionType.RECOMMEND_RETRY, ActionType.WHATSAPP_LINK, ActionType.SMS_LINK, ActionType.EMAIL_LINK):
        payment_link_result = razorpay_client.create_payment_link(
            amount_paise=amount_paise,
            customer_name="Valued Customer",
            customer_email=str(event_entity.get("email", "customer@example.com")),
            customer_contact=str(event_entity.get("contact", "+919876543210")),
            description=f"Recovery link for failed payment {payment_id}",
            reference_id=decision.decision_id,
        )

    response_data = {
        "status": "SUCCESS",
        "razorpay_event": event_name,
        "payment_id": payment_id,
        "engine_decision": {
            "decision_id": decision.decision_id,
            "selected_action": selected_action.value,
            "decision_mode": decision.decision_mode.value,
            "baseline_probability": decision.baseline_probability,
            "selected_action_score": decision.selected_action_score.to_dict() if decision.selected_action_score else None,
        },
        "payment_link_generated": payment_link_result,
        "trace_id": recovery_result.trace_id,
    }

    return JSONResponse(response_data, status_code=200)


async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({"status": "HEALTHY", "engine": "Unified Recovery Engine v1.0.0"})


routes = [
    Route("/health", endpoint=health_check, methods=["GET"]),
    Route("/webhooks/razorpay", endpoint=handle_razorpay_webhook, methods=["POST"]),
]

app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
