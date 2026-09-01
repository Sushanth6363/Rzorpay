# FULL PLAN — UNIFIED RECOVERY ENGINE

**Role**: Principal Product Manager + Principal Architect + ML Lead, executing a Razorpay Track 3 AI Revenue Recovery submission.

**Preconditions**: architecture frozen (`p0.2-closure.md`) · dataset research complete (`docs/DATASET_RESEARCH.md`) · implementation specification exists (`p0.1`, `p0.2`, `p0.2-patch`) · **P0 methodology fixes applied (`strategy/STRATEGY.md`)** · **DGP documented (`docs/EXPERIMENT_METHODOLOGY.md`)**.

> Read `strategy/STRATEGY.md` alongside this document. It carries the twelve P0/P1 methodology fixes — safety-constrained exploration, the model-estimate vs causal-measurement separation, executable point-in-time validity, and the falsification suite — and its acceptance criteria gate implementation readiness.

**Task**: convert the frozen architecture into a convincing, working prototype. Do not redesign unless a genuine implementation blocker is found.

**The goal is not the largest system. It is the smallest system that convincingly proves:**

> AI can select the right recovery intervention — or abstain — while a shared safety/orchestration layer prevents unnecessary, conflicting, duplicated, or unsafe customer contacts.

---

# 1. CURRENT PROJECT POSITION

Established:

```
Existing ecosystem
        ↓
Independent recovery agents
        ↓
No shared recovery/contact state
        ↓
Potential duplicate/conflicting interventions
```

Introduced:

```
                    Unified Recovery Engine
                            │
            ┌───────────────┼────────────────┐
            ↓               ↓                ↓
         Validate        Diagnose        AI Recovery
            │               │                │
            └───────────────┼────────────────┘
                            ↓
                     Candidate actions
                            ↓
                       AI ranking
                            ↓
                     Policy filtering
                            ↓
                       Arbitration
                            ↓
                     Contact Ledger
                            ↓
                     Action / Abstain
                            ↓
                         Outcome
                            ↓
                Incremental measurement
                            ↓
                       Feedback loop
                            ↓
                       Model update
```

**The architecture is frozen. The next objective is evidence.**

---

# 2. STRATEGIC PRIORITY

```
P0 — AI recovery actually works
P0 — Contact safety actually works
P0 — Incremental recovery is measured correctly
P1 — Real-world calibration is incorporated
P1 — Feedback loop works
P1 — Multi-agent advantage is demonstrated
P2 — Dashboard / polish
P2 — Additional realism
```

**Never spend time on P2 while a P0 capability is broken.**

---

# 3. THE CORE PRODUCT THESIS — FIVE CLAIMS

**Claim 1 — Recovery qualification.** The system distinguishes a recoverable opportunity from a phantom / restricted / already-recovered one.

**Claim 2 — AI action selection.** Given `retry`, `payment link`, `reminder`, `method update`, `no action`, the AI ranks them by expected incremental recovery.

**Claim 3 — Safe orchestration.** Multiple agents cannot independently consume unlimited customer-contact opportunities. The shared ledger and arbitration layer enforce contact budget, customer cooldown, single-writer arbitration, idempotency, tenant isolation.

**Claim 4 — Incremental recovery.** The system separates *recovered because of the intervention* from *would have recovered anyway*. Self-cure is never counted as AI-generated recovery.

**Claim 5 — Learning loop.** Outcomes become future training data:

```
prediction → intervention → outcome → attribution → training example
          → new model → evaluation → promotion / rejection
```

## Evidence map — what proves each claim

| # | Claim | Evidence artefact | Phase |
|---|---|---|---|
| 1 | Recovery qualification | Stage 0 report split deterministic/probabilistic; phantom-risk value avoided; adversarial abstention rate | 7 |
| 2 | AI action selection | A5 vs A3 with CI; disagreement rate; calibration (Brier, slope) | 10–12 |
| 3 | Safe orchestration | 100-worker concurrency test; cap binds; idempotency; tenant isolation; arbitration trace | 2, 15 |
| 4 | Incremental recovery | Timestamp attribution; self-cure excluded; arm-level difference with CI | 16, 17, 20 |
| 5 | Learning loop | v1 → outcomes → v2 → gate → promote/reject → rollback, holdout locked | 18, 19 |

