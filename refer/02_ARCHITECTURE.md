# 02 — ARCHITECTURE

Canonical implementation architecture. **Frozen** (`p0.2-closure.md`). Changes require an ADR.

**Implemented and verified 2026-09-05 at commit `e803e36`** — 62 modules, 255 passing tests.
Until 2026-09-05 this line read *"Every component below is `PLANNED`. None is implemented"*,
which was written before the build and never updated. Two contracts below were **never built**
and are marked as such inline: Multi-Agent Arbitration (superseded by the shared contact budget)
and red-team mode. Everything else exists. See `01_PROJECT_STATE.md` for the module inventory.

The `Owner:` paths below are the **delivered** ones. Several differ from the plan — the planned
`app/policy/`, `app/actions/`, `app/candidates/`, `app/ingestion/` and `app/simulation/`
packages were consolidated into `app/pipeline/`, `app/dispatch/`, `app/realtime/` and
`app/sandbox/`. `09_IMPLEMENTATION_ROADMAP.md` carries the full planned-vs-delivered map.

---

## Component contracts

### RecoveryOpportunity
- **Purpose**: canonical unit of work; all four streams map into it
- **Inputs**: ingested event (payment / cart / subscription / invoice)
- **Outputs**: opportunity with `merchant_id`, `canonical_customer_id`, `gross_at_risk_paise`
- **Owner**: `app/realtime/` + `app/pipeline/dataset_adapter.py` (ADR-0012)
- **Dependencies**: identity resolution
- **State**: `OPEN` → `CLOSED_NOT_AT_RISK` | `ACTIONED` | `RESOLVED`
- **Failure modes**: duplicate delivery; unresolvable identity
- **Safety constraints**: money is integer paise; every row merchant-scoped
- **Tests**: replay every event twice → identical state; unresolved identity stays distinct

### Stage 0 — Validate
- **Purpose**: decide whether money was genuinely at risk, before anything else happens
- **Inputs**: opportunity, transaction records, statutory rate table
- **Outputs**: `VALID_RECOVERY` | `PHANTOM_RISK` | `RESTRICTED` | `ALREADY_RECOVERED` | `UNKNOWN`, plus basis and confidence
- **Owner**: `app/validation/` — split `objective/` and `probabilistic/`
- **Failure modes**: wrong rate table wrongly closes a receivable; over-wide self-cure window
- **Safety constraints**: objective checks are rule-gated, never LLM-judged; probabilistic closures are reversible and carry confidence
- **Tests**: TDS → `PHANTOM_RISK` → zero contacts; adversarial cases abstain

### Stage 1 — Diagnose
- **Purpose**: classify why the failure happened; cluster related failures
- **Outputs**: one of `INSUFFICIENT_FUNDS` `PAYMENT_METHOD_FAILURE` `AUTHENTICATION_FAILURE` `GATEWAY_FAILURE` `CUSTOMER_CANCELLATION` `EXPIRED_METHOD` `TDS_WITHHOLDING` `UNKNOWN`, plus a correlation cluster id
- **Owner**: `app/diagnosis/`
- **Safety constraints**: diagnosis is a feature, never a permission
- **Tests**: 40 failures on one issuer cluster into one event

### Candidate Generation
- **Purpose**: enumerate feasible actions for a validated opportunity
- **Outputs**: `RECOMMEND_RETRY` `SEND_PAYMENT_LINK` `SEND_REMINDER` `UPDATE_PAYMENT_METHOD` `NO_ACTION`
- **Owner**: `app/pipeline/candidate_generator.py`
- **Safety constraints**: `NO_ACTION` is **always** present; the generator may never bypass policy
- **Tests**: `NO_ACTION` in every candidate set

### Hard Safety / Policy Filter
- **Purpose**: decide which actions are permissible — once, before scoring is used and before exploration
- **Inputs**: opportunity, customer flags, budget view, payment state, outage state
- **Outputs**: eligible action set + per-candidate block reasons
- **Owner**: `app/pipeline/safety_filter.py`, with `app/pipeline/escalation.py` layered **under**
  it (ADR-0015 — escalation may only remove a candidate, never revive one)
- **Constraints checked**: opt-out · cooldown · contact budget · merchant policy · legal restriction · payment state · already-recovered · outage · retry ownership · action eligibility · tenant isolation
- **Safety constraints**: this set **is** the exploration pool (INV-3)
- **Tests**: blocked candidate reserves nothing; 2,000-seed exploration property test

### AI Decision
- **Purpose**: rank eligible actions by expected value
- **Inputs**: `ScoringContext` — opportunity, point-in-time features, eligible actions, policy view, budget view, payment state
- **Outputs**: per-action `p̂`, `Δ̂`, expected value
- **Owner**: `app/scoring/`
- **Safety constraints**: holds **no** database write access, **no** credentials, **no** path to the executor
- **Tests**: static call-graph assertions; identical context hash across A3/A5

