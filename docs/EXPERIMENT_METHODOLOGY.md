# EXPERIMENT METHODOLOGY — DATA-GENERATING PROCESS

**Purpose**: an evaluator reading this document alone must be able to answer

> *How exactly did a simulated customer decide whether to recover?*

without reading the source. Reproducibility means the numbers can be regenerated **and** the mechanism can be criticised.

**Status**: specification. Values marked `[calibrated]` are set from public aggregate data (`docs/DATASET_RESEARCH.md`); values marked `[authored]` are chosen by this project and are the numbers to distrust first.

**Standing disclosure**: every outcome produced by this process is **synthetic**. Public real-world data grounds selected environmental distributions only. No recovery outcome in this repository is observed.

---

# 1. GENERATION ORDER

Deterministic given `(seed, reference_timestamp, config)`. No wall-clock reads anywhere.

```
GeneratorConfig{seed, reference_timestamp, CalibrationConfig, ...}
        ↓
merchants  →  customers  →  payment/subscription/cart/invoice events
        ↓
failure injection            [calibrated]
        ↓
outage injection             [calibrated]
        ↓
latent payer attributes      [authored]  ← never visible to the engine
        ↓
RecoveryOpportunity set  →  content_hash
```

Every entity draws from its own RNG substream, `Random(sha256(seed | entity_id))`, so generation is order-independent and identical opportunities receive identical draws across arms (common random numbers).

All money is **integer paise**. All timestamps are offsets from `reference_timestamp`.

---

# 2. FAILURE DISTRIBUTIONS `[calibrated]`

Per-issuer failure probability and failure-type mix are set from published NPCI bank-wise technical-decline and business-decline statistics, subject to the licence check recorded in `docs/DATASET_RESEARCH.md` §9. If terms do not permit extraction, published *ranges* from secondary reporting are used instead and cited inline.

| Parameter | Source | Shape |
|---|---|---|
| `p_failure_by_issuer` | NPCI TD% + BD% per bank | per-issuer probability, remitter and beneficiary roles distinguished |
| `failure_type_mix` | NPCI TD vs BD split, mapped to the diagnosis taxonomy | categorical distribution |
| `issuer_share` | NPCI approved-transaction volume per bank | categorical distribution over issuers |
| `b2b_ageing` | MSME Samadhaan age-category pendency reports | distribution over ageing buckets |

Failure types map to Stage 1 diagnosis categories:

```
INSUFFICIENT_FUNDS · PAYMENT_METHOD_FAILURE · AUTHENTICATION_FAILURE
GATEWAY_FAILURE · CUSTOMER_CANCELLATION · EXPIRED_METHOD · TDS_WITHHOLDING · UNKNOWN
```

`GATEWAY_FAILURE` is not drawn independently — it is produced by the outage process (§4).

**Provenance**: the extracted table is hashed and stamped `dataset_type = PUBLIC_REAL` in every run's provenance block. Generated outcomes remain `dataset_type = SYNTHETIC`.

---

# 3. LATENT PAYER ATTRIBUTES `[authored]`

Each synthetic customer carries latent attributes that drive their behaviour. **These are never visible to the engine** — the simulator hands the engine an event view, and every `_`-prefixed field is unreachable (`p0.1-12`, `test_simulator_internals_are_not_reachable_from_the_engine`).

| Attribute | Range | Meaning |
|---|---|---|
| `_intent` | [0, 1] | genuine intent to pay |
| `_liquidity` | [0, 1] | ability to pay now; recovers over time |
| `_channel_affinity` | per channel | responsiveness to link vs reminder vs method-update |
| `_self_cure_propensity` | [0, 1] | probability of resolving without contact |
| `_fatigue` | [0, 1] | sensitivity to repeated contact |
| `_deliberate_cancel` | bool | subscription cancellations that must never be chased |

---

# 4. OUTAGE PROCESS `[calibrated]`

Outages are issuer-scoped and time-bounded. During an outage window for issuer *i*:

- payments on issuer *i* fail with elevated probability, typed `GATEWAY_FAILURE`
- a retry attempted inside the window succeeds with probability ≈ 0
- other issuers are unaffected

Outage count and duration are drawn per seed; severity is set from the NPCI technical-decline range for that issuer. The **downtime signal** delivered to arms `A3`/`A5` reports the outage with the same start/end boundaries the process used — this is what makes `A3 − A2` a clean measurement of consuming a *correct* signal.

