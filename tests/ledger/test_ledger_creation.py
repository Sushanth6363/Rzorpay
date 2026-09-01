"""Tests for Contact Ledger Creation, Isolation, and Round-trip Persistence (M3-01, M3-02, M3-03)."""

import pytest
import sqlite3
from app.db.init import init_db
from app.db.dal import TenantScopeViolation
from app.domain.enums import ActionType, LedgerStatus
from app.ledger.engine import ContactLedgerEngine
from app.clock import FakeClock


@pytest.fixture
def db_conn():
    conn = init_db(":memory:")
    yield conn
    conn.close()


def test_m3_01_ledger_creation(db_conn):
    """M3-01: Ledger creation creates record and updates budget counters."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")
    entry = engine.reserve_contact(
        customer_id="cust_100",
        opportunity_id="opp_100",
        action_type=ActionType.WHATSAPP_LINK,
        intervention_idempotency_key="key_100",
        cap=3,
    )
    assert entry is not None
    assert entry.merchant_id == "merch_01"
    assert entry.customer_id == "cust_100"
    assert entry.status == LedgerStatus.RESERVED

    budget = engine.get_customer_budget("cust_100")
    assert budget is not None
    assert budget.reserved_count == 1
    assert budget.consumed_count == 0
    assert budget.available_slots == 2


def test_m3_02_ledger_tenant_isolation(db_conn):
    """M3-02: Tenant isolation prevents cross-tenant access to ledger entries."""
    engine_a = ContactLedgerEngine(db_conn, merchant_id="merch_A")
    engine_b = ContactLedgerEngine(db_conn, merchant_id="merch_B")

    entry_a = engine_a.reserve_contact(
        customer_id="cust_same",
        opportunity_id="opp_A",
        action_type=ActionType.SMS_LINK,
        intervention_idempotency_key="key_shared",
        cap=3,
    )
    assert entry_a is not None

    # Merchant B should not see Merchant A's ledger entry
    entry_b_read = engine_b.get_ledger_entry(entry_a.ledger_id)
    assert entry_b_read is None

    # Merchant B should have independent budget for cust_same
    budget_b = engine_b.get_customer_budget("cust_same")
    assert budget_b is None or budget_b.reserved_count == 0

    # Unscoped cross-tenant access directly via DAL raises TenantScopeViolation
    with pytest.raises(TenantScopeViolation):
        engine_a.dal._verify_tenant_match("merch_B")


def test_m3_03_ledger_persistence_round_trip(db_conn):
    """M3-03: Ledger entry round-trip persistence with 100% data fidelity."""
    clock = FakeClock("2026-09-01T12:00:00Z")
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01", clock=clock)

    entry = engine.reserve_contact(
        customer_id="cust_rt",
        opportunity_id="opp_rt",
        action_type=ActionType.EMAIL_LINK,
        intervention_idempotency_key="key_rt",
        cap=3,
    )
    assert entry is not None

    retrieved = engine.get_ledger_entry(entry.ledger_id)
    assert retrieved is not None
    assert retrieved.ledger_id == entry.ledger_id
    assert retrieved.merchant_id == "merch_01"
    assert retrieved.customer_id == "cust_rt"
    assert retrieved.opportunity_id == "opp_rt"
    assert retrieved.action_type == ActionType.EMAIL_LINK
    assert retrieved.intervention_idempotency_key == "key_rt"
    assert retrieved.status == LedgerStatus.RESERVED
    assert retrieved.created_at == "2026-09-01T12:00:00+00:00"

