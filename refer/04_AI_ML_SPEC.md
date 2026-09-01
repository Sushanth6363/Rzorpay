# 04 — AI / ML SPECIFICATION

**Status**: entirely `PLANNED`. No model has been trained. No metric has been observed.

---

## What "AI recovery" means here

**Stage 2 action selection, and nothing else.** A calibrated model estimates recovery probability conditional on each eligible action — including `NO_ACTION` — from which expected value is derived and ranked. Arbitration, policy and the ledger are deterministic *by design*, not by omission.

## The scorers

| Name | What it is | Role |
|---|---|---|
| Heuristic baseline | hand-written, readable, tuned on seeds 1–10 with an equal effort budget | the honest comparison |
| Linear / additive baseline | `LogisticRegression` | optional sanity reference |
| CatBoost | S-learner, action included as a feature | the AI under test |
| `NO_ACTION` | a scored candidate, never a fallback | the counterfactual baseline |

---

## THE DISTINCTION THAT MUST NEVER BLUR

```
MODEL OUTPUT              p̂(x,a) = P̂(Y=1 | X=x, A=a)
                          an action-conditional PREDICTION

DERIVED QUANTITY          Δ̂(x,a) = p̂(x,a) − p̂(x, NO_ACTION)
                          named in full, every time it appears:
                          "estimated incremental effect under the simulator's
                           data-generating process"
                          used for RANKING ONLY

EXPERIMENTAL MEASUREMENT  Δ = E[Y|A=a] − E[Y|A=control]
                          estimated where randomisation holds
                          the ONLY source of a reported claim
```

`Δ̂` is **not** a proven causal uplift at the individual level. It is a difference between two predictions from a model that is itself the thing under test.

**Rule**: a claim may only be sourced from the experiment. Model estimates never appear in a results headline. An agent that describes `Δ̂` as measured causal uplift is making an error, not a simplification.

### Three estimators for the population effect

| Estimator | Randomisation source | Validity | Use |
|---|---|---|---|
| Arm-level (A5−A3, A2−A1) | seed-level, identical inputs | **cleanest** | the headline |
| Explored subset only | ε-exploration, uniform over eligible | unbiased, small n, wide CI | corroboration |
| IPW over all decisions | recorded propensities | unbiased *if* propensities are correct | diagnostic |

Every reported number states: point estimate · confidence interval · sample size · **randomisation unit** · seed.

---

## Expected value

```
EV(x,a) = Δ̂(x,a) × recoverable_paise − action_cost_paise
```

**Calibration is a gate before EV is trusted**: Brier improved over baseline, calibration slope ∈ [0.85, 1.15]. Uncalibrated probabilities make the ranking arbitrary, so the EV arithmetic is meaningless until calibration passes.

## Exploration / exploitation

ε = 0.05 of **eligible** opportunities, arm A5 only. Deterministic: `hash(experiment_id | opportunity_id) % 100 < 5`. Selects uniformly among **policy-eligible** actions. May override a VALUE abstention; never a SAFETY one. Propensity recorded on every decision — `1/len(eligible)` when explored, `1.0` when exploited. See INV-3.

Without exploration, `p̂(x,a)` for rarely-chosen actions is estimated from a self-selected sample and `Δ̂` is unreliable. **Exploration is what makes the model possible, not an optional extra.**

## Features

- Every feature is a `FeatureRecord{feature_name, value, observed_at, source, scope}`
- **Invariant**: `feature.observed_at <= decision_timestamp` — enforced by raising, gated in CI
- **Denylist**: future payment outcome · future contact response · future gateway state · future customer behaviour · future recovery status · future chargeback · future retry result · all simulator internals (`_`-prefixed)
- **Scope**: merchant-local, or on the small cross-merchant whitelist (issuer failure rate, method base success rate)
- `merchant_id` is deliberately **not** a feature

## Data partitions

| Role | Seeds | Used for | Never used for |
|---|---|---|---|
| `INITIAL_TRAINING_SET` | 1–10 | train v1; tune the heuristic | any reported comparison |
| `MODEL_SELECTION_SET` | 11–15 | the promotion gate | training, reported numbers |
| `FINAL_HOLDOUT_SET` | 16–20 | touched **once**, after promotion is decided | training, feature selection, thresholds, promotion |
| `EXPERIMENT_SET` | 21–60 | A1–A5 comparisons with v1 pinned; its outcomes train v2 | evaluating v2 |

`FINAL_HOLDOUT_SET` sits behind `HoldoutGate`, which raises until promotion is final.

## Model versions and promotion

Artefacts: `models/vN.cbm` + `vN.meta.json` (`model_version`, `artifact_hash`, `features_version`, `trained_on_seeds`, metrics, `promoted_at`) + a `model_registry` row + a git tag. No MLflow (ADR-0008).

Promotion requires **all four**: Brier improved · calibration slope ∈ [0.9, 1.1] · AUC not worse by more than 0.01 · replayed false-contact rate not worse.

**The newest model is not automatically the production model.** Rollback is exercised explicitly, and every decision stays stamped with the model that actually ran.

## Metrics

Calibration (Brier, reliability curve, slope) · AUC · ranking quality (top-k EV vs oracle) · disagreement rate vs the heuristic (descriptive, full population, never inferential) · abstention rate by reason · wrongly-suppressed rate.

## Leakage prevention

Point-in-time assertion on every feature · label `observed_at > decision_timestamp` · denylist · simulator internals unreachable · splits grouped by customer **and** ordered by time · permuted-label canary must yield AUC ∈ (0.45, 0.55).

## What the model is NOT

Not an LLM. Not an agent. Not a policy authority. Not permitted to write to the database or hold credentials. **Not evidence of production performance under any circumstance.**