---

# 4. THE MOST IMPORTANT STRATEGIC RULE — NO DEMO MODEL

```
BAD                                 GOOD
dashboard                           real opportunity
    ↓ fake AI prediction                ↓ real features (point-in-time)
    ↓ hardcoded successful recovery     ↓ real model inference
                                        ↓ real policy filtering
                                        ↓ real arbitration
                                        ↓ real ledger reservation
                                        ↓ synthetic provider
                                        ↓ real outcome
                                        ↓ real attribution
```

**Every important number displayed in the dashboard must originate from the actual engine.** Enforced, not trusted:

```python
def test_no_hardcoded_metrics_in_the_ui():
    for widget in dashboard_widgets():
        assert widget.source_query is not None
        assert not widget.literal_values

def test_dashboard_renders_only_from_a_completed_run():
    with pytest.raises(NoRunSelected):
        render_dashboard(run_id=None)
```

---

# 5. RECONCILIATION WITH THE FROZEN ARCHITECTURE

Four implementation decisions to settle before code. None reopens the architecture.

### R1 — "Train on incremental recovery" is not directly implementable

Incremental recovery is a difference between arms, not a per-row label. No logged row carries it.

**Resolution — the closest valid analogue:**

```
S-learner: one model, action included as a feature

    p(x, a)      = P(recovery within attribution window | features x, action a)
    uplift(x, a) = p(x, a) − p(x, NO_ACTION)
    EV(x, a)     = uplift(x, a) × recoverable_paise − action_cost_paise
```

The **difference against `NO_ACTION` is the incremental estimate**. This is why `NO_ACTION` must be a *scored candidate*, not a fallback — it is the counterfactual baseline the EV calculation rests on.

`Δ̂` is named in full wherever it appears: **estimated incremental effect under the simulator's data-generating process**. It is used for ranking only. It is *not* an experimentally proven causal effect — that comes from the arm-level comparison. See `STRATEGY.md` P0 FIX 2 for the three-quantity separation.

Training data comes from the ε-exploration log with propensities (`p0.2` FIX 9). Without exploration, `p(x, a)` for rarely-chosen actions is estimated from a self-selected sample and the uplift is unreliable. **The 5% exploration is what makes Phase 11 possible at all.**

**Exploration is safety-constrained** (`STRATEGY.md` P0 FIX 1): the hard policy filter runs first, and the eligible set *is* the exploration pool. Exploration may override a VALUE abstention (`below_value_threshold`, `cost_exceeds_benefit`) but never a SAFETY abstention (`unexplained_shortfall`, `identity_unresolved`, `policy_indeterminate`, `payment_state_unknown`, `contact_cooldown`). A random seed can never produce an ineligible action.

### R2 — Disagreement rate is descriptive, not inferential

```
disagreement_rate  = decisions where argmax(AI) ≠ argmax(heuristic) / all decisions
                     descriptive · computed across 24,000 decisions (600 × 40 seeds)

outcome difference = A5 − A3, paired across 40 seeds, with CI
                     inferential · unit of analysis = seed
```

Computing a confidence interval at n = 24,000 would be the false-precision error identified in `p0.2-closure.md` §1.

### R3 — Anti-rigging discipline for Phases 6 and 12

Phase 6 correctly forbids making the response function identical to the heuristic. The inverse risk is quieter and worse: **author a response function containing patterns only CatBoost can capture, and you have authored the AI's victory.**

**Binding sequence — response function written and frozen before either scorer exists:**

