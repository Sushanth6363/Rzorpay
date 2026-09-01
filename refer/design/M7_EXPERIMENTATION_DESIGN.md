# M7 — EXPERIMENTATION, INCREMENTAL RECOVERY MEASUREMENT & FEEDBACK LOOP DESIGN

**Status**: PROPOSED & APPROVED  
**Date**: 2026-09-01  
**Milestone**: M7 — Experimentation, Incremental Recovery Measurement & Feedback Loop  

---

## 1. Architectural Overview & Objective

Milestone M7 completes the measurement and feedback loop of the **Unified Recovery Engine**. It establishes a trustworthy, reproducible, and auditable experimentation framework to answer the central question:

> **Does the AI recovery engine produce more revenue recovery than what would have occurred without the intervention?**

```text
       Raw Opportunities / Failure Events
                      │
                      ▼
       ┌──────────────────────────────┐
       │  Experiment Randomization    │ -> Deterministic Hashing: sha256(exp_id | merch_id | cust_id | opp_id | seed)
       └──────────────┬───────────────┘
                      │
   ┌──────────────────┼──────────────────┬──────────────────┬──────────────────┐
   ▼                  ▼                  ▼                  ▼                  ▼
┌──────┐          ┌───────┐          ┌──────┐           ┌──────┐           ┌──────┐
│  A1  │          │ A2ns  │          │  A2  │           │  A3  │           │  A5  │   + [ CONTROL / NO_ACTION ]
└──┬───┘          └───┬───┘          └──┬───┘           └──┬───┘           └──┬───┘
   │                  │                  │                  │                  │
   └──────────────────┴──────────────────┼──────────────────┴──────────────────┘
                                         │
                                         ▼
                       ┌──────────────────────────────────┐
                       │ Closed-Loop Recovery Orchestrator│ (M4 -> M5 -> M3 -> M6)
                       └─────────────────┬────────────────┘
                                         │
                                         ▼
                       ┌──────────────────────────────────┐
                       │ Attribution & Observation Log    │ (Self-cure ₹0 attribution)
                       └─────────────────┬────────────────┘
                                         │
                                         ▼
                       ┌──────────────────────────────────┐
                       │ Statistical Evaluator & Metrics  │ (Paired t-test, Newcombe CI, Holm-Bonferroni)
                       └─────────────────┬────────────────┘
                                         │
                                         ▼
                       ┌──────────────────────────────────┐
                       │ Feedback Loop & Training Records │ (Feature X / Outcome Y separation, zero leakage)
                       └──────────────────────────────────┘
```

---

## 2. Five Pre-Registered Arms (ADR-0011)

| Arm ID | Canonical Name | Ledger + Arbitration | Stage 0 Validation | Downtime Signal | Scorer | Description |
|---|---|---|---|---|---|---|
| `CONTROL` | `NO_ACTION_BASELINE` | ✗ | ✗ | ✗ | None | Uncontacted counterfactual baseline for natural self-cure recovery. |
| `A1` | `BASELINE_INDEPENDENT` | ✗ | ✗ | ✗ | Rules | Simple independent rule engine (recommends retry without shared ledger). |
| `A2ns` | `UNIFIED_NO_STAGE0` | ✓ | ✗ | ✗ | Heuristic | Shared ledger & atomic contact arbitration active; no Stage 0 validation. |
| `A2` | `UNIFIED_NO_DOWNTIME` | ✓ | ✓ | ✗ | Heuristic | Shared ledger & Stage 0 active; no downtime signal. |
| `A3` *(alias A4)* | `UNIFIED_DOWNTIME_HEURISTIC` | ✓ | ✓ | ✓ | Heuristic | Shared ledger + Stage 0 + downtime signal; heuristic scoring. |
| `A5` | `UNIFIED_DOWNTIME_CATBOOST` | ✓ | ✓ | ✓ | CatBoost S-Learner | Full AI decision engine (S-Learner, Incremental EV, Safety Filters, Epsilon Exploration). |

---

## 3. Randomization & Anti-Leakage Rules

1. **Deterministic Seeded Randomization**:
   Assign arm via `sha256(f"{experiment_id}|{merchant_id}|{customer_id}|{opportunity_id}|{seed}")`. Identical seed + opportunity produces 100% identical assignment.
2. **Outcome Independence**:
   Arm assignment occurs strictly before decision execution and is completely independent of customer payment outcomes.
3. **Hard Safety Non-Overridability (INV-3)**:
   Safety rejections (`KNOWN_GATEWAY_OUTAGE`, `CONTACT_BUDGET_UNAVAILABLE`) remain non-overridable. No treatment arm can execute safety-rejected actions.
4. **Tenant Isolation (INV-1)**:
   All assignment operations are merchant-scoped.

---

## 4. Metrics & Statistical Methodology

### Primary Metric
- **Incremental Recovery Rate ($\Delta \text{Rate}$)**: Treatment Recovery Rate $-$ Control Baseline Recovery Rate on the primary comparison (`A2 vs A1`).

### Secondary Metrics
- **Gross Recovered Revenue**: Sum of all simulated payment successes (`gross_recovered_paise`).
- **Attributed Recovery**: Sum of intervention-attributed revenue (`attributed_recovered_paise`). Self-cure payments strictly yield **₹0 AI attribution**.
- **Net Incremental Value**: $(\text{Gross Treatment Paise} - \text{Gross Control Paise}) - \text{Total Action Cost Paise}$.
- **Abstention & Contact Cap Breach Rates**: Verified 0 cap breaches.

### Statistical Intervals
- **Paired t-interval**: Evaluated over $n = 40$ seeds for per-seed recovery differences.
- **Newcombe Difference Interval**: Proportion difference between treatment and control.
- **Holm–Bonferroni Correction**: Applied to secondary multiplicity family (`A2ns vs A1`, `A2 vs A2ns`, `A3 vs A2`, `A5 vs A3`).
- **Inconclusive Verdict**: If 95% CI includes zero, reported as `INCONCLUSIVE` or `INSUFFICIENT_SAMPLE`. Never claimed as false significance.

---

## 5. Feedback Loop & Data Transformation

Transforms `RecoveryObservation` -> `TrainingRecord` for offline retraining:
- $X$: Decision-time feature vector (point-in-time compliant, `INV-7`).
- $A$: Selected recovery action.
- $Y$: Observed outcome (`PAYMENT_SUCCESS` vs `PAYMENT_FAILED` / `NO_PAYMENT`).
- Post-decision fields strictly excluded from decision feature vectors.
