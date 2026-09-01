# STRATEGY.md — UNIFIED RECOVERY ENGINE

**Status**: architecture frozen (`p0.2-closure.md`) · dataset research complete (`docs/DATASET_RESEARCH.md`) · **P0 fix pass applied**.
**Companion**: `strategy/full_plan.md` carries the 22-phase breakdown and the 10-day schedule. This document carries the methodology that makes the evidence defensible.

**Thesis:**

> AI can select the right recovery intervention — or abstain — while a shared safety/orchestration layer prevents unnecessary, conflicting, duplicated, or unsafe customer contacts.

**What this pass defends against.** Seven rejections a strong evaluator can reach, and where each is answered:

| Rejection | Answered by |
|---|---|
| "just a rules engine" | FIX 5, FIX 6 — measured disagreement + A5 vs A3 outcome |
| "AI theater" | FIX 6, FIX 12 — falsification tests; pre-committed honest null |
| "causal claims without causal evidence" | FIX 2 — model estimate vs experimental measurement, never collapsed |
| "unsafe exploration" | FIX 1 — safety filter precedes exploration; value/safety trigger split |
| "data leakage" | FIX 3 — executable point-in-time invariant, fails CI |
| "uncontrolled agent automation" | FIX 7, FIX 8 — five separated deciders; retry ownership outside the engine |
| "a dashboard over a simulator" | §4, FIX 11 — every number from the engine; DGP fully documented |

---

# P0 FIX 1 — SAFETY-CONSTRAINED EXPLORATION

## The invariant

**Exploration is not permission to execute any action.** The hard safety/policy filter runs *before* the exploration pool exists.

```
RecoveryOpportunity
        ↓
Stage 0 — Validate
        ↓
Stage 1 — Diagnose
        ↓
Candidate Generation
        ↓
HARD SAFETY / POLICY FILTER          ← eligibility decided here, once
        ↓
Eligible Actions                     ← this set IS the exploration pool
        ↓
AI Decision
        ↓
Exploration OR Exploitation          ← both draw only from Eligible Actions
        ↓
Arbitration
        ↓
Contact Budget / Ledger
        ↓
Execution
```

An action is removed from the pool if it violates any of: customer opt-out · customer cooldown · contact budget · merchant policy · legal restrictions · payment state · already-recovered state · gateway outage state · retry ownership · action-specific eligibility · tenant isolation.

```
Candidate actions:  RETRY · PAYMENT_LINK · REMINDER
Gateway outage = TRUE
Eligible:           PAYMENT_LINK · REMINDER
RETRY is removed BEFORE exploration.
```

## The tension this creates, and the resolution

Constraining exploration to eligible actions is necessary but not sufficient. A second question sits underneath it:

> If exploitation would have chosen `NO_ACTION`, may exploration override that and contact the customer?

Both answers cost something:

- **Never override** → no counterfactual data for the *intervention vs no-intervention* contrast, which is exactly the contrast `Δ̂` needs (FIX 2). Uplift estimation becomes impossible.
- **Always override** → the system contacts people it judged should not be contacted, which is the "unsafe exploration" rejection.

**Resolution — split the abstention triggers by kind.** Exploration may override a *value* judgment. It may never override a *safety* judgment.

| Trigger | Kind | Exploration |
|---|---|---|
| `unexplained_shortfall` (Stage 0 confidence below τ) | **SAFETY** | forbidden |
| `identity_unresolved` | **SAFETY** | forbidden |
| `policy_indeterminate` | **SAFETY** | forbidden |
| `payment_state_unknown` | **SAFETY** | forbidden |
| `contact_cooldown` | **SAFETY** | forbidden |
| `below_value_threshold` | **VALUE** | permitted |
| `cost_exceeds_benefit` | **VALUE** | permitted |

When a SAFETY trigger fires, the eligible set collapses to `{NO_ACTION}` and there is nothing to explore. When only a VALUE trigger fires, exploration may select an intervention — and that is the case that yields the counterfactual data.