```
1. write P(recovery | state, action); commit; git-tag it
2. write the heuristic scorer, tuned on INITIAL_TRAINING_SET (seeds 1–10)
3. train CatBoost, same seeds, same effort budget
4. pre-register the A5 vs A3 analysis
5. only then run on EXPERIMENT_SET (seeds 21–60)
```

Neither scorer's author inspects the response function's parameters while writing the scorer. In a two-person team, ideally different people write the response function and the heuristic. If impossible, the git history must show the response function frozen first — that record is the evidence, and an evaluator can check it.

**Pre-committed honest outcome**: if CatBoost does not beat the heuristic, that is the reported result.

### R4 — Calibration is gated on one manual check

`docs/DATASET_RESEARCH.md` returned **CONDITIONAL PASS**: NPCI and Samadhaan terms could not be verified automatically (NPCI returned HTTP 403).

- **Terms permit** → extract tables, hash them, use as generator priors.
- **Unclear or restrictive** → use published *ranges* from secondary reporting as priors, cite inline, redistribute nothing.

Either path satisfies Phases 4–5. Do the check on **day 1** so it is not discovered on day 8.

### Phase mapping — one plan, not two

`p0.2-closure.md` §11 defines 13 phases; this plan defines 22. Same work, different granularity.

| Frozen phase | This plan |
|---|---|
| 1 Domain models + database | 0, 1 |
| 2 Contact ledger + atomic reservation | 2 |
| 3 Stage 0 validation | 7 |
| 4 Stage 1 diagnosis | 8 |
| 5 Stage 2 candidate generation | 9 |
| 6 Heuristic + AI scoring | 10, 11, 13 |
| 7 Policy engine + arbitration | 14, 15 |
| 8 Payment state + downtime suppression | 3 |
| 9 Execution + reconciliation | 3 |
| 10 Outcome attribution | 16 |
| 11 Experiment runner | 4, 5, 6, 17, 20, 21 |
| 12 Feedback loop + model registry | 18, 19 |
| 13 Dashboard / demo | 22, 23 |

Where they differ in ordering, **the frozen plan wins** — in particular its rule that the experiment runner must execute end-to-end on an empty engine before Phases 7–16 count as done.

---

# 6. IMPLEMENTATION PHASES

## PHASE 0 — REPOSITORY AND ENVIRONMENT

**Deliver**: Python environment · database · dependency management · configuration · logging · pytest.

**Acceptance**: fresh environment → install → run tests → all foundational tests pass.

**Do not build frontend yet.**

## PHASE 1 — DOMAIN + DATABASE

**Implement**: `Merchant` · `Customer` · `Payment` · `RecoveryOpportunity` · `RecoveryAction` · `Agent` · `ContactBudget` · `ContactReservation` · `Decision` · `Outcome` · `Experiment` · `ModelVersion` · `AuditEvent`.

**Use**: integer paise · UTC timestamps · `merchant_id` tenant scope · explicit enums.

**Acceptance**: create / retrieve / update opportunity; tenant cannot access another tenant.

## PHASE 2 — CONTACT SAFETY CORE

**Build this BEFORE the AI.**

**Implement**: `ContactBudget` · `ContactReservation` · `ContactLedger` · `ReservationStateMachine` · `ArbitrationDecision`.

**Prove**: cap = 10 · 100 concurrent attempts · successful reservations ≤ 10.

**Test**: duplicate reservation · double release · double execute · execution unknown · expired reservation · cross-tenant reservation.

> Note: the test fixture uses `cap = 10`; the **shipped default remains 4/customer/month**, swept 2/4/6/8. Do not let the fixture leak into config.

This is one of the most important safety controls in the system.

## PHASE 3 — PAYMENT / EXECUTION SIMULATOR

Synthetic provider simulating: success · failure · timeout · ambiguous response · gateway outage.

**The recovery engine must not own actual payment retry execution:**

```
Recovery Engine → recommend / suppress → Payment infrastructure → execution
```

The engine emits `RECOMMEND_RETRY`, holds no retry-capable credential, and a static call-graph test proves no path from engine code to a retry API. This preserves retry ownership.

