# 09 — IMPLEMENTATION ROADMAP

Canonical build sequence. **Every milestone is `NOT_STARTED`.**

**Two ordering rules that override intuition:**
1. **Safety before AI.** The ledger (M3) precedes the model (M8). A model producing decisions an unsafe ledger executes proves nothing.
2. **The experiment runner before the features it measures.** M12's skeleton runs on an empty engine early. Defining "correct" first is what stops the eval harness from being the thing that runs out of time.

---

## M1 — Project setup (M1.1 Foundation)
- **Goal**: reproducible environment, first commit
- **Dependencies**: none
- **Files**: `requirements.txt`, `pytest.ini`, `.gitignore`, `.env.example`, `Makefile`, `app/__init__.py`, `tests/__init__.py`, `tests/test_smoke.py`
- **Tests**: `pytest` executes smoke test (`tests/test_smoke.py::test_app_import_and_version PASSED`)
- **DoD**: fresh clone → `pip install -r requirements.txt` → `pytest` green; **repo has initial commit `eb52c38`**
- **Status**: `COMPLETED` (2026-09-01, commit `eb52c38`)

## M1.2 — Razorpay Test Mode Integration Research & Spec
- **Goal**: official Razorpay Test Mode API/webhook capability matrix and provider-neutral adapter specification
- **Dependencies**: M1
- **Files**: `refer/integrations/RAZORPAY_TEST_MODE.md`, `refer/decisions/ADR-0012-adapter-boundary-and-canonical-event.md`, `ADR-0013-webhook-verification-and-idempotency.md`, `ADR-0014-streamlit-judge-sandbox-architecture.md`
- **Tests**: n/a (specification)
- **DoD**: document all verified Test Mode capabilities vs unverified internal capabilities; define `CanonicalEvent` contract
- **Status**: `IN_PROGRESS`

## M2 — Domain model + database
- **Goal**: schema and types that make invalid states unrepresentable
- **Dependencies**: M1
- **Files**: `app/db/schema.sql`, `app/db/init.py`, `app/db/dal.py`, `app/domain/models.py`, `enums.py`, `money.py`, `app/clock.py`
- **Tests**: schema applies on SQLite WAL; `CHECK` constraints present; unscoped query raises `TenantScopeViolation`; no float money fields; no wall-clock calls outside the clock adapter
- **DoD**: create/read/update an opportunity; tenant cannot read across merchants
- **Status**: `NOT_STARTED`

## M3 — Contact ledger  ⟵ **highest priority, hard gate**
- **Goal**: the budget binds under concurrency
- **Dependencies**: M2
- **Files**: `app/ledger/reservation.py`, `app/ledger/transitions.py`
- **Tests**: cap binds after executions · same idempotency key → one slot · 7 invalid transitions rejected · repeated transitions idempotent · expiry cannot race execution · 2/10/100 concurrent workers · Hypothesis fuzz
- **DoD**: **all ledger tests green.** Until then, no other milestone starts
- **Status**: `NOT_STARTED`

## M4 — Recovery core loop & Event Adapters
- **Goal**: an opportunity flows end to end via dual paths (Razorpay Test Mode + Deterministic Simulator)
- **Dependencies**: M3
- **Files**: `app/adapters/base.py`, `app/adapters/razorpay/*`, `app/adapters/simulator/*`, `app/ingestion/events.py`, `app/identity/resolve.py`, `app/candidates/generate.py`
- **Tests**: webhook signature verification; duplicate event no-op; `NO_ACTION` in every candidate set; unresolved identity stays distinct
- **DoD**: event → canonical event → opportunity → candidates, persisted and traceable for both `RAZORPAY_TEST` and `SIMULATED` sources
- **Status**: `NOT_STARTED`

## M5 — Safety layer
- **Goal**: eligibility decided once, before scoring and exploration
- **Dependencies**: M4
- **Files**: `app/policy/hard_filter.py`, `app/policy/triggers.py`, `app/policy/versions/`
- **Tests**: policy-blocked candidate reserves nothing · 7 abstention triggers · SAFETY vs VALUE split · 2,000-seed exploration property test · TOCTOU recheck aborts and releases
- **DoD**: INV-1, INV-3, INV-9 tests green
- **Status**: `NOT_STARTED`

## M6 — Simulator & Event Factory
- **Goal**: reproducible synthetic world with a frozen response function and judge scenario factory
- **Dependencies**: M2
- **Files**: `app/simulation/generate.py`, `response.py`, `provider_sim.py`, `app/data/base.py`, `synthetic_adapter.py`
- **Tests**: same seed + reference timestamp → identical hash across processes and days · hash sensitive to every input · generation order-independent · simulator internals unreachable
- **DoD**: `make generate` produces a hashed opportunity set; **`response.py` git-tagged before M7**
- **Status**: `NOT_STARTED`

