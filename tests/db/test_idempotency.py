"""Acceptance tests for event deduplication and idempotency.

Test Coverage:
- M2-11: Duplicate event ingestion deduplication within tenant scope
- Same idempotency key for different merchants coexists cleanly
"""

import pytest
from app.db.init import init_db
from app.db.dal import TenantScopedDB
from app.domain.enums import EventType, EventSource
from app.domain.models import EventLog


@pytest.fixture
def db_conn():
    conn = init_db(":memory:")
    yield conn
    conn.close()


def test_m2_11_duplicate_event_idempotency(db_conn) -> None:
    """M2-11: Verify duplicate event with same merchant_id + idempotency_key is ignored."""
    dal_a = TenantScopedDB(db_conn, merchant_id="merch_10")
    
    event1 = EventLog(
        event_id="evt_001",
        merchant_id="merch_10",
        source_event_id="src_999",
        event_type=EventType.FAILED_PAYMENT,
        source=EventSource.RAZORPAY_TEST,
        payload_json='{"amount": 1000}',
        idempotency_key="idempotency_key_abc_123",
    )

    # First ingestion succeeds
    assert dal_a.save_event_if_new(event1) is True

    # Duplicate ingestion with same idempotency key returns False (ignored)
    event1_dup = EventLog(
        event_id="evt_002",
        merchant_id="merch_10",
        source_event_id="src_999",
        event_type=EventType.FAILED_PAYMENT,
        source=EventSource.RAZORPAY_TEST,
        payload_json='{"amount": 1000}',
        idempotency_key="idempotency_key_abc_123",
    )
    assert dal_a.save_event_if_new(event1_dup) is False


def test_merchant_scoped_idempotency(db_conn) -> None:
    """Verify same idempotency key across different merchants is allowed."""
    dal_a = TenantScopedDB(db_conn, merchant_id="merch_A")
    dal_b = TenantScopedDB(db_conn, merchant_id="merch_B")

    event_a = EventLog(
        event_id="evt_a",
        merchant_id="merch_A",
        source_event_id="src_1",
        event_type=EventType.FAILED_PAYMENT,
        source=EventSource.RAZORPAY_TEST,
        payload_json='{}',
        idempotency_key="shared_idempotency_key",
    )
    event_b = EventLog(
        event_id="evt_b",
        merchant_id="merch_B",
        source_event_id="src_1",
        event_type=EventType.FAILED_PAYMENT,
        source=EventSource.RAZORPAY_TEST,
        payload_json='{}',
        idempotency_key="shared_idempotency_key",
    )

    assert dal_a.save_event_if_new(event_a) is True
    assert dal_b.save_event_if_new(event_b) is True
