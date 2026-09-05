# ADR-0026 — The agent loop is deliberately thin, and runs the evaluated engine

- **Status:** ACCEPTED
- **Date:** 2026-09-05 *(recorded retrospectively; the decision was made when the module was written)*
- **Affects:** architecture, claims, experiment integrity
- **Code:** `app/agent/loop.py`
- **Related:** ADR-0007 (no agent framework), ADR-0011 (arms), ADR-0017 (training source), ADR-0021 (follow-up timing), ADR-0023 (durable case)

## Context

Track 3 asks for an **agent**. The word invites a particular answer: a framework, a
planner, tool definitions, and a language model deciding what to do next.

ADR-0007 already rejected an LLM on the decision path, for a reason that has not changed —
a decision to contact a customer for money must be reproducible, auditable and explainable
from a number, and a sampled token is none of those. But that ADR was written about the
*decision*. It did not answer what the surrounding loop should be.

There is also a subtler risk, and it is the one that actually matters for the claims this
project makes. If the live path constructs its own scorer, then the engine a judge watches
send an email is **not** the engine the experiment measured. Every number in
`results/RESULTS.md` would describe a different program than the demo. That is not a
performance concern; it is an integrity one.

## Decision

`RecoveryAgent.run_cycle(case_id)` is a small function that:

1. loads the case,
2. delegates the decision to the **existing** orchestrator,
3. creates or reuses a payment link,
4. dispatches through `ChannelDispatcher`,
5. schedules the next review,
6. records each step on the case timeline.

It contains **no policy of its own**. It does not decide who to contact, which channel to
use, whether escalation is permitted, or when to give up. Those live in the pipeline, the
safety filter, the escalation module and the follow-up scheduler, all of which are covered
by the experiment. The agent is the thing that keeps calling them.

Crucially it builds its orchestrator with `build_orchestrator_for_arm(ExperimentArm.A5)`,
the same constructor the evaluation uses, with the **fitted** model. **The live engine is
the evaluated engine.**

Follow-ups are scheduled only when the dispatch outcome is `SENT` or `SKIPPED`. A dispatch
that failed has not consumed an attempt, so scheduling the next rung would let a broken
channel walk the ladder.

## The property this preserves

"Agentic" here means the loop closes without a human in it: the engine decides, acts,
schedules its own next review, wakes itself, re-reads state, and decides again — until the
money arrives or the stopping rules end it. That is a property of the *loop*, not of the
technology used to write it. A planner would add a plausible-sounding narrator on top of
decisions that are already made by expected value, and it would make them harder to audit.

## A defect this decision prevented, and one it exposed

**Prevented:** an earlier version of the live path constructed an *unfitted* model while the
evaluated A5 arm used a fitted one. The demo and the report would have been two different
engines, and the report is the artifact making the claims. Routing through
`build_orchestrator_for_arm` closed that gap by construction rather than by discipline.

**Exposed:** because the agent is thin, a missing call is a missing behaviour with no
fallback to hide it. `followup.schedule()` was not being called at all, so every CSV case
got exactly one contact and then silence — the entire mechanism of ADR-0021 was unreachable
from this path. A thicker agent with its own retry policy would have masked that with
plausible behaviour.

## Consequences

- The demo and the experiment cannot diverge without someone deliberately changing the arm
  constructor.
- The loop is testable without mocking a framework: give it a case id, assert what it
  recorded.
- There is no natural-language explanation of *why* an action was chosen beyond the EV
  arithmetic. That is a real trade, and the arithmetic is the more defensible artifact.

## Alternatives considered

- **An agent framework** (tools, planner, memory). Adds a dependency, a prompt surface and
  a non-determinism source to a decision that is already a deterministic argmax.
- **An LLM for action selection.** Rejected by ADR-0007; nothing here changes that.
- **An LLM for message copy.** Genuinely tempting, and rejected for now: outbound text about
  money owed must be reviewable in advance and identical across runs.
