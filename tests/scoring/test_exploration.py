"""Tests for Safety-Constrained Epsilon-Exploration (M5-16..20, INV-3, ADR-0004)."""

import pytest
from app.domain.enums import ActionType, DecisionMode, EligibilityStatus, SafetyRejectReason
from app.domain.models import ActionCandidate, CandidateScore
from app.scoring.exploration import ExplorationManager


def create_sample_scores() -> list[CandidateScore]:
    return [
        CandidateScore(
            action_type=ActionType.WHATSAPP_LINK,
            eligibility=EligibilityStatus.ELIGIBLE,
            raw_probability=0.55,
            baseline_probability=0.15,
            incremental_effect=0.40,
            incremental_value_paise=4000,
            action_cost_paise=25,
            expected_value_paise=3975,
            is_eligible=True,
        ),
        CandidateScore(
            action_type=ActionType.NO_ACTION,
            eligibility=EligibilityStatus.ELIGIBLE,
            raw_probability=0.15,
            baseline_probability=0.15,
            incremental_effect=0.0,
            incremental_value_paise=0,
            action_cost_paise=0,
            expected_value_paise=0,
            is_eligible=True,
        ),
        CandidateScore(
            action_type=ActionType.RECOMMEND_RETRY,
            eligibility=EligibilityStatus.SAFETY_REJECTED,
            raw_probability=0.80,
            baseline_probability=0.15,
            incremental_effect=0.65,
            incremental_value_paise=6500,
            action_cost_paise=0,
            expected_value_paise=6500,
            is_eligible=False,
            reject_reason=SafetyRejectReason.KNOWN_GATEWAY_OUTAGE,
        ),
    ]


def test_m5_16_zero_epsilon_produces_exploitation_only():
    """M5-16: Verify epsilon=0.0 produces EXPLOIT mode exclusively."""
    scores = create_sample_scores()
    mgr = ExplorationManager(epsilon=0.0)

    for seed in range(50):
        action, mode, _ = mgr.select_action(scores)
        assert mode == DecisionMode.EXPLOIT
        assert action == ActionType.WHATSAPP_LINK  # Top EV action


def test_m5_17_forced_exploration_works():
    """M5-17: Verify forced EXPLORE mode selects randomly among eligible candidates."""
    scores = create_sample_scores()
    mgr = ExplorationManager(epsilon=0.05, random_seed=42)

    action, mode, _ = mgr.select_action(scores, force_mode=DecisionMode.EXPLORE)
    assert mode == DecisionMode.EXPLORE
    assert action in (ActionType.WHATSAPP_LINK, ActionType.NO_ACTION)


def test_m5_18_safety_rejected_candidate_never_explored():
    """M5-18: Verify SAFETY_REJECTED candidate is NEVER selected by exploration (INV-3)."""
    scores = create_sample_scores()
    # Epsilon = 1.0 forces exploration 100% of the time
    mgr = ExplorationManager(epsilon=1.0)

    for seed in range(200):
        mgr.random_seed = seed
        action, mode, score = mgr.select_action(scores)
        assert action != ActionType.RECOMMEND_RETRY  # Outage-suppressed retry can NEVER be selected!
        assert action in (ActionType.WHATSAPP_LINK, ActionType.NO_ACTION)


def test_m5_19_all_rejected_candidates_safely_abstains():
    """M5-19: Verify when all candidates are safety-rejected, exploration safely abstains to NO_ACTION."""
    rejected_scores = [
        CandidateScore(
            action_type=ActionType.WHATSAPP_LINK,
            eligibility=EligibilityStatus.SAFETY_REJECTED,
            raw_probability=0.55,
            baseline_probability=0.15,
            incremental_effect=0.40,
            incremental_value_paise=4000,
            action_cost_paise=25,
            expected_value_paise=3975,
            is_eligible=False,
            reject_reason=SafetyRejectReason.CONTACT_BUDGET_UNAVAILABLE,
        ),
    ]

    mgr = ExplorationManager(epsilon=1.0)
    action, mode, _ = mgr.select_action(rejected_scores)

    assert action == ActionType.NO_ACTION
    assert mode == DecisionMode.SAFE_ABSTENTION
