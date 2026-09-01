# 07 — EXPERIMENT METHODOLOGY

Canonical experiment specification. Full data-generating-process disclosure lives in `docs/EXPERIMENT_METHODOLOGY.md`; this file is the operational summary.

> **STATUS OF ALL RESULTS: `NOT YET RUN`.** No experiment has been executed. Every number appearing anywhere in this project is `EXPECTED` or `ILLUSTRATIVE`. No agent may convert an expected result into an observed one without an entry in `experiments/EXPERIMENT_INDEX.md` backed by a real run.

---

## Arms — five distinct configurations

| Arm | Canonical name | Ledger + arbitration | Stage 0 | Downtime | Scorer |
|---|---|---|---|---|---|
| `A1` | `BASELINE_INDEPENDENT` | ✗ | ✗ | ✗ | rules |
| `A2ns` | `UNIFIED_NO_STAGE0` | ✓ | ✗ | ✗ | heuristic |
| `A2` | `UNIFIED_NO_DOWNTIME` | ✓ | ✓ | ✗ | heuristic |
| `A3` *(alias `A4`)* | `UNIFIED_DOWNTIME_HEURISTIC` | ✓ | ✓ | ✓ | heuristic |
| `A5` | `UNIFIED_DOWNTIME_CATBOOST` | ✓ | ✓ | ✓ | CatBoost |

> **`A4` is not an additional architectural treatment.** It is the paired control configuration used to isolate the scorer contribution in the A4/A5 comparison, and it is the same configuration as `A3`. Five configurations execute, not six.

## Comparisons

| Comparison | Measures | Isolates exactly |
|---|---|---|
| **A2 vs A1** *(primary)* | Unified Recovery Engine lift | ledger + arbitration + Stage 0, **jointly** |
| A2ns vs A1 | ledger + arbitration contribution (D1) | ledger + arbitration, without Stage 0 |
| A2 vs A2ns | validation contribution | Stage 0 |
| A3 vs A2 | downtime contribution | the downtime signal |
| A5 vs A3 | AI scorer contribution | the scoring function |

**Not isolable, and stated as such**: the shared ledger cannot be separated from cross-stream arbitration — they are one mechanism.

**Forbidden phrasing**: "AI lift" for `A2 − A1` (it bundles four changes), and any claim of production uplift from any comparison.

## Randomisation and seeds

**Simulation mode** (this experiment): all arms consume the identical opportunity set and the identical arm-blind world model, hash-asserted. **Unit of analysis = the seed, n = 40.** Analysis is paired.

**Randomised mode** (specified, not run): unit is `(merchant_id, canonical_customer_id)`, assigned as `sha256(experiment_id | merchant_id | canonical_customer_id) mod k`, stratified on merchant, opportunity-count bucket and amount decile.

| Role | Seeds |
|---|---|
| `INITIAL_TRAINING_SET` | 1–10 |
| `MODEL_SELECTION_SET` | 11–15 |
| `FINAL_HOLDOUT_SET` | 16–20 — behind `HoldoutGate`, touched once, after promotion is decided |
| `EXPERIMENT_SET` | 21–60 |

## Exploration and propensity

ε = 0.05 of eligible opportunities, A5 only, deterministic. Uniform over **policy-eligible** actions. Propensity recorded on every decision. May override a VALUE abstention, never a SAFETY one.

## Statistics

| Metric | Interval method |
|---|---|
| Recovered paise per opportunity (simulation) | paired t-interval on per-seed differences, n = seeds |
| Recovery rate | Newcombe interval for a difference of proportions |
| Relative lift | BCa bootstrap over the randomisation unit |
| Direction check | Wilcoxon signed-rank (paired) |
| Paired proportions (false-contact, phantom removal) | McNemar |

**Power**: MDE computed from a 5-seed pilot and **published**, with every assumption stated (baseline rate, SD of paired differences, α = 0.05 two-sided, power = 0.80, allocation 1:1 paired, unit = seed). No power calculation is fabricated from assumed values.

**Multiplicity**: `A2 vs A1` primary, uncorrected. Secondary family — `A2ns vs A1`, `A2 vs A2ns`, `A3 vs A2`, `A5 vs A3` — Holm–Bonferroni; raw and adjusted both printed.

**Inconclusive rule**: if the interval includes zero — *"The difference is inconclusive at this sample size (95% CI [a, b], MDE = m). This is not evidence of no effect."* Never "trending", never "directionally better".

## Metrics

**Primary**: incremental recovery rate = treatment recovery rate − control recovery rate, at the randomisation unit.

**Secondary** (never promoted to headline): incremental recovered revenue · revenue per contact · contacts per customer · phantom-risk value avoided · false-contact rate · abstention rate · downtime suppressions · wrongly-suppressed rate · unresolved-execution rate.

The renderer marks exactly one metric `primary: true`; zero or more than one fails the build.

Six recovery metrics stay distinct and are never collapsed: gross recovered · self-cured · attributed recovery · incremental recovery · incremental recovery rate · relative lift.

## Falsification tests

| # | Null condition | Expected | Failure means |
|---|---|---|---|
| 1 | All actions equally effective | A5 ≈ A3, CI includes zero | the AI is exploiting non-signal |
| 2 | Features carry no signal | no material uplift | leakage |
| 3 | `NO_ACTION` dominates | abstention > 80%, fewer contacts | bias toward acting |
| 4 | Labels permuted within seed | AUC ∈ (0.45, 0.55), uplift ≈ 0 | leakage |

All four run in CI and are reported in the submission, including where the project's own advantage disappears.

## Anti-rigging

The response function is written and **git-tagged before either scorer exists**; `test_response_function_frozen_before_scorers` asserts the commit ordering, and `test_simulator_unchanged_after_first_evaluation_run` compares file hashes. If the second fails, results are void and must be re-run.

Pre-registration is written to `experiments/preregistration.json` and git-tagged before the first evaluation run.

## Result status vocabulary

```
EXPECTED      what the design predicts — a hypothesis
OBSERVED      produced by a real run, recorded in EXPERIMENT_INDEX.md with commit + seeds
NOT YET RUN   the current state of every result in this project
```

**Never replace an EXPECTED value with a fabricated OBSERVED one.** If asked for results that do not exist, the correct answer is *"NOT YET RUN"*.
