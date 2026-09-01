# NEXT STEPS — Unified Recovery Engine

**Current Focus**: Milestone M7 — Multi-Arm Experimentation & Simulation Benchmarking Framework.

---

## Immediate Next Steps (M7 Preparation)

1. **5-Arm Experimentation Pipeline**:
   - Implement experiment controller for arms:
     - `A1`: Simple Rule / Fixed Retry Policy
     - `A2ns`: Heuristic Prioritization without Safety Controls
     - `A2`: Heuristic Prioritization with Safety Controls
     - `A3`: Machine Learning Probability Ranking without Counterfactual Baseline
     - `A5`: Full AI Decision Engine (S-Learner, Incremental EV, Safety Filters, Epsilon Exploration)
2. **Simulation Benchmark Runner**:
   - Execute batch simulation across 10,000+ synthetic/historical payment failure events.
   - Collect structured `RecoveryObservation` records for all 5 arms under identical event inputs.
3. **Judge-Facing Metrics & Visualizations**:
   - Calculate primary metrics: Net Recovered Revenue (paise), Incremental Recovery Rate (%), Safety Invariant Violation Count (strictly 0), Contact Cap Breach Count (strictly 0).
   - Build Streamlit Judge Dashboard tab for side-by-side strategy comparison.
4. **Final System Verification**:
   - Run end-to-end regression suite and update final build log and architecture handoff document.
