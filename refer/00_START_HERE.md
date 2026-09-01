# 00 — START HERE

**Five-minute orientation.** Read this first, then `01_PROJECT_STATE.md`, then `progress/CURRENT_STATUS.md`.

> **Documentation is evidence, not truth. Code plus executed tests determine implementation status.**

---

## CURRENT PROJECT STATUS (keep this block current)

## CURRENT PROJECT STATUS (keep this block current)

```
CURRENT PROJECT STATUS:   IMPLEMENTATION STARTED (M1 COMPLETE)
CURRENT PHASE:            Implementation Phase (M1 Foundation verified)
CURRENT MILESTONE:        M1 — Project setup (COMPLETED)
LAST COMPLETED TASK:      M1.1 — Repository + Reproducibility Foundation (2026-09-01)
CURRENT TASK:             M1.2 — Razorpay Test Mode Integration Research & Spec
NEXT TASK:                M2 — Domain model + Database schema (sqlite WAL)
BLOCKERS:                 B-1 RESOLVED (Git commit `eb52c38`). B-2 (Deadline verification) open.
OPEN QUESTIONS:           1. Actual deadline — decides 10-day vs 3-day plan
                          2. NPCI / MSME Samadhaan licence terms (fallback active)
                          3. Razorpay Payment Downtime API access (simulator fallback active)
LAST VERIFIED TEST:       tests/test_smoke.py::test_app_import_and_version PASSED (2026-09-01)
LAST VERIFIED EXPERIMENT: NONE — no experiment has ever been run
```

**Verified 2026-09-01 by direct execution**: `.venv` running Python 3.12.9 LTS, `pytest` 1 passed in 1.92s, Git repository active (`eb52c38`), 0 secrets in scanned code.

---

## What are we building?

A **Unified Recovery Engine**: a single decision system sitting above four revenue-leak channels (failed payment, abandoned checkout, failed subscription renewal, overdue B2B invoice). It ingests events via **dual paths** (**Razorpay TEST MODE** webhooks/APIs where available and a **Deterministic Simulator** for sandbox/red-team scenarios), validates whether money was genuinely lost (**Stage 0**), diagnoses why (**Stage 1**), ranks candidate interventions including `NO_ACTION` using a calibrated CatBoost model (**Stage 2 AI**), enforces a shared per-customer contact budget across streams via an atomic SQLite contact ledger, arbitrates competing agent proposals deterministically, executes interventions safely, attributes recovery accurately (excluding self-cure), and presents full audit traces via an interactive **Streamlit Judge Sandbox** deployable to a **Public Live Demo**.

## Why?

Razorpay ships **twelve single-purpose recovery agents across two platforms** (7 Agent Studio + 5 RazorpayX) with no published shared customer state. A customer appearing in three of them can receive three messages from three systems, none aware of the others. Nothing published arbitrates across leak types for the same customer, and nothing checks whether the "at-risk" money was ever at risk. In our prototype, these 12 agents are modeled as **SIMULATED AGENT RECOMMENDATIONS** competing for the single contact slot.

## What problem does it solve?

1. Redundant and conflicting customer contact across independent agents.
2. Chasing revenue that was never actually lost (TDS withholding, self-cured retries, carts completed elsewhere, deliberate cancellations).
3. Recovery attempts fired into a known gateway outage.

## What is novel?

| | |
|---|---|
| **D1** | Shared per-customer contact ledger + cross-stream arbitration |
| **D3** | Stage 0 — validate that money was lost *before* acting (a gate, not a report) |
| **D2** | Consuming Razorpay's downtime signal at the *recovery* layer (narrow claim) |
| **Sandbox** | Interactive Judge Sandbox with Sandbox, Live Test, and Red-Team modes |
| — | Abstention as a first-class output; per-case permission derivation |

## What is NOT novel (never claim it)

Approval gates · review-first mode · opt-out suppression · audit trail · outage **detection** · payment links · retries. All shipped and blogged by Razorpay. We comply with their published standard and cite it; we do not claim it.

## What is the AI component?

**Stage 2 action selection.** A calibrated CatBoost model estimating `P(recovery | features, action)` for each eligible action including `NO_ACTION`, from which an expected value is derived and ranked. That is the whole AI. Arbitration, policy and the ledger are deterministic **by design**.

