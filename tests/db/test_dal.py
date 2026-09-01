"""Acceptance tests for Data Access Layer (DAL) persistence & round-trip fidelity.

Test Coverage:
- M2-09: RecoveryOpportunity persistence
- M2-10: Persistence round trip (zero precision or data loss)
- M2-20: Serialization & Enum value preservation
"""

import pytest
from app.clock import FakeClock
from app.db.init import init_db
from app.db.dal import TenantScopedDB
from app.domain.enums import EventType, OpportunityStatus, EventSource
from app.domain.models import RecoveryOpportunity
from app.domain.money import Money


@pytest.fixture
def db_conn():
    conn = init_db(":memory:")
    yield conn
    conn.close()


def test_m2_09_opportunity_persistence(db_conn) -> None:
    """M2-09: Verify RecoveryOpportunity model persists cleanly via DAL."""
    dal = TenantScopedDB(db_conn, merchant_id="merch_001")
    opp = RecoveryOpportunity(
        opportunity_id="opp_1001",
        merchant_id="merch_001",
        customer_id="cust_555",
        source_event_id="evt_888",
        event_type=EventType.FAILED_PAYMENT,
        amount=Money(10050),  # ₹100.50
        currency="INR",
        status=OpportunityStatus.NEW,
        source=EventSource.RAZORPAY_TEST,
        occurred_at="2026-09-01T12:00:00Z",
        observed_at="2026-09-01T12:00:01Z",
    )

    dal.create_opportunity(opp)
    retrieved = dal.get_opportunity("opp_1001")
    assert retrieved is not None
    assert retrieved.opportunity_id == "opp_1001"
    assert retrieved.merchant_id == "merch_001"


def test_m2_10_persistence_round_trip(db_conn) -> None:
    """M2-10: Verify 100% round-trip fidelity across domain -> DB -> domain."""
    clock = FakeClock()
    dal = TenantScopedDB(db_conn, merchant_id="merch_alpha", clock=clock)
    
    original = RecoveryOpportunity(
        opportunity_id="opp_alpha_99",
        merchant_id="merch_alpha",
        customer_id="cust_99",
        source_event_id="evt_src_99",
        event_type=EventType.AUTOPAY_FAILURE,
        amount=Money(499900),  # ₹4,999.00
        currency="INR",
        status=OpportunityStatus.STAGE_1_DIAGNOSED,
        source=EventSource.SIMULATED,
        occurred_at="2026-09-01T08:30:00Z",
        observed_at="2026-09-01T08:30:05Z",
        created_at=clock.now_iso(),
        updated_at=clock.now_iso(),
    )

    dal.create_opportunity(original)
    fetched = dal.get_opportunity("opp_alpha_99")

    assert fetched == original
    assert fetched.amount.amount_paise == 499900
    assert fetched.amount.to_rupees_str() == "4999.00"


def test_m2_20_serialization_and_enum_preservation(db_conn) -> None:
    """M2-20: Verify enum values are stored as stable strings and reconstructed cleanly."""
    dal = TenantScopedDB(db_conn, merchant_id="merch_beta")
    opp = RecoveryOpportunity(
        opportunity_id="opp_beta_1",
        merchant_id="merch_beta",
        customer_id="cust_1",
        source_event_id="evt_beta_1",
        event_type=EventType.PAYMENT_DOWNTIME,
        amount=Money(500),
        currency="INR",
        status=OpportunityStatus.RESERVED,
        source=EventSource.RAZORPAY_TEST,
        occurred_at="2026-09-01T10:00:00Z",
        observed_at="2026-09-01T10:00:00Z",
    )

    dal.create_opportunity(opp)
    
    # Direct DB inspection of string enum columns
    cursor = db_conn.execute(
        "SELECT event_type, status, source FROM opportunities WHERE merchant_id='merch_beta' AND opportunity_id='opp_beta_1'"
    )
    row = cursor.fetchone()
    assert row["event_type"] == "PAYMENT_DOWNTIME"
    assert row["status"] == "RESERVED"
    assert row["source"] == "RAZORPAY_TEST"

    # Reconstruction via DAL
    fetched = dal.get_opportunity("opp_beta_1")
    assert isinstance(fetched.event_type, EventType)
    assert isinstance(fetched.status, OpportunityStatus)
    assert isinstance(fetched.source, EventSource)