## PHASE 4 — DATA STRATEGY

Dataset research conclusion: **`USE_EXTERNAL_DATA_FOR_CALIBRATION`**.

Do NOT pretend public datasets contain payment-recovery causal outcomes — they do not; this was searched for directly and does not exist.

- **NPCI** → issuer / payment failure distributions, where legally usable
- **MSME Samadhaan** → B2B delayed-payment ageing / pendency distributions, where legally usable

These calibrate the synthetic environment. **They do not provide recovery labels.**

## PHASE 5 — REAL-DATA CALIBRATION

```
CalibrationConfig
  failure probability
  failure-type distribution
  issuer distribution
  B2B ageing distribution
```

```
real-world aggregate data → calibration parameters → synthetic generator → RecoveryOpportunity
```

Provenance preserved: calibration inputs carry `dataset_type = PUBLIC_REAL`; generated outcomes remain `dataset_type = SYNTHETIC`. The `CalibrationSource` protocol is structurally separate from `DatasetAdapter`, so a calibration source cannot emit opportunities or outcomes.

## PHASE 6 — SYNTHETIC RESPONSE MODEL

Create `P(recovery | state, action)` depending on: `failure_reason` · `amount` · `customer_history` · `time_since_failure` · `subscription_state` · `action` · `gateway_state`.

**Do NOT make the response function identical to the heuristic scorer**, or CatBoost has nothing to learn. Realistic but controlled patterns; must contain interactions a linear heuristic cannot express.

Its internal parameters are never visible to the feature builder (`p0.1-12`: `test_simulator_internals_are_not_reachable_from_the_engine`). Written and frozen **before** either scorer — see R3.

## PHASE 7 — STAGE 0

**Implement**: `VALID_RECOVERY` · `PHANTOM_RISK` · `RESTRICTED` · `ALREADY_RECOVERED` · `UNKNOWN`.

**Test**: TDS withholding · deliberate cancellation · already paid · invalid state.

**Demonstrate**:

```
₹1,00,000 apparent risk → TDS withholding → PHANTOM_RISK → ₹0 customer contacts
```

The value is **avoided unnecessary recovery effort**, not "revenue recovered." Deterministic and probabilistic accuracy are reported in separate tables; there is no single Stage 0 accuracy number.

## PHASE 8 — STAGE 1 DIAGNOSIS

`INSUFFICIENT_FUNDS` · `PAYMENT_METHOD_FAILURE` · `AUTHENTICATION_FAILURE` · `GATEWAY_FAILURE` · `CUSTOMER_CANCELLATION` · `EXPIRED_METHOD` · `TDS_WITHHOLDING` · `UNKNOWN`.

Diagnosis is made available to the AI scorer as a feature.

## PHASE 9 — CANDIDATE GENERATION

For each validated opportunity, generate feasible actions: `RETRY_LATER` · `SEND_PAYMENT_LINK` · `SEND_REMINDER` · `UPDATE_PAYMENT_METHOD` · `NO_ACTION`.

**The candidate generator must not bypass policy.**

## PHASE 10 — HEURISTIC BASELINE

A transparent heuristic answering *"what would a simple non-ML decision engine choose?"* Its ranking is logged. This is the AI comparison baseline. Tuned on `INITIAL_TRAINING_SET` with the same effort budget as the model.

## PHASE 11 — CATBOOST AI RECOVERY

Per R1: S-learner with action as a feature; `uplift = p(x,a) − p(x, NO_ACTION)`;

```
EV(a) = uplift(x, a) × recoverable_revenue − action_cost
```

then rank. Trained on `INITIAL_TRAINING_SET` (seeds 1–10) only.

**Calibration is a gate before EV is trusted** — Brier improved over baseline, calibration slope ∈ [0.85, 1.15]. Uncalibrated probabilities make the EV ranking arbitrary.

## PHASE 12 — PROVE THE AI IS NOT DECORATIVE

