# 00 — START HERE

**Five-minute orientation.** Read this first, then `01_PROJECT_STATE.md`, then `progress/CURRENT_STATUS.md`.

> **Documentation is evidence, not truth. Code plus executed tests determine implementation status.**

---

## CURRENT PROJECT STATUS (keep this block current)

```
CURRENT PROJECT STATUS:   DESIGN COMPLETE — IMPLEMENTATION NOT STARTED
CURRENT PHASE:            Pre-implementation (architecture frozen)
CURRENT MILESTONE:        M1 — Project setup  (NOT STARTED)
LAST COMPLETED TASK:      refer/ handoff system created (2026-09-01)
CURRENT TASK:             None in progress
NEXT TASK:                M1.1 — create venv, requirements.txt, repo skeleton, first git commit
BLOCKERS:                 1. Repository has ZERO git commits — nothing is version controlled
                          2. Submission deadline unverified; third-party sources say 2026-09-05
                             (4 days from today). NOT confirmed by Razorpay. VERIFY FIRST.
OPEN QUESTIONS:           1. Actual deadline (see above) — decides 10-day vs 3-day plan
                          2. NPCI / MSME Samadhaan licence terms (blocks calibration; fallback exists)
LAST VERIFIED TEST:       NONE — no test has ever been run
LAST VERIFIED EXPERIMENT: NONE — no experiment has ever been run
```

**Verified 2026-09-01 by direct inspection**: no `.py` files exist, `git log` reports no commits, no `requirements.txt`, no `Makefile`, no database. The `app/` directory exists but is empty.

---

## What are we building?

A **Unified Recovery Engine**: one decision system sitting above four revenue-leak types (failed payment, abandoned checkout, failed subscription renewal, overdue B2B invoice). For each at-risk case it decides whether money was genuinely lost, diagnoses why, ranks the possible interventions — including doing nothing — and executes at most one, under a contact budget shared across all four streams.

## Why?

Razorpay ships **twelve single-purpose recovery agents across two platforms** (7 Agent Studio + 5 RazorpayX) with no published shared customer state. A customer appearing in three of them can receive three messages from three systems, none aware of the others. Nothing published arbitrates across leak types for the same customer, and nothing checks whether the "at-risk" money was ever at risk.

## What problem does it solve?

1. Redundant and conflicting customer contact across independent agents.
2. Chasing revenue that was never actually lost (TDS withholding, self-cured retries, carts completed elsewhere, deliberate cancellations).
3. Recovery attempts fired into a known gateway outage.

## What is novel?

| | |
|---|---|
| **D1** | Shared per-customer contact ledger + cross-stream arbitration |
| **D3** | Stage 0 — validate that money was lost *before* acting (a gate, not a report) |
| **D2** | Consuming Razorpay's own downtime signal at the *recovery* layer (narrow claim) |
| — | Abstention as a first-class output; per-case permission derivation |

## What is NOT novel (never claim it)

Approval gates · review-first mode · opt-out suppression · audit trail · outage **detection** · payment links · retries. All shipped and blogged by Razorpay. We comply with their published standard and cite it; we do not claim it.

## What is the AI component?

**Stage 2 action selection.** A calibrated CatBoost model estimating `P(recovery | features, action)` for each eligible action including `NO_ACTION`, from which an expected value is derived and ranked. That is the whole AI. Arbitration, policy and the ledger are deterministic **by design**.

## What is the safety component?

The hard policy filter, the atomic contact ledger, deterministic arbitration, tenant isolation, and abstention. See `05_SAFETY_INVARIANTS.md` — those invariants are non-negotiable without an ADR.

## What is simulated vs real?

| Simulated / synthetic | Really built |
|---|---|
| Razorpay payments, message delivery, customer response, gateway outages, execution outcomes | Contact ledger, policy engine, arbitration, AI model, attribution, experiment + statistics, audit trail |

Environmental distributions (issuer failure rates, B2B ageing) are **calibrated** from public real data. **No recovery outcome in this project is real.**

## What is already implemented?

**Nothing.** Zero lines of code. See `01_PROJECT_STATE.md` — every component is `PLANNED`.

## What should be built next?

`M1.1` — repository skeleton and first commit. Then `M3` (contact ledger) before any AI work. See `progress/NEXT_STEPS.md`.

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
