"""AI Recovery Decision Engine for M5 Milestone.

INVARIANTS:
1. DECISION PREPARATION ONLY: M5 outputs AIRecoveryDecision but DOES NOT reserve contact slots or execute payments (M6 responsibility).
2. HARD SAFETY FILTER RESPECTED: AI ranks eligible candidates only. SAFETY_REJECTED candidates can NEVER be selected or explored.
3. INCREMENTAL EV RANKING: Actions are ranked by EV(x,a) = delta_hat(x,a) * amount_paise - action_cost_paise against NO_ACTION counterfactual.
4. DETERMINISTIC REPRODUCIBILITY: Given identical inputs and seed, evaluate_decision produces 100% reproducible AIRecoveryDecision.
"""

import hashlib
from typing import List, Optional
from app.domain.enums import AbstentionReason, ActionType, DecisionMode
from app.domain.models import AIRecoveryDecision, CandidateScore, RecoveryDecisionContext
from app.scoring.ev_calculator import EVCalculator
from app.scoring.exploration import ExplorationManager
from app.scoring.s_learner import CatBoostSLearner


class AIRecoveryDecisionEngine:
    """Orchestrates S-learner probability scoring, incremental EV ranking, and safety-constrained exploration."""

    def __init__(
        self,
        learner: Optional[CatBoostSLearner] = None,
        epsilon: float = 0.05,
        model_version: str = "v1.0.0-baseline",
    ) -> None:
        self.learner = learner or CatBoostSLearner()
        self.ev_calculator = EVCalculator(model=self.learner)
        self.epsilon = epsilon
        self.model_version = model_version

    def evaluate_decision(
        self,
        context: RecoveryDecisionContext,
        force_mode: Optional[DecisionMode] = None,
        random_seed: Optional[int] = None,
    ) -> AIRecoveryDecision:
        """Evaluate AI recovery decision for a given RecoveryDecisionContext."""
        opp = context.opportunity
        merchant_id = opp.merchant_id
        customer_id = opp.customer_id
        opportunity_id = opp.opportunity_id

        # Generate deterministic decision_id
        raw_id = f"{merchant_id}_{opportunity_id}_{context.decision_timestamp}_{random_seed}"
        hash_suffix = hashlib.md5(raw_id.encode("utf-8")).hexdigest()[:8]
        decision_id = f"dec_{opportunity_id}_{hash_suffix}"

        # 1. Calculate baseline and CandidateScores via EVCalculator
        baseline_prob, scores = self.ev_calculator.calculate_scores(context)

        # 2. Select action via ExplorationManager
        exploration_mgr = ExplorationManager(
            epsilon=self.epsilon,
            random_seed=random_seed,
        )

        selected_action_type, decision_mode, selected_score = exploration_mgr.select_action(
            scores=scores,
            force_mode=force_mode,
        )

        # 3. Determine abstention reason if applicable
        abstention_reason = AbstentionReason.NONE
        if decision_mode == DecisionMode.SAFE_ABSTENTION:
            abstention_reason = AbstentionReason.SAFETY_FILTER_REJECTION
        elif not self.learner.is_fitted:
            abstention_reason = AbstentionReason.INSUFFICIENT_TRAINING_DATA
        elif selected_action_type == ActionType.NO_ACTION and len(context.get_eligible_candidates()) > 1:
            abstention_reason = AbstentionReason.NEGATIVE_EXPECTED_VALUE

        return AIRecoveryDecision(
            decision_id=decision_id,
            merchant_id=merchant_id,
            opportunity_id=opportunity_id,
            customer_id=customer_id,
            selected_action=selected_action_type,
            decision_mode=decision_mode,
            model_version=self.model_version,
            decision_timestamp=context.decision_timestamp,
            baseline_probability=baseline_prob,
            selected_action_score=selected_score,
            candidate_scores=scores,
            abstention_reason=abstention_reason,
            provenance=context.provenance,
            exploration_epsilon=self.epsilon,
            random_seed=random_seed,
            is_contact_reserved=False,  # EXPLICIT M5 INVARIANT
        )