**Mandatory milestone.** Same opportunities, same candidate actions, same policy constraints, through heuristic and CatBoost.

Measure **decision disagreement rate**. All numbers come from the experiment, not from an example.

Also report **where** they disagree — by failure reason, amount band, ageing bucket. *"The AI diverges mainly on expired-method cases above ₹10,000"* is a far more interesting finding than a bare percentage, and nearly free to compute.

Measured on the **complete evaluation population** — no sampling, no illustrative examples. Report agreement rate, disagreement rate, the full 5×5 action-switch matrix, and `NO_ACTION` selection rate per scorer. For every disagreement case: heuristic EV, AI EV, actual outcome, attributed recovery.

Then determine whether AI-selected differences produce better outcomes (A5 − A3, seed-level, with CI). **If they do not, report that honestly. Do not tune the experiment solely to make AI win** — enforced by `test_simulator_unchanged_after_first_evaluation_run`, not by promise.

## PHASE 13 — ABSTENTION

`NO_ACTION` as a genuine AI decision — generated, scored and ranked alongside interventions, never a fallback reached by exhaustion. Triggers: high self-cure probability · low incremental value · recent contact (cooldown) · gateway outage · policy uncertainty · ambiguous identity · unknown payment state.

Each trigger is tagged `SAFETY` or `VALUE` (`STRATEGY.md` P0 FIX 1), which determines whether exploration may override it. The decision record stores `no_action_probability`, `selected_action_probability`, `estimated_incremental_effect`, `expected_value`, `abstention_reason` and `abstention_kind`.

**Measure**: abstention rate · contacts avoided · revenue/contact · incremental recovery · **wrongly-suppressed rate** (cases abstained on that another arm recovered by acting).

Reporting only abstention's benefit and never its cost is the gap a hostile evaluator finds in ten seconds.

This is one of the strongest ways to demonstrate the AI optimises recovery rather than message volume.

## PHASE 14 — POLICY LAYER

```
AI → candidate ranking → policy → arbitration
```

Never `AI → direct execution`. Policy overrides are tested explicitly; a policy-blocked candidate reserves nothing.

## PHASE 15 — MULTI-AGENT ARBITRATION

Agents: `SubscriptionAgent` · `PaymentFailureAgent` · `ReminderAgent` · `AbandonedCartAgent`, each producing proposals.

```
proposals → shared customer state → contact budget → AI scores
          → policy → arbitration → one selected action
```

Demonstrate collision prevention with a trace showing which proposals were suppressed and why.

## PHASE 16 — OUTCOME ATTRIBUTION

Record: contact timestamp · payment timestamp · action · payment state.

**Critical rule:**

```
payment_timestamp < contact_timestamp  →  SELF_CURED  →  attributed_recovery = 0
```

Ordering is checked against **delivery** timestamps, not send timestamps, and precedes every attribution-window test. The system never claims credit for recovery that happened before contact.

## PHASE 17 — INCREMENTAL EXPERIMENT

```
A1     Independent-agent baseline
A2ns   Unified without Stage 0
A2     Unified + Stage 0
A3     Unified + downtime
A5     Unified + downtime + AI
```

Same opportunity population · same initial state · same seed · same contact budgets, hash-asserted. `A4` is an alias of `A3`, not a sixth arm.

## PHASE 18 — FEEDBACK LOOP

```
Model v1 → predictions → outcomes → attribution → training dataset
         → Model v2 → selection → holdout evaluation → promotion gate
```

Track `model_version` · `feature_version` · `training_dataset_version`. **Do not leak future outcomes into features** — every feature carries `as_of`, asserted ≤ `decision_timestamp`.

## PHASE 19 — MODEL GOVERNANCE

Promotion requires **all four**: recovery performance acceptable · calibration acceptable · no safety regression · no material false-contact regression.

**The newest model is not automatically the production model.** Rollback is exercised explicitly.

## PHASE 20 — EXPERIMENT ANALYSIS