Exploration is additionally bounded: ε = 0.05 of *eligible* opportunities, deterministic (`hash(experiment_id | opportunity_id) % 100 < 5`), and it consumes contact budget through the same ledger path as any other action. It gets no privileges anywhere.

## Implementation

```python
def select_action(ctx, scores, policy, rng_free=False) -> Decision:
    eligible = policy.hard_filter(ctx, ctx.candidates)      # 11 constraints, before anything
    assert ActionType.NO_ACTION in eligible                 # always available

    if policy.safety_triggers_fired(ctx):                   # SAFETY kind
        return Decision.abstain(reason=policy.first_safety_trigger(ctx),
                                explorable=False, eligible=eligible)

    exploit = max(eligible, key=lambda a: scores[a].expected_value)

    if not is_exploration_slot(ctx.experiment_id, ctx.opportunity_id):
        return Decision.exploit(exploit, eligible=eligible, propensity=1.0)

    chosen = ctx.rng.choice(eligible)                       # eligible ONLY — never candidates
    return Decision.explore(chosen, eligible=eligible,
                            propensity=1.0 / len(eligible), would_have_chosen=exploit)
```

`policy.hard_filter` is the single source of eligibility. No other code path may construct an action set.

## Tests — a random seed must never be able to create an invalid action

```python
@given(seed=integers(), ctx=recovery_contexts())
def test_exploration_can_never_produce_an_ineligible_action(seed, ctx):
    d = select_action(ctx, scores(ctx), POLICY, rng=Random(seed))
    assert d.action in POLICY.hard_filter(ctx, ctx.candidates)

def test_exploration_cannot_bypass_policy():
    open_dispute(M, C)
    for s in range(2000):
        assert select_action(ctx(M, C), scores, POLICY, rng=Random(s)).action is ActionType.NO_ACTION

def test_exploration_cannot_bypass_contact_budget():
    exhaust_budget(M, C)
    for s in range(2000):
        d = select_action(ctx(M, C), scores, POLICY, rng=Random(s))
        assert d.action is ActionType.NO_ACTION
    assert budget(M, C).reserved_count + budget(M, C).consumed_count <= budget(M, C).cap

def test_exploration_cannot_contact_opted_out_customers():
    opt_out(M, C)
    for s in range(2000):
        assert select_action(ctx(M, C), scores, POLICY, rng=Random(s)).action is ActionType.NO_ACTION
    assert sender.sent == []

def test_exploration_cannot_retry_during_known_outage():
    outage(issuer="HDFC")
    for s in range(2000):
        d = select_action(ctx_issuer("HDFC"), scores, POLICY, rng=Random(s))
        assert d.action is not ActionType.RECOMMEND_RETRY

def test_exploration_cannot_cross_tenant_boundaries():
    for s in range(2000):
        d = select_action(ctx(M_A, C), scores, POLICY, rng=Random(s))
        assert d.merchant_id == "M_A"
        assert reservations_for(M_B) == []

def test_exploration_never_overrides_a_safety_abstention():
    for trig in SAFETY_TRIGGERS:
        fire(trig)
        for s in range(500):
            assert select_action(ctx(M, C), scores, POLICY, rng=Random(s)).action is ActionType.NO_ACTION

def test_exploration_may_override_a_value_abstention():
    set_all_candidate_ev(50_00)                       # below_value_threshold
    outcomes = {select_action(ctx(M, C), scores, POLICY, rng=Random(s)).action for s in range(500)}
    assert len(outcomes) > 1                          # counterfactual data is actually collected
```

---

# P0 FIX 2 — THE INCREMENTAL RECOVERY CLAIM

Three quantities. Three names. Never collapsed into one.

### 1 — Model output (an estimate, not an effect)

