"""Tests for Execution State Transitions, Invariant Enforcement, and Anti-Double-Counting (M3-08, M3-09, M3-10, M3-11, M3-14, M3-15, M3-16)."""

import pytest
from app.db.init import init_db
from app.domain.enums import ActionType, LedgerStatus
from app.ledger.engine import ContactLedgerEngine


@pytest.fixture
def db_conn():
    conn = init_db(":memory:")
    yield conn
    conn.close()


def test_m3_08_execution_attempt_transition(db_conn):
    """M3-08: Transition to EXECUTION_ATTEMPTED updates state without modifying counters."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")
    entry = engine.reserve_contact("cust_exec", "opp_1", ActionType.WHATSAPP_LINK, "k1")

    res = engine.record_execution_attempt(entry.ledger_id)
    assert res is True

    updated = engine.get_ledger_entry(entry.ledger_id)
    assert updated.status == LedgerStatus.EXECUTION_ATTEMPTED
    assert updated.attempted_at is not None

    budget = engine.get_customer_budget("cust_exec")
    assert budget.reserved_count == 1
    assert budget.consumed_count == 0


def test_m3_09_confirmed_execution_transition(db_conn):
    """M3-09: Confirmed execution transitions reserved slot to consumed count."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")
    entry = engine.reserve_contact("cust_exec", "opp_1", ActionType.WHATSAPP_LINK, "k2")

    res = engine.record_execution_result(entry.ledger_id, success=True)
    assert res is True

    updated = engine.get_ledger_entry(entry.ledger_id)
    assert updated.status == LedgerStatus.EXECUTED

    budget = engine.get_customer_budget("cust_exec")
    assert budget.reserved_count == 0
    assert budget.consumed_count == 1


def test_m3_10_failed_execution_transition(db_conn):
    """M3-10: Failed execution (non-ambiguous) transitions reserved slot to consumed count (failed-closed)."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")
    entry = engine.reserve_contact("cust_exec", "opp_1", ActionType.SMS_LINK, "k3")

    res = engine.record_execution_result(entry.ledger_id, success=False)
    assert res is True

    updated = engine.get_ledger_entry(entry.ledger_id)
    assert updated.status == LedgerStatus.FAILED_CLOSED

    budget = engine.get_customer_budget("cust_exec")
    assert budget.reserved_count == 0
    assert budget.consumed_count == 1


def test_m3_11_execution_unknown_transition(db_conn):
    """M3-11: EXECUTION_UNKNOWN holds slot in reserved_count without consuming or releasing."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")
    entry = engine.reserve_contact("cust_exec", "opp_1", ActionType.EMAIL_LINK, "k4")

    res = engine.mark_execution_unknown(entry.ledger_id)
    assert res is True

    updated = engine.get_ledger_entry(entry.ledger_id)
    assert updated.status == LedgerStatus.EXECUTION_UNKNOWN

    budget = engine.get_customer_budget("cust_exec")
    assert budget.reserved_count == 1  # Slot remains held in reserved_count!
    assert budget.consumed_count == 0


def test_m3_14_invalid_state_transition_rejection(db_conn):
    """M3-14: Invalid state transitions are strictly rejected."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")
    entry = engine.reserve_contact("cust_inv", "opp_1", ActionType.WHATSAPP_LINK, "k5")

    # Mark executed (terminal)
    engine.record_execution_result(entry.ledger_id, success=True)

    # Attempt illegal transition: EXECUTED -> RESERVED
    res = engine.dal.transition_ledger_status(entry.ledger_id, target_status=LedgerStatus.RESERVED)
    assert res is False

    # Attempt illegal transition: EXECUTED -> RELEASED
    res2 = engine.release_reservation(entry.ledger_id)
    assert res2 is False


def test_m3_15_no_double_consumption(db_conn):
    """M3-15: Repeated execution processing does not cause double consumption."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")
    entry = engine.reserve_contact("cust_dc", "opp_1", ActionType.WHATSAPP_LINK, "k6")

    engine.record_execution_result(entry.ledger_id, success=True)
    budget1 = engine.get_customer_budget("cust_dc")
    assert budget1.consumed_count == 1

    # Attempt duplicate execution processing
    res = engine.record_execution_result(entry.ledger_id, success=True)
    assert res is True  # Idempotent True returned

    budget2 = engine.get_customer_budget("cust_dc")
    assert budget2.consumed_count == 1  # Consumed count remains strictly 1!


def test_m3_16_no_double_release(db_conn):
    """M3-16: Repeated release requests do not decrement capacity twice."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")
    entry = engine.reserve_contact("cust_dr", "opp_1", ActionType.WHATSAPP_LINK, "k7")

    engine.release_reservation(entry.ledger_id)
    budget1 = engine.get_customer_budget("cust_dr")
    assert budget1.reserved_count == 0

    # Attempt duplicate release
    res = engine.release_reservation(entry.ledger_id)
    assert res is True  # Idempotent True

    budget2 = engine.get_customer_budget("cust_dr")
    assert budget2.reserved_count == 0