**Primary metric:**

```
Incremental Recovery Rate = Treatment Recovery Rate − Control Recovery Rate
```

**Secondary**: incremental recovered revenue · revenue/contact · contacts/customer · phantom-risk value avoided · false-contact rate · abstention rate · downtime suppressions.

**Report**: point estimate · confidence interval · sample size · **randomisation unit**.

Do not claim production uplift. Use **"under the synthetic data-generating process"** for every synthetic result.

## PHASE 21 — OPTIONAL CRITEO VALIDATION

Run separately. Purpose: **validate the measurement/uplift machinery**. Not: train a payment recovery model. Never mixed with the recovery experiment; documented as *measurement-method validation*.

Licence: **CC BY-NC-SA 4.0** — non-commercial, attribution required, downloaded at runtime and never vendored into the repo.

## PHASE 22 — FINAL DEMO

One coherent story, one customer followed end-to-end, then four short proofs.

```
BEAT 1  ₹50,000 failed payment
        → Stage 0: VALID_RECOVERY
        → Stage 1: INSUFFICIENT_FUNDS
        → candidate actions → AI scoring → payment link = highest expected value
        → policy check → arbitration → contact budget reservation → message sent
        → customer pays → incremental attribution → recovery recorded

BEAT 2  high self-cure probability → AI → NO_ACTION
        (the AI declining to act is the strongest single moment in the demo)

BEAT 3  two agents compete → arbitration → one contact
        with the trace showing which was suppressed and why

BEAT 4  gateway outage → retry suppressed → batched on resolution

BEAT 5  execution timeout → EXECUTION_UNKNOWN → reconciliation
        (nobody else will show this; it is the clearest signal of engineering seriousness)

CLOSE   results table with CIs, then: what this does not prove
```

---

# 7. BUILD SCHEDULE — 10 DAYS, 2 PEOPLE

Two tracks touching different files, so they run in parallel without conflict. **A = engine/safety · B = data/experiment.**

| Day | Track A (engine + safety) | Track B (data + experiment) | Gate at end of day |
|---|---|---|---|
| **1** | Phase 0–1: env, schema, domain models, integer paise, `FixedClock`, tenant scope | **Licence check (R4)** · Phase 6: write and **freeze the response function** | Schema applies on SQLite WAL; response function git-tagged |
| **2** | **Phase 2: contact safety core** — `transition()`, six states, CAS, `consumption_basis` | Phase 4–5: calibration config; generator with seeded RNG + content hash | **HARD GATE**: 100-worker test green; cap binds; reproducibility hash stable |
| **3** | Phase 3: synthetic provider + reconciliation ladder | Phase 17 skeleton: experiment runner runs **end-to-end on an empty engine** | Runner produces a report shape; ambiguous-send resolves three ways |
| **4** | Phase 7: Stage 0 · Phase 8: diagnosis | Phase 16: outcome attribution + timeline rules | Self-cure test green; phantom-risk report split |
| **5** | Phase 9: candidate generation · Phase 14: policy layer | Phase 10: heuristic scorer, tuned on seeds 1–10 | Policy-blocked candidate reserves nothing; heuristic frozen |
| **6** | Phase 15: multi-agent arbitration + A1 baseline | Phase 11: CatBoost, seeds 1–10, calibration checked | Two agents → one contact, with trace; Brier + slope reported |
| **7** | Phase 13: abstention · downtime suppression wiring | **Phase 12: AI-vs-heuristic disagreement run** | All triggers fire; disagreement rate is a real number |
| **8** | Phase 22: demo script, five cases, run live | **Phase 17/20: full experiment, 40 seeds, 5 arms** + analysis | Results table with CIs; MDE published; guardrails reported |
| **9** | Phase 23: dashboard — trace screen first | Phase 18–19: feedback loop v1→v2→gate→rollback | Trace screen renders from the DB; promotion gate decided |
| **10** | README, claim-language scan, freeze, tag | Phase 21 Criteo (only if days 1–9 are clean) | Forbidden-phrase scan clean; repo tagged |