```
p̂(x, a) = P̂(Y = 1 | X = x, A = a)

  Y = recovery outcome within the attribution window
  X = information available at decision time (point-in-time, FIX 3)
  A = action
```

Name it **action-conditional recovery probability**. It is a prediction.

### 2 — Derived quantity (a model-based estimate)

```
Δ̂(x, a) = p̂(Y=1 | x, a) − p̂(Y=1 | x, NO_ACTION)
```

Name it, in full, every time it appears:

> **estimated incremental effect under the simulator's data-generating process**

It is **not** an experimentally proven causal uplift at the individual level. It is a difference between two model predictions, and its validity rests entirely on the model being correct — which is the thing under test. It is used for **ranking**, and ranking only.

### 3 — Population-level causal measurement (the actual evidence)

```
Δ = E[Y | A = a] − E[Y | A = NO_ACTION]
```

estimated where randomisation holds. Three estimators, with different validity — say which one produced each number:

| Estimator | Randomisation source | Validity | Use |
|---|---|---|---|
| **Arm-level difference** (A5 − A3, A2 − A1) | seed-level assignment, identical inputs | **cleanest** — the headline | primary evidence |
| **Explored subset only** | ε-exploration, uniform over eligible | unbiased, small n, wide CI | corroboration |
| **IPW over all decisions** | recorded propensities | unbiased *if* propensities are correct | diagnostic |

Report for every one: point estimate · confidence interval · sample size · **randomisation unit** · seed.

### The rule

```
MODEL       estimates action-conditional outcome     ->  ranking
EXPERIMENT  measures incremental effect              ->  claims
```

**A claim may only be sourced from the experiment.** Model estimates never appear in a results headline.

```python
def test_model_estimates_never_appear_as_experimental_claims():
    for c in report().claims:
        assert c.source in {"arm_level", "explored_subset", "ipw"}
        assert c.source != "model_estimate"

def test_every_claim_names_its_randomisation_unit():
    for c in report().claims:
        assert c.randomisation_unit in {"seed", "customer"} and c.n is not None

def test_delta_hat_is_always_fully_named():
    text = render_report() + read("README.md")
    for m in re.finditer(r"incremental effect", text, re.I):
        window = text[m.start()-120:m.end()+120]
        assert "under the" in window and "data-generating process" in window
```

---

# P0 FIX 3 — POINT-IN-TIME FEATURE VALIDITY

An executable invariant, not a discipline.

```
feature.observed_at  ≤  decision_timestamp     for every feature, every time
label.observed_at    >  decision_timestamp     for every training label
```

```python
@dataclass(frozen=True)
class FeatureRecord:
    feature_name: str
    value: float | int | str
    observed_at: str          # mandatory; no default
    source: str
    scope: str                # 'merchant_local' | 'global_whitelisted'

FORBIDDEN_AT_DECISION_TIME = {
    "future_payment_outcome", "future_contact_response", "future_gateway_state",
    "future_customer_behavior", "future_recovery_status", "future_chargeback",
    "future_retry_result",
    # concrete column names that would carry them
    "recovered_paise", "payment_at", "outcome_status", "promise_kept",
    "contacts_after_decision", "final_amount", "chargeback_at", "retry_result",
    # simulator internals
    "_payer_propensity", "_will_pay", "_self_cure_flag", "_true_response_curve",
}

def build_features(ctx, decision_timestamp) -> FeatureVector:
    fv = assemble(ctx)
    for f in fv:
        if f.feature_name in FORBIDDEN_AT_DECISION_TIME:
            raise LeakageError(f"forbidden feature: {f.feature_name}")
        if f.observed_at > decision_timestamp:
            raise LeakageError(f"future feature: {f.feature_name} @ {f.observed_at} "
                               f"> decision {decision_timestamp}")
    return fv
```

**Required tests — a violation fails CI, it does not warn:**

