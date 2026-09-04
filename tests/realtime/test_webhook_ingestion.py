"""Real-time webhook ingestion (ADR-0018).

These tests cover the three properties that separate a live endpoint from a demo script:
it refuses traffic it cannot authenticate, it survives Razorpay's retries without
contacting anyone twice, and it can actually reach all four recovery streams.
"""

import hashlib
import hmac
import importlib
import json

import pytest

from app.domain.enums import EventType
from app.realtime.event_mapper import map_webhook, resolve_stream

SECRET = "test_secret_123"


def _event(name: str, key: str, entity: dict) -> dict:
    return {"event": name, "account_id": "acc_test", "payload": {key: {"entity": entity}}}


# --- Stream mapping: the live path must reach all four streams --------------------------


@pytest.mark.parametrize(
    "event_name, key, expected",
    [
        ("payment.failed", "payment", EventType.FAILED_PAYMENT),
        ("payment_link.expired", "payment_link", EventType.ABANDONED_CHECKOUT),
        ("subscription.halted", "subscription", EventType.FAILED_SUBSCRIPTION_RENEWAL),
        ("invoice.partially_paid", "invoice", EventType.OVERDUE_B2B_INVOICE),
    ],
)
def test_all_four_streams_are_reachable_from_real_webhooks(event_name, key, expected):
    """The old mapping produced only two streams, making half the product unreachable live."""
    raw = map_webhook(_event(event_name, key, {"id": "ent_1", "amount": 250000, "created_at": 1767225600}))

    assert raw is not None
    assert raw["event_type"] == expected.value


def test_a_successful_event_is_not_a_recovery_opportunity():
    """`subscription.charged` succeeded. Manufacturing an opportunity from it would chase a paid bill."""
    assert resolve_stream("subscription.charged") is None
    assert map_webhook(_event("subscription.charged", "subscription", {"id": "s1", "amount": 500})) is None


def test_an_unrecognised_event_is_dropped_rather_than_guessed():
    """A misfiled event would be recovered under the wrong policy — worse than not acting."""
    assert resolve_stream("account.updated") is None
    assert map_webhook(_event("account.updated", "payment", {"id": "x", "amount": 100})) is None


def test_zero_amount_is_not_revenue_at_risk():
    assert map_webhook(_event("payment.failed", "payment", {"id": "p", "amount": 0})) is None


def test_epoch_timestamps_are_converted_not_replaced_with_a_placeholder():
    """Razorpay sends epoch seconds; the old code fell back to a hardcoded 2026 date."""
    raw = map_webhook(_event("payment.failed", "payment", {"id": "p", "amount": 1000, "created_at": 1767225600}))

    assert raw["occurred_at"].startswith("2026-01-01")
    assert raw["observed_at"] == raw["occurred_at"]


def test_b2b_invoice_carries_the_facts_the_tds_derivation_needs():
    """Without amount_paid and the section, the withholding position cannot be derived."""
    raw = map_webhook(_event("invoice.partially_paid", "invoice", {
        "id": "inv_1", "amount": 10_000_000, "amount_paid": 9_000_000,
        "created_at": 1767225600, "status": "partially_paid",
        "notes": {"tds_section": "194J", "payee_type": "COMPANY"},
    }))

    assert raw["amount_received_paise"] == 9_000_000
    assert raw["tds_section"] == "194J"
    assert raw["payee_type"] == "COMPANY"


def test_entity_is_found_under_each_razorpay_family_key():
    """Razorpay nests the entity under a different key per family; the old code read only `payment`."""
    raw = map_webhook(_event("invoice.expired", "invoice", {"id": "i1", "amount": 5000, "created_at": 1767225600}))

    assert raw is not None and raw["event_id"] == "i1"


# --- Security: the endpoint must fail closed --------------------------------------------


@pytest.fixture()
def listener(monkeypatch):
    """Reload the listener with a known webhook secret configured."""
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", SECRET)
    monkeypatch.setenv("ALLOW_UNSIGNED_WEBHOOKS", "0")
    from app.realtime import config as cfg
    importlib.reload(cfg)
    import app.api.webhook_listener as wl
    importlib.reload(wl)
    wl.razorpay_client.webhook_secret = SECRET
    return wl