## The cut line

If the schedule slips, cut in **this order, from the top**:

```
1. Phase 21 Criteo validation          (stretch; nothing depends on it)
2. Dashboard beyond the trace screen   (one screen is enough)
3. Phase 18–19 feedback loop           (demote to described design + the v1→v2 script only)
4. Phase 15 fourth agent               (two agents prove collision as well as four)
5. Stage 0 probabilistic checks        (keep the deterministic TDS gate)
```

**Never cut**: Phase 2 (contact safety) · Phase 16 (attribution) · Phase 17/20 (experiment). Those three are the thesis.

**Day-2 hard gate.** If the 100-worker reservation test is not green at end of day 2, stop feature work and fix it. A broken ledger invalidates every number produced afterwards, and the failure is silent — the system will look like it works.

---

# 8. DASHBOARD STRATEGY

The dashboard is an **observability layer**, not a separate product. Build *"Why did the engine do this?"* first; build nothing else until it works.

```
Opportunity          #47 · ₹50,000 · merchant M_A · customer C_112
Stage 0              VALID_RECOVERY
Stage 1              INSUFFICIENT_FUNDS  (confidence 0.81)

Candidate actions              p(recovery)   uplift   Expected value
  payment_link                     0.61       0.29      ₹14,500   SELECTED
  reminder                         0.44       0.12      ₹ 6,000
  recommend_retry                  0.38       0.06      ₹ 3,000
  method_update                    0.52       0.20      ₹10,000   blocked: live_promise
  no_action                        0.32          —            —

Policy               allowed (opt-out: no · dispute: no · cooldown: 96h since last)
Agent proposals      SubscriptionAgent(₹2,100) · PaymentFailureAgent(₹14,500)
Arbitration          PaymentFailureAgent wins · 1 suppressed (lower EV)
Reservation          res_8f21 · reserved → executed · basis CONFIRMED_SENT
Outcome              paid T+31h → RECOVERED_ATTRIBUTED → ₹50,000
Provenance           model v1 · features v3 · policy v2 · arm A5 · seed 34
```

Every field is a column in `decision_trace`. The screen is a rendering of that view — **no LLM writes any of it**, which is also the answer when an evaluator asks whether the explanation is post-hoc narration.

Then, only if time remains: recovery metrics · contact savings · phantom-risk filtering · agent collisions · downtime suppression · feedback/model versions.

---

# 9. EVIDENCE HIERARCHY — NEVER COLLAPSED

| Level | Evidence | Proves | Never claims |
|---|---|---|---|
| **1** | Unit / integration tests | correctness of the pipeline | anything about recovery |
| **2** | Concurrency + tenant-isolation tests | safety properties hold under stress | production-scale safety |
| **3** | Synthetic experiment (5 arms, 40 seeds) | behaviour under the authored, calibrated simulator | real-world uplift |
| **4** | Public calibration data (NPCI, Samadhaan) | selected environmental distributions are externally grounded | that outcomes are real |
| **5** | Criteo uplift validation *(optional)* | the measurement machinery is correct on real randomised data | anything about payment recovery |

Levels 4 and 5 are the easiest to overstate. Level 4 means *the failure distribution came from NPCI* — not that the results are real. Level 5 means *the estimator is correct* — it says nothing about recovery.

---

# 10. WHAT NOT TO OPTIMISE

```
DO NOT optimise for            OPTIMISE for
largest recovered ₹ figure     incremental recovery
most contacts                  contact efficiency
highest raw conversion         safety
most complex architecture      correct attribution
most agents                    reproducibility
largest model                  explainability
most impressive dashboard
```

---

# 11. STOP CONDITIONS — CHECKLIST WITH EVIDENCE

Stop building when every row has a green artefact.