```python
def test_no_future_features():
    with pytest.raises(LeakageError, match="future feature"):
        build_features(ctx_with(FeatureRecord("contacts_30d", 3, "T0+5d", "ledger",
                                              "merchant_local")), decision_timestamp="T0")

def test_training_cutoff():
    ds = build_training_dataset(outcomes)
    assert (ds.feature_observed_at <= ds.decision_timestamp).all()

def test_inference_cutoff():
    for d in decisions(run_id):
        assert all(f["observed_at"] <= d.decision_timestamp
                   for f in json.loads(d.feature_snapshot))

def test_outcome_not_available_at_decision_time():
    for d in decisions(run_id):
        names = {f["feature_name"] for f in json.loads(d.feature_snapshot)}
        assert names & FORBIDDEN_AT_DECISION_TIME == set()
```

CI gate: `pytest -m leakage` runs on every commit; any failure blocks merge.

---

# P0 FIX 4 — `NO_ACTION` AS A FIRST-CLASS ACTION

`NO_ACTION` is generated by the candidate generator, scored by the scorer, and ranked against interventions. It is never a fallback reached by exhaustion — it is the counterfactual baseline `Δ̂` is measured against, so if it is not scored, the model has no uplift to compute.

**Required fields on every decision record:**

```
selected_action
no_action_probability                 p̂(x, NO_ACTION)
selected_action_probability           p̂(x, selected)
estimated_incremental_effect          Δ̂(x, selected)
expected_value                        Δ̂ × recoverable_paise − action_cost_paise
abstention_reason                     populated iff selected_action == NO_ACTION
abstention_kind                       'SAFETY' | 'VALUE' | null      (FIX 1)
```

When `NO_ACTION` wins, the reason is recorded from: high self-cure probability · low expected incremental value · recent customer contact · gateway degradation · insufficient confidence · policy restriction.

```python
def test_no_action_is_scored_on_every_decision():
    for d in decisions(run_id):
        cands = json.loads(d.candidate_actions)
        assert any(c["action"] == "no_action" for c in cands)
        assert d.no_action_probability is not None

def test_no_action_wins_are_always_explained():
    for d in decisions(run_id):
        if d.selected_action == "no_action":
            assert d.abstention_reason in KNOWN_REASONS
            assert d.abstention_kind in {"SAFETY", "VALUE"}
        else:
            assert d.abstention_reason is None

def test_estimated_incremental_effect_is_derived_not_stored_raw():
    for d in decisions(run_id):
        assert isclose(d.estimated_incremental_effect,
                       d.selected_action_probability - d.no_action_probability, abs_tol=1e-9)
```

---

# P1 FIX 5 — MAKE THE AI DIFFERENCE MEASURABLE

Identical opportunities, identical eligible sets, identical policy constraints, through the heuristic and through CatBoost.

**Measured on the complete evaluation population — no cherry-picking, no illustrative examples:**

```
agreement_rate            argmax(AI) == argmax(heuristic)
disagreement_rate         1 − agreement_rate
action_switch_matrix      heuristic action × AI action (full 5×5)
no_action_selection_rate  per scorer
```

**For every disagreement case** — all of them, written to a table:

```
opportunity_id · heuristic_action · heuristic_expected_value
               · ai_action        · ai_expected_value
               · actual_outcome   · attributed_recovery_paise
               · arm · seed
```

Plus the breakdown that makes it interesting rather than a bare percentage: disagreement by failure reason, amount band, ageing bucket.

```python
def test_disagreement_uses_the_complete_population():
    assert disagreement_table().n == decisions_in(EXPERIMENT_SET).count()
    assert not disagreement_table().is_sampled

def test_scorers_saw_identical_eligible_sets():
    for a, b in zip(decisions("A3"), decisions("A5")):
        assert a.opportunity_id == b.opportunity_id
        assert set(a.eligible_actions) == set(b.eligible_actions)
```

**Disagreement rate is descriptive**, computed across all decisions. It is not evidence of superiority and is never reported as such.

---

