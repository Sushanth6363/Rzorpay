# 01 — PROJECT STATE

**Last full verification**: 2026-09-01, by direct repository inspection.
**Verification method**: `find . -name "*.py"` → none · `git log` → *"branch master does not have any commits yet"* · `git ls-files` → empty · no `requirements.txt`, `Makefile`, `pytest.ini`, `pyproject.toml`, or `*.db`.

## Status vocabulary

`PLANNED` · `IN_PROGRESS` · `IMPLEMENTED` · `TESTED` · `VERIFIED` · `BLOCKED` · `DEPRECATED` · `REJECTED` · `UNKNOWN`

Vague phrases — "mostly done", "basically working", "should work", "probably implemented" — are forbidden in this file. If a status cannot be established, write `UNKNOWN — REQUIRES VERIFICATION`.

---

## Summary

| Status | Count |
|---|---|
| `IMPLEMENTED` or beyond | **0** |
| `IN_PROGRESS` | 0 |
| `PLANNED` | 21 |
| `REJECTED` | 4 |

**No component of this system has been implemented, tested, or verified.** The design is complete and frozen; the code does not exist.

---

## Components

### Foundation

**Repository skeleton**
- Status: `PLANNED`
- Location: — (does not exist)
- Tests: —
- Last verification: 2026-09-01 — confirmed absent
- Known limitations: repository has **zero git commits**; nothing is under version control
- Dependencies: none
- Next action: create venv, `requirements.txt`, package layout, first commit

**Database schema (SQLite)**
- Status: `PLANNED`
- Location: — (planned `app/db/schema.sql`)
- Tests: — (planned `tests/test_schema.py`)
- Last verification: 2026-09-01 — confirmed absent
- Known limitations: single-process SQLite by design (ADR-0002)
- Dependencies: repository skeleton
- Next action: write schema with `CHECK (reserved_count + consumed_count <= cap)`

**Domain model**
- Status: `PLANNED` · Location: planned `app/domain/` · Tests: — · Verified 2026-09-01 absent
- Constraints: integer paise, UTC, `merchant_id` on every tenant-scoped entity, explicit enums
- Next action: frozen dataclasses + enums after schema

### Safety core

**Contact ledger / atomic reservation**
- Status: `PLANNED` · Location: planned `app/ledger/` · Tests: planned `tests/test_ledger.py`
- Last verification: 2026-09-01 — confirmed absent
- Known limitations: correctness scoped to single-process SQLite; not distributed
- Dependencies: schema, domain model
- Next action: `reserve_contact_budget()` + single `transition()` with CAS; then the 2/10/100-worker test
- **This is the highest-priority component in the project.** See ADR-0003.

**Reservation state machine**
- Status: `PLANNED` · six states, eight legal transitions, all others rejected (`05_SAFETY_INVARIANTS.md` INV-2)

**Policy engine (hard filter)**
- Status: `PLANNED` · Location: planned `app/policy/` · 11 hard constraints; SAFETY vs VALUE trigger split (ADR-0004)

**Tenant isolation**
- Status: `PLANNED` · Location: planned `app/db/dal.py` (`TenantScopedDB`) · nine object classes to cover

**Arbitration**
- Status: `PLANNED` · Location: planned `app/arbitration/` · deterministic, single-writer, never an agent

### Recovery pipeline

**Stage 0 — Validate** · `PLANNED` · planned `app/validation/` · five verdicts; deterministic and probabilistic reported separately
**Stage 1 — Diagnose** · `PLANNED` · planned `app/diagnosis/` · eight failure categories
**Candidate generation** · `PLANNED` · planned `app/candidates/` · `NO_ACTION` always present
**Downtime consumer** · `PLANNED` · planned `app/downtime/` · separate module, not inside diagnosis
**Action executor** · `PLANNED` · planned `app/actions/` · sole holder of send credentials; no retry capability
**Attribution** · `PLANNED` · planned `app/attribution/` · timeline rules; self-cure excluded

### AI / ML

**Heuristic scorer** · `PLANNED` · planned `app/scoring/heuristic.py` · tuned on seeds 1–10, frozen before eval
**CatBoost scorer** · `PLANNED` · planned `app/scoring/model.py` · S-learner, action as feature (ADR-0005)
**Feature builder (point-in-time)** · `PLANNED` · planned `app/models/features.py` · `observed_at <= decision_timestamp` enforced
**Model registry** · `PLANNED` · `models/*.cbm` + `*.meta.json` + git tag; no MLflow (ADR-0008)
**Feedback loop** · `PLANNED` · ε-exploration with propensities; v1→v2→gate→rollback

### Simulation / experiment

**Synthetic generator** · `PLANNED` · planned `app/simulation/generate.py` · seeded, hashed, `FixedClock`
**Response function** · `PLANNED` · planned `app/simulation/response.py` · **must be git-tagged before either scorer exists**
**Payment provider simulator** · `PLANNED` · five outcomes incl. ambiguous and outage
**Experiment runner** · `PLANNED` · planned `app/evaluation/run.py` · 5 arms, hash-asserted identical inputs
**Statistics** · `PLANNED` · planned `app/evaluation/stats.py` · paired t, Wilcoxon, bootstrap, Holm, McNemar
**Falsification suite** · `PLANNED` · four null conditions

### Interface

**Streamlit dashboard** · `PLANNED` · planned `app/dashboard.py` · trace screen first (ADR-0010)
**FastAPI webhook endpoint** · `PLANNED` (optional) · one endpoint, demo vividness only

### Calibration data

**NPCI issuer failure rates** · `BLOCKED` — licence terms unverified (page returned HTTP 403 to automated fetch). Fallback defined: published ranges from secondary sources, cited inline, nothing redistributed.
**MSME Samadhaan ageing** · `BLOCKED` — same reason, same fallback.

### Rejected (do not reintroduce without an ADR)

**PostgreSQL / Redis / Docker** · `REJECTED` for the prototype — ADR-0002
**Agent frameworks (LangChain, LangGraph, AutoGen, CrewAI)** · `REJECTED` — ADR-0007
**LLM on the decision path** · `REJECTED` — ADR-0007
**React / Next / Vite / Node** · `REJECTED` — ADR-0010

---

## Tests

**No test has ever been executed.** `tests/` does not exist. Every row of `testing/TEST_MATRIX.md` is `NOT_RUN`.

## Experiments

**No experiment has ever been run.** `experiments/EXPERIMENT_INDEX.md` is empty by design. Every number appearing in `final.md` §4 is **illustrative and explicitly labelled as such in that document** — it is a target shape, not a result. No agent may present those figures as observed.

## Known open items requiring verification

| Item | Why it matters |
|---|---|
| Submission deadline | Third-party sources say 2026-09-05; Razorpay has never published it. Decides which roadmap applies. |
| NPCI / Samadhaan licence terms | Blocks calibration; fallback exists so it does not block the build |
| Razorpay Payment Downtime API access | Support-request gated; simulate and declare on camera if not granted |
| Razorpay retry-state interface | Assumed, never verified. Engine therefore only recommends retries (ADR-0006) |
