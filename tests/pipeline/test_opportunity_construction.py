"""Tests for M4 CanonicalEvent ingestion, opportunity construction, idempotency, and tenant isolation (M4-01..03)."""

import pytest
from app.db.init import init_db
from app.db.dal import TenantScopedDB, TenantScopeViolation
from app.domain.enums import EventSource, EventType, OpportunityStatus
from app.domain.models import CanonicalEvent, RecoveryOpportunity
from app.domain.money import Money
from app.pipeline.recovery_pipeline import RecoveryPipeline


@pytest.fixture
def fresh_conn():
    conn = init_db(":memory:")
    yield conn
    conn.close()


def test_m4_01_canonical_event_to_opportunity(fresh_conn):
    """M4-01: Verify CanonicalEvent correctly constructs a persistent RecoveryOpportunity."""
    merchant_id = "merch_alpha"
    db = TenantScopedDB(fresh_conn, merchant_id=merchant_id)
    pipeline = RecoveryPipeline(db=db)

    event = CanonicalEvent(
        event_id="evt_001",
        merchant_id=merchant_id,
        customer_id="cust_100",
        source_event_id="pay_100",
        event_type=EventType.FAILED_PAYMENT,
        amount=Money.from_rupees(500),
        currency="INR",
        source=EventSource.RAZORPAY_TEST,
        idempotency_key="idem_alpha_pay_100",
        occurred_at="2026-09-01T10:00:00+00:00",
    )

    ctx = pipeline.process_canonical_event(event)

    assert ctx.opportunity.opportunity_id == "opp_merch_alpha_pay_100"
    assert ctx.opportunity.merchant_id == merchant_id
    assert ctx.opportunity.customer_id == "cust_100"
    assert ctx.opportunity.amount.amount_paise == 50000
    assert ctx.opportunity.event_type == EventType.FAILED_PAYMENT

    # Verify database persistence
    retrieved = db.get_opportunity("opp_merch_alpha_pay_100")
    assert retrieved is not None
    assert retrieved.customer_id == "cust_100"


def test_m4_02_opportunity_idempotency(fresh_conn):
    """M4-02: Verify repeated ingestion of the same canonical event produces 1 logical opportunity."""
    merchant_id = "merch_alpha"
    db = TenantScopedDB(fresh_conn, merchant_id=merchant_id)
    pipeline = RecoveryPipeline(db=db)

    event = CanonicalEvent(
        event_id="evt_001",
        merchant_id=merchant_id,
        customer_id="cust_100",
        source_event_id="pay_100",
        event_type=EventType.FAILED_PAYMENT,
        amount=Money.from_rupees(500),
        currency="INR",
        source=EventSource.RAZORPAY_TEST,
        idempotency_key="idem_alpha_pay_100",
        occurred_at="2026-09-01T10:00:00+00:00",
    )

    ctx1 = pipeline.process_canonical_event(event)
    ctx2 = pipeline.process_canonical_event(event)
    ctx3 = pipeline.process_canonical_event(event)

    assert ctx1.opportunity.opportunity_id == ctx2.opportunity.opportunity_id == ctx3.opportunity.opportunity_id

    # Check database table directly
    cursor = fresh_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM opportunities WHERE merchant_id = ?", (merchant_id,))
    count = cursor.fetchone()[0]
    assert count == 1


def test_m4_03_tenant_isolation(fresh_conn):
    """M4-03: Verify tenant isolation prevents cross-tenant opportunity reading or mutation."""
    db_alpha = TenantScopedDB(fresh_conn, merchant_id="merch_alpha")
    db_beta = TenantScopedDB(fresh_conn, merchant_id="merch_beta")

    pipeline_alpha = RecoveryPipeline(db=db_alpha)

    event_alpha = CanonicalEvent(
        event_id="evt_alpha",
        merchant_id="merch_alpha",
        customer_id="cust_shared",
        source_event_id="pay_alpha",
        event_type=EventType.FAILED_PAYMENT,
        amount=Money.from_rupees(100),
        currency="INR",
        source=EventSource.SIMULATED,
        idempotency_key="idem_alpha",
        occurred_at="2026-09-01T10:00:00+00:00",
    )

    ctx_alpha = pipeline_alpha.process_canonical_event(event_alpha)

    # Merchant Beta cannot read Merchant Alpha's opportunity
    assert db_beta.get_opportunity(ctx_alpha.opportunity.opportunity_id) is None

    # Merchant Beta attempting to save Merchant Alpha's opportunity raises TenantScopeViolation
    with pytest.raises(TenantScopeViolation):
        db_beta.create_opportunity(ctx_alpha.opportunity)
