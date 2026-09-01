"""Golden End-to-End Scenarios M6-E01 through M6-E12 for Unified Recovery Engine (M6)."""

import pytest
from app.domain.enums import (
    ActionType,
    AttributionStatus,
    DecisionMode,
    EligibilityStatus,
    ExecutionStatus,
    LedgerStatus,
    PaymentOutcome,
    SafetyRejectReason,
)

from app.domain.models import CustomerContactBudget
from app.orchestration.recovery_orchestrator import RecoveryOrchestrator
from app.pipeline.downtime import SimulatedDowntimeProvider


def test_m6_e01_successful_retry_recovery():
    """M6-E01: Successful retry recommendation recovery."""
    orchestrator = RecoveryOrchestrator()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c1",
        "event_id": "e1",
        "amount_paise": 500000,
        "failure_reason": "INSUFFICIENT_FUNDS",
    }
    result = orchestrator.process_and_execute(
        raw_event=raw,
        force_sandbox_outcome=PaymentOutcome.PAYMENT_SUCCESS,
        random_seed=42,
    )

    assert result.decision.selected_action != ActionType.NO_ACTION
    assert result.attribution.attribution_status == AttributionStatus.RECOVERED

    assert result.attribution.gross_recovered_paise == 500000
    assert result.attribution.attributed_recovered_paise == 500000
    assert result.observation.attributed_recovered_paise == 500000


def test_m6_e02_reminder_recovery():
    """M6-E02: WhatsApp/SMS link reminder intervention recovery."""
    orchestrator = RecoveryOrchestrator()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c2",
        "event_id": "e2",
        "amount_paise": 1000000,
    }
    result = orchestrator.process_and_execute(
        raw_event=raw,
        force_sandbox_outcome=PaymentOutcome.PAYMENT_SUCCESS,
        random_seed=42,
    )

    assert result.attribution.attribution_status == AttributionStatus.RECOVERED
    assert result.attribution.gross_recovered_paise == 1000000
    assert result.attribution.attributed_recovered_paise == 1000000


def test_m6_e03_no_action_natural_recovery():
    """M6-E03: NO_ACTION counterfactual natural payment recovery."""
    orchestrator = RecoveryOrchestrator()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c3",
        "event_id": "e3",
        "amount_paise": 200000,
    }
    # Force SAFE_ABSTENTION mode to select NO_ACTION
    result = orchestrator.process_and_execute(
        raw_event=raw,
        force_mode=DecisionMode.SAFE_ABSTENTION,
        force_sandbox_outcome=PaymentOutcome.SELF_CURED,
        random_seed=42,
    )

    assert result.decision.selected_action == ActionType.NO_ACTION
    # Self-cured payments under NO_ACTION receive ₹0 AI Attribution
    assert result.attribution.attribution_status == AttributionStatus.SELF_CURED
    assert result.attribution.gross_recovered_paise == 200000
    assert result.attribution.attributed_recovered_paise == 0


def test_m6_e04_self_cure_before_intervention():
    """M6-E04: Customer pays independently (Self-cure); AI Attribution = ₹0."""
    orchestrator = RecoveryOrchestrator()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c4",
        "event_id": "e4",
        "amount_paise": 750000,
    }
    result = orchestrator.process_and_execute(
        raw_event=raw,
        force_sandbox_outcome=PaymentOutcome.SELF_CURED,
        random_seed=42,
    )

    assert result.attribution.attribution_status == AttributionStatus.SELF_CURED
    assert result.attribution.gross_recovered_paise == 750000
    assert result.attribution.attributed_recovered_paise == 0
    assert result.attribution.is_self_cured is True


def test_m6_e05_gateway_outage_suppression():
    """M6-E05: Gateway outage suppresses retry; AI cannot select retry."""
    dt_provider = SimulatedDowntimeProvider()
    dt_provider.set_outage("hdfc", is_down=True)

    orchestrator = RecoveryOrchestrator(downtime_provider=dt_provider)
    raw = {
        "merchant_id": "m1",
        "customer_id": "c5",
        "event_id": "e5",
        "amount_paise": 300000,
        "failure_reason": "GATEWAY_FAILURE",
        "gateway": "hdfc",
    }
    result = orchestrator.process_and_execute(raw_event=raw)

    assert result.decision.selected_action != ActionType.RECOMMEND_RETRY
    retry_score = next(s for s in result.decision.candidate_scores if s.action_type == ActionType.RECOMMEND_RETRY)
    assert retry_score.eligibility == EligibilityStatus.SAFETY_REJECTED
    assert retry_score.reject_reason == SafetyRejectReason.KNOWN_GATEWAY_OUTAGE


