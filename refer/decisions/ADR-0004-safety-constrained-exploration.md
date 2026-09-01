# ADR-0004 — Safety-constrained exploration; SAFETY vs VALUE triggers

**Date**: 2026-08-31
**Status**: ACCEPTED
**Author/Agent**: Claude Opus 5, ratified by project owner

## Decision
The hard policy filter runs before exploration, and its output set **is** the exploration pool. Abstention triggers are typed: exploration may override a VALUE trigger but never a SAFETY trigger.

## Context
Epsilon-exploration is required so the model can observe outcomes for actions it would not have chosen; without it, `p(x,a)` for rare actions comes from a self-selected sample.

## Problem
Two failure modes pull opposite ways. Unrestricted exploration contacts people the system judged should not be contacted. Fully restricted exploration collects no counterfactual data for the intervention-vs-no-intervention contrast — which is exactly what the incremental estimate needs.

## Options considered
1. Exploration over eligible actions, with typed triggers (CHOSEN)
2. Exploration only when the argmax is already an intervention
3. Unrestricted exploration over all candidates

## Decision rationale
Option 3 is unsafe. Option 2 never explores the NO_ACTION boundary, so uplift estimation stays impossible. Option 1 draws the line where it belongs: exploration may override a judgement about *value*, never a judgement about *safety*.

## Trade-offs
Some contacts are sent that exploitation would not have sent. Bounded at 5% of eligible opportunities, and only where the abstention was a value judgement.

## Impact
SAFETY = unexplained_shortfall, identity_unresolved, policy_indeterminate, payment_state_unknown, contact_cooldown. VALUE = below_value_threshold, cost_exceeds_benefit. When a SAFETY trigger fires the eligible set collapses to {NO_ACTION}.

## What this prevents
The 'unsafe exploration' rejection, and the silent alternative of an unlearnable model.

## Affected components
`app/policy/triggers.py`, `app/scoring/`, INV-3

## Tests required
Property test over 2,000 seeds x 6 constraints; exploration never overrides a SAFETY abstention; exploration does produce variety under a VALUE abstention.

## Evidence
`strategy/STRATEGY.md` P0 FIX 1.

## Reversal conditions
If a trigger is reclassified between SAFETY and VALUE — which itself requires an ADR.

## Related ADRs
ADR-0003, ADR-0005
