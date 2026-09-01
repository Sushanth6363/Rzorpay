# M6 — SANDBOX EXECUTION, RECOVERY OUTCOME & ATTRIBUTION DESIGN

**Status**: FINAL DESIGN
**Milestone**: M6 — Sandbox Execution, Recovery Outcome & Attribution Loop
**Date**: 2026-09-01

---

## 1. Executive Summary

Milestone M6 completes the closed-loop execution and attribution surface of the **Unified Recovery Engine**. M6 connects the decision outputs from M5 (`AIRecoveryDecision`) into an atomic contact slot reservation system, executes interventions against a deterministic stateful sandbox, reconciles ambiguous execution attempts (`EXECUTION_UNKNOWN`), classifies customer payment outcomes (handling self-cures with zero AI attribution), records reproducible experiment observations, and provides trace visibility for judge exploration.

---

## 2. Contracts & Boundaries

### A. Execution Contract (M5 Hand-off to M6)

M6 receives the `AIRecoveryDecision` produced by M5 alongside the `RecoveryDecisionContext`:

```python
from app.domain.models import AIRecoveryDecision, RecoveryDecisionContext

# Required Fields from M5 Output:
# - decision_id: str
# - merchant_id: str
# - customer_id: str
# - opportunity_id: str
# - selected_action: ActionType (e.g. RECOMMEND_RETRY, WHATSAPP_LINK, NO_ACTION)
# - decision_mode: DecisionMode (EXPLOIT | EXPLORE | SAFE_ABSTENTION)
# - decision_timestamp: str
# - model_version: str
# - selected_action_score: Optional[CandidateScore]
```

**Invariant**: If `selected_action == ActionType.NO_ACTION` or `decision_mode == DecisionMode.SAFE_ABSTENTION`, M6 skips contact reservation and directly records an uncontacted observation. If `selected_action != ActionType.NO_ACTION`, M6 MUST attempt atomic slot reservation prior to sandbox execution.

### B. Sandbox Execution Contract

The Sandbox Executor interface abstracts intervention execution into a controlled, credential-free, simulated environment:

```python
class SandboxActionRequest:
    action_id: str
    decision_id: str
    merchant_id: str
    customer_id: str
    opportunity_id: str
    action_type: ActionType
    amount_paise: int
    requested_at: str
    idempotency_key: str

class SandboxExecutionResult:
    execution_id: str
    action_id: str
    status: ExecutionStatus  # EXECUTED | FAILED_CLOSED | EXECUTION_UNKNOWN
    delivered_at: Optional[str]
    failure_reason: Optional[str]
    raw_response: Dict[str, Any]
    provenance: DataProvenance = DataProvenance.SIMULATED_EXTERNAL_STATE
```

### C. Outcome & Payment State Machine Contract

The payment lifecycle within the sandbox is governed by an explicit state machine:

```text
               ┌─────────────────────────────────────────┐
               │             PAYMENT_FAILED              │
               └────────────────────┬────────────────────┘
                                    │
           ┌────────────────────────┴────────────────────────┐
           │                                                 │
 [Customer Pays Before Action]                   [Action Executed / Retry]
           │                                                 │
           ▼                                                 ▼
┌─────────────────────┐                          ┌─────────────────────┐
│     SELF_CURED      │                          │   EXECUTION RESULT  │
│ (Attribution: ₹0)   │                          └──────────┬──────────┘
└─────────────────────┘                                     │
                                         ┌──────────────────┼──────────────────┐
                                         ▼                  ▼                  ▼
                                 ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
                                 │PAYMENT_SUCCESS│  │PAYMENT_FAILED │  │    UNKNOWN    │
                                 └───────────────┘  └───────────────┘  └───────┬───────┘
                                                                               │
                                                                               ▼
                                                                     [M3 Reconciliation]
                                                                               │
                                                             ┌─────────────────┼─────────────────┐
                                                             ▼                 ▼                 ▼
                                                      ┌─────────────┐   ┌──────────────┐  ┌──────────────┐
                                                      │ DELIVERED   │   │  NOT_SENT    │  │  UNRESOLVED  │
                                                      │ (Slot: Hold)│   │(Slot: Release│  │ (Slot: Hold) │
                                                      └─────────────┘   └──────────────┘  └──────────────┘
```