### NO_ACTION
- **Purpose**: the counterfactual baseline, and a genuine decision
- **Safety constraints**: consumes no budget slot; always scored; reason and kind recorded when it wins

### Exploration / Exploitation
- **Purpose**: collect counterfactual data without unsafe behaviour
- **Owner**: `app/scoring/` selection step
- **Safety constraints**: eligible actions only; may override a VALUE abstention, never a SAFETY one; ε = 0.05 deterministic; propensity recorded

### Multi-Agent Arbitration — **NOT BUILT; superseded by the contact ledger**
- **Purpose (as planned)**: choose one action per customer across competing stream agents
- **Owner (as planned)**: `app/arbitration/` — **does not exist.** Neither does `app/agents/`.
  No agent objects are simulated anywhere in this project.
- **What actually arbitrates**: the shared per-customer contact budget below. All four streams
  contend for **one** atomic slot; `BEGIN IMMEDIATE` plus the DB `CHECK` decides, with a single
  writer. Deterministic, serialized, and enforced by the database rather than by a ranking
  function — which is the stronger version of the same guarantee.
- **How the effect is measured**: as an arm contrast, not as agent objects. **A1** gives each
  stream its own budget row so nothing arbitrates; **A2ns/A2** share one slot. A1 spends 1,500
  contacts (22.73 per customer) for recovery statistically indistinguishable from A2's 1,336
  (20.24). See `app/experiment/policies.py` and `results/RESULTS.md`.
- **Recorded in**: `01_PROJECT_STATE.md` §Not built · `09_IMPLEMENTATION_ROADMAP.md` M9.
  **Never claim 12 competing agents.**

### Contact Ledger / Atomic Reservation
- **Purpose**: enforce the shared per-customer contact budget under concurrency
- **Owner**: `app/ledger/` — the **only** writer of budget tables
- **State**: `reserved` → `executed` | `released` | `expired` | `execution_unknown` → `executed` | `released` | `unresolved`
- **Failure modes**: lost update (the T0 race); double release; expiry racing execution; send succeeded but write failed
- **Safety constraints**: `reserved_count + consumed_count <= cap` enforced by a DB `CHECK`; every transition is a compare-and-swap
- **Tests**: cap binds; same key → one slot; 100-worker fuzz; 7 invalid transitions rejected

### Execution
- **Purpose**: perform the single arbitrated action
- **Owner**: `app/dispatch/` — sole holder of send credentials; off unless
  `RECOVERY_DISPATCH_ENABLED`
- **Safety constraints**: re-checks `flags_version` inside the same transaction as `reserved → executed`; an ambiguous provider response never auto-releases

### Downtime Suppression
- **Purpose**: suppress retry recommendations and contact into a known outage
- **Owner**: `app/downtime/` — separate module, not embedded in diagnosis
- **Safety constraints**: scope-limited to the affected method/issuer; staggered batch on resolution

### Retry Ownership
- **Safety constraints**: engine emits `RECOMMEND_RETRY` only; holds no retry credential; `EXECUTE_RETRY` is absent from the action enum (ADR-0006)

### Outcome Reconciliation
- **Purpose**: resolve `execution_unknown` on a bounded ladder (1m/5m/30m/2h/6h/24h)
- **Safety constraints**: never re-sends; terminal `unresolved` is fail-closed, queued for human review, and reported as a rate

### Self-Cure / Attribution
- **Purpose**: separate caused-by-intervention from would-have-happened
- **Safety constraints**: a payment before the first **delivered** intervention is `SELF_CURED`, attributed zero, always
- **Tests**: ordering test; self-cure rate agrees across arms within 2pp

### Feedback / Model Training
- **Safety constraints**: point-in-time features; propensities recorded; holdout locked until promotion is decided; model hash constant within a run

### Experimentation
- **Safety constraints**: identical inputs hash-asserted across arms; pre-registration git-tagged before the first run

---

## Data flow

```
event → ingest+dedup → identity resolve → Stage 0 → Stage 1
      → candidates (incl. NO_ACTION) → HARD POLICY FILTER → eligible set
      → scoring (pure, no I/O) → explore | exploit → arbitration
      → atomic reservation (BEGIN IMMEDIATE) → execution (+ TOCTOU recheck)
      → provider → outcome → attribution → experiment → feedback → next model
```

## Credential and write boundaries

```
scoring/       no DB writes · no credentials · no executor reference
ledger/        ONLY module writing budget tables
actions/       ONLY module holding send credentials
arbitration/   deterministic; single writer per customer
policy/        read-only; the sole source of eligibility
```

These are architectural invariants enforced by static tests, not conventions.
