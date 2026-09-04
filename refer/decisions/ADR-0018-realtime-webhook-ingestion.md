# ADR-0018 — Real-time webhook ingestion: durable, idempotent, fail-closed

- **Status:** ACCEPTED
- **Date:** 2026-09-04
- **Affects:** ingestion, security, downtime signal, Stage 0, PII
- **Code:** `app/realtime/`, `app/api/webhook_listener.py`
- **Tests:** `tests/realtime/test_webhook_ingestion.py` (25)

## Context

A webhook endpoint existed but could not function as a real-time system. Four defects, each
found by driving it over HTTP rather than by reading it.

## Decisions

**1. One durable, shared database.** The handler built `RecoveryOrchestrator()` at import,
defaulting to `init_db(":memory:")`. The server and dashboard are separate processes, so
each held a private database: no ingested event could ever appear in the UI, and every
decision was lost on restart. Now one WAL-mode SQLite file, with a `live_feed` table the UI
tails. Connections and orchestrators are **thread-local** — Starlette acknowledges on the
event loop and processes on a worker thread, and SQLite connections are thread-bound.

**2. Signature verification fails closed.** Verification was skipped whenever no secret was
configured, so an unauthenticated POST to a public URL would run the engine and mint payment
links. Absent configuration is now a 401. `ALLOW_UNSIGNED_WEBHOOKS=1` reopens it for local
testing and logs loudly on every request.

**3. Idempotent delivery.** Razorpay retries until it gets a 2xx, so a slow response meant
the same failed payment was recovered twice — two messages to one customer, two slots off
one contact budget. Deliveries are keyed on Razorpay's event id; a retry returns
`DUPLICATE_IGNORED` without acting. One row per delivery, advanced in place (an
`INSERT OR IGNORE` would silently DROP the completion and leave every event at ACCEPTED).

**4. Explicit event mapping — never a family prefix.** The original mapping was
`"FAILED_PAYMENT" if "payment" in event_name else "ABANDONED_CHECKOUT"`. A prefix fallback
is actively dangerous here: `payment.captured` and `payment.authorized` are **successes**,
and a `payment.` fallback turned them into `FAILED_PAYMENT` — the engine would have chased
customers who had just paid, the exact phantom recovery Stage 0 exists to prevent.
`payment.downtime.*` was likewise turned into a failed payment instead of a gateway signal.
Unenumerated events are dropped, never guessed.

**5. Downtime is consumed, not simulated.** `payment.downtime.*` drives
`LiveRazorpayDowntimeProvider`. INV-4 is unchanged — a known outage suppresses retries and
outreach — but *known* now means Razorpay told us. Provenance is `REAL_DATA`. Outages are
persisted so they survive restart; forgetting one means resuming contact about a gateway
still down. The lookup **fails safe** (reports healthy) rather than raising, since a
throwing downtime check inside the decision path would take the pipeline down.

**6. Resolutions are consumed.** `payment.captured` / `order.paid` / `invoice.paid` /
`payment_link.paid` mark the entity paid. Webhooks are unordered, so a capture can arrive
before the failure for an earlier attempt; without persisting it the engine cannot learn
the customer already paid.

**7. No determinism seed on the live path.** `random_seed=42` was hardcoded, so live
exploration replayed the same draw forever. Live traffic gets no seed.

**8. Fast acknowledgement.** Full orchestration plus an outbound API call ran inside the
request, so a slow dependency produced a timeout and therefore a retry — turning one failure
into duplicate contact attempts. The request records durably, acknowledges, then processes.

## Safety posture

Outbound dispatch is **OFF by default**. The engine decides and writes a full audit trail
but sends nothing until `RECOVERY_DISPATCH_ENABLED` is set, and refuses live (`rzp_live_`)
credentials unless `RECOVERY_ALLOW_LIVE_CREDENTIALS` is *separately* set. Two independent
gates, because the difference between a demo and contacting a stranger should not be one
environment variable.

## Known limitation, stated

`subscription.*` events are not available on the demo Razorpay account, so **live traffic
reaches 3 of the 4 streams**. The fourth is exercised only in the batch evaluation. This is
disclosed rather than left for a reviewer to discover.