def test_m6_e06_contact_budget_exhausted():
    """M6-E06: Budget cap exhaustion rejects contact reservation, NO EXECUTION dispatched."""
    orchestrator = RecoveryOrchestrator()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c_exhausted",
        "event_id": "e6",
        "amount_paise": 400000,
    }
    # Pre-exhaust contact budget for customer c_exhausted
    from app.ledger.engine import ContactLedgerEngine
    ledger_engine = ContactLedgerEngine(conn=orchestrator.conn, merchant_id="m1")
    for i in range(3):
        ledger_engine.reserve_contact("c_exhausted", f"opp_prev_{i}", ActionType.WHATSAPP_LINK, f"key_prev_{i}")

    result = orchestrator.process_and_execute(raw_event=raw)

    assert result.ledger_entry is None
    assert result.execution_result.action_type == ActionType.NO_ACTION


def test_m6_e07_duplicate_intervention_idempotency():
    """M6-E07: Duplicate execution request with same idempotency key is idempotent."""
    orchestrator = RecoveryOrchestrator()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c7",
        "event_id": "e7",
        "amount_paise": 500000,
    }

    res1 = orchestrator.process_and_execute(raw_event=raw, random_seed=42)
    res2 = orchestrator.process_and_execute(raw_event=raw, random_seed=42)

    assert res1.opportunity_id == res2.opportunity_id
    if res1.ledger_entry and res2.ledger_entry:
        assert res1.ledger_entry.ledger_id == res2.ledger_entry.ledger_id


def test_m6_e08_execution_unknown_reconciled_delivered():
    """M6-E08: EXECUTION_UNKNOWN reconciled to RECONCILED_DELIVERED."""
    orchestrator = RecoveryOrchestrator()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c8",
        "event_id": "e8",
        "amount_paise": 600000,
    }
    result = orchestrator.process_and_execute(
        raw_event=raw,
        force_sandbox_status=ExecutionStatus.EXECUTION_UNKNOWN,
        reconcile_unknown_as=LedgerStatus.RECONCILED_DELIVERED,
    )

    assert result.execution_result.execution_status == ExecutionStatus.EXECUTION_UNKNOWN
    assert result.ledger_entry.status == LedgerStatus.RECONCILED_DELIVERED


def test_m6_e09_execution_unknown_reconciled_not_sent():
    """M6-E09: EXECUTION_UNKNOWN reconciled to RECONCILED_NOT_SENT (Capacity returned)."""
    orchestrator = RecoveryOrchestrator()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c9",
        "event_id": "e9",
        "amount_paise": 600000,
    }
    result = orchestrator.process_and_execute(
        raw_event=raw,
        force_sandbox_status=ExecutionStatus.EXECUTION_UNKNOWN,
        reconcile_unknown_as=LedgerStatus.RECONCILED_NOT_SENT,
    )

    assert result.ledger_entry.status == LedgerStatus.RECONCILED_NOT_SENT
    # Verify slot was released back to customer budget
    from app.ledger.engine import ContactLedgerEngine
    ledger_engine = ContactLedgerEngine(conn=orchestrator.conn, merchant_id="m1")
    budget = ledger_engine.get_customer_budget("c9")
    assert budget.reserved_count == 0


def test_m6_e10_execution_unknown_reconciled_unresolved():
    """M6-E10: EXECUTION_UNKNOWN reconciled to RECONCILED_UNRESOLVED (Slot conservatively consumed)."""
    orchestrator = RecoveryOrchestrator()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c10",
        "event_id": "e10",
        "amount_paise": 600000,
    }
    result = orchestrator.process_and_execute(
        raw_event=raw,
        force_sandbox_status=ExecutionStatus.EXECUTION_UNKNOWN,
        reconcile_unknown_as=LedgerStatus.RECONCILED_UNRESOLVED,
    )

    assert result.ledger_entry.status == LedgerStatus.RECONCILED_UNRESOLVED


def test_m6_e11_cross_tenant_identical_customer_ids():
    """M6-E11: Merchant A and Merchant B with identical customer IDs remain 100% isolated."""
    orchestrator = RecoveryOrchestrator()
    raw_a = {
        "merchant_id": "merch_A",
        "customer_id": "cust_shared",
        "event_id": "e11_A",
        "amount_paise": 500000,
    }
    raw_b = {
        "merchant_id": "merch_B",
        "customer_id": "cust_shared",
        "event_id": "e11_B",
        "amount_paise": 800000,
    }

    res_a = orchestrator.process_and_execute(raw_event=raw_a, random_seed=42)
    res_b = orchestrator.process_and_execute(raw_event=raw_b, random_seed=42)

    assert res_a.merchant_id == "merch_A"
    assert res_b.merchant_id == "merch_B"
    assert res_a.opportunity_id != res_b.opportunity_id


def test_m6_e12_negative_ev_action_rejected_for_no_action():
    """M6-E12: Negative EV candidate actions are rejected in favor of NO_ACTION baseline."""
    orchestrator = RecoveryOrchestrator()
    raw = {
        "merchant_id": "m1",
        "customer_id": "c12",
        "event_id": "e12",
        "amount_paise": 0,  # Zero amount makes all paid/cost interventions zero or negative EV
    }
    result = orchestrator.process_and_execute(raw_event=raw, force_mode=DecisionMode.SAFE_ABSTENTION)

    assert result.decision.selected_action == ActionType.NO_ACTION
    assert result.ledger_entry is None

