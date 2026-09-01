"""Acceptance tests for multi-tenant isolation guarantees.

Test Coverage:
- M2-12: Cross-tenant read isolation
- M2-13: Cross-tenant mutation isolation
- M2-14: Cross-tenant scope violation exception enforcement
"""

import pytest
from app.db.init import init_db
from app.db.dal import TenantScopedDB, TenantScopeViolation
from app.domain.enums import EventType, OpportunityStatus, EventSource
from app.domain.models import RecoveryOpportunity
from app.domain.money import Money


@pytest.fixture
def db_conn():
    conn = init_db(":memory:")
    yield conn
    conn.close()


def test_m2_12_cross_tenant_read_isolation(db_conn) -> None:
    """M2-12: Merchant A creates Opportunity X. Merchant A can read X; Merchant B cannot."""
    dal_a = TenantScopedDB(db_conn, merchant_id="merchant_A")
    dal_b = TenantScopedDB(db_conn, merchant_id="merchant_B")

    opp_x = RecoveryOpportunity(
        opportunity_id="opp_X",
        merchant_id="merchant_A",
        customer_id="cust_100",
        source_event_id="evt_100",
        event_type=EventType.FAILED_PAYMENT,
        amount=Money(5000),
        currency="INR",
        status=OpportunityStatus.NEW,
        source=EventSource.RAZORPAY_TEST,
        occurred_at="2026-09-01T12:00:00Z",
        observed_at="2026-09-01T12:00:00Z",
    )
    dal_a.create_opportunity(opp_x)

    # Merchant A retrieves successfully
    retrieved_a = dal_a.get_opportunity("opp_X")
    assert retrieved_a is not None
    assert retrieved_a.opportunity_id == "opp_X"

    # Merchant B retrieves nothing
    retrieved_b = dal_b.get_opportunity("opp_X")
    assert retrieved_b is None


def test_m2_13_cross_tenant_mutation_isolation(db_conn) -> None:
    """M2-13: Merchant A cannot consume Merchant B's contact budget or access Merchant B's records."""
    dal_a = TenantScopedDB(db_conn, merchant_id="merchant_A")
    dal_b = TenantScopedDB(db_conn, merchant_id="merchant_B")

    # Initialize budget for Customer 1 under Merchant B
    dal_b.init_contact_budget("cust_shared", cap=2)

    # Merchant B reserves 1 slot
    assert dal_b.reserve_contact_slot("cust_shared") is True
    budget_b = dal_b.get_contact_budget("cust_shared")
    assert budget_b.reserved_count == 1

    # Merchant A reserves for cust_shared under Merchant A scope (isolated budget)
    assert dal_a.reserve_contact_slot("cust_shared") is True
    budget_a = dal_a.get_contact_budget("cust_shared")
    assert budget_a.reserved_count == 1

    # Merchant B's budget remains unchanged at 1 reserved
    budget_b_after = dal_b.get_contact_budget("cust_shared")
    assert budget_b_after.reserved_count == 1


def test_m2_14_tenant_scope_violation_enforcement(db_conn) -> None:
    """M2-14: Verify TenantScopeViolation raised if DAL initialized invalidly or cross-tenant model passed."""
    with pytest.raises(TenantScopeViolation, match="Merchant ID cannot be empty"):
        TenantScopedDB(db_conn, merchant_id="")

    dal_a = TenantScopedDB(db_conn, merchant_id="merchant_A")
    opp_b = RecoveryOpportunity(
        opportunity_id="opp_cross",
        merchant_id="merchant_B",  # Mismatch with dal_a
        customer_id="cust_1",
        source_event_id="evt_1",
        event_type=EventType.FAILED_PAYMENT,
        amount=Money(100),
        currency="INR",
        status=OpportunityStatus.NEW,
        source=EventSource.RAZORPAY_TEST,
        occurred_at="2026-09-01T12:00:00Z",
        observed_at="2026-09-01T12:00:00Z",
    )

    with pytest.raises(TenantScopeViolation, match="Cross-tenant access prohibited"):
        dal_a.create_opportunity(opp_b)
