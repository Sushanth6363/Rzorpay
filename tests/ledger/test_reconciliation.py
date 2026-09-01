"""Tests for Reconciliation Engine Ladder & Idempotency (M3-12, M3-13, M3-24)."""

import pytest
from app.db.init import init_db
from app.domain.enums import ActionType, LedgerStatus
from app.ledger.engine import ContactLedgerEngine


@pytest.fixture
def db_conn():
    conn = init_db(":memory:")
    yield conn
    conn.close()


def test_m3_12_unknown_reconciliation_ladder(db_conn):
    """M3-12: Bounded reconciliation resolves EXECUTION_UNKNOWN to terminal outcomes."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")

    # Case A: Reconcile to DELIVERED -> reserved-1, consumed+1
    entry_a = engine.reserve_contact("cust_recA", "opp_A", ActionType.WHATSAPP_LINK, "key_rec_A")
    engine.mark_execution_unknown(entry_a.ledger_id)
    res_a = engine.reconcile(entry_a.ledger_id, LedgerStatus.RECONCILED_DELIVERED)
    assert res_a is True
    budget_a = engine.get_customer_budget("cust_recA")
    assert budget_a.reserved_count == 0
    assert budget_a.consumed_count == 1

    # Case B: Reconcile to NOT_SENT -> reserved-1 (capacity returned)
    entry_b = engine.reserve_contact("cust_recB", "opp_B", ActionType.SMS_LINK, "key_rec_B")
    engine.mark_execution_unknown(entry_b.ledger_id)
    res_b = engine.reconcile(entry_b.ledger_id, LedgerStatus.RECONCILED_NOT_SENT)
    assert res_b is True
    budget_b = engine.get_customer_budget("cust_recB")
    assert budget_b.reserved_count == 0
    assert budget_b.consumed_count == 0
    assert budget_b.available_slots == 3

    # Case C: Reconcile to UNRESOLVED (fail closed) -> reserved-1, consumed+1
    entry_c = engine.reserve_contact("cust_recC", "opp_C", ActionType.EMAIL_LINK, "key_rec_C")
    engine.mark_execution_unknown(entry_c.ledger_id)
    res_c = engine.reconcile(entry_c.ledger_id, LedgerStatus.RECONCILED_UNRESOLVED)
    assert res_c is True
    budget_c = engine.get_customer_budget("cust_recC")
    assert budget_c.reserved_count == 0
    assert budget_c.consumed_count == 1


def test_m3_13_reconciliation_idempotency(db_conn):
    """M3-13: Re-invoking reconciliation on an already reconciled entry is idempotent."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")
    entry = engine.reserve_contact("cust_idem_rec", "opp_1", ActionType.WHATSAPP_LINK, "key_idem_rec")
    engine.mark_execution_unknown(entry.ledger_id)

    # First reconciliation call
    res1 = engine.reconcile(entry.ledger_id, LedgerStatus.RECONCILED_DELIVERED)
    assert res1 is True

    budget1 = engine.get_customer_budget("cust_idem_rec")
    assert budget1.consumed_count == 1

    # Second reconciliation call
    res2 = engine.reconcile(entry.ledger_id, LedgerStatus.RECONCILED_DELIVERED)
    assert res2 is True

    budget2 = engine.get_customer_budget("cust_idem_rec")
    assert budget2.consumed_count == 1  # Consumed count unchanged!


def test_m3_24_no_slot_leakage(db_conn):
    """M3-24: Full sequence (reserve -> execution unknown -> reconcile -> retry reconcile) causes zero slot leakage."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")
    entry = engine.reserve_contact("cust_leak", "opp_1", ActionType.SMS_LINK, "key_leak", cap=3)

    budget_init = engine.get_customer_budget("cust_leak")
    assert budget_init.reserved_count == 1

    engine.mark_execution_unknown(entry.ledger_id)
    engine.reconcile(entry.ledger_id, LedgerStatus.RECONCILED_NOT_SENT)
    engine.reconcile(entry.ledger_id, LedgerStatus.RECONCILED_NOT_SENT)

    budget_final = engine.get_customer_budget("cust_leak")
    assert budget_final.reserved_count == 0
    assert budget_final.consumed_count == 0
    assert budget_final.available_slots == 3  # Zero slot leakage verified!
