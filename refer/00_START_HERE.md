# 00 — START HERE

**Five-minute orientation.** Read this first, then `01_PROJECT_STATE.md`, then `progress/CURRENT_STATUS.md`.

> **Documentation is evidence, not truth. Code plus executed tests determine implementation status.**

---

## CURRENT PROJECT STATUS (keep this block current)

```
CURRENT PROJECT STATUS:   BUILD COMPLETE — submittable
CURRENT PHASE:            Documentation reconciliation & submission
CURRENT MILESTONE:        M9 complete (2026-09-01); six post-M9 feature commits (2026-09-04)
LAST COMPLETED TASK:      Excel handoff report for unrecovered cases (e803e36, 2026-09-04)
CURRENT TASK:             Re-sync status docs against the code (2026-09-05)
NEXT TASK:                Submission package — see progress/NEXT_STEPS.md
BLOCKERS:                 none blocking. OD-2, OD-3 open (calibration licence, downtime API access)
OPEN QUESTIONS:           1. Deadline believed 2026-09-05 — that is today; treat as submittable now
                          2. NPCI / MSME Samadhaan licence terms (fallback active)
                          3. Razorpay Payment Downtime API access (live path built; simulator fallback active)
LAST VERIFIED TEST:       full suite — 255 passed in 9.0s (2026-09-05, e803e36)
LAST VERIFIED EXPERIMENT: 200 events x 20 seeds, batch hash 0837b24c… ; primary A2-A1 = -0.0148
                          (p=0.1846) INCONCLUSIVE; A5-A3 = +0.0005, ADR-0020 P1 FALSIFIED
```

**Verified 2026-09-05 by direct execution**: `.venv` on Python 3.12.9, `pytest` **255 passed in 9.0s**, `scripts/verify_environment.py` quality gate **PASSED** (6/6, zero hardcoded secrets), evaluation regenerated at `e803e36` on a clean tree reproducing the committed batch hash and primary comparison exactly.

---

## What are we building?

A **Unified Recovery Engine**: a single decision system sitting above four revenue-leak channels (failed payment, abandoned checkout, failed subscription renewal, overdue B2B invoice). It ingests events via **dual paths** (**Razorpay TEST MODE** webhooks/APIs where available and a **Deterministic Simulator** for sandbox scenarios), validates whether money was genuinely lost (**Stage 0**), diagnoses why (**Stage 1**), ranks candidate interventions including `NO_ACTION` using a calibrated CatBoost model (**Stage 2 AI**), enforces a shared per-customer contact budget across streams via an atomic SQLite contact ledger — **that shared budget is the arbitration mechanism; streams contend for one slot and the atomic cap decides** — executes interventions safely, attributes recovery accurately (excluding self-cure), and presents full audit traces via an interactive **Streamlit judge dashboard** deployable as a public demo.

## Why?

Razorpay ships **twelve single-purpose recovery agents across two platforms** (7 Agent Studio + 5 RazorpayX) with no published shared customer state. A customer appearing in three of them can receive three messages from three systems, none aware of the others. Nothing published arbitrates across leak types for the same customer, and nothing checks whether the "at-risk" money was ever at risk.

**How we model that, precisely.** We do not simulate twelve named agents as objects. The uncoordinated world is modelled as experiment arm **A1**, where each stream reserves against its own budget row so nothing arbitrates; the coordinated world is **A2ns/A2**, where all streams contend for one atomic per-customer slot. The difference between those arms *is* the measurement: A1 spends 1,500 contacts (22.73 per customer) for recovery statistically indistinguishable from A2's 1,336 (20.24). See `app/experiment/policies.py` and the contact-efficiency table in `results/RESULTS.md`.

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
| **Sandbox** | Judge dashboard with a readable decision trace, a Live Test tab, and safety invariants that are *executed* rather than asserted |
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
| Uncoordinated vs coordinated recovery | **MODELLED AS EXPERIMENT ARMS** (A1 = per-stream budgets, nothing arbitrates; A2 = one shared atomic slot). No agent objects exist. |
| Core Recovery Engine | **REAL** Python domain models, SQLite ledger, Stage 0-2 logic |
| AI Scoring & Policy | **REAL** CatBoost ML model, hard safety filter, atomic CAS ledger |

Environmental distributions (issuer failure rates, B2B ageing) are **calibrated** from public real data. **No recovery outcome in this project claims real-world production Razorpay data.**

## What is already implemented?

**All of it, on the critical path.** 62 modules / 10,530 lines under `app/`, 255 passing tests, one reproducible evaluation. Verified 2026-09-05 at `e803e36`:

- **Foundation** — schema (WAL, `CHECK` cap), domain model (integer paise, injectable clock), tenant-scoped DAL
- **Safety core** — atomic contact ledger (`app/ledger/`), reservation state machine, hard policy filter, tenant isolation
- **Pipeline** — Stage 0 validate, Stage 1 diagnose, candidate generation, compliant escalation (`app/pipeline/escalation.py`), TDS derivation (`app/pipeline/tds.py`), downtime consumer
- **AI** — CatBoost S-learner trained on the engine's own logged outcomes, EV calculator, point-in-time feature builder, file registry, ε-exploration
- **Real-time** — HMAC-verified fail-closed webhook ingestion, retry/dead-letter/reconciliation/replay guard, follow-up on silence
- **Measurement** — 6-arm runner, Holm-Bonferroni, `results/RESULTS.md`, Excel handoff report for unrecovered cases
- **Interface** — Streamlit judge dashboard with live safety checks

Two planned features were **never built** and are recorded as such in `01_PROJECT_STATE.md` §Not built: a red-team mode, and a competing-agent arbitrator (arbitration is the shared budget instead).

## What should be built next?

Nothing on the critical path. Remaining work is submission packaging — see `progress/NEXT_STEPS.md`.


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
Compliant escalation ceiling ← one rung, on confirmed evidence, after the
                              quiet period; layered UNDER safety, so it can
                              only remove a candidate, never revive one
        ↓
Eligible Actions            ← this set IS the exploration pool
        ↓
AI Decision                 p̂(x,a), Δ̂ vs NO_ACTION, expected value
        ↓
Exploration OR Exploitation ε = 0.05, eligible actions only
        ↓
Atomic Contact Reservation  BEGIN IMMEDIATE; reserved + consumed < cap
                            ← this IS the cross-stream arbitration:
                              one slot, single writer, the cap decides
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
