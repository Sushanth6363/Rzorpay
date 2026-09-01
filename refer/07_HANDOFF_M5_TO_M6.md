# 07 — HANDOFF: M5 AI DECISION ENGINE TO M6 ARBITRATION ENGINE

**Date**: 2026-09-01
**Source Milestone**: M5 — AI Recovery Decision Engine (COMPLETED)
**Target Milestone**: M6 — Arbitration Engine & Multi-Opportunity Optimization

---

## 1. Verified M5 State & Artifacts

Milestone M5 has been fully implemented, verified, and tested against 113 total passing unit, integration, scenario, and property-based tests (100% pass rate).

### Key Verified Components

1. **S-Learner Model (`app/scoring/s_learner.py`)**:
   - `CatBoostSLearner`: Single CatBoost model with action encoded as an explicit feature alongside context features ($X + A$).
   - Predicts $p(x,a) = P(Y=1 | X=x, A=a)$.
   - Fixed random seed (default 42) ensures 100% deterministic probability predictions.
   - Cold-start fallback: Heuristic baseline probabilities used when training data is missing or insufficient (<10 samples), recording `AbstentionReason.INSUFFICIENT_TRAINING_DATA`.

2. **Counterfactual Baseline & EV Calculator (`app/scoring/ev_calculator.py`)**:
   - Evaluates $P(x, NO\_ACTION)$ baseline first for every decision context.
   - Incremental effect $\hat{\Delta}(x,a) = \hat{p}(x,a) - \hat{p}(x, NO\_ACTION)$ strictly enforced.
   - Monetary Expected Value calculated in integer paise:
     $EV(x,a) = \text{round}(\hat{\Delta}(x,a) \times amount\_paise) - action\_cost\_paise$
   - Negative uplift (e.g. $p(action)=0.60, p(NO\_ACTION)=0.70 \implies \hat{\Delta} = -0.10$) produces negative EV and prevents high raw probability ranking bypass.

3. **Point-in-Time Feature Safety (`app/scoring/feature_builder.py`)**:
   - Enforces $observed\_at \le decision\_timestamp$ (**INV-7**).
   - Checks denylisted post-decision fields, raising `PointInTimeLeakageError` on any violation.
   - Strictly excludes `merchant_id` from model feature vector (**INV-1**) to eliminate merchant bias.

4. **Safety-Constrained $\varepsilon$-Exploration (`app/scoring/exploration.py`)**:
   - Epsilon-greedy exploration ($\varepsilon=0.05$) operates ONLY over actions approved as `ELIGIBLE` by M4 hard safety filter (**ADR-0004**, **INV-3**).
   - Candidates marked `SAFETY_REJECTED` (gateway outage, budget cap exhaustion) can NEVER be selected or explored.

5. **File-Based Model Registry (`app/scoring/registry.py`)**:
   - `FileBasedModelRegistry` stores model artifacts at `models/vN.cbm` with sibling `vN.meta.json` containing SHA256 artifact hash, feature schema, and metrics (**ADR-0008**).

6. **Structured Decision Record (`AIRecoveryDecision`)**:
   - `AIRecoveryDecisionEngine` returns an audit-ready decision record containing `decision_id`, baseline probability, candidate scores, selected action, decision mode (`EXPLOIT` | `EXPLORE` | `SAFE_ABSTENTION`), and provenance.
   - **M5 Invariant**: `is_contact_reserved` is strictly `False`. M5 DOES NOT reserve contact slots or execute payments.

---

## 2. Interface Contracts for M6

M6 (Arbitration Engine) will consume `AIRecoveryDecision` outputs from M5:

```python
from app.scoring import AIRecoveryDecisionEngine
from app.pipeline import RecoveryPipeline

# Step 1: M4 Pipeline processes raw event into RecoveryDecisionContext
pipeline = RecoveryPipeline(db=db, clock=clock, downtime_provider=downtime_provider)
context = pipeline.process_raw_event(raw_event, decision_timestamp=clock.now_iso())

# Step 2: M5 AI Engine scores candidates and returns AIRecoveryDecision
ai_engine = AIRecoveryDecisionEngine(learner=learner, epsilon=0.05)
ai_decision = ai_engine.evaluate_decision(context, random_seed=42)

# Step 3: M6 Arbitration Engine will take ai_decision and:
#   - Check global merchant-level arbitration & contact budget
#   - Atomically reserve contact slot via ContactLedger (reserve_slot) if selected_action != NO_ACTION
#   - Dispatch intervention or log decision record
```

---

## 3. Verified Golden Scenarios

The AI decision engine has been validated against 10 standardized Golden Scenarios (`AI-01` to `AI-10`):
- `AI-01`: `NO_ACTION` wins when all interventions have negative incremental EV.
- `AI-02`: Retry recommendation wins when it has positive incremental EV and zero action cost.
- `AI-03`: Customer message (WhatsApp) beats retry based on higher incremental EV.
- `AI-04`: Lower raw probability action wins due to lower action cost and higher incremental EV.
- `AI-05`: Active gateway outage forces retry into `SAFETY_REJECTED`; AI cannot select retry.
- `AI-06`: Exploration ($\varepsilon=1.0$) cannot select safety-rejected candidate (**INV-3**).
- `AI-07`: Budget cap exhaustion leaves outreach candidates `SAFETY_REJECTED`; AI safely falls back.
- `AI-08`: Future-dated feature raises `PointInTimeLeakageError` (**INV-7**).
- `AI-09`: Insufficient training data produces safe cold-start fallback with heuristic baselines.
- `AI-10`: Identical inputs and seed produce 100% identical decision records.

---

## 4. Test Suite Summary

- **Total Tests**: 113
- **Passing**: 113 (100% pass rate)
- **Execution Time**: ~5.5 seconds
