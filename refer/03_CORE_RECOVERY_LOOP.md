# 03 — CORE RECOVERY LOOP

The exact runtime sequence. **Implemented and verified 2026-09-05 at `e803e36`** (481 tests).
Until 2026-09-05 this line read *"Every stage is `PLANNED`; no code exists yet"*, written before
the build and never updated. `Code:` paths below are the **delivered** ones; stage 9 was never
built as designed and says so.

```
Payment / Revenue Event → RecoveryOpportunity → Stage 0 Validate → Stage 1 Diagnose
  → Candidate Generation → Hard Safety Filter → Compliant Escalation Ceiling
  → AI Recovery Decision → NO_ACTION vs Intervention → Policy Recheck
  → Atomic Contact Reservation  ← this IS the cross-stream arbitration
  → Execution → Outcome → Self-Cure / Attribution
  → Follow-up on silence → Experiment Result → Feedback Dataset → Future Model Version
```

---

## 1. Event → RecoveryOpportunity
- **What happens**: event ingested, deduplicated on `source_event_id`, identity resolved within the merchant partition, opportunity created
- **Code**: `app/realtime/event_mapper.py` · `app/pipeline/dataset_adapter.py` (ADR-0012)
- **In**: raw event · **Out**: `RecoveryOpportunity`
- **Can fail**: duplicate delivery; identity below confidence threshold — fail toward *distinct*, never merge
- **Test proves it**: replay every event twice → identical state

## 2. Stage 0 — Validate
- **What happens**: deterministic checks (TDS, payment↔invoice match, duplicate payment, already settled), then confidence-gated probabilistic checks (self-cured retry, cart completed elsewhere, deliberate cancellation)
- **Code**: `app/validation/objective/` · `app/validation/probabilistic/`
- **In**: opportunity + transaction records + statutory table · **Out**: verdict + basis + confidence
- **Can fail**: wrong rate table wrongly closes a receivable; over-wide self-cure window wrongly closes a real case
- **Test proves it**: TDS case → `PHANTOM_RISK` → zero contacts; adversarial cases abstain
- **Phantom exits here.** Reported as *phantom-risk value avoided* — never as revenue recovered.

## 3. Stage 1 — Diagnose
- **What happens**: failure-reason classification over the published error taxonomy; cross-case correlation clusters failures by issuer / method / time window
- **Code**: `app/diagnosis/classify.py` · `app/diagnosis/correlate.py`
- **In**: validated opportunity · **Out**: diagnosis + cluster id
- **Can fail**: 40 unrelated failures wrongly clustered as one outage, or vice versa
- **Test proves it**: injected outage → correct cluster; correlation precision reported

## 4. Candidate Generation
- **What happens**: enumerate feasible actions; `NO_ACTION` always included
- **Code**: `app/pipeline/candidate_generator.py`
- **Can fail**: generator bypassing policy (architecturally forbidden)
- **Test proves it**: `NO_ACTION` present in every candidate set

## 5. Hard Safety Filter
- **What happens**: 11 constraints applied; ineligible actions removed *with* reasons; the surviving set becomes the exploration pool
- **Code**: `app/pipeline/safety_filter.py` (then `app/pipeline/escalation.py`, ADR-0015)
- **In**: candidates + flags + budget + payment state + outage · **Out**: eligible set + block reasons
- **Can fail**: an ineligible action surviving into scoring or exploration
- **Test proves it**: 2,000 random seeds cannot produce an ineligible action (INV-3)

## 6. AI Recovery Decision
- **What happens**: scorer returns `p̂(x,a)` per eligible action; `Δ̂ = p̂(x,a) − p̂(x, NO_ACTION)`; `EV = Δ̂ × recoverable_paise − action_cost`
- **Code**: `app/scoring/heuristic.py` | `app/scoring/model.py`
- **Can fail**: uncalibrated probabilities make the EV ranking arbitrary
- **Test proves it**: identical `ScoringContext` hash across A3/A5; Brier + calibration-slope gate

## 7. NO_ACTION vs Intervention
- **What happens**: abstention triggers evaluated in order. SAFETY triggers collapse the eligible set to `{NO_ACTION}`. VALUE triggers permit exploration
- **Code**: `app/policy/triggers.py`
- **Can fail**: forced intervention when abstaining was correct
- **Test proves it**: each of seven triggers produces its reason code and consumes no budget

