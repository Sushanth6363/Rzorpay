# ADR-0003 — Atomic reservation and reserved+consumed cap semantics

**Date**: 2026-08-30
**Status**: ACCEPTED
**Author/Agent**: Claude Opus 5, ratified by project owner

## Decision
The contact cap is checked as `reserved_count + consumed_count < cap` inside the WHERE clause of a single conditional UPDATE, backed by a DB `CHECK` constraint. Every state transition is a compare-and-swap whose rowcount decides the counter movement.

## Context
The original P0 repair specified atomic reservation but checked `reserved_count >= cap`, while `mark_reservation_executed` decremented `reserved_count`. After four executed contacts the customer sat at `reserved_count = 0` and the check passed.

## Problem
The monthly cap did not bind. D1 — the project's central claim — was inoperative, and the failure was invisible in a demo.

## Options considered
1. Check `reserved + consumed` in the UPDATE, plus a CHECK constraint (CHOSEN)
2. Keep a single `used_count` and never split reserved/consumed
3. Application-level check before the UPDATE

## Decision rationale
Option 3 is the read-then-write race the whole design exists to avoid. Option 2 loses the ability to distinguish in-flight from confirmed, which the reconciliation ladder needs. Option 1 keeps both and makes the invariant enforceable by the database, so any residual bug raises instead of over-contacting.

## Trade-offs
Two counters to keep consistent instead of one. Mitigated by routing all counter movement through a single `transition()` function.

## Impact
`consumed_count` means *permanently unavailable for reuse* — confirmed sent OR failed closed after an unresolved execution (`RECONCILED_UNRESOLVED`).

**Why `RECONCILED_UNRESOLVED` consumes the contact slot**:
Because the system cannot safely assume the intervention did not happen; releasing capacity back to the customer's contact budget could permit a duplicate intervention. The conservative policy is therefore to consume the slot (`reserved_count - 1, consumed_count + 1`) and send the case to the human-review queue. `contacts_sent` must be computed as `COUNT(status='EXECUTED' OR status='RECONCILED_DELIVERED')`, never directly from `consumed_count`.


## What this prevents
Silent budget overrun — the exact harm D1 claims to prevent.

## Affected components
`app/ledger/`, INV-2, all contact metrics

## Tests required
Cap binds after executions; same idempotency key consumes one slot; repeated transitions idempotent; expiry cannot race execution; 2/10/100 workers; Hypothesis fuzz.

## Evidence
Defect found by reading the P0-1 pseudocode; recorded in `p0.1-technical-correction.md` I-1.

## Reversal conditions
Only if the cap semantics themselves change — for example a rolling window instead of a calendar month.

## Related ADRs
ADR-0002, ADR-0004