def test_a_forged_signature_is_rejected(listener):
    body = json.dumps(_event("payment.failed", "payment", {"id": "p", "amount": 1000})).encode()

    ok, reason = listener._verify(body, "deadbeef")

    assert ok is False
    assert "invalid signature" in reason


def test_a_valid_signature_is_accepted(listener):
    body = json.dumps(_event("payment.failed", "payment", {"id": "p", "amount": 1000})).encode()
    sig = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()

    ok, _ = listener._verify(body, sig)

    assert ok is True


def test_missing_secret_refuses_traffic_instead_of_opening_the_door(monkeypatch):
    """The original code SKIPPED verification when unconfigured, so any POST ran the engine.

    An unauthenticated endpoint that mints payment links is a way to make someone else's
    engine contact strangers. Absent configuration must be a refusal.
    """
    monkeypatch.delenv("RAZORPAY_WEBHOOK_SECRET", raising=False)
    monkeypatch.setenv("ALLOW_UNSIGNED_WEBHOOKS", "0")
    from app.realtime import config as cfg
    importlib.reload(cfg)
    import app.api.webhook_listener as wl
    importlib.reload(wl)

    ok, reason = wl._verify(b"{}", "")

    assert ok is False
    assert "not configured" in reason


# --- Dispatch gates: nothing leaves the process by accident ------------------------------


def test_dispatch_is_off_by_default(monkeypatch):
    monkeypatch.delenv("RECOVERY_DISPATCH_ENABLED", raising=False)
    from app.realtime import config as cfg
    importlib.reload(cfg)

    allowed, reason = cfg.dispatch_permitted("rzp_test_abc")

    assert allowed is False
    assert "DRY_RUN" in reason


def test_live_credentials_need_a_second_explicit_acknowledgement(monkeypatch):
    """Enabling dispatch must not be enough to start charging real customers."""
    monkeypatch.setenv("RECOVERY_DISPATCH_ENABLED", "1")
    monkeypatch.delenv("RECOVERY_ALLOW_LIVE_CREDENTIALS", raising=False)
    from app.realtime import config as cfg
    importlib.reload(cfg)

    allowed, reason = cfg.dispatch_permitted("rzp_live_realkey")

    assert allowed is False
    assert "REFUSED" in reason


# --- Idempotency: Razorpay retries until it gets a 2xx -----------------------------------


@pytest.fixture()
def feed(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOVERY_DB_PATH", str(tmp_path / "rt.db"))
    from app.realtime import config as cfg
    importlib.reload(cfg)
    from app.realtime import ingest as ing
    importlib.reload(ing)
    return ing


def test_a_redelivered_event_is_recognised(feed):
    """Without this, a retry means a second message and a second slot off the budget."""
    assert feed.already_seen("evt_1") is False

    feed.record(razorpay_event_id="evt_1", razorpay_event="payment.failed", status="ACCEPTED")

    assert feed.already_seen("evt_1") is True


def test_a_delivery_advances_in_place_rather_than_duplicating(feed):
    """One row per delivery. INSERT OR IGNORE would silently DROP the completion, leaving
    every event displayed as ACCEPTED forever."""
    feed.record(
        razorpay_event_id="evt_2", razorpay_event="payment.failed", status="ACCEPTED",
        raw_event={"merchant_id": "m1", "event_type": "FAILED_PAYMENT", "amount_paise": 5000},
    )
    feed.record(
        razorpay_event_id="evt_2", razorpay_event="payment.failed", status="PROCESSED",
        selected_action="SMS_LINK", dispatch_state="SUPPRESSED",
    )

    rows = feed.recent(10)
    assert len(rows) == 1
    row = rows[0]
    assert row["status"] == "PROCESSED"
    assert row["selected_action"] == "SMS_LINK"
    # Fields from the first pass survive the second.
    assert row["event_type"] == "FAILED_PAYMENT"
    assert row["amount_paise"] == 5000