## 8. Policy — execution-time recheck
- **What happens**: `flags_version` re-read inside the same transaction that flips `reserved → executed`; if it changed, the hard policy re-runs
- **Code**: `app/policy/` + `app/actions/executor.py`
- **Can fail**: opt-out or dispute arriving between decision and send (TOCTOU)
- **Test proves it**: opt-out mid-flight → abort, release, audit, nothing sent

## 9. Cross-stream arbitration — **the ledger, not an arbitrator**
- **What happens**: nothing separate happens here. Arbitration *is* stage 10: all four streams
  contend for one atomic per-customer contact slot and the cap decides. There is no ranking of
  competing agent proposals, because there are no agents.
- **Code**: `app/ledger/reservation.py` (see stage 10) · `app/experiment/policies.py` for the
  A1-vs-A2 contrast that measures the effect
- **Planned as**: `app/arbitration/arbitrate.py` plus `app/agents/*.py`, 12 simulated agent
  recommendations. **Never built** — recorded in `01_PROJECT_STATE.md` §Not built.
- **Can fail**: claiming an arbitrator exists. It does not; the guarantee comes from
  `BEGIN IMMEDIATE` and a DB `CHECK`, which is stronger than a deterministic ranking function.
- **Test proves it**: A1 (per-stream budgets, nothing arbitrates) spends 1,500 contacts / 22.73
  per customer; A2 (one shared slot) spends 1,336 / 20.24 for statistically indistinguishable
  recovery.

## 10. Atomic Contact Reservation
- **What happens**: `BEGIN IMMEDIATE`; look up by idempotency key **first**; conditional `UPDATE … WHERE reserved_count + consumed_count < cap`; insert reservation; write decision record — all one transaction
- **Code**: `app/ledger/reservation.py` · `app/ledger/transitions.py`
- **Can fail**: lost update (the T0 race) if implemented as read-then-write; slot leaked on idempotent retry
- **Test proves it**: cap binds after executions; same key → one slot; 2/10/100 workers; Hypothesis fuzz
- **This is the highest-risk stage in the system.** It fails silently.

## 11. Execution
- **What happens**: CAS `reserved → executed`, commit, **then** send. Ambiguous response → `execution_unknown`, slot held, reconciliation ladder
- **Code**: `app/actions/executor.py` · `app/simulation/provider_sim.py`
- **Can fail**: send succeeded but the local write failed — the most dangerous failure in the system
- **Test proves it**: ambiguous → delivered | not_sent | unresolved; never re-sent; send count stays 1

## 12. Outcome
- **What happens**: provider result and any payment recorded with timestamps
- **Code**: `app/actions/` · `app/attribution/`
- **Can fail**: send timestamp used where delivery timestamp is required

## 13. Self-Cure / Attribution
- **What happens**: ordered timeline rules — payment before the first delivered intervention → `SELF_CURED`, attributed zero. Within the attribution window → `RECOVERED_ATTRIBUTED` (last touch). Outside it → `RECOVERED_UNATTRIBUTED`. After the observation window → `NOT_RECOVERED` + `post_window_payment`
- **Code**: `app/attribution/classify.py`
- **Can fail**: claiming credit for a payment that preceded contact
- **Test proves it**: payment-before-delivery; window boundaries; partial payment + TDS tolerance

## 14. Experiment Result
- **What happens**: per-seed aggregation, paired differences, confidence intervals, Holm correction over the secondary family
- **Code**: `app/evaluation/run.py` · `app/evaluation/stats.py`
- **Can fail**: computing a CI at decision level (n=24,000) instead of seed level (n=40)
- **Test proves it**: identical `input_hash` and `world_hash` across arms; null experiment reports *inconclusive*

## 15. Feedback Dataset → Future Model Version
- **What happens**: point-in-time dataset built with propensities; v2 trained; promotion gate runs on `MODEL_SELECTION_SET`; holdout unlocked only after the decision is final
- **Code**: `app/models/train.py` · `app/models/registry.py`
- **Can fail**: future outcomes leaking into historical features; holdout touched before promotion
- **Test proves it**: holdout locked; bad model rejected; model hash constant within a run
