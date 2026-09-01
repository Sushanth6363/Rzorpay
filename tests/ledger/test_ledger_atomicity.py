"""Tests for Ledger Atomicity, Transaction Rollback, and Failure Injection (M3-06, M3-07, M3-21)."""

import pytest
import sqlite3
from app.db.init import init_db
from app.domain.enums import ActionType
from app.ledger.engine import ContactLedgerEngine


@pytest.fixture
def db_conn():
    conn = init_db(":memory:")
    yield conn
    conn.close()


def test_m3_06_reservation_ledger_atomicity(db_conn):
    """M3-06: Budget increment and ledger entry creation occur atomically."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")

    entry = engine.reserve_contact(
        customer_id="cust_atom",
        opportunity_id="opp_atom",
        action_type=ActionType.WHATSAPP_LINK,
        intervention_idempotency_key="key_atom",
        cap=1,
    )
    assert entry is not None

    budget = engine.get_customer_budget("cust_atom")
    assert budget.reserved_count == 1

    # Attempt second reservation with cap=1 -> should return None cleanly without partial state
    entry2 = engine.reserve_contact(
        customer_id="cust_atom",
        opportunity_id="opp_atom2",
        action_type=ActionType.SMS_LINK,
        intervention_idempotency_key="key_atom2",
        cap=1,
    )
    assert entry2 is None

    budget_after = engine.get_customer_budget("cust_atom")
    assert budget_after.reserved_count == 1
    assert budget_after.total_active_slots == 1


def test_m3_07_m3_21_transaction_rollback_on_failure(db_conn):
    """M3-07 / M3-21: Transaction rollback on failure injection leaves database consistent."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")
    engine.dal.init_contact_budget("cust_fail", cap=3)

    # Force error by breaking schema table inside custom SQL or simulating ledger failure
    db_conn.execute("DROP TABLE contact_ledger;")

    # Attempt reservation -> ledger insert will fail
    with pytest.raises(sqlite3.OperationalError):
        engine.reserve_contact(
            customer_id="cust_fail",
            opportunity_id="opp_fail",
            action_type=ActionType.EMAIL_LINK,
            intervention_idempotency_key="key_fail",
            cap=3,
        )

    # Recreate table and verify budget count remained 0 because of transaction rollback!
    db_conn.execute("""
        CREATE TABLE contact_ledger (
            ledger_id TEXT NOT NULL, merchant_id TEXT NOT NULL, customer_id TEXT NOT NULL,
            opportunity_id TEXT NOT NULL, action_type TEXT NOT NULL, intervention_idempotency_key TEXT NOT NULL,
            status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            attempted_at TEXT, resolved_at TEXT, metadata_json TEXT DEFAULT '{}',
            PRIMARY KEY (merchant_id, ledger_id)
        );
    """)

    budget = engine.get_customer_budget("cust_fail")
    assert budget.reserved_count == 0  # Counter rollback verified!
