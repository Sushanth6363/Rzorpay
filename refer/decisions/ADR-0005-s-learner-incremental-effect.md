# ADR-0005 — S-learner for incremental effect; a model estimate is not a causal claim

**Date**: 2026-08-31
**Status**: ACCEPTED
**Author/Agent**: Claude Opus 5, ratified by project owner

## Decision
One CatBoost model with action as a feature. `delta_hat(x,a) = p_hat(x,a) - p_hat(x, NO_ACTION)` is used for ranking only, and is always named 'estimated incremental effect under the simulator's data-generating process'. Reported claims come only from the arm-level experiment.

## Context
The strategy asked the model to predict incremental recovery. Incremental recovery is a difference between arms; no logged row carries it as a label.

## Problem
Training on incremental recovery directly is impossible, and describing an action-conditional probability difference as a proven causal uplift is a claim the design cannot support.

## Options considered
1. S-learner, action as a feature (CHOSEN)
2. T-learner, one model per action
3. Direct uplift trees
4. Train on raw recovery, ignore the counterfactual

## Decision rationale
Option 2 splits an already-small dataset four ways. Option 3 adds a dependency and complexity for marginal benefit at this scale. Option 4 abandons the incremental framing entirely. Option 1 is implementable, keeps all data in one model, and makes NO_ACTION the explicit baseline.

## Trade-offs
`delta_hat` validity rests on the model being correct, which is the thing under test. This is why it ranks but never claims.

## Impact
NO_ACTION must be a scored candidate, not a fallback. Epsilon-exploration with recorded propensities becomes mandatory rather than optional.

## What this prevents
Confusing a model prediction with a measured causal effect — the 'causal claims without causal evidence' rejection.

## Affected components
`app/scoring/model.py`, `app/models/`, `04_AI_ML_SPEC.md`, `07_EXPERIMENT_METHODOLOGY.md`

## Tests required
Calibration gate before EV is trusted; delta_hat equals selected minus no-action probability; no claim sourced from a model estimate.

## Evidence
`strategy/STRATEGY.md` P0 FIX 2; `full_plan.md` R1.

## Reversal conditions
If real logged data with randomised action assignment ever becomes available, a direct uplift estimator becomes viable.

## Related ADRs
ADR-0004, ADR-0011
