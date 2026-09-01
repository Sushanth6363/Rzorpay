# CURRENT STATUS — Unified Recovery Engine

**Last Updated**: 2026-09-01
**Current Milestone**: M5 — AI Recovery Decision Engine (COMPLETED)

---

## Completed Milestones

- [x] **M1.1**: Repository & reproducibility foundation
- [x] **M1.2**: Environment alignment & quality gates
- [x] **M2**: Domain Model + Database Schema + SQLite WAL Persistence Foundation
- [x] **M3**: Atomic Contact Ledger & Reconciliation Engine
- [x] **M4**: Recovery Pipeline & Candidate Generators
- [x] **M5**: AI Recovery Decision Engine

---

## Milestone M5 Status Summary

- **CatBoost S-Learner Architecture (ADR-0005)**: Implemented `CatBoostSLearner` single model predicting $p(x,a) = P(Y=1 | X=x, A=a)$ with action as an explicit feature.
- **Counterfactual Baseline ($NO\_ACTION$)**: Every decision context evaluates $P(x, NO\_ACTION)$ first. Incremental effect $\hat{\Delta}(x,a) = \hat{p}(x,a) - \hat{p}(x, NO\_ACTION)$ is strictly enforced.
- **Expected Value (EV) Calculation**: Monetary EV calculated as $EV(x,a) = \hat{\Delta}(x,a) \times amount\_paise - action\_cost\_paise$ strictly in integer paise. Negative uplift produces negative EV and prevents raw high probability ranking bypass.
- **Point-in-Time Feature Safety (INV-7)**: `FeatureBuilder` enforces $observed\_at \le decision\_timestamp$ and checks denylisted post-decision fields, raising `PointInTimeLeakageError` on any future leakage.
- **Safety-Constrained Exploration (ADR-0004, INV-3)**: Epsilon-exploration ($\varepsilon=0.05$) selects ONLY from actions approved as `ELIGIBLE` by M4 hard safety filter. `SAFETY_REJECTED` candidates can NEVER be selected or explored.
- **Multi-Tenant Isolation (INV-1)**: `merchant_id` excluded from model feature vector to eliminate merchant bias; tenant isolation enforced across all evaluation contexts.
- **File-Based Model Registry (ADR-0008)**: Models registered under `models/vN.cbm` with sibling `vN.meta.json` containing SHA256 artifact hash, feature schema, and metrics. Zero external ML platform dependencies.
- **Audit-Ready AI Decision Record**: Produces `AIRecoveryDecision` containing `decision_id`, baseline probability, candidate scores, incremental EV, decision mode, and provenance.
- **No Contact Slot Consumption**: Maintained strict invariant that M5 decision preparation does NOT reserve contact slots or execute payments (`is_contact_reserved=False`).
- **Test Matrix Verification**: 113 / 113 tests passing (100% pass rate), including Golden AI Decision Scenarios `AI-01` through `AI-10`.
