"""Razorpay webhook payload -> canonical engine event (ADR-0018).

The previous mapping was two lines:

    "FAILED_PAYMENT" if "payment" in event_name else "ABANDONED_CHECKOUT"

which collapses every Razorpay event into one of two streams. A `subscription.halted` was
read as a failed payment; an `invoice.expired` became an abandoned checkout. The engine
claims to unify FOUR streams and the live path could only ever produce two of them —
so three quarters of the product was unreachable from real traffic.

This maps Razorpay's actual event vocabulary onto the engine's streams, and pulls the
entity out of the right place in the payload for each one (Razorpay nests the entity under
a different key per event family, which the old code also ignored).

INVARIANT: an unrecognised event returns None. The listener then acknowledges and drops it
rather than guessing a stream — a misfiled event would be silently recovered against the
wrong policy, which is worse than not acting.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.domain.enums import EventType

# Razorpay event name -> engine stream. Prefix matched longest-first, so `payment.failed`
# resolves before the generic `payment.` family.
EVENT_STREAM_MAP = {
    # --- Recovery opportunities ---------------------------------------------------------
    "payment.failed": EventType.FAILED_PAYMENT,
    "payment_link.expired": EventType.ABANDONED_CHECKOUT,
    "payment_link.cancelled": EventType.ABANDONED_CHECKOUT,
    "checkout.abandoned": EventType.ABANDONED_CHECKOUT,
    "subscription.halted": EventType.FAILED_SUBSCRIPTION_RENEWAL,
    "subscription.pending": EventType.FAILED_SUBSCRIPTION_RENEWAL,
    "invoice.expired": EventType.OVERDUE_B2B_INVOICE,
    "invoice.partially_paid": EventType.OVERDUE_B2B_INVOICE,
}

# Money ARRIVED. These are not opportunities and must never be treated as one — chasing a
# customer who has just paid is the phantom recovery Stage 0 exists to prevent. Enumerated
# explicitly so they can never fall through to a family default.
RESOLUTION_EVENTS = frozenset({
    "payment.authorized", "payment.captured",
    "order.paid", "invoice.paid",
    "payment_link.paid", "payment_link.partially_paid",
    "subscription.charged",
})

# Gateway health, not customer debt. These drive the downtime signal (INV-4, D2), not the
# recovery pipeline. Mapping them to an opportunity would invent a failed payment out of an
# infrastructure notice.
DOWNTIME_EVENTS = frozenset({
    "payment.downtime.started",
    "payment.downtime.updated",
    "payment.downtime.resolved",
})

# Which payload key holds the entity, per event family.
ENTITY_KEYS = ("payment", "subscription", "invoice", "payment_link", "order")


def resolve_stream(event_name: str) -> Optional[EventType]:
    """Map a Razorpay event name to an engine stream, or None if it is not recoverable."""
    name = (event_name or "").strip().lower()
    # EXPLICIT ONLY. A family-prefix fallback is unsafe here: `payment.captured` and
    # `payment.authorized` are SUCCESSES, and a fallback on the `payment.` family turned
    # them into FAILED_PAYMENT — the engine would have chased customers who had just paid,
    # which is the exact phantom recovery Stage 0 exists to prevent. `payment.downtime.*`
    # was likewise turned into a failed payment instead of a gateway-health signal.
    # An unenumerated event is dropped, never guessed.
    return EVENT_STREAM_MAP.get(name)


def extract_entity(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Pull the entity out of Razorpay's per-family nesting."""
    container = payload.get("payload", {}) or {}
    for key in ENTITY_KEYS:
        entity = (container.get(key, {}) or {}).get("entity")
        if isinstance(entity, dict) and entity:
            return entity
    return {}


def _iso(created_at: Any) -> str:
    """Razorpay sends epoch seconds. Convert, never invent a placeholder date."""
    if isinstance(created_at, (int, float)) and created_at > 0:
        return datetime.fromtimestamp(float(created_at), tz=timezone.utc).isoformat()
    if isinstance(created_at, str) and created_at.strip():
        return created_at
    return datetime.now(timezone.utc).isoformat()


def map_webhook(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convert a verified Razorpay webhook body into a raw engine event.

    Returns None when the event does not represent recoverable revenue, so the caller can
    acknowledge and drop it instead of manufacturing an opportunity.
    """
    event_name = str(payload.get("event", "")).lower()
    stream = resolve_stream(event_name)
    if stream is None:
        return None

    entity = extract_entity(payload)
    if not entity:
        return None

    entity_id = str(entity.get("id") or "").strip()
    if not entity_id:
        return None

    amount_paise = entity.get("amount") or entity.get("amount_due") or 0
    try:
        amount_paise = int(amount_paise)
    except (TypeError, ValueError):
        amount_paise = 0
    if amount_paise <= 0:
        return None  # nothing at risk; Stage 0 would reject it anyway

    occurred_at = _iso(entity.get("created_at"))

    customer_id = str(
        entity.get("customer_id")
        or entity.get("email")
        or entity.get("contact")
        or f"cust_{entity_id}"
    )

    raw: Dict[str, Any] = {
        "merchant_id": str(payload.get("account_id") or "merch_razorpay_live"),
        "customer_id": customer_id,
        "event_id": entity_id,
        "event_type": stream.value,
        "amount_paise": amount_paise,
        "currency": str(entity.get("currency", "INR")),
        "occurred_at": occurred_at,
        "observed_at": occurred_at,
        "gateway": str(entity.get("bank") or entity.get("wallet") or "razorpay").lower(),
        "razorpay_event": event_name,
    }

    failure_reason = entity.get("error_reason") or entity.get("error_code")
    if failure_reason:
        raw["failure_reason"] = str(failure_reason).upper()

    # B2B receivables carry the facts the TDS derivation needs (ADR-0016). Supplied only
    # when Razorpay actually provides them - a missing figure yields UNDETERMINED, which
    # never suppresses a recovery.
    if stream == EventType.OVERDUE_B2B_INVOICE:
        raw["invoice_status"] = str(entity.get("status", "OVERDUE")).upper()
        paid = entity.get("amount_paid")
        if paid is not None:
            try:
                raw["amount_received_paise"] = int(paid)
            except (TypeError, ValueError):
                pass
        notes = entity.get("notes") or {}
        if isinstance(notes, dict):
            if notes.get("tds_section"):
                raw["tds_section"] = str(notes["tds_section"])
            if notes.get("payee_type"):
                raw["payee_type"] = str(notes["payee_type"])

    return raw
