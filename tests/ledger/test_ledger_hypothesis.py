"""Property-based tests for Contact Ledger Engine using Hypothesis (M3-36)."""

import pytest
from hypothesis import given, strategies as st
from app.db.init import init_db
from app.domain.enums import ActionType, LedgerStatus
from app.ledger.engine import ContactLedgerEngine


@given(
    cap=st.integers(min_value=1, max_value=10),
    num_reservations=st.integers(min_value=1, max_value=20),
)
def test_m3_hypothesis_budget_cap_invariant(cap: int, num_reservations: int):
    """Property test: For any random sequence of reservation requests, total active slots NEVER exceed cap."""
    conn = init_db(":memory:")
    engine = ContactLedgerEngine(conn, merchant_id="merch_hyp")

    granted_count = 0
    for i in range(num_reservations):
        entry = engine.reserve_contact(
            customer_id="cust_hyp",
            opportunity_id=f"opp_{i}",
            action_type=ActionType.WHATSAPP_LINK,
            intervention_idempotency_key=f"hyp_key_{i}",
            cap=cap,
        )
        if entry is not None:
            granted_count += 1

    budget = engine.get_customer_budget("cust_hyp")
    conn.close()

    assert budget is not None
    assert budget.reserved_count >= 0
    assert budget.consumed_count >= 0
    assert budget.reserved_count + budget.consumed_count <= cap
    assert granted_count == min(cap, num_reservations)


@given(
    outcome=st.sampled_from([
        LedgerStatus.RECONCILED_DELIVERED,
        LedgerStatus.RECONCILED_NOT_SENT,
        LedgerStatus.RECONCILED_UNRESOLVED,
    ])
)
def test_m3_hypothesis_reconciliation_idempotency(outcome: LedgerStatus):
    """Property test: Reconciliation operation is perfectly idempotent for any valid terminal outcome."""
    conn = init_db(":memory:")
    engine = ContactLedgerEngine(conn, merchant_id="merch_hyp")

    entry = engine.reserve_contact("cust_rec_hyp", "opp_hyp", ActionType.SMS_LINK, "key_hyp_rec")
    engine.mark_execution_unknown(entry.ledger_id)

    # Apply reconciliation once
    res1 = engine.reconcile(entry.ledger_id, outcome)
    budget1 = engine.get_customer_budget("cust_rec_hyp")

    # Apply reconciliation second time
    res2 = engine.reconcile(entry.ledger_id, outcome)
    budget2 = engine.get_customer_budget("cust_rec_hyp")
    conn.close()

    assert res1 is True
    assert res2 is True
    assert budget1.reserved_count == budget2.reserved_count
    assert budget1.consumed_count == budget2.consumed_count