Arms `A1`, `A2ns`, `A2` do not receive the signal. That asymmetry is deliberate, declared in `arm.signals_enabled`, and printed in the results table.

---

# 5. SELF-CURE MECHANISM `[authored]`

Self-cure is generated **independently of any intervention**, before any decision is made. This is the property that makes attribution testable rather than circular.

```
For each opportunity, draw a self-cure time:

    T_selfcure ~ Exponential(rate = λ(_intent, _liquidity, failure_type))

    λ is highest for INSUFFICIENT_FUNDS (liquidity returns)
    λ is near zero for EXPIRED_METHOD and CUSTOMER_CANCELLATION
    λ = 0 when _deliberate_cancel is true

If T_selfcure ≤ observation_window and no intervention was delivered before it,
the payment occurs at T_selfcure and the outcome is SELF_CURED.
```

**The self-cure clock runs regardless of what the engine does.** A payment arriving before the first delivered intervention is `SELF_CURED` and attributed zero — checked against *delivery* timestamps, not send timestamps.

Because all arms face identical seeded data and identical latent attributes, **self-cure rate must agree across arms to within 2pp**. A larger gap means the harness is broken, and it is reported as a validity check rather than a result.

---

# 6. RESPONSE FUNCTION `[authored]` — THE CENTRAL OBJECT

`P(recovery | state, action)`. This is the number to distrust first, and the submission says so.

```
logit P(recover | x, a) =
      β0
    + β_intent      · _intent
    + β_liquidity   · _liquidity(t)                     # recovers with time since failure
    + β_action[a]                                       # base effect per action
    + β_fit[a, failure_type]                            # INTERACTION: action × diagnosis
    + β_channel[a]  · _channel_affinity[channel(a)]     # INTERACTION: action × customer
    + β_amount      · log1p(amount_paise)
    + β_fatigue     · _fatigue · contacts_recent
    + β_outage[a]   · outage_active(issuer)             # retry ≈ 0 during outage
    + ε,   ε ~ Logistic(0, σ)                           # irreducible noise
```

**The `β_fit` and `β_channel` interaction terms are the learnable structure.** They mean the best action depends jointly on failure type and customer attributes — for example, a method-update outperforms a payment link on `EXPIRED_METHOD` but not on `INSUFFICIENT_FUNDS`. A scorer that ignores the interaction leaves value on the table; one that captures it does better.

Two anti-rigging constraints, both checkable:

1. **The response function is written and git-tagged before either scorer exists.** `test_response_function_frozen_before_scorers` asserts the commit ordering.
2. **It is not modified after the first evaluation run.** `test_simulator_unchanged_after_first_evaluation_run` compares file hashes. If it fails, the results are void and must be re-run.

It is deliberately *not* identical to the heuristic scorer — otherwise there is nothing to learn — and deliberately *not* constructed to contain patterns only a gradient-boosted tree can find. The falsification suite (§10) is what detects a violation of the second, softer constraint.

`σ` is set so that the Bayes-optimal policy is meaningfully better than random but meaningfully worse than perfect. Its value is published; the sensitivity sweep re-runs the comparison at ±20%.

---

# 7. ACTION EFFECTS `[authored]`

| Action | Effect channel | Cost | Notes |
|---|---|---|---|
| `RECOMMEND_RETRY` | `β_action` + `β_outage` | low | near-zero effect during an outage; engine recommends only, never executes |
| `SEND_PAYMENT_LINK` | `β_action` + `β_channel[link]` | medium | strongest on `INSUFFICIENT_FUNDS` once liquidity recovers |
| `SEND_REMINDER` | `β_action` + `β_channel[reminder]` | low | weak but cheap |
| `UPDATE_PAYMENT_METHOD` | `β_action` + `β_fit[·, EXPIRED_METHOD]` | medium | strongest on `EXPIRED_METHOD`, weak elsewhere |
| `NO_ACTION` | baseline | zero | the counterfactual `Δ̂` is measured against |

Every action consumes exactly one contact slot except `NO_ACTION`, which consumes none.

---

# 8. RANDOMISATION AND SEEDS

## Seed roles

| Role | Seeds | Used for | Never used for |
|---|---|---|---|
| `INITIAL_TRAINING_SET` | 1–10 | train v1; tune the heuristic with an equal effort budget | any reported comparison |
| `MODEL_SELECTION_SET` | 11–15 | the promotion gate (v2 vs v1) | training, reported numbers |
| `FINAL_HOLDOUT_SET` | 16–20 | touched once, after promotion is decided | training, feature selection, thresholds, promotion |
| `EXPERIMENT_SET` | 21–60 | the A1–A5 comparisons with v1 pinned; its outcomes train v2 | evaluating v2 |

