"""Acceptance tests for multi-threaded / multi-worker concurrent database reservation safety.

Test Coverage:
- M2-19: Concurrent reservation safety (10 workers competing for cap=5 slots)
"""

import os
import tempfile
import concurrent.futures
import pytest
from app.db.init import init_db, get_db_connection
from app.db.dal import TenantScopedDB


def test_m2_19_concurrent_reservation_safety() -> None:
    """M2-19: MANDATORY CONCURRENCY ACCEPATANCE TEST.

    10 concurrent worker threads attempt to reserve contact slots for cap=5.
    Asserts exact cap enforcement: exactly 5 granted, 5 rejected, reserved_count <= 5.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        # Initialize DB in WAL mode
        init_conn = init_db(db_path)
        dal_init = TenantScopedDB(init_conn, merchant_id="merch_concurrent")
        dal_init.init_contact_budget("cust_concurrent", cap=5)
        init_conn.close()

        def worker_attempt(worker_id: int) -> bool:
            # Each worker gets its own connection to the WAL database file
            conn = get_db_connection(db_path)
            dal = TenantScopedDB(conn, merchant_id="merch_concurrent")
            try:
                granted = dal.reserve_contact_slot("cust_concurrent")
                return granted
            finally:
                conn.close()


        # Launch 10 worker threads simultaneously
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker_attempt, i) for i in range(10)]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        print(f"\nEXECUTED RESULTS: {results}")
        successful_reservations = sum(1 for r in results if r is True)
        rejected_reservations = sum(1 for r in results if r is False)

        # Verify assertions
        assert successful_reservations == 5, f"Expected 5 successful, got {successful_reservations}. Full results: {results}"

        assert rejected_reservations == 5

        # Inspect final database counter state
        check_conn = init_db(db_path)
        dal_check = TenantScopedDB(check_conn, merchant_id="merch_concurrent")
        budget = dal_check.get_contact_budget("cust_concurrent")
        check_conn.close()

        assert budget is not None
        assert budget.reserved_count == 5
        assert budget.reserved_count + budget.consumed_count <= 5

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