**Outcome Statuses**:
- `PAYMENT_SUCCESS`: Customer completed payment following intervention (or retry).
- `PAYMENT_FAILED`: Payment remains unrecovered after intervention attempt.
- `NO_PAYMENT`: Action delivered/failed, but no payment attempted by customer.
- `EXECUTION_UNKNOWN`: Transport or provider timeout during intervention execution; requires reconciliation.

### D. Attribution Contract

Attribution strictly separates **Self-Cured** payments from **AI-Attributed Recovery**:

1. **Self-Cure Rule**:
   If a payment succeeds *at or before* the intervention delivery timestamp ($t_{\text{payment}} \le t_{\text{delivered}}$) or if `NO_ACTION` was chosen and the customer pays naturally:
   - `attribution_status` = `SELF_CURED`
   - `gross_recovered_paise` = `amount_paise`
   - `attributed_recovered_paise` = `0` (**CRITICAL INVARIANT**)

2. **Intervention Recovery Rule**:
   If payment succeeds within the valid attribution window following delivered intervention ($t_{\text{delivered}} < t_{\text{payment}} \le t_{\text{delivered}} + \Delta_{\text{window}}$):
   - `attribution_status` = `RECOVERED`
   - `gross_recovered_paise` = `amount_paise`
   - `attributed_recovered_paise` = `amount_paise`

3. **Failed Intervention Rule**:
   If payment does not succeed within attribution window:
   - `attribution_status` = `FAILED_UNRECOVERED`
   - `gross_recovered_paise` = `0`
   - `attributed_recovered_paise` = `0`

4. **Gross vs Incremental Recovery**:
   - `Gross Recovered`: Raw sum of recovered payments.
   - `Attributed Recovered`: Sum of recovered payments directly attributed to delivered interventions.
   - `Incremental Recovered`: Population-level difference $\sum (\text{Attributed Recovered}) - \text{Expected Counterfactual Baseline Recovery}$.

### E. Reconciliation Contract for `EXECUTION_UNKNOWN`

When sandbox returns `EXECUTION_UNKNOWN`:
1. Ledger status set to `EXECUTION_UNKNOWN`. Contact slot remains **HELD** (`reserved_count` maintained) to prevent duplicate outreach.
2. System NEVER automatically resends an `EXECUTION_UNKNOWN` intervention (**INV-6**).
3. The entry enters the M3 Reconciliation Ladder:
   - `RECONCILED_DELIVERED` $\implies$ Slot transitions from `reserved_count` to `consumed_count` (Slot consumed). Outcome observed.
   - `RECONCILED_NOT_SENT` $\implies$ Slot released (`reserved_count` decremented). Zero capacity consumed.
   - `RECONCILED_UNRESOLVED` $\implies$ Slot conservatively treated as `consumed_count` (Slot held/consumed) to prevent duplicate customer contact. Sent to human audit.

---

## 3. End-to-End Recovery Correlation Trace

Every recovery execution produces a fully auditable correlation chain:

$$\text{event\_id} \longrightarrow \text{opportunity\_id} \longrightarrow \text{decision\_id} \longrightarrow \text{ledger\_id} \longrightarrow \text{execution\_id} \longrightarrow \text{outcome\_id} \longrightarrow \text{attribution\_id}$$

This ensures zero unexplained "₹ recovered" figures in the Streamlit UI or audit logs.

---

## 4. Invariants Enforced in M6

- **INV-1 (Tenant Isolation)**: All DAL queries, ledger operations, and sandbox states are merchant-scoped.
- **INV-3 (Exploration Safety)**: Exploration cannot select `SAFETY_REJECTED` candidates.
- **INV-4 (Gateway Outage)**: Retries and outreach are suppressed during active downtime.
- **INV-6 (Execution Unknown)**: `EXECUTION_UNKNOWN` never automatically retries; slot held until reconciliation.
- **INV-7 (Point-in-Time Safety)**: Feature snapshots and attribution timestamps enforce strict causality.
- **ADR-0003 (Contact Budget)**: Atomic single-row CAS constraint (`reserved + consumed <= cap`).
- **ADR-0006 (Retry Ownership)**: Engine recommends retries (`RECOMMEND_RETRY`), payment execution remains external.
