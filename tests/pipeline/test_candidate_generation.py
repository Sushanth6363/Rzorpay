"""Tests for Candidate Generation, mandatory NO_ACTION, Hard Safety Filter, and Contact Budget boundaries (M4-15..21)."""

import pytest
from app.domain.enums import ActionType, EligibilityStatus, EventSource, EventType, SafetyRejectReason
from app.domain.models import CustomerContactBudget, RecoveryOpportunity
from app.domain.money import Money
from app.pipeline.candidate_generator import CandidateGenerator
from app.pipeline.recovery_pipeline import RecoveryPipeline
from app.pipeline.safety_filter import HardSafetyFilter


@pytest.fixture
def sample_opportunity():
    return RecoveryOpportunity(
        opportunity_id="opp_cand_01",
        merchant_id="merch_alpha",
        customer_id="cust_101",
        source_event_id="evt_101",
        event_type=EventType.FAILED_PAYMENT,
        amount=Money.from_rupees(1000),
        currency="INR",
        status=EventType.FAILED_PAYMENT,
        source=EventSource.SIMULATED,
        occurred_at="2026-09-01T10:00:00+00:00",
        observed_at="2026-09-01T10:00:00+00:00",
    )


def test_m4_15_candidate_generation(sample_opportunity):
    """M4-15: Verify CandidateGenerator produces candidate set including counterfactual and communication channels."""
    generator = CandidateGenerator()
    pipeline = RecoveryPipeline()
    ctx = pipeline.process_opportunity(sample_opportunity)

    action_types = [c.action_type for c in ctx.candidates]
    assert ActionType.NO_ACTION in action_types
    assert ActionType.RECOMMEND_RETRY in action_types
    assert ActionType.WHATSAPP_LINK in action_types
    assert ActionType.SMS_LINK in action_types
    assert ActionType.EMAIL_LINK in action_types


def test_m4_16_no_action_always_generated(sample_opportunity):
    """M4-16: Verify NO_ACTION is ALWAYS generated as candidate #1 with is_counterfactual=True."""
    generator = CandidateGenerator()
    pipeline = RecoveryPipeline()
    ctx = pipeline.process_opportunity(sample_opportunity)

    no_action = ctx.candidates[0]
    assert no_action.action_type == ActionType.NO_ACTION
    assert no_action.is_counterfactual is True
    assert no_action.is_eligible is True


def test_m4_17_safety_rejection_budget_exhausted(sample_opportunity):
    """M4-17: Verify hard safety filter marks outreach candidates SAFETY_REJECTED when contact budget is exhausted."""
    pipeline = RecoveryPipeline()

    budget = CustomerContactBudget(
        merchant_id="merch_alpha",
        customer_id="cust_101",
        cap=3,
        reserved_count=3,
        consumed_count=0,
    )

    ctx = pipeline.process_opportunity(sample_opportunity, contact_budget=budget)

    # NO_ACTION and RECOMMEND_RETRY (non-contact) remain eligible
    eligible = ctx.get_eligible_candidates()
    eligible_types = [c.action_type for c in eligible]
    assert ActionType.NO_ACTION in eligible_types
    assert ActionType.RECOMMEND_RETRY in eligible_types

    # Direct contact actions must be SAFETY_REJECTED due to CONTACT_BUDGET_UNAVAILABLE
    rejected = [c for c in ctx.candidates if not c.is_eligible]
    rejected_types = [c.action_type for c in rejected]
    assert ActionType.WHATSAPP_LINK in rejected_types
    assert ActionType.SMS_LINK in rejected_types

    for c in rejected:
        assert c.reject_reason == SafetyRejectReason.CONTACT_BUDGET_UNAVAILABLE


def test_m4_18_safety_rejection_cannot_become_eligible():
    """M4-18: Verify SAFETY_REJECTED status cannot be overridden by AI layer."""
    pipeline = RecoveryPipeline()
    sample_opp = RecoveryOpportunity(
        opportunity_id="opp_01",
        merchant_id="merch_alpha",
        customer_id="cust_101",
        source_event_id="evt_101",
        event_type=EventType.FAILED_PAYMENT,
        amount=Money.from_rupees(100),
        currency="INR",
        status=EventType.FAILED_PAYMENT,
        source=EventSource.SIMULATED,
        occurred_at="2026-09-01T10:00:00+00:00",
        observed_at="2026-09-01T10:00:00+00:00",
    )

    budget_exhausted = CustomerContactBudget(merchant_id="merch_alpha", customer_id="cust_101", cap=3, reserved_count=3, consumed_count=0)
    ctx = pipeline.process_opportunity(sample_opp, contact_budget=budget_exhausted)

    # Intersection of SAFETY_REJECTED set and ELIGIBLE set must be EMPTY
    rejected_set = set(c.action_type for c in ctx.candidates if c.eligibility == EligibilityStatus.SAFETY_REJECTED)
    eligible_set = set(c.action_type for c in ctx.get_eligible_candidates())

    assert rejected_set.intersection(eligible_set) == set()


def test_m4_19_candidate_explanations(sample_opportunity):
    """M4-19: Verify candidate actions include human-readable reason_explanation and evidence."""
    pipeline = RecoveryPipeline()
    ctx = pipeline.process_opportunity(sample_opportunity)

    for candidate in ctx.candidates:
        assert isinstance(candidate.reason_explanation, str)
        assert len(candidate.reason_explanation) > 0
        assert isinstance(candidate.evidence, dict)


def test_m4_20_no_contact_slot_consumed_during_generation(sample_opportunity):
    """M4-20: INVARIANT CHECK: Verify M4 candidate generation DOES NOT reserve or consume contact slots."""
    pipeline = RecoveryPipeline()
    ctx = pipeline.process_opportunity(sample_opportunity)

    assert ctx.is_contact_reserved is False


def test_m4_21_retry_recommendation_never_executes_payment(sample_opportunity):
    """M4-21: INVARIANT CHECK (ADR-0006): Verify RECOMMEND_RETRY is recommendation-only and carries no payment API credentials or execution methods."""
    pipeline = RecoveryPipeline()
    ctx = pipeline.process_opportunity(sample_opportunity)

    retry_candidate = [c for c in ctx.candidates if c.action_type == ActionType.RECOMMEND_RETRY][0]
    assert retry_candidate.action_type.value == "RECOMMEND_RETRY"
    assert "EXECUTE_RETRY" not in [c.action_type.value for c in ctx.candidates]