## M7 — Heuristic baseline
- **Goal**: the honest comparison
- **Dependencies**: M5, M6
- **Files**: `app/scoring/base.py`, `app/scoring/heuristic.py`
- **Tests**: pure function, no I/O; identical `ScoringContext` across arms; parameters frozen at a recorded commit
- **DoD**: A1, A2ns, A2 runnable; heuristic tuned on seeds 1–10 only
- **Status**: `NOT_STARTED`

## M8 — CatBoost AI Model
- **Goal**: the AI under test estimating $P(Y=1 \mid X, A)$ and incremental EV vs `NO_ACTION`
- **Dependencies**: M7
- **Files**: `app/scoring/model.py`, `app/models/train.py`, `features.py`, `registry.py`
- **Tests**: point-in-time assertions raise on violation (`pytest -m leakage`) · calibration slope ∈ [0.85, 1.15] · Brier improved · arms differ only in the scorer
- **DoD**: `models/v1.cbm` + metadata; A3 and A5 runnable
- **Status**: `NOT_STARTED`

## M9 — Multi-Agent Arbitration
- **Goal**: competing agents (12 simulated agent recommendations), one contact slot
- **Dependencies**: M3, M5
- **Files**: `app/arbitration/arbitrate.py`, `app/agents/*.py`
- **Tests**: two agents → one contact with real suppression reasons; deterministic under reordering
- **DoD**: collision prevention demonstrated with a trace
- **Status**: `NOT_STARTED`

## M10 — Attribution
- **Goal**: separate caused from would-have-happened (distinguishing self-cure)
- **Dependencies**: M4, M6
- **Files**: `app/attribution/classify.py`
- **Tests**: payment before delivery → `SELF_CURED` · window boundaries · partial + TDS tolerance · post-window censoring · self-cure agrees across arms
- **DoD**: INV-8 green; six recovery metrics distinct
- **Status**: `NOT_STARTED`

## M11 — Feedback Loop
- **Goal**: outcomes become the next model version
- **Dependencies**: M8, M10
- **Files**: `app/models/train.py`, `registry.py`
- **Tests**: dataset roles disjoint · holdout locked until promotion decided · v2 never evaluated on its training data · bad model rejected · model hash constant within a run
- **DoD**: v1 → v2 → gate → promote/reject → rollback, executed once
- **Status**: `NOT_STARTED`

## M12 — Experiments
- **Goal**: the evidence harness comparing AI vs baseline arms
- **Dependencies**: M7, M8, M9, M10
- **Files**: `app/evaluation/run.py`, `stats.py`, `falsification.py`, `experiments/preregistration.json`
- **Tests**: identical `input_hash` and `world_hash` across arms · tuning ∩ eval seeds = ∅ · exactly one primary metric · null experiment reports inconclusive · Holm applied · four falsification runs
- **DoD**: `results/report.json` regenerable from seeds alone; pre-registration git-tagged **before** the first run
- **Status**: `NOT_STARTED`

## M13 — Streamlit Judge Interactive Sandbox & Decision Trace
- **Goal**: "Why did the engine do this?" — Interactive Judge Sandbox with Live Test, Sandbox, and Red-Team modes
- **Dependencies**: M12
- **Files**: `app/ui/app.py`, `app/ui/trace.py`, `app/ui/sandbox.py`, `app/ui/red_team.py`, `app/ui/db_inspector.py`
- **Tests**: trace answers all six audit questions · renders without an LLM · no hardcoded values · every widget has a source query · 9 red-team attack cards return verified `PASS`/`FAIL`
- **DoD**: Judge sandbox fully operational with zero pre-scripted outputs; safe read-only database inspector active
- **Status**: `NOT_STARTED`

## M14 — Public Live Demo Deployment & Final Submission Package
- **Goal**: deployable public HTTPS URL + complete submission package
- **Dependencies**: M13
- **Files**: `README.md`, `RESULTS.md`, deployment config, video walk-through
- **Tests**: full suite green · secret scan clean · public deployment boots cleanly in zero-credential `SIMULATION MODE`
- **DoD**: public live demo URL active; repo frozen and tagged; video matches code exactly
- **Status**: `NOT_STARTED`


---

## Compressed paths

If time is short, see `strategy/TOOLCHAIN.md` §19. Summary:

- **7 days**: cut Criteo, dashboard beyond the trace screen, M11, the 4th agent, Stage 0 probabilistic checks
- **5 days**: also cut arms A2ns and A2 (keep A1, A3, A5), downtime suppression, falsification tests 3–4
- **3 days**: M1 → M2 → M3 → minimal M4–M10 on one stream → two arms (A1 vs A5), 20 seeds, trace screen, demo

**Never cut**: M3 (ledger), M10 (attribution), M12 (experiment). Those three are the thesis.
