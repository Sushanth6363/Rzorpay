# ADR-0007 — No agent framework; no LLM on the decision path

**Date**: 2026-08-31
**Status**: ACCEPTED
**Author/Agent**: Claude Opus 5, ratified by project owner

## Decision
Recovery agents are plain Python classes emitting scored proposals. No LangChain, LangGraph, AutoGen, CrewAI or Agents SDK. No LLM API is required; message drafting is templated.

## Context
The project is an AI buildathon submission, so there is pressure to use an agent framework because it looks like AI.

## Problem
Arbitration must be deterministic and auditable. A framework whose value is LLM-driven control flow would be used against its own purpose, and would obscure where the actual intelligence lives.

## Options considered
1. Plain Python classes and a deterministic arbitrator (CHOSEN)
2. LangGraph for agent orchestration
3. CrewAI for multi-agent coordination

## Decision rationale
The frozen architecture states arbitration must not be an agent. The recovery intelligence is action-conditional prediction + NO_ACTION + expected value + feedback — none of which is an orchestration problem. And 'Where is the AI?' gets a better answer: 'Stage 2 action selection, a calibrated CatBoost model comparing five actions against NO_ACTION' beats 'we used an agent framework' in any technical room.

## Trade-offs
The project will not appear to use fashionable tooling. Accepted deliberately.

## Impact
Removes an API key, a cost, a rate limit and a failure mode. Keeps the explanation of any decision readable from a database row.

## What this prevents
The 'AI theater' rejection, and non-deterministic arbitration.

## Affected components
`app/agents/`, `app/arbitration/`, `08_TOOLCHAIN.md` deny-list

## Tests required
Arbitration is deterministic under reordering; explanation renders without an LLM; no LLM dependency in requirements.txt.

## Evidence
`p0.1` Part 15 (agent boundaries); `strategy/TOOLCHAIN.md` §9.

## Reversal conditions
If free-text promise extraction from real customer replies becomes a build target, a scoped LLM call for extraction only — never for permission — could be justified.

## Related ADRs
ADR-0010
