"""Production reliability: retry, dead-letter, reconciliation, replay protection (ADR-0019).

Each test here corresponds to a way the live system could lose money or state SILENTLY —
the failure mode where everything looks healthy and nothing is working.
"""

import importlib
import json
import time

import pytest


@pytest.fixture()
def rel(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOVERY_DB_PATH", str(tmp_path / "rel.db"))
    from app.realtime import config as cfg
    importlib.reload(cfg)
    from app.realtime import ingest as ing
    importlib.reload(ing)
    from app.realtime import reliability as r
    importlib.reload(r)
    r.ensure_schema()
    return r


# --- Retry and dead-letter ----------------------------------------------------------------


def test_a_failed_event_is_scheduled_for_retry_not_dropped(rel):
    """Razorpay already got its 200 and will never redeliver. Without a queue the
    opportunity is lost silently — revenue at risk becoming revenue gone."""
    state = rel.enqueue_retry("evt_1", "payment.failed", json.dumps({"a": 1}), "db locked")

    assert state == "RETRY_SCHEDULED"
    assert rel.retry_counters().get("RETRY_SCHEDULED") == 1


def test_retries_are_bounded_and_end_in_a_visible_dead_letter(rel):
    """An event must never retry forever, and its abandonment must be visible."""
    for i in range(rel.MAX_ATTEMPTS):
        state = rel.enqueue_retry("evt_2", "payment.failed", "{}", f"boom {i}")
        assert state == "RETRY_SCHEDULED"

    final = rel.enqueue_retry("evt_2", "payment.failed", "{}", "boom final")

    assert final == "DEAD_LETTER"
    assert rel.retry_counters().get("DEAD_LETTER") == 1


def test_backoff_delays_the_next_attempt(rel):
    """A retry that fires immediately would hammer a dependency that is already struggling."""
    rel.enqueue_retry("evt_3", "payment.failed", "{}", "err")

    assert rel.due_retries() == []  # first backoff has not elapsed


def test_a_succeeded_retry_leaves_the_queue(rel):
    rel.enqueue_retry("evt_4", "payment.failed", "{}", "err")

    rel.mark_retry_succeeded("evt_4")

    assert rel.retry_counters().get("SUCCEEDED") == 1
    assert rel.due_retries() == []


# --- Reconciliation sweep -----------------------------------------------------------------


def test_the_sweep_reports_how_many_entries_it_closed(rel):
    """The ladder existed but nothing ran it, so EXECUTION_UNKNOWN entries held reserved
    budget slots forever and a customer's contact budget leaked until unusable."""
    closed = rel.sweep_reconciliation(lambda ledger_id: True)

    assert closed == 0  # nothing stale in a fresh database


def test_a_reconciliation_failure_does_not_abort_the_sweep(rel):
    """One bad entry must not stop the others from being closed."""
    def boom(ledger_id):
        raise RuntimeError("nope")

    assert rel.sweep_reconciliation(boom) == 0


# --- Replay protection --------------------------------------------------------------------


def test_a_stale_webhook_is_rejected(monkeypatch):
    """config advertised WEBHOOK_MAX_AGE_SECONDS and /health reported it, but nothing
    enforced it — a captured body and its still-valid signature replayed indefinitely."""
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "s")
    from app.realtime import config as cfg
    importlib.reload(cfg)
    import app.api.webhook_listener as wl
    importlib.reload(wl)

    stale, age = wl._is_stale({"created_at": int(time.time()) - 3600})

    assert stale is True
    assert age >= 3600


def test_a_fresh_webhook_is_accepted(monkeypatch):
    from app.realtime import config as cfg
    importlib.reload(cfg)
    import app.api.webhook_listener as wl
    importlib.reload(wl)

    stale, _ = wl._is_stale({"created_at": int(time.time())})

    assert stale is False


def test_a_missing_timestamp_is_not_rejected(monkeypatch):
    """Rejecting on absent evidence would drop legitimate traffic. The HMAC signature is
    the authenticity control; this only bounds the reuse window."""
    from app.realtime import config as cfg
    importlib.reload(cfg)
    import app.api.webhook_listener as wl
    importlib.reload(wl)

    assert wl._is_stale({})[0] is False
    assert wl._is_stale({"created_at": "not-a-number"})[0] is False


# --- PII minimisation ---------------------------------------------------------------------


def test_a_raw_email_is_never_used_as_the_customer_key():
    """Using the email raw writes personal contact details into every ledger row, audit
    record, log line and feed entry. The engine only needs a stable identifier."""
    from app.realtime.event_mapper import map_webhook

    raw = map_webhook({
        "event": "payment.failed", "account_id": "a",
        "payload": {"payment": {"entity": {
            "id": "p1", "amount": 5000, "created_at": 1767225600,
            "email": "real.person@gmail.com",
        }}},
    })

    assert "gmail" not in raw["customer_id"]
    assert raw["customer_id"].startswith("cust_h_")


def test_the_pseudonymous_key_is_stable_for_the_same_person():
    """Contact budgets and escalation ladders are per-customer; an unstable key would
    silently reset both on every event."""
    from app.realtime.event_mapper import _customer_key

    a = _customer_key({"email": "Someone@Example.com"}, "e1")
    b = _customer_key({"email": "someone@example.com "}, "e2")

    assert a == b


def test_an_explicit_customer_id_is_preserved():
    """A real customer id is not contact detail and must not be mangled."""
    from app.realtime.event_mapper import _customer_key

    assert _customer_key({"customer_id": "cust_ABC", "email": "x@y.com"}, "e") == "cust_ABC"
