"""Tests for Multi-threaded Concurrency and Cross-tenant Isolation on Contact Ledger (M3-18, M3-19, M3-20)."""

import os
import tempfile
import pytest
from concurrent.futures import ThreadPoolExecutor
from app.db.init import init_db, get_db_connection
from app.domain.enums import ActionType
from app.ledger.engine import ContactLedgerEngine


@pytest.fixture
def db_path():
    tmp_dir = tempfile.mkdtemp()
    db_file = os.path.join(tmp_dir, "test_ledger_concurrency.db")
    conn = init_db(db_file)
    conn.close()
    yield db_file
    try:
        os.remove(db_file)
    except OSError:
        pass


def _worker_same_key(db_path: str, merchant_id: str, customer_id: str, idempotency_key: str):
    conn = get_db_connection(db_path)
    engine = ContactLedgerEngine(conn, merchant_id=merchant_id)
    entry = engine.reserve_contact(
        customer_id=customer_id,
        opportunity_id="opp_concurrent_same",
        action_type=ActionType.WHATSAPP_LINK,
        intervention_idempotency_key=idempotency_key,
        cap=3,
    )
    conn.close()
    return entry


def test_m3_18_concurrent_same_intervention_reservation(db_path):
    """M3-18: 10 concurrent threads reserving identical intervention idempotency key produce 1 slot allocation."""
    merchant_id = "merch_conc_same"
    customer_id = "cust_conc_same"
    key = "same_key_999"

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(_worker_same_key, db_path, merchant_id, customer_id, key)
            for _ in range(10)
        ]
        results = [f.result() for f in futures]

    # All 10 threads receive a valid entry
    assert all(r is not None for r in results)
    ledger_ids = {r.ledger_id for r in results}
    assert len(ledger_ids) == 1  # Exactly ONE unique ledger record created!

    # Check budget
    conn = get_db_connection(db_path)
    engine = ContactLedgerEngine(conn, merchant_id=merchant_id)
    budget = engine.get_customer_budget(customer_id)
    conn.close()

    assert budget.reserved_count == 1
    assert budget.consumed_count == 0


def _worker_distinct_key(db_path: str, merchant_id: str, customer_id: str, worker_id: int, cap: int):
    conn = get_db_connection(db_path)
    engine = ContactLedgerEngine(conn, merchant_id=merchant_id)
    entry = engine.reserve_contact(
        customer_id=customer_id,
        opportunity_id=f"opp_worker_{worker_id}",
        action_type=ActionType.SMS_LINK,
        intervention_idempotency_key=f"distinct_key_worker_{worker_id}",
        cap=cap,
    )
    conn.close()
    return entry


def test_m3_19_concurrent_different_interventions_reservation(db_path):
    """M3-19: 10 concurrent threads reserving distinct intervention keys under cap=5 grant exactly 5 reservations."""
    merchant_id = "merch_conc_diff"
    customer_id = "cust_conc_diff"
    cap = 5

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(_worker_distinct_key, db_path, merchant_id, customer_id, i, cap)
            for i in range(10)
        ]
        results = [f.result() for f in futures]

    granted = [r for r in results if r is not None]
    rejected = [r for r in results if r is None]

    assert len(granted) == cap  # Exactly 5 granted
    assert len(rejected) == 5   # Exactly 5 rejected

    conn = get_db_connection(db_path)
    engine = ContactLedgerEngine(conn, merchant_id=merchant_id)
    budget = engine.get_customer_budget(customer_id)
    conn.close()

    assert budget.reserved_count == 5
    assert budget.total_active_slots == 5


def _worker_tenant(db_path: str, merchant_id: str, customer_id: str, worker_id: int):
    conn = get_db_connection(db_path)
    engine = ContactLedgerEngine(conn, merchant_id=merchant_id)
    entry = engine.reserve_contact(
        customer_id=customer_id,
        opportunity_id=f"opp_{merchant_id}_{worker_id}",
        action_type=ActionType.EMAIL_LINK,
        intervention_idempotency_key=f"key_{merchant_id}_{worker_id}",
        cap=3,
    )
    conn.close()
    return entry


def test_m3_20_cross_tenant_concurrent_isolation(db_path):
    """M3-20: Concurrent reservations for Merchant A and Merchant B targeting same customer_id maintain isolated budgets."""
    customer_id = "shared_customer_123"

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures_a = [
            executor.submit(_worker_tenant, db_path, "merchant_alpha", customer_id, i)
            for i in range(3)
        ]
        futures_b = [
            executor.submit(_worker_tenant, db_path, "merchant_beta", customer_id, i)
            for i in range(3)
        ]
        results_a = [f.result() for f in futures_a]
        results_b = [f.result() for f in futures_b]

    assert all(r is not None for r in results_a)
    assert all(r is not None for r in results_b)

    conn = get_db_connection(db_path)
    engine_a = ContactLedgerEngine(conn, merchant_id="merchant_alpha")
    engine_b = ContactLedgerEngine(conn, merchant_id="merchant_beta")

    budget_a = engine_a.get_customer_budget(customer_id)
    budget_b = engine_b.get_customer_budget(customer_id)
    conn.close()

    assert budget_a.reserved_count == 3
    assert budget_b.reserved_count == 3
