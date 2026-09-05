# 09 — IMPLEMENTATION ROADMAP

**This is the original plan, reconciled against what was actually built.** It was written
before implementation with an M1–M14 numbering; the build ran on an M1–M9 scheme and then
continued past it in sixteen unnumbered commits. Both are recorded below. Statuses were
re-stamped on **2026-09-05** against commit `e803e36` (33 commits, 255 passing tests).

> **Read the file paths as intent, not as a map.** Several planned modules landed under
> different names: `app/adapters/` + `app/ingestion/` → `app/pipeline/dataset_adapter.py` and
> `app/realtime/`; `app/policy/` → `app/pipeline/safety_filter.py`; `app/candidates/` →
> `app/pipeline/candidate_generator.py`; `app/simulation/` → `app/sandbox/`;
> `app/evaluation/` → `app/experiment/`; `app/models/` → `app/scoring/`. Two planned
> packages — `app/arbitration/` and `app/agents/` — do not exist at all; see M9. For the real
> layout, read `01_PROJECT_STATE.md` or `ls app/`.

## Planned vs delivered

| Planned | Delivered as | Status |
|---|---|---|
| M1 setup | M1.1 | done |
| M1.2 Razorpay Test Mode research | M1.2 | done, minus the capability-matrix document |
| M2 domain + database | M2 | done |
| M3 contact ledger | M3 | done |
| M4 recovery loop + adapters | M4 | done |
| M5 safety layer | M4 (`safety_filter.py`) | done |
| M6 simulator | M6 (`app/sandbox/`) | done |
| M7 heuristic baseline | M5 (`heuristic.py`) | done |
| M8 CatBoost model | M5 (`s_learner.py`) | done |
| **M9 multi-agent arbitration** | **not built as described** — arbitration is the shared atomic contact budget | see M9 |
| M10 attribution | M6 (`app/attribution/`) | done |
| M11 feedback loop | M7 (`feedback_loop.py`) | done |
| M12 experiments | M7 (`app/experiment/`) | done |
| M13 judge sandbox | M8 + M9 (`app/ui/dashboard.py`) | done, minus red-team mode |
| M14 deployment & submission | M9 | code done; video and submission outstanding |

**Two ordering rules that override intuition:**
1. **Safety before AI.** The ledger (M3) precedes the model (M8). A model producing decisions an unsafe ledger executes proves nothing.
2. **The experiment runner before the features it measures.** M12's skeleton runs on an empty engine early. Defining "correct" first is what stops the eval harness from being the thing that runs out of time.