`FINAL_HOLDOUT_SET` is behind `HoldoutGate`, which raises until promotion is final.

## Assignment

**Simulation mode (this experiment).** All arms consume the identical opportunity set and the identical arm-blind world model, hash-asserted. The unit of analysis is the **seed**, n = 40. Analysis is paired: per-seed differences, t-interval on the mean of differences, Wilcoxon signed-rank as the direction check.

**Randomised mode (specified, not run here).** Randomisation unit is `(merchant_id, canonical_customer_id)`, assigned deterministically as `sha256(experiment_id | merchant_id | canonical_customer_id) mod k`, stratified on merchant, opportunity-count bucket, and amount decile.

## Exploration probability

ε = 0.05 of **eligible** opportunities in arm `A5` only. Deterministic: `hash(experiment_id | opportunity_id) % 100 < 5`.

Exploration selects uniformly among **policy-eligible** actions — never among raw candidates. It may override a `VALUE` abstention (`below_value_threshold`, `cost_exceeds_benefit`) but never a `SAFETY` abstention (`unexplained_shortfall`, `identity_unresolved`, `policy_indeterminate`, `payment_state_unknown`, `contact_cooldown`). See `strategy/STRATEGY.md` P0 FIX 1.

Every decision records its `propensity`: `1/len(eligible)` when explored, `1.0` when exploited.

---

# 9. WHAT THE ENGINE SEES

The engine receives an **event view**, not simulator state:

```
VISIBLE     payment_id, merchant_id, canonical_customer_id, amount_paise,
            failure_code, failure_timestamp, method, issuer,
            prior contact history (as of decision time), prior failure history,
            subscription state, invoice ageing, downtime signal (A3/A5 only)

HIDDEN      every _-prefixed latent attribute, T_selfcure, the response function's
            parameters, the outcome, and anything with observed_at > decision_timestamp
```

Enforced by `test_simulator_internals_are_not_reachable_from_the_engine` and the point-in-time invariant in `strategy/STRATEGY.md` P0 FIX 3.

---

# 10. FALSIFICATION CONDITIONS

Four null configurations run in CI. Each is a setting where the AI **should not** show an advantage; if it does, the cause is leakage or simulator bias and must be investigated before any result is reported.

| # | Configuration | Expected |
|---|---|---|
| 1 | `EqualEffectsResponse` — all actions equally effective | A5 ≈ A3; CI includes zero |
| 2 | `ShuffledFeatures` — features carry no signal | no material uplift; predictions ≈ base rate |
| 3 | `NoActionDominatesResponse` — every intervention is net-negative | abstention > 80%; contacts/customer below A3 |
| 4 | Labels permuted within seed | AUC ∈ (0.45, 0.55); mean uplift ≈ 0 |

Results from all four are reported in the submission. Showing the settings where the project's own advantage disappears is more credible to a technical evaluator, not less.

---

# 11. REPRODUCIBILITY

```
same seed + same reference_timestamp + same config  =  identical opportunity set
```

Verified by `dataset_hash` — SHA-256 over canonical JSON of config plus opportunities, sorted keys, integer money. The hash is stable across processes, across machines, and across calendar days; three tests assert exactly that.

Every run's report carries:

```
experiment_id · dataset_id · dataset_version · dataset_type · seed · model_version
+ calibration_sources[] (id, version, licence, content_hash)
+ code_version (git sha) · policy_version · features_version
```

`make eval` regenerates every number in the submission from the seed list alone.

---

# 12. KNOWN LIMITATIONS OF THIS PROCESS

1. **The response function is authored.** It is the dominant error term and it carries no confidence interval. No sample size fixes this.
2. **Calibration grounds the environment, not the outcomes.** Real NPCI rates set how often and why payments fail. How customers respond to being contacted is invented.
3. **Interaction structure is a modelling choice.** `β_fit` and `β_channel` were chosen because action-fit plausibly depends on failure type. That plausibility is an argument, not evidence.
4. **Self-cure rates are authored**, and self-cure is the quantity that most directly determines measured incremental recovery.
5. **Tight confidence intervals describe sampling error inside this simulator.** They say nothing about distance from the real-world value.

Every result derived from this process is reported with the phrase **"under the synthetic data-generating process."**
