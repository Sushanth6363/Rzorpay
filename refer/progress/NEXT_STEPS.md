# NEXT STEPS — Unified Recovery Engine

**Current Focus**: Preparing for Milestone M6 — Arbitration Engine & Multi-Opportunity Optimization.

---

## Immediate Next Steps (M6 Preparation)

1. **Multi-Opportunity Arbitration Engine**:
   - Implement global merchant-level arbitration across concurrent opportunities.
   - Enforce capacity-constrained global expected value maximization under contact caps.

2. **Atomic Budget Reservation Integration**:
   - Integrate M5 `AIRecoveryDecision` outputs with M3 `ContactLedger` atomic reservation (`reserve_slot`).
   - Transition selected intervention action from `NEW` to `RESERVED` status atomically.

3. **Opt-Out & Cooldown Arbitration**:
   - Apply customer-level contact cooldown windows (e.g. max 1 contact per 24 hours).
   - Abort reservation and release budget if opt-out or cooldown triggers between decision and execution.

4. **Multi-Arm Experimentation Framework (M7)**:
   - Prepare five experiment arms (A1, A2ns, A2, A3, A5) per ADR-0011.
   - Set up pre-registration and primary metric evaluation (incremental recovery rate).