## What is the safety component?

The hard policy filter, the atomic contact ledger, deterministic arbitration, tenant isolation, and abstention. See `05_SAFETY_INVARIANTS.md` — those invariants are non-negotiable without an ADR.

## What is simulated vs real?

| Input Path / Component | Execution Model |
|---|---|
| Razorpay Test Mode Events | **REAL** test events via Razorpay Webhooks (`source: RAZORPAY_TEST`) |
| Simulator / Sandbox Events | **SIMULATED** deterministic event factory (`source: SIMULATED`) |
| 12 Recovery Agents | **SIMULATED AGENT RECOMMENDATIONS** competing for arbitration |
| Core Recovery Engine | **REAL** Python domain models, SQLite ledger, Stage 0-2 logic |
| AI Scoring & Policy | **REAL** CatBoost ML model, hard safety filter, atomic CAS ledger |

Environmental distributions (issuer failure rates, B2B ageing) are **calibrated** from public real data. **No recovery outcome in this project claims real-world production Razorpay data.**

## What is already implemented?

- **M1.1 Repository Foundation**: `.gitignore`, `requirements.txt`, `pytest.ini`, `.env.example`, `Makefile`, `app/__init__.py`, `tests/__init__.py`, `tests/test_smoke.py`. Verified by `pytest` (1 passed) and Git commit `eb52c38`.

## What should be built next?

`M1.2` — Razorpay Test Mode Research & Specification (`refer/integrations/RAZORPAY_TEST_MODE.md`). Then `M2` (domain model & database schema) and `M3` (contact ledger). See `progress/NEXT_STEPS.md`.


## What must never change without an ADR?

The nine safety invariants (`05_SAFETY_INVARIANTS.md`), the five experiment arms, the primary metric, the database choice, the model choice, exploration behaviour, attribution logic, and the toolchain deny-list. See `decisions/ADR_INDEX.md`.

---

## Architecture (canonical)

```
Payment / Revenue Event
        ↓
RecoveryOpportunity
        ↓
Stage 0 — Validate          is the money genuinely at risk?
        ↓  (phantom → CLOSE, no contact)
Stage 1 — Diagnose          why did it fail?
        ↓
Candidate Generation        incl. NO_ACTION, always
        ↓
HARD SAFETY / POLICY FILTER ← eligibility decided ONCE, here
        ↓
Eligible Actions            ← this set IS the exploration pool
        ↓
AI Decision                 p̂(x,a), Δ̂ vs NO_ACTION, expected value
        ↓
Exploration OR Exploitation ε = 0.05, eligible actions only
        ↓
Multi-Agent Arbitration     deterministic, single-writer
        ↓
Atomic Contact Reservation  BEGIN IMMEDIATE; reserved + consumed < cap
        ↓
Execution                   engine recommends retries, never executes them
        ↓
Outcome → Self-Cure / Attribution
        ↓
Experiment Result → Feedback Dataset → Future Model Version
```

---

## Document map

| Read for | File |
|---|---|
| What exists and what does not | `01_PROJECT_STATE.md` |
| Component contracts | `02_ARCHITECTURE.md` |
| The runtime loop, stage by stage | `03_CORE_RECOVERY_LOOP.md` |
| What "AI" means here, precisely | `04_AI_ML_SPEC.md` |
| The nine non-negotiables | `05_SAFETY_INVARIANTS.md` |
| Which data is real, which is not | `06_DATA_AND_DATASETS.md` |
| Arms, seeds, statistics | `07_EXPERIMENT_METHODOLOGY.md` |
| Approved stack, deny-list | `08_TOOLCHAIN.md` |
| Build order and milestones | `09_IMPLEMENTATION_ROADMAP.md` |
| Why a decision was made | `decisions/ADR_INDEX.md` |
| Live status | `progress/CURRENT_STATUS.md` |
| How to work on this project | `handoff/AGENT_HANDOFF.md` |

**Source documents** (`final.md`, `p0.1`, `p0.2*`, `strategy/`, `docs/`) remain in the repository root and are preserved unchanged. `refer/` consolidates them; it does not replace them.
