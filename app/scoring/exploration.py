"""Safety-Constrained Epsilon-Exploration Manager for M5 AI Decision Engine (ADR-0004, INV-3).

INVARIANTS:
1. INV-3 Exploration Safety: Exploration can ONLY select from actions already approved as ELIGIBLE by M4 hard safety filter.
2. Safety rejections (KNOWN_GATEWAY_OUTAGE, CONTACT_BUDGET_UNAVAILABLE, etc.) can NEVER be explored.
3. Injectable random generator / seed abstraction for deterministic testing.
"""

import random
from typing import List, Optional, Tuple
from app.domain.enums import ActionType, DecisionMode
from app.domain.models import CandidateScore


class ExplorationManager:
    """Manages safety-constrained epsilon-greedy exploration over policy-eligible actions."""

    def __init__(
        self,
        epsilon: float = 0.05,
        random_seed: Optional[int] = None,
    ) -> None:
        self.epsilon = epsilon
        self.random_seed = random_seed

    def select_action(
        self,
        scores: List[CandidateScore],
        force_mode: Optional[DecisionMode] = None,
    ) -> Tuple[ActionType, DecisionMode, Optional[CandidateScore]]:
        """Select action candidate based on EV ranking and safety-constrained epsilon-exploration.
        
        Returns:
            Tuple of (selected_action_type, decision_mode, selected_candidate_score)
        """
        # Filter eligible candidate scores ONLY (INV-3)
        eligible_scores = [s for s in scores if s.is_eligible]

        if not eligible_scores:
            # Safe abstention fallback to NO_ACTION if zero actions survived safety filter
            return ActionType.NO_ACTION, DecisionMode.SAFE_ABSTENTION, None

        # Determine exploitation candidate (highest expected value)
        # Note: scores are pre-sorted by EV descending
        top_exploit_score = eligible_scores[0]

        # Handle forced decision mode (used in testing or explicit configuration)
        if force_mode == DecisionMode.SAFE_ABSTENTION:
            no_action_score = next((s for s in scores if s.action_type == ActionType.NO_ACTION), None)
            return ActionType.NO_ACTION, DecisionMode.SAFE_ABSTENTION, no_action_score

        if force_mode == DecisionMode.EXPLOIT:
            return top_exploit_score.action_type, DecisionMode.EXPLOIT, top_exploit_score

        if force_mode == DecisionMode.EXPLORE and len(eligible_scores) > 1:
            rng = random.Random(self.random_seed) if self.random_seed is not None else random.Random()
            chosen_score = rng.choice(eligible_scores)
            return chosen_score.action_type, DecisionMode.EXPLORE, chosen_score


        # Epsilon-greedy selection
        rng = random.Random(self.random_seed) if self.random_seed is not None else random.Random()

        if rng.random() < self.epsilon and len(eligible_scores) > 1:
            # EXPLORE among ELIGIBLE actions ONLY
            chosen_score = rng.choice(eligible_scores)
            return chosen_score.action_type, DecisionMode.EXPLORE, chosen_score

        # EXPLOIT top EV action
        return top_exploit_score.action_type, DecisionMode.EXPLOIT, top_exploit_score
