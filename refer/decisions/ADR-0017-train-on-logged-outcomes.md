# ADR-0017 — The S-learner trains on the engine's own logged outcomes

- **Status:** ACCEPTED
- **Date:** 2026-09-03
- **Affects:** AI/ML, experiment, claims
- **Code:** `app/scoring/logged_dataset.py`
- **Related:** ADR-0005 (S-learner), ADR-0011 (arms)

## Context

A5 (CatBoost) was significantly **worse** than A3 (the transparent heuristic), and that was
being reported as an honest finding about the model. It was not a fact about CatBoost. It
was a train/serve mismatch.

`SyntheticDatasetGenerator` built labels from an independent, hand-authored probability
table that **disagrees with the sandbox the model is graded in**:

| Action | Sandbox (graded in) | Training table | Heuristic |
|---|---|---|---|
| AGENT_DIAL | 0.70 | 0.37 | 0.55 |
| **RECOMMEND_RETRY** | **0.65** | **0.27** | 0.50 |
| WHATSAPP_LINK | 0.55 | 0.32 | 0.45 |
| SMS_LINK | 0.40 | 0.30 | 0.35 |
| IVR_CALL | 0.35 | 0.27 | 0.40 |
| EMAIL_LINK | 0.30 | 0.22 | 0.25 |

`RECOMMEND_RETRY` sits near the **bottom** of the training table and is the **second best**
action in the sandbox. The model learned that world faithfully and was then scored in a
different one — while the heuristic's hand-written baselines happened to match the grading
world's ordering almost exactly.

The obvious alternative explanation was ruled out first. Decomposing the gap showed it was
**not** an exploration confound:

- clean scorer effect (exploit vs exploit): **−4.75%** — *worse* than the −3.05% headline
- exploration: **+1.70%** — it *helped*

## Decision

Generate the training set the way a production recovery engine actually gets one: replay
opportunities through the real pipeline, dispatch into the real sandbox, and log what
happened.

- **Seed disjoint from evaluation.** Batch seed 7 and outcome seeds 1–10, versus
  evaluation's batch seed 42 and seeds 21–40. No opportunity and no outcome draw is shared.
  This is the property ADR-0005 always claimed, and this module is the first code to
  actually provide it — the previous comment asserting seed disjointness was describing
  something that did not exist.
- **Same feature path.** Rows come from `FeatureBuilder` on a real
  `RecoveryDecisionContext`, never hand-assembled, so train and serve cannot drift.
- **Uniform logging policy.** Every action is logged for every opportunity, so the training
  set carries no action-selection bias from the policy being learned. This is the clean
  off-policy setup, not the model grading its own homework.

**The simulator's probabilities are untouched.** This changes *where labels come from*,
never *what they are*.

## Result

A5 became exactly equal to A3 — a VOID ablation under ADR-0011, not a win. The evaluator now
detects the identical-arm condition and declares it rather than presenting a tie as parity.
That result motivated ADR-0020.

## Why this is not leakage

In production you train on your own historical recovery outcomes, from the same world you
then act in. That is not leakage; that is having training data. The rule that matters is
temporal and seed disjointness, which is preserved and is stronger here than it was before.
