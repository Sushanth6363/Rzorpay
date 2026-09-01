# 09 — IMPLEMENTATION ROADMAP

Canonical build sequence. **Every milestone is `NOT_STARTED`.**

**Two ordering rules that override intuition:**
1. **Safety before AI.** The ledger (M3) precedes the model (M8). A model producing decisions an unsafe ledger executes proves nothing.
2. **The experiment runner before the features it measures.** M12's skeleton runs on an empty engine early. Defining "correct" first is what stops the eval harness from being the thing that runs out of time.

---

## M1 — Project setup
- **Goal**: reproducible environment, first commit
- **Dependencies**: none
- **Files**: `requirements.txt`, `pyproject.toml` or `pytest.ini`, `.gitignore`, `.env.example`, `Makefile`, `app/__init__.py`
- **Tests**: `pytest` collects and runs an empty suite
- **DoD**: fresh clone → `pip install -r requirements.txt` → `pytest` green; **repo has at least one commit**
- **Status**: `NOT_STARTED`

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

## M4 — Recovery core loop
- **Goal**: an opportunity flows end to end with stub stages
- **Dependencies**: M3
- **Files**: `app/ingestion/events.py`, `app/identity/resolve.py`, `app/candidates/generate.py`
- **Tests**: duplicate event no-op; `NO_ACTION` in every candidate set; unresolved identity stays distinct
- **DoD**: event → opportunity → candidates, persisted and traceable
- **Status**: `NOT_STARTED`

## M5 — Safety layer
- **Goal**: eligibility decided once, before scoring and exploration
- **Dependencies**: M4
- **Files**: `app/policy/hard_filter.py`, `app/policy/triggers.py`, `app/policy/versions/`
- **Tests**: policy-blocked candidate reserves nothing · 7 abstention triggers · SAFETY vs VALUE split · 2,000-seed exploration property test · TOCTOU recheck aborts and releases
- **DoD**: INV-1, INV-3, INV-9 tests green
- **Status**: `NOT_STARTED`

## M6 — Simulator
- **Goal**: reproducible synthetic world with a frozen response function
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

## M8 — CatBoost
- **Goal**: the AI under test
- **Dependencies**: M7
- **Files**: `app/scoring/model.py`, `app/models/train.py`, `features.py`, `registry.py`
- **Tests**: point-in-time assertions raise on violation (`pytest -m leakage`) · calibration slope ∈ [0.85, 1.15] · Brier improved · arms differ only in the scorer
- **DoD**: `models/v1.cbm` + metadata; A3 and A5 runnable
- **Status**: `NOT_STARTED`

## M9 — Arbitration
- **Goal**: competing agents, one contact
- **Dependencies**: M3, M5
- **Files**: `app/arbitration/arbitrate.py`, `app/agents/*.py`
- **Tests**: two agents → one contact with real suppression reasons; deterministic under reordering
- **DoD**: collision prevention demonstrated with a trace
- **Status**: `NOT_STARTED`

## M10 — Attribution
- **Goal**: separate caused from would-have-happened
- **Dependencies**: M4, M6
- **Files**: `app/attribution/classify.py`
- **Tests**: payment before delivery → `SELF_CURED` · window boundaries · partial + TDS tolerance · post-window censoring · self-cure agrees across arms
- **DoD**: INV-8 green; six recovery metrics distinct
- **Status**: `NOT_STARTED`

## M11 — Feedback
- **Goal**: outcomes become the next model
- **Dependencies**: M8, M10
- **Files**: `app/models/train.py`, `registry.py`
- **Tests**: dataset roles disjoint · holdout locked until promotion decided · v2 never evaluated on its training data · bad model rejected · model hash constant within a run
- **DoD**: v1 → v2 → gate → promote/reject → rollback, executed once
- **Status**: `NOT_STARTED`

## M12 — Experiments
- **Goal**: the evidence
- **Dependencies**: M7, M8, M9, M10
- **Files**: `app/evaluation/run.py`, `stats.py`, `falsification.py`, `experiments/preregistration.json`
- **Tests**: identical `input_hash` and `world_hash` across arms · tuning ∩ eval seeds = ∅ · exactly one primary metric · null experiment reports inconclusive · Holm applied · four falsification runs
- **DoD**: `results/report.json` regenerable from seeds alone; pre-registration git-tagged **before** the first run
- **Status**: `NOT_STARTED`

## M13 — Dashboard
- **Goal**: "why did the engine do this?"
- **Dependencies**: M12
- **Files**: `app/dashboard.py`
- **Tests**: trace answers all six audit questions · renders without an LLM · no hardcoded values · every widget has a source query
- **DoD**: the trace screen works; nothing else is built until it does
- **Status**: `NOT_STARTED`

## M14 — Final demo
- **Goal**: five beats, five minutes
- **Dependencies**: M13
- **Files**: `README.md`, `RESULTS.md`, demo script, recording
- **Tests**: full suite green · forbidden-phrase scan clean · `make eval` reproduces every README number
- **DoD**: repo frozen and tagged; video matches the code exactly
- **Status**: `NOT_STARTED`

---

## Compressed paths

If time is short, see `strategy/TOOLCHAIN.md` §19. Summary:

- **7 days**: cut Criteo, dashboard beyond the trace screen, M11, the 4th agent, Stage 0 probabilistic checks
- **5 days**: also cut arms A2ns and A2 (keep A1, A3, A5), downtime suppression, falsification tests 3–4
- **3 days**: M1 → M2 → M3 → minimal M4–M10 on one stream → two arms (A1 vs A5), 20 seeds, trace screen, demo

**Never cut**: M3 (ledger), M10 (attribution), M12 (experiment). Those three are the thesis.
