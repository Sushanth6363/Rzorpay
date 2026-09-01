# ADR-0006 — Retry ownership stays outside the recovery engine

**Date**: 2026-08-30
**Status**: ACCEPTED
**Author/Agent**: Claude Opus 5, ratified by project owner

## Decision
The engine emits `RECOMMEND_RETRY`. `EXECUTE_RETRY` does not exist in the action enum. The executor holds no retry-capable credential. `EXECUTION_UNKNOWN` never triggers an automatic retry.

## Context
Razorpay's payment infrastructure retries independently. No public interface exposing attempt history has been verified, and the project must not present assumed API fields as real ones.

## Problem
An engine-side cap of 3 layered on an unknown processor-side count is not a safety property — it is an assumption presented as one. From the customer's perspective the true count could be higher.

## Options considered
1. Recommend only, never execute (CHOSEN)
2. Execute with a local cap of 3
3. Execute after querying Razorpay's attempt history

## Decision rationale
Option 3 requires an interface nobody has verified. Option 2 makes an unverifiable safety claim. Option 1 narrows the product claim but makes it true — and the narrower claim is defensible in a room containing the person who built the retry system.

## Trade-offs
The project can no longer claim end-to-end retry-cap enforcement. `final.md` F26 and one line of the action board change.

## Impact
D2 survives intact: downtime suppression now suppresses *recommendations* and contacts, and the post-resolution beat becomes one merchant-approved batch. Only who presses the button changes.

## What this prevents
An unverifiable safety claim, and inventing an API contract.

## Affected components
`app/actions/`, `app/policy/`, INV-5, INV-6

## Tests required
EXECUTE_RETRY absent from the enum; credential scopes disjoint; no call path from engine to a retry API; unknown retry state blocks recommendation; send count stays 1 after an ambiguous response.

## Evidence
`docs/DATASET_RESEARCH.md` provenance table; `p0.1` Part 19; `p0.2` FIX 11.

## Reversal conditions
If Razorpay's retry-state interface is verified, execution with a coordinated cap becomes possible.

## Related ADRs
ADR-0003