# P1 FIX 6 — PROVE THE DIFFERENCES MATTER

The frozen paired comparison: **A3 (unified + downtime, no AI) vs A5 (unified + downtime + AI)**, identical seeded inputs, unit of analysis = seed, n = 40.

| | Metric |
|---|---|
| **Primary** | incremental recovery |
| Secondary | recovered revenue · revenue/contact · contacts/customer · phantom contacts · abstention rate · false-contact rate |

**The pre-commitment, made before the run and git-tagged:**

- CI entirely above zero → the model measurably improves action selection *under the synthetic data-generating process*.
- CI includes zero → **report that the model does not measurably outperform the heuristic.** The case for the AI layer then rests on separately-measured capabilities (calibrated abstention, open-hypothesis diagnosis, cross-case correlation), each with its own number.
- CI entirely below zero → the heuristic wins. Ship it as the default scorer and say so on camera.

**Do not modify the simulator after observing results to make A5 win.** Enforced by evidence, not by promise: the response function is git-tagged before either scorer exists (see §R3 in `full_plan.md`), and an evaluator can check the history.

```python
def test_response_function_frozen_before_scorers():
    assert commit_time(tag("response-function-frozen")) < first_commit_time("scoring/heuristic.py")
    assert commit_time(tag("response-function-frozen")) < first_commit_time("scoring/model.py")

def test_simulator_unchanged_after_first_evaluation_run():
    assert file_hash_at("simulation/response.py", first_eval_run_sha()) == current_hash("simulation/response.py")
```

The second test is the one that matters. If it ever fails, the results are void and must be re-run.

---

# P1 FIX 7 — THE SAFETY / AI BOUNDARY

Five deciders. Each answers exactly one question. None answers another's.

```
AI                          Which permissible action has the highest expected value?
Policy                      Which actions are permissible?
Arbitration                 Which permissible agent proposal wins under shared constraints?
Ledger                      Can the contact/action budget be consumed?
Execution infrastructure    Did the action actually execute?
```

```
AI  ≠  policy  ≠  arbitration  ≠  execution
```

**The AI never directly executes a payment action.** Structural, not conventional: the scorer module returns scores and nothing else — it holds no database write access, no credentials, and no reference to the executor.

```python
def test_scorer_cannot_write_or_execute():
    assert scoring_module.db_write_grants() == []
    assert scoring_module.credential_scopes() == []
    assert static_callgraph_paths("scoring", "actions.executor") == []
    assert static_callgraph_paths("scoring", "ledger") == []

def test_each_decider_owns_exactly_one_question():
    assert not hasattr(scorer, "is_permitted")
    assert not hasattr(policy_engine, "expected_value")
    assert not hasattr(arbitrator, "hard_filter")
```

---

# P1 FIX 8 — RETRY OWNERSHIP

The Recovery Engine may **recommend**, **suppress**, and **rank** a retry. It never becomes the execution owner.

```
Recovery Engine → recommendation / suppression → payment infrastructure / retry executor
                → execution result → Recovery Engine
```

Execution result supports: `SUCCESS` · `FAILURE` · `TIMEOUT` · `EXECUTION_UNKNOWN`.

**On `EXECUTION_UNKNOWN` the engine must not assume failure and must not issue another retry.** It waits for reconciliation (the bounded ladder in `p0.2` FIX 2). The slot stays held in `reserved_count`; the terminal outcome is `executed`, `released`, or fail-closed `unresolved`.

```python
def test_execution_unknown_never_triggers_an_immediate_retry():
    r = send_with(provider=Ambiguous(then=DeliveryStatus.UNKNOWN))
    run_all_schedulers(hours=72)
    assert retry_recommendations_for(r.case_id) == 1      # the original, not a second
    assert sender.send_count(r.id) == 1

def test_execution_unknown_is_not_recorded_as_failure():
    r = send_with(provider=Ambiguous(then=DeliveryStatus.UNKNOWN))
    assert outcome_status(r.case_id) != "FAILURE"
    assert status(r.id) == "execution_unknown"
```

