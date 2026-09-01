"""Expected Value Calculator & Incremental Effect Scorer for M5 AI Decision Engine.

INVARIANTS:
1. ADR-0005: Incremental Effect delta_hat(x,a) = p_hat(x,a) - p_hat(x, NO_ACTION).
2. Expected Value EV(x,a) = round(delta_hat(x,a) * amount_paise) - action_cost_paise.
3. Integer paise representation strictly maintained for all monetary values.
4. Hard safety rejections (ELIGIBLE vs SAFETY_REJECTED) are strictly preserved.
"""

from typing import List, Tuple
from app.domain.enums import ActionType, EligibilityStatus
from app.domain.models import ActionCandidate, CandidateScore, RecoveryDecisionContext
from app.scoring.costs import get_action_cost_paise
from app.scoring.s_learner import CatBoostSLearner


class EVCalculator:
    """Calculates S-learner probabilities, incremental effects, and Expected Value (EV) scores."""

    def __init__(self, model: CatBoostSLearner) -> None:
        self.model = model

    def calculate_scores(
        self,
        context: RecoveryDecisionContext,
    ) -> Tuple[float, List[CandidateScore]]:
        """Calculate CandidateScore for all candidate actions in context.
        
        Returns:
            Tuple of (baseline_probability, List[CandidateScore]) sorted by expected_value_paise descending.
        """
        # 1. Estimate baseline probability P(Y=1 | X, NO_ACTION)
        baseline_prob = self.model.predict_action_probability(context, ActionType.NO_ACTION)

        amount_paise = context.opportunity.amount.amount_paise
        scores: List[CandidateScore] = []

        for candidate in context.candidates:
            action_type = candidate.action_type
            action_cost = get_action_cost_paise(action_type)

            if action_type == ActionType.NO_ACTION:
                raw_prob = baseline_prob
                inc_effect = 0.0
                inc_val_paise = 0
                ev_paise = 0
            else:
                raw_prob = self.model.predict_action_probability(context, action_type)
                inc_effect = raw_prob - baseline_prob
                # Deterministic rounding to integer paise
                inc_val_paise = int(round(inc_effect * amount_paise))
                ev_paise = inc_val_paise - action_cost

            score = CandidateScore(
                action_type=action_type,
                eligibility=candidate.eligibility,
                raw_probability=raw_prob,
                baseline_probability=baseline_prob,
                incremental_effect=inc_effect,
                incremental_value_paise=inc_val_paise,
                action_cost_paise=action_cost,
                expected_value_paise=ev_paise,
                is_eligible=candidate.is_eligible,
                reject_reason=candidate.reject_reason,
            )
            scores.append(score)

        # Sort scores: Eligible actions first by expected_value_paise descending, then safety_rejected actions
        scores.sort(
            key=lambda s: (
                1 if s.is_eligible else 0,
                s.expected_value_paise,
                # Deterministic tie-breaker by action_type string
                s.action_type.value,
            ),
            reverse=True,
        )

        return baseline_prob, scores
