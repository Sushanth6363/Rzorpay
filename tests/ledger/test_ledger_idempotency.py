"""Tests for Ledger Deterministic Idempotency & Duplicate Reservations (M3-04, M3-05)."""

import pytest
from app.db.init import init_db
from app.domain.enums import ActionType
from app.ledger.engine import ContactLedgerEngine


@pytest.fixture
def db_conn():
    conn = init_db(":memory:")
    yield conn
    conn.close()


def test_m3_04_deterministic_intervention_idempotency(db_conn):
    """M3-04: Deterministic intervention idempotency returns identical record."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")

    entry1 = engine.reserve_contact(
        customer_id="cust_idem",
        opportunity_id="opp_idem",
        action_type=ActionType.WHATSAPP_LINK,
        intervention_idempotency_key="idempotent_key_001",
        cap=3,
    )
    assert entry1 is not None

    # Repeated call with same idempotency key
    entry2 = engine.reserve_contact(
        customer_id="cust_idem",
        opportunity_id="opp_idem",
        action_type=ActionType.WHATSAPP_LINK,
        intervention_idempotency_key="idempotent_key_001",
        cap=3,
    )
    assert entry2 is not None
    assert entry1.ledger_id == entry2.ledger_id


def test_m3_05_duplicate_reservation_does_not_consume_extra_capacity(db_conn):
    """M3-05: Duplicate reservation attempt does NOT consume additional budget capacity."""
    engine = ContactLedgerEngine(db_conn, merchant_id="merch_01")

    # Reserve once
    entry1 = engine.reserve_contact(
        customer_id="cust_dup",
        opportunity_id="opp_dup",
        action_type=ActionType.SMS_LINK,
        intervention_idempotency_key="dup_key_555",
        cap=3,
    )
    budget1 = engine.get_customer_budget("cust_dup")
    assert budget1.reserved_count == 1

    # Attempt same reservation 5 times
    for _ in range(5):
        engine.reserve_contact(
            customer_id="cust_dup",
            opportunity_id="opp_dup",
            action_type=ActionType.SMS_LINK,
            intervention_idempotency_key="dup_key_555",
            cap=3,
        )

    budget2 = engine.get_customer_budget("cust_dup")
    assert budget2.reserved_count == 1  # Reserved count remains strictly 1!
    assert budget2.available_slots == 2
