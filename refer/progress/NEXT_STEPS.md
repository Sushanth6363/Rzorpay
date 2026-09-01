# NEXT STEPS

Prioritised queue. **P0 items block everything below them.**

---

## P0 — must do

### P0-1 — Verify the submission deadline
- **Why**: third-party sources say 2026-09-05 (4 days away); Razorpay has never published it. This decides whether the 10-day, 5-day or 3-day roadmap applies, and therefore what gets built at all.
- **Dependency**: none
- **Definition of done**: deadline confirmed or best-available evidence recorded in `CURRENT_STATUS.md`, and the applicable roadmap named.
- **Status**: NOT_STARTED
- **Owner**: human (cannot be resolved by an agent)

### P0-2 — Initialise the repository and make the first commit (M1.1)
- **Why**: zero commits exist. The anti-rigging evidence depends on commit ordering (response function frozen before either scorer) and cannot be reconstructed later. Every subsequent step assumes version control.
- **Dependency**: none
- **Definition of done**: `.gitignore`, `requirements.txt`, `pytest.ini`, `app/__init__.py`, `tests/__init__.py`, `tests/test_smoke.py`, `.env.example`, `Makefile`; `pytest` runs 1 real smoke test and passes; initial commit created.
- **Status**: COMPLETED (Commit: `eb52c38fde3018ac12417474e158f5f90638f802`, Date: 2026-09-01)

### P0-2b — Reproducibility, Quality Gate & Handoff Foundation (M1.2)
- **Why**: Make repository reproducible, independently verifiable, secret-scanned, and quality-gated before building domain model and database layer.
- **Dependency**: P0-2
- **Definition of done**: `tests/test_environment.py` created; `scripts/verify_environment.py` passes 6/6 quality checks; `refer/REPRODUCIBILITY.md` created; `Makefile` updated; agent handoff documented.
- **Status**: COMPLETED (Date: 2026-09-01)

### P0-3 — Schema + domain model (M2)
- **Why**: everything else persists through it. The CHECK constraints are the enforcement mechanism for INV-2.
- **Dependency**: P0-2b
- **Definition of done**: schema applies on SQLite WAL; CHECK constraints present; `TenantScopedDB` rejects unscoped SQL; integer-paise money type; `FakeClock` injected everywhere; 20 M2 acceptance tests pass.
- **Status**: COMPLETED (Date: 2026-09-01)

### P0-4 — Contact ledger (M3) — **hard gate**
- **Why**: the project's central safety claim. It fails silently, so it must be proven before anything is built on top of it.
- **Dependency**: P0-3
- **Definition of done**: all ledger and reconciliation tests in `TEST_MATRIX.md` show `PASS` with a date and commit — including 10-worker multi-threaded concurrency safety tests and Hypothesis property fuzzing.
- **Status**: COMPLETED (Date: 2026-09-01)

### P0-5 — Recovery pipeline & candidate generators (M4)
- **Why**: provides stage 0 validation, stage 1 diagnosis, and candidate action generation before scoring or policy evaluation.
- **Dependency**: P0-4
- **Definition of done**: Stage 0 and Stage 1 modules implemented with 30 new unit, scenario, and property tests (86 total passing tests).
- **Status**: COMPLETED (Date: 2026-09-01)

### P0-6 — AI Scorer & Counterfactual Policy Engine (M5)
- **Why**: turns RecoveryDecisionContext candidates into calibrated recovery probability scores (P_recovery), cost-benefit trade-off calculations, and optimal action arbitration.
- **Dependency**: P0-5
- **Definition of done**: Scorer module, CatBoost model interface, counterfactual policy evaluator, and arbitration layer implemented and verified with unit tests.
- **Status**: NOT_STARTED

---

## P1 — should do

### P1-1 — Freeze the response function (M6, partial)
- **Why**: it must be git-tagged before either scorer exists, or the anti-rigging evidence is unavailable and the A5 vs A3 comparison is open to the charge of being authored to win.
- **Dependency**: P0-2 (needs git)
- **Definition of done**: `app/simulation/response.py` committed and tagged `response-function-frozen`; no scorer file exists in history before that tag.
- **Status**: NOT_STARTED

### P1-2 — Check NPCI / Samadhaan licence terms
- **Why**: decides whether calibration uses extracted tables or published ranges.
- **Dependency**: none
- **Definition of done**: terms recorded in `06_DATA_AND_DATASETS.md`; path chosen; `BLOCKED` status cleared.
- **Status**: NOT_STARTED · **Owner**: human

### P1-3 — Experiment runner skeleton (M12, partial)
- **Why**: it must run end-to-end on an empty engine before the features it measures are built. Defining "correct" first is what stops the harness from being the thing that runs out of time.
- **Dependency**: P0-3
- **Definition of done**: `make eval` produces a report shape with zero opportunities and no error.
- **Status**: NOT_STARTED

---

## P2 — optional

| # | Item | Why | Status |
|---|---|---|---|
| P2-1 | FastAPI `POST /downtime/events` | makes one demo beat tangible; a function call proves the same thing less vividly | NOT_STARTED |
| P2-2 | Criteo estimator validation | validates the CI machinery on real randomised data; nothing depends on it | NOT_STARTED |
| P2-3 | Dashboard beyond the trace screen | one screen is enough | NOT_STARTED |
| P2-4 | 4th recovery agent | two agents prove collision as well as four | NOT_STARTED |

---

## Cut order if time runs short

```
1. P2-2 Criteo
2. P2-3 dashboard beyond the trace screen
3. M11 feedback loop (demote to design + the v1→v2 script)
4. P2-4 fourth agent
5. Stage 0 probabilistic checks (keep the deterministic TDS gate)
```

**Never cut**: M3 (ledger) · M10 (attribution) · M12 (experiment).
