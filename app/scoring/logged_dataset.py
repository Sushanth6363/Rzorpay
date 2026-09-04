"""Training data logged from the engine's OWN outcomes (ADR-0017).

THE BUG THIS REPLACES
    `SyntheticDatasetGenerator` builds training rows from an independent, hand-authored
    probability table that disagrees with the sandbox the model is then evaluated against.
    The two worlds rank actions differently — most starkly, RECOMMEND_RETRY sits near the
    BOTTOM of the training table (~0.27) and is the SECOND BEST action in the simulator
    (0.65). The S-learner learned that table faithfully and was then scored in a world where
    it was wrong.

    So "the model loses to the heuristic" was never a fact about CatBoost. It was a fact
    about training the model on one world and grading it in another, while the heuristic's
    hand-written baselines happened to match the grading world's ordering almost exactly.

WHAT THIS DOES INSTEAD
    Generates the training set the way a production recovery engine actually gets one: by
    replaying opportunities through the real pipeline, dispatching actions into the real
    sandbox, and recording what actually happened. Features come from the same
    `FeatureBuilder` used at decision time, so train and serve cannot drift.

INVARIANTS:
1. SEED DISJOINT FROM EVALUATION. Training uses batch seed {TRAIN_BATCH_SEED} and outcome
   seeds {TRAIN_SEEDS}; evaluation uses batch seed 42 and seeds 21-40. No opportunity and no
   outcome draw is shared. This is the property ADR-0005 always claimed and this module is
   the first to actually provide.
2. SAME FEATURE PATH. Rows are built by FeatureBuilder from a real RecoveryDecisionContext —
   never hand-assembled — so a feature cannot exist in training that does not exist at
   serving time.
3. UNIFORM LOGGING POLICY. Every action is logged for every opportunity, so the training set
   carries no action-selection bias from the policy being learned. This is the clean
   off-policy setup; it is not the model grading its own homework.
4. NO TUNING. This module changes WHERE the labels come from, never what they are. The
   simulator's outcome probabilities are untouched. If the model still loses after learning
   from real outcomes, that result stands and is reported.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.clock import FakeClock
from app.domain.enums import ActionType, DataProvenance, PaymentOutcome
from app.domain.models import SandboxActionRequest
from app.sandbox.simulator import SandboxSimulator
from app.scoring.feature_builder import FeatureBuilder

# Disjoint from the evaluation batch seed (42) and evaluation seeds (21-40).
TRAIN_BATCH_SEED = 7
TRAIN_SEEDS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
TRAIN_EVENTS = 150
TRAIN_REFERENCE_TIMESTAMP = "2025-01-01T00:00:00+00:00"

# A recovery counts as a success exactly as attribution counts it: an intervention-driven
# payment. SELF_CURED is deliberately NOT a success label for a contacted action - it is the
# counterfactual baseline the S-learner needs in order to estimate an incremental effect.
SUCCESS_OUTCOME = PaymentOutcome.PAYMENT_SUCCESS


def generate_logged_training_data(
    num_events: int = TRAIN_EVENTS,
    batch_seed: int = TRAIN_BATCH_SEED,
    seeds: Optional[tuple] = None,
    reference_timestamp: str = TRAIN_REFERENCE_TIMESTAMP,
) -> List[Dict[str, Any]]:
    """Replay training opportunities through the real engine and log observed outcomes.

    Returns rows shaped exactly like `FeatureBuilder.build_feature_dict` output plus a
    `recovered` label, ready for `CatBoostSLearner.fit`.
    """
    # Imported here to avoid a circular import at module load (batch -> tds -> ...).
    from app.experiment.batch import generate_batch
    from app.pipeline.recovery_pipeline import RecoveryPipeline

    events = generate_batch(
        num_events=num_events,
        batch_seed=batch_seed,
        reference_timestamp=reference_timestamp,
    )
    outcome_seeds = seeds if seeds is not None else TRAIN_SEEDS

    rows: List[Dict[str, Any]] = []

    for event in events:
        decision_ts = event.get("decision_timestamp") or reference_timestamp
        clock = FakeClock(decision_ts)
        # No DB: this is offline replay for label generation, so no contact budget is
        # consulted and no ledger row is written. Escalation and budget are POLICY, applied
        # at decision time; they must not censor the outcome data the model learns from.
        pipeline = RecoveryPipeline(clock=clock)
        simulator = SandboxSimulator(clock=clock)

        try:
            context = pipeline.process_raw_event(
                raw_data=event, decision_timestamp=decision_ts
            )
        except Exception:
            # A malformed training opportunity is skipped, never silently mislabelled.
            continue

        amount_paise = context.opportunity.amount.amount_paise

        for action in ActionType:
            try:
                features = FeatureBuilder.build_feature_dict(context, action)
            except Exception:
                continue

            for seed in outcome_seeds:
                request = SandboxActionRequest(
                    action_id=f"train_{context.opportunity.opportunity_id}_{action.value}_{seed}",
                    decision_id=f"train_dec_{seed}",
                    merchant_id=context.opportunity.merchant_id,
                    customer_id=context.opportunity.customer_id,
                    opportunity_id=context.opportunity.opportunity_id,
                    action_type=action,
                    amount_paise=amount_paise,
                    requested_at=decision_ts,
                    idempotency_key=(
                        f"train_{context.opportunity.opportunity_id}_{action.value}_{seed}"
                    ),
                )
                result = simulator.execute_action(request=request, random_seed=seed)

                row = dict(features)
                row["recovered"] = 1 if result.payment_outcome == SUCCESS_OUTCOME else 0
                row["provenance"] = DataProvenance.SIMULATED_EXTERNAL_STATE.value
                rows.append(row)

    return rows