| # | Condition | Evidence artefact |
|---|---|---|
| 1 | Stage 0 removes phantom opportunities | phantom-risk report, split deterministic/probabilistic |
| 2 | AI ranks multiple recovery actions | `decision_trace` with ≥3 scored candidates and EVs |
| 3 | AI sometimes selects differently from the heuristic | disagreement rate + breakdown by failure reason |
| 4 | AI can abstain | 7 trigger tests green; abstention rate per arm |
| 5 | Policy can override AI | trace with top candidate blocked; no reservation made |
| 6 | Multiple agents cannot exceed contact budgets | 100-worker test; `reserved + consumed ≤ cap` |
| 7 | Duplicate contacts are prevented | same-idempotency-key test; one reservation, one slot |
| 8 | Downtime suppresses retry recommendations | 40 failures, one issuer, suppressed, batched on resolution |
| 9 | Ambiguous execution reconciles safely | three ladder outcomes; never re-sent; `unresolved_rate` reported |
| 10 | Self-cure is not falsely attributed | payment-before-delivery test; `SELF_CURED`, no decision id |
| 11 | Incremental recovery is measured | A2 vs A1 with CI at seed level; MDE published |
| 12 | Outcomes feed the model-update loop | v1→v2→gate→promote/reject→rollback, holdout locked |
| 13 | Real public data calibrates the simulator | calibration provenance block with licence and hash |
| 14 | All claims appropriately scoped | forbidden-phrase scan clean; capability split in six locations |

**At 14/14: STOP BUILDING.** Move to: testing → experiment → analysis → demo → presentation.

---

# 12. FINAL RAZORPAY EVALUATOR TEST

Rehearse until each answer is one breath long.

| Question | Answer |
|---|---|
| *Where is the AI?* | Stage 2 action selection. |
| *What does it actually predict?* | Expected incremental recovery for each feasible intervention — `p(x,a) − p(x, NO_ACTION)`, times recoverable value, minus cost. |
| *Why isn't this just automation?* | The AI selects among competing interventions and can abstain, while arbitration and policy enforce system-level safety. |
| *Why do you need the shared ledger?* | Independent agents lack a unified customer-contact budget and can make conflicting or redundant interventions. Here is the trace where three would have fired and one did. |
| *How do you know recovery was caused by you?* | Timestamp-aware incremental attribution and treatment/control measurement; self-cures are excluded. |
| *Is your data real?* | Environmental distributions are calibrated using public real-world data where permitted, while intervention outcomes remain synthetic. We do not claim production recovery uplift. |
| *Why should Razorpay care?* | The system sits above individual recovery agents as a shared decision-and-safety layer, allowing AI recovery optimisation without letting independent agents compete for customer attention unchecked. |
| *Which number do you trust least?* | The payer-response function. I wrote it. That is why the claim is a delta against baselines on identical data, not an absolute. |
| *What did the AI get wrong?* | *(have a real case ready — a wrongly-suppressed contact or a miscalibrated bucket. Having one is worth more than not having one.)* |

---

# 13. FINAL SUCCESS CONDITION

The evaluator observes:

```
REALISTIC INPUT → VALIDATE → DIAGNOSE → AI RECOVERY DECISION → POLICY
   → MULTI-AGENT ARBITRATION → CONTACT LEDGER → SAFE EXECUTION
   → REALISTIC SYNTHETIC OUTCOME → INCREMENTAL ATTRIBUTION
   → EXPERIMENT → FEEDBACK → NEXT MODEL
```

and concludes:

> **This is not an AI model attached to a payment workflow. It is a governed AI recovery decision system with a shared safety and orchestration layer.**

That is the standard the implementation must meet.

---

# FINAL EXECUTION RULE

Do not ask *"what feature can we add next?"*

Ask *"what evidence is still missing to prove the core thesis?"* — then implement only what produces that evidence.

The architecture is frozen. The dataset research is complete. The schedule is set.

**Now build, measure, falsify, and prove.**

Start: Day 1, Track A — Phase 0. Track B — the licence check, then freeze the response function.
