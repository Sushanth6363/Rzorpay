# ADR-0019 — Production reliability: retry, dead-letter, reconciliation, replay guard

- **Status:** ACCEPTED
- **Date:** 2026-09-04
- **Affects:** ingestion, contact ledger, security, observability, PII
- **Code:** `app/realtime/reliability.py`, `app/api/webhook_listener.py`
- **Tests:** `tests/realtime/test_reliability.py` (12)

## Context

Three ways the live system lost money or state **silently** — the failure mode where
everything looks healthy and nothing is working — plus one control that was advertised and
absent.

## Decisions

**1. Failed processing is retried, then dead-lettered visibly.** A background decision that
threw was marked `ENGINE_ERROR` and forgotten. Razorpay had already received its 200, so it
would never redeliver: one transient lock and that customer is never recovered, with no
retry and no alert. Revenue at risk became revenue gone.

Now a durable retry queue with bounded exponential backoff (30s / 2m / 10m / 30m) and then
`DEAD_LETTER`, surfaced on `/metrics`. Retries re-enter the same idempotent engine path
under the same intervention idempotency key, so a retry cannot double-contact anyone.

**2. The reconciliation ladder actually runs.** The ledger has a full `EXECUTION_UNKNOWN`
ladder and **nothing ever invoked it**. Entries sat unresolved forever holding reserved
budget slots that were never consumed or released — a customer's contact budget leaked until
they could not be contacted at all.

A periodic sweep closes entries stale past 30 minutes, **fail closed**:
`RECONCILED_UNRESOLVED` *consumes* the slot. Releasing it would risk contacting a customer
who may already have received the message. Capacity is cheaper than a duplicate contact.

**3. Replay protection is enforced.** `WEBHOOK_MAX_AGE_SECONDS` was defined in config and
reported on `/health` while nothing checked it, so a captured body with its still-valid
signature could be replayed indefinitely. **A documented-but-absent control is worse than a
missing one**, because everything downstream assumes it is there. Now enforced. A missing or
unreadable timestamp is still accepted — the HMAC is the authenticity control, and rejecting
on absent evidence would drop legitimate traffic; this only bounds the reuse window.

**4. PII is minimised.** The mapper used a raw email or phone as the customer key whenever
Razorpay supplied no `customer_id`, writing personal contact details into every ledger row,
audit record, log line and feed entry. The engine only ever needs a **stable identifier**,
never the address. Contact details are hashed to a stable pseudonymous key; dispatch
resolves the real address at send time and the engine never stores it. Stability matters:
contact budgets and escalation ladders are per-customer, so an unstable key would silently
reset both on every event.

**5. Observability that reveals silent failure.** `/metrics` reports dead letters and stale
unresolved contacts specifically — the states where the system looks fine while losing
money — plus an `alerts` array that calls out `DISPATCH IS LIVE` and
`UNSIGNED WEBHOOKS ACCEPTED`.

## Consequences

- An event can now be recovered late rather than not at all.
- Budget no longer leaks, so the contact cap keeps meaning what it says.
- Retries add load during an incident; backoff is bounded and attempts are capped to keep
  that from compounding.

## Not done, and honestly so

- **No contact-budget time window.** The cap is lifetime-per-customer with no monthly reset.
  A production system needs a rolling window; this does not have one.
- **No rate limiting** on the webhook endpoint.
- **No circuit breaker** on the outbound Razorpay API.
- **Backpressure is unbounded** — a large burst spawns unbounded background tasks.
