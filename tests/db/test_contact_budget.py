"""Acceptance tests for contact budget invariants, reservation semantics, and constraint enforcement.

Test Coverage:
- M2-15: Normal reservation sequence (cap=3 -> 1, 2, 3 granted)
- M2-16: Cap exhaustion (4th attempt rejected)
- M2-17: Direct DB CHECK constraint attack raises sqlite3.IntegrityError
- M2-18: Transaction rollback on mutation error
"""

import pytest
import sqlite3
from app.db.init import init_db
from app.db.dal import TenantScopedDB


@pytest.fixture
def db_conn():
    conn = init_db(":memory:")
    yield conn
    conn.close()


def test_m2_15_contact_budget_normal_reservation(db_conn) -> None:
    """M2-15: Reserve contact slots sequentially under cap=3."""
    dal = TenantScopedDB(db_conn, merchant_id="merch_1")
    dal.init_contact_budget("cust_1", cap=3)

    assert dal.reserve_contact_slot("cust_1") is True  # Reserved 1
    assert dal.reserve_contact_slot("cust_1") is True  # Reserved 2
    assert dal.reserve_contact_slot("cust_1") is True  # Reserved 3

    budget = dal.get_contact_budget("cust_1")
    assert budget.reserved_count == 3
    assert budget.consumed_count == 0
    assert budget.available_slots == 0


def test_m2_16_contact_cap_exhaustion(db_conn) -> None:
    """M2-16: Cap=3; 4th reservation attempt rejected."""
    dal = TenantScopedDB(db_conn, merchant_id="merch_1")
    dal.init_contact_budget("cust_2", cap=3)

    # 3 normal reservations
    for _ in range(3):
        assert dal.reserve_contact_slot("cust_2") is True

    # 4th reservation rejected
    assert dal.reserve_contact_slot("cust_2") is False

    budget = dal.get_contact_budget("cust_2")
    assert budget.reserved_count == 3

    # Transition 2 to executed, 1 to consumed
    assert dal.mark_reservation_executed("cust_2") is True
    budget_after = dal.get_contact_budget("cust_2")
    assert budget_after.reserved_count == 2
    assert budget_after.consumed_count == 1

    # Total active (2 reserved + 1 consumed = 3 == cap) -> still rejected
    assert dal.reserve_contact_slot("cust_2") is False


def test_m2_17_direct_db_check_constraint_attack(db_conn) -> None:
    """M2-17: Mandatory attack test. Direct SQL INSERT violating reserved+consumed <= cap raises IntegrityError."""
    dal = TenantScopedDB(db_conn, merchant_id="merch_attack")
    dal.init_contact_budget("victim_cust", cap=3)

    # Attempt raw SQL write bypassing application logic with reserved_count=2, consumed_count=2 (total 4 > cap 3)
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        db_conn.execute(
            """
            UPDATE contact_budgets
            SET reserved_count = 2, consumed_count = 2
            WHERE merchant_id = 'merch_attack' AND customer_id = 'victim_cust';
            """
        )


def test_m2_18_transaction_rollback(db_conn) -> None:
    """M2-18: Verify transaction rollback preserves original state when mutation fails."""
    dal = TenantScopedDB(db_conn, merchant_id="merch_rollback")
    dal.init_contact_budget("cust_rb", cap=5)
    dal.reserve_contact_slot("cust_rb")

    budget_before = dal.get_contact_budget("cust_rb")
    assert budget_before.reserved_count == 1

    # Force a transaction error
    try:
        db_conn.execute("BEGIN TRANSACTION;")
        db_conn.execute(
            "UPDATE contact_budgets SET reserved_count = reserved_count + 1 WHERE merchant_id='merch_rollback';"
        )
        # Execute invalid query that crashes transaction
        db_conn.execute("INSERT INTO non_existent_table VALUES (1);")
        db_conn.commit()
    except sqlite3.OperationalError:
        db_conn.rollback()

    budget_after = dal.get_contact_budget("cust_rb")
    assert budget_after.reserved_count == 1  # Unchanged