*Both rules held in practice: the ledger landed before the scorer, and the runner before the arms it measures.*

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
- **Files**: ~~`refer/integrations/RAZORPAY_TEST_MODE.md`~~ (never written — the capability
  content lives in ADR-0012 and ADR-0018), `refer/decisions/ADR-0012-adapter-boundary-and-canonical-event.md`
  (written 2026-09-05), ~~`ADR-0013`~~ and ~~`ADR-0014`~~ (**withdrawn** — see
  `decisions/ADR_INDEX.md` §Withdrawn; 0013's subject is recorded in ADR-0018 and ADR-0019,
  0014's in ADR-0010)
- **Tests**: n/a (specification)
- **DoD**: document all verified Test Mode capabilities vs unverified internal capabilities; define `CanonicalEvent` contract
- **Status**: `COMPLETED` — `CanonicalEvent` defined and implemented (`app/domain/models.py:41`);
  the standalone capability-matrix document was never written and is recorded as not built

## M2 — Domain model + database
- **Goal**: schema and types that make invalid states unrepresentable
- **Dependencies**: M1
- **Files**: `app/db/schema.sql`, `app/db/init.py`, `app/db/dal.py`, `app/domain/models.py`, `enums.py`, `money.py`, `app/clock.py`
- **Tests**: schema applies on SQLite WAL; `CHECK` constraints present; unscoped query raises `TenantScopeViolation`; no float money fields; no wall-clock calls outside the clock adapter
- **DoD**: create/read/update an opportunity; tenant cannot read across merchants
- **Status**: `COMPLETED` — `tests/db/` + `tests/domain/` (26 tests)

## M3 — Contact ledger  ⟵ **highest priority, hard gate**
- **Goal**: the budget binds under concurrency
- **Dependencies**: M2
- **Files**: `app/ledger/reservation.py`, `app/ledger/transitions.py`
- **Tests**: cap binds after executions · same idempotency key → one slot · 7 invalid transitions rejected · repeated transitions idempotent · expiry cannot race execution · 2/10/100 concurrent workers · Hypothesis fuzz
- **DoD**: **all ledger tests green.** Until then, no other milestone starts
- **Status**: `COMPLETED` — `tests/ledger/` (25 tests, incl. Hypothesis fuzz and concurrency)

## M4 — Recovery core loop & Event Adapters
- **Goal**: an opportunity flows end to end via dual paths (Razorpay Test Mode + Deterministic Simulator)
- **Dependencies**: M3
- **Files**: delivered as `app/pipeline/dataset_adapter.py`, `app/realtime/event_mapper.py`,
  `app/api/webhook_listener.py`, `app/pipeline/candidate_generator.py` (the planned
  `app/adapters/`, `app/ingestion/`, `app/identity/`, `app/candidates/` packages do not exist)
- **Tests**: webhook signature verification; duplicate event no-op; `NO_ACTION` in every candidate set; unresolved identity stays distinct
- **DoD**: event → canonical event → opportunity → candidates, persisted and traceable for both `RAZORPAY_TEST` and `SIMULATED` sources
- **Status**: `COMPLETED` — ADR-0012 records the boundary; `tests/realtime/test_webhook_ingestion.py` (25)

## M5 — Safety layer
- **Goal**: eligibility decided once, before scoring and exploration
- **Dependencies**: M4
- **Files**: delivered as `app/pipeline/safety_filter.py` and `app/pipeline/escalation.py`
  (no `app/policy/` package)
- **Tests**: policy-blocked candidate reserves nothing · 7 abstention triggers · SAFETY vs VALUE split · 2,000-seed exploration property test · TOCTOU recheck aborts and releases
- **DoD**: INV-1, INV-3, INV-9 tests green
- **Status**: `COMPLETED` — `tests/pipeline/` (safety, properties, escalation)

## M6 — Simulator & Event Factory
- **Goal**: reproducible synthetic world with a frozen response function and judge scenario factory
- **Dependencies**: M2
- **Files**: delivered as `app/sandbox/simulator.py`, `app/sandbox/outcome_model.py`,
  `app/sandbox/scenarios.py`, `app/experiment/batch.py` (no `app/simulation/` package)
- **Tests**: same seed + reference timestamp → identical hash across processes and days · hash sensitive to every input · generation order-independent · simulator internals unreachable
- **DoD**: `make generate` produces a hashed opportunity set; **`response.py` git-tagged before M7**
- **Status**: `COMPLETED` — batch content hash `0837b24c…` reproduces at `e803e36`. The outcome
  model was later revised under ADR-0020 (context-dependent DGP; prediction P1 falsified).

## M7 — Heuristic baseline
- **Goal**: the honest comparison
- **Dependencies**: M5, M6
- **Files**: `app/scoring/heuristic.py`, `app/scoring/engine.py`
- **Tests**: pure function, no I/O; identical `ScoringContext` across arms; parameters frozen at a recorded commit
- **DoD**: A1, A2ns, A2 runnable; heuristic tuned on seeds 1–10 only
- **Status**: `COMPLETED` — and it **wins**: A5 (CatBoost) does not beat A3 (heuristic) under the
  simulator. Reported rather than tuned away.

## M8 — CatBoost AI Model
- **Goal**: the AI under test estimating $P(Y=1 \mid X, A)$ and incremental EV vs `NO_ACTION`
- **Dependencies**: M7
- **Files**: `app/scoring/s_learner.py`, `app/scoring/feature_builder.py`,
  `app/scoring/registry.py`, `app/scoring/logged_dataset.py` (no `app/models/` package)
- **Tests**: point-in-time assertions raise on violation (`pytest -m leakage`) · calibration slope ∈ [0.85, 1.15] · Brier improved · arms differ only in the scorer
- **DoD**: `models/v1.cbm` + metadata; A3 and A5 runnable
- **Status**: `COMPLETED` — registry is file-based per ADR-0008; retrained on the engine's own
  logged outcomes under ADR-0017. Calibration slope remains an open item (OD-2 licence).

## M9 — Multi-Agent Arbitration — **NOT BUILT AS DESCRIBED**
- **Goal (as planned)**: competing agents (12 simulated agent recommendations), one contact slot
- **Dependencies**: M3, M5
- **Files (as planned)**: `app/arbitration/arbitrate.py`, `app/agents/*.py` — **neither exists.**
- **What was built instead**: arbitration **is** the shared atomic contact budget. All streams
  contend for one per-customer slot in `app/ledger/`; `BEGIN IMMEDIATE` plus
  `CHECK (reserved_count + consumed_count <= cap)` decides, with a single writer. No agent
  objects are simulated.
- **How the effect is measured**: experiment arms rather than agent objects — **A1** gives each
  stream its own budget row so nothing arbitrates; **A2ns/A2** share one atomic slot. A1 spends
  1,500 contacts (22.73 per customer) for recovery statistically indistinguishable from A2's
  1,336 (20.24). See `app/experiment/policies.py`.
- **Status**: `NOT_BUILT` as specified · `SUPERSEDED` by the shared-ledger design. Recorded in
  `01_PROJECT_STATE.md` §Not built. **Do not claim 12 simulated agents anywhere.**

## M10 — Attribution
- **Goal**: separate caused from would-have-happened (distinguishing self-cure)
- **Dependencies**: M4, M6
- **Files**: `app/attribution/`
- **Tests**: payment before delivery → `SELF_CURED` · window boundaries · partial + TDS tolerance · post-window censoring · self-cure agrees across arms
- **DoD**: INV-8 green; six recovery metrics distinct
- **Status**: `COMPLETED` — `tests/attribution/` + M6 golden scenarios; self-cure attributed ₹0

## M11 — Feedback Loop
- **Goal**: outcomes become the next model version
- **Dependencies**: M8, M10
- **Files**: `app/experiment/feedback_loop.py`, `app/scoring/logged_dataset.py`, `app/scoring/registry.py`
- **Tests**: dataset roles disjoint · holdout locked until promotion decided · v2 never evaluated on its training data · bad model rejected · model hash constant within a run
- **DoD**: v1 → v2 → gate → promote/reject → rollback, executed once
- **Status**: `COMPLETED` — training on logged outcomes recorded in ADR-0017

## M12 — Experiments
- **Goal**: the evidence harness comparing AI vs baseline arms
- **Dependencies**: M7, M8, M9, M10
- **Files**: `app/experiment/runner.py`, `app/experiment/policies.py`,
  `scripts/run_evaluation.py`, `experiments/preregistration.json`
- **Tests**: identical `input_hash` and `world_hash` across arms · tuning ∩ eval seeds = ∅ · exactly one primary metric · null experiment reports inconclusive · Holm applied · four falsification runs
- **DoD**: `results/report.json` regenerable from seeds alone; pre-registration git-tagged **before** the first run
- **Status**: `COMPLETED` — `make eval` regenerates `results/report.json` + `RESULTS.md` from
  seeds; primary A2−A1 = −0.0148 (p=0.1846) **INCONCLUSIVE**, reported as such

## M13 — Streamlit Judge Interactive Sandbox & Decision Trace
- **Goal**: "Why did the engine do this?" — Interactive Judge Sandbox with Live Test, Sandbox, and Red-Team modes
- **Dependencies**: M12
- **Files**: delivered as `app/ui/dashboard.py` (single module). ~~`app/ui/red_team.py`~~
  **never built.**
- **Tests**: trace answers all six audit questions · renders without an LLM · no hardcoded
  values · every widget has a source query · ~~9 red-team attack cards~~ — **not built**; the
  Safety tab instead *executes* live invariant checks
- **DoD**: Judge sandbox fully operational with zero pre-scripted outputs; safe read-only database inspector active
- **Status**: `COMPLETED` minus red-team mode (recorded in `01_PROJECT_STATE.md` §Not built).
  `tests/ui/` (10 tests).

## M14 — Public Live Demo Deployment & Final Submission Package
- **Goal**: deployable public HTTPS URL + complete submission package
- **Dependencies**: M13
- **Files**: `README.md`, `results/RESULTS.md`, `streamlit_app.py`, video walk-through
- **Tests**: full suite green · secret scan clean · public deployment boots cleanly in zero-credential `SIMULATION MODE`
- **DoD**: public live demo URL active; repo frozen and tagged; video matches code exactly
- **Status**: `IN_PROGRESS` — suite green (255), secret scan clean (6/6 gate), `streamlit_app.py`
  ready. **Outstanding: deploy decision, video, submission.** See `progress/NEXT_STEPS.md`.


---

## Compressed paths

*Historical — none of these were needed. Recorded because the reasoning about what is
load-bearing is still the right reasoning.*

If time is short, see `strategy/TOOLCHAIN.md` §19. Summary:

- **7 days**: cut Criteo, dashboard beyond the trace screen, M11, the 4th agent, Stage 0 probabilistic checks
- **5 days**: also cut arms A2ns and A2 (keep A1, A3, A5), downtime suppression, falsification tests 3–4
- **3 days**: M1 → M2 → M3 → minimal M4–M10 on one stream → two arms (A1 vs A5), 20 seeds, trace screen, demo

**Never cut**: M3 (ledger), M10 (attribution), M12 (experiment). Those three are the thesis.

*What was actually cut, in the end: nothing on that list. The two things dropped were the
competing-agent arbitrator (M9) and red-team mode (M13) — neither of which appears above,
because neither was ever load-bearing.*