---

# P1 FIX 9 — FEEDBACK LOOP PROVENANCE

```
prediction → action → execution → outcome → attribution → training example
           → model version → offline evaluation → promotion gate
```

**Every training example preserves, without exception:**

```
opportunity_id · merchant_id · decision_timestamp · feature_version · model_version
action · outcome · attribution · dataset_version · experiment_id
+ propensity · is_exploration · abstention_kind
```

```python
REQUIRED = {"opportunity_id","merchant_id","decision_timestamp","feature_version",
            "model_version","action","outcome","attribution","dataset_version",
            "experiment_id","propensity","is_exploration"}

def test_every_training_example_carries_full_provenance():
    ds = build_training_dataset(outcomes)
    assert REQUIRED <= set(ds.columns)
    assert ds[list(REQUIRED)].notna().all().all()

def test_future_outcomes_never_leak_into_historical_features():
    ds = build_training_dataset(outcomes)
    assert (ds.feature_observed_at <= ds.decision_timestamp).all()
    assert (ds.outcome_observed_at >  ds.decision_timestamp).all()
```

---

# P1 FIX 10 — REAL DATA VS SYNTHETIC OUTCOMES

```
NPCI / public real data → environment calibration → synthetic opportunity generation
                       → synthetic recovery response → controlled experiment
```

**Never say:** *"NPCI proves our recovery model works."*

**Say, verbatim:**

> Public real-world aggregate data grounds selected environmental distributions; recovery outcomes remain synthetic because no suitable public intervention/outcome dataset was identified.

Criteo, if used at all, stays a **separate estimator-methodology validation experiment** and is never reported alongside recovery results.

```python
def test_no_real_dataset_is_credited_with_recovery_evidence():
    text = render_report() + read("README.md")
    for src in ["NPCI", "Samadhaan", "Criteo"]:
        for m in re.finditer(src, text):
            window = text[m.start()-200:m.end()+200].lower()
            assert not re.search(r"prov(es|en)|demonstrates that .* recover", window)

def test_criteo_results_are_in_their_own_section():
    assert section_of("criteo") == "estimator_validation"
    assert "criteo" not in section_text("results").lower()
```

---

# P1 FIX 11 — DATA-GENERATING-PROCESS DISCLOSURE

Created: **`docs/EXPERIMENT_METHODOLOGY.md`**, documenting failure distributions · response function · self-cure mechanism · action effects · noise · exploration probability · randomisation · seed generation · treatment/control assignment.

The test it must pass: an evaluator reading it can answer

> *How exactly did a simulated customer decide whether to recover?*

without reading the source. Reproducibility means the numbers can be regenerated **and** the mechanism can be criticised.

---

# P1 FIX 12 — FALSIFICATION TESTS

Testing only that the system succeeds proves nothing. These test conditions where the AI **should not** show an advantage. If it does, the cause is leakage or simulator bias — investigate before reporting anything.

| # | Null condition | Expected | Failure means |
|---|---|---|---|
| 1 | All actions have equal true recovery probability | AI ≈ heuristic; CI includes zero | the AI is exploiting something that is not signal |
| 2 | Features carry no predictive signal (randomised) | no material uplift; calibration ≈ base rate | leakage |
| 3 | `NO_ACTION` dominates every intervention | high abstention; low contact volume | the model is biased toward acting |
| 4 | Outcome labels permuted within seed | uplift ≈ 0; AUC ≈ 0.5 | leakage |

