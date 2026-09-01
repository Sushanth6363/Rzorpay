"""Tests for Contact Cap Preservation, Audit Trail Reconstructability, and Injectable Timestamps (M3-17, M3-22, M3-23)."""

import pytest
import sqlite3
from app.db.init import init_db
from app.domain.enums import ActionType, LedgerStatus
from app.ledger.engine import ContactLedgerEngine
from app.clock import FakeClock


@pytest.fixture
def db_conn():
    conn = init_db(":memory:")
    yield conn
    conn.close()


def test_m3_17_contact_cap_preservation_under_transitions(db_conn):
    """M3-17: Contact cap invariant reserved + consumed <= cap holds under all state transitions."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")
    customer_id = "cust_cap_test"
    cap = 2

    # Reserve 2 slots (cap full)
    e1 = engine.reserve_contact(customer_id, "opp_1", ActionType.WHATSAPP_LINK, "key_1", cap=cap)
    e2 = engine.reserve_contact(customer_id, "opp_2", ActionType.SMS_LINK, "key_2", cap=cap)
    assert e1 is not None and e2 is not None

    # 3rd reservation rejected
    e3 = engine.reserve_contact(customer_id, "opp_3", ActionType.EMAIL_LINK, "key_3", cap=cap)
    assert e3 is None

    # Transition e1 to EXECUTED (reserved=1, consumed=1)
    engine.record_execution_result(e1.ledger_id, success=True)
    budget = engine.get_customer_budget(customer_id)
    assert budget.reserved_count == 1
    assert budget.consumed_count == 1
    assert budget.total_active_slots == 2

    # Attempt raw DB attack to exceed cap -> database CHECK constraint aborts
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            "UPDATE contact_budgets SET reserved_count = 2 WHERE merchant_id = ? AND customer_id = ?",
            ("merch_01", customer_id),
        )


def test_m3_22_audit_trail_reconstruction(db_conn):
    """M3-22: Complete audit trail is reconstructable from audit_logs table."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")
    customer_id = "cust_audit"

    entry = engine.reserve_contact(customer_id, "opp_audit", ActionType.WHATSAPP_LINK, "key_audit")
    engine.record_execution_attempt(entry.ledger_id)
    engine.record_execution_result(entry.ledger_id, success=True)

    cursor = db_conn.execute(
        "SELECT action, entity_type, entity_id, timestamp FROM audit_logs WHERE merchant_id = ? ORDER BY timestamp ASC",
        ("merch_01",),
    )
    logs = cursor.fetchall()
    assert len(logs) >= 3

    actions = [row["action"] for row in logs]
    assert "RESERVE" in actions
    assert LedgerStatus.EXECUTION_ATTEMPTED.value in actions
    assert LedgerStatus.EXECUTED.value in actions


def test_m3_23_injectable_timestamps(db_conn):
    """M3-23: FakeClock injects deterministic timestamps into all ledger entries and audit records."""
    clock = FakeClock("2026-09-01T08:00:00Z")
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01", clock=clock)

    entry = engine.reserve_contact("cust_clock", "opp_clock", ActionType.SMS_LINK, "key_clock")
    assert entry.created_at == "2026-09-01T08:00:00+00:00"

    clock.advance(300)  # Advance 5 minutes
    engine.record_execution_result(entry.ledger_id, success=True)

    updated = engine.get_ledger_entry(entry.ledger_id)
    assert updated.resolved_at == "2026-09-01T08:05:00+00:00"

