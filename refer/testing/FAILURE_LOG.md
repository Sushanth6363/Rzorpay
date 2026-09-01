# FAILURE LOG

Every meaningful failure is recorded here. **Historical failures are never deleted** — they are marked resolved. A deleted failure is a lesson lost, and repeated bugs are the cost.

## Template

```
Failure ID:
Date:
Component:
Observed behavior:
Expected behavior:
Reproduction steps:
Root cause:
Fix:
Regression test:
Commit:
Status:            OPEN / FIXED / WONTFIX / SUPERSEDED
Lessons learned:
```

---

## Pre-implementation design defects

These were found by review before any code existed. They are recorded because the same mistakes are easy to reintroduce during implementation.

### F-0001 — Contact cap did not bind
- **Date**: 2026-08-30
- **Component**: contact ledger (design)
- **Observed**: cap checked as `reserved_count >= cap`, while `mark_reservation_executed` decremented `reserved_count`. After 4 executed contacts a customer sat at `reserved_count = 0` and the check passed, admitting contacts 5, 6, 7…
- **Expected**: the 5th contact in a month is rejected.
- **Root cause**: the counter named in the check measured in-flight contacts, not used contacts.
- **Fix**: check `reserved_count + consumed_count < cap` inside the UPDATE; add a DB CHECK constraint.
- **Regression test**: `test_cap_binds_across_executed_contacts`
- **Status**: FIXED IN DESIGN — **not yet implemented or verified**
- **Lesson**: a counter's name is not its semantics. The invariant belongs in the database, so a residual bug raises instead of over-contacting.

### F-0002 — Budget slot leaked on idempotent retry
- **Date**: 2026-08-30
- **Component**: contact ledger (design)
- **Observed**: counter incremented before the reservation INSERT; the IntegrityError path returned the existing reservation without rolling back the increment.
- **Expected**: a repeated request consumes at most one slot.
- **Root cause**: write ordering — counter first, dedup check second.
- **Fix**: look up by idempotency key first and return before touching any counter.
- **Regression test**: `test_same_idempotency_key_consumes_one_slot`
- **Status**: FIXED IN DESIGN — not yet implemented
- **Lesson**: the dedup check must precede every side effect, not follow it.

### F-0003 — Idempotency key contained a timestamp
- **Date**: 2026-08-30
- **Component**: contact ledger (design)
- **Observed**: key was `(customer, merchant, month, case_id, decision_epoch)` where `decision_epoch` was a wall-clock reading, so a retrying worker generated a new key and never reached the dedup path.
- **Fix**: caller-supplied deterministic key; `decision_epoch` becomes an arbitration run id.
- **Status**: FIXED IN DESIGN — not yet implemented
- **Lesson**: an idempotency key containing anything that varies between retries is not an idempotency key.

### F-0004 — `execution_unknown` had no exit
- **Date**: 2026-08-31
- **Component**: reservation state machine (design)
- **Observed**: every CAS guard read `status='reserved'`, so release, expire and mark_executed all no-opped against `execution_unknown`. A reservation entering that state held its slot forever.
- **Fix**: bounded reconciliation ladder with three terminal outcomes, including fail-closed `unresolved`.
- **Status**: FIXED IN DESIGN — not yet implemented
- **Lesson**: adding a state without adding its exits creates a trap door.

### F-0005 — Ambiguous send counted as confirmed
- **Date**: 2026-08-31
- **Component**: contact accounting (design)
- **Observed**: an unconfirmed send incremented `consumed_count`, which was documented as "confirmed sent", making an ambiguous send indistinguishable from a delivered one in every metric.
- **Fix**: `consumed_count` redefined by capacity meaning; `consumption_basis` column carries the delivery fact; `contacts_sent` computed as `COUNT(status='executed')`.
- **Status**: FIXED IN DESIGN — not yet implemented
- **Lesson**: a counter used by metrics needs a definition metrics can rely on.

---

## Implementation failures

*(none yet — no code exists)*