```python
def test_null_equal_action_effects():
    r = run_experiment(response=EqualEffectsResponse(), seeds=range(20))
    assert covers(delta(r, "A5", "A3").ci95, 0.0)

def test_null_no_predictive_signal():
    r = run_experiment(features=ShuffledFeatures(), seeds=range(20))
    assert abs(delta(r, "A5", "A3").point) < NEGLIGIBLE
    assert abs(calibration(r, "A5").mean_pred - base_rate(r)) < 0.05

def test_null_no_action_dominates():
    r = run_experiment(response=NoActionDominatesResponse(), seeds=range(20))
    assert r.metrics["A5"]["abstention_rate"] > 0.80
    assert r.metrics["A5"]["contacts_per_customer"] < r.metrics["A3"]["contacts_per_customer"]

def test_permuted_labels_produce_no_uplift():
    ds = permute_labels_within_seed(build_training_dataset(outcomes))
    m = train(ds)
    assert 0.45 < offline_auc(m) < 0.55
    assert abs(mean_uplift(m)) < NEGLIGIBLE
```

**All four run in CI and are reported in the submission.** A project that shows the settings where its own advantage disappears is more credible to a technical evaluator, not less.

---

# FINAL ACCEPTANCE CRITERIA

Not implementation-ready until every line is true and has a test behind it.

| ✔ | Criterion | Evidence |
|---|---|---|
| ☐ | Exploration cannot bypass safety policy | FIX 1 · property test over 2,000 seeds |
| ☐ | Exploration cannot violate contact budgets | FIX 1 · budget invariant under exploration |
| ☐ | Exploration cannot violate tenant isolation | FIX 1 · cross-tenant exploration test |
| ☐ | Exploration cannot retry during gateway outage | FIX 1 · outage exploration test |
| ☐ | AI action probability is distinguished from causal effect | FIX 2 · three-quantity table; claim-source test |
| ☐ | Population incremental recovery uses experimental comparison | FIX 2 · claims sourced from arm-level only |
| ☐ | `NO_ACTION` is a genuine candidate | FIX 4 · scored on every decision |
| ☐ | Point-in-time feature validation is executable | FIX 3 · `build_features` raises |
| ☐ | Future-feature leakage fails CI | FIX 3 · `pytest -m leakage` blocks merge |
| ☐ | AI vs heuristic disagreement is measured | FIX 5 · complete population, no sampling |
| ☐ | AI vs non-AI outcomes measured on frozen experiments | FIX 6 · A5 vs A3, 40 seeds, paired |
| ☐ | Retry execution ownership stays outside the engine | FIX 8 · no `EXECUTE_RETRY`, no credential, no call path |
| ☐ | `EXECUTION_UNKNOWN` cannot trigger unsafe immediate retry | FIX 8 · send count stays 1 after 72h |
| ☐ | Feedback examples preserve model/data/experiment provenance | FIX 9 · 12 required columns, non-null |
| ☐ | Real datasets used only for claims they support | FIX 10 · proof-language scan |
| ☐ | Synthetic outcomes explicitly labelled synthetic | FIX 10 · provenance block on every run |
| ☐ | Criteo not presented as payment-recovery evidence | FIX 10 · separate section test |
| ☐ | Data-generating process documented | FIX 11 · `docs/EXPERIMENT_METHODOLOGY.md` |
| ☐ | Falsification tests exist | FIX 12 · four null conditions in CI |
| ☐ | Dashboard values originate from real experiment outputs | §4 · `source_query` on every widget |
| ☐ | No hardcoded success/recovery numbers | §4 · literal-value scan |
| ☐ | Final claims scoped to the evidence produced | FIX 2, FIX 10 · forbidden-phrase scan |

---

# FINAL RULE

After these fixes: **do not add features.** No more agents, dashboards, datasets, models, architecture, or APIs until the acceptance criteria pass.

Then move immediately:

```
IMPLEMENT → TEST → RUN FROZEN EXPERIMENTS → ANALYZE FAILURES
          → FIX ONLY REAL FAILURES → DEMO
```

The objective is no longer to make the architecture sound impressive. The objective is credible evidence that the Unified Recovery Engine performs AI-driven recovery decisioning while enforcing a measurable system-level safety layer.
