# ADR-0012 — Provider-neutral adapter boundary and the `CanonicalEvent` contract

- **Status:** ACCEPTED
- **Date decided:** 2026-09-01 · **Date written:** 2026-09-05
- **Affects:** ingestion, adapters, domain model, point-in-time discipline
- **Code:** `app/domain/models.py` (`CanonicalEvent`), `app/pipeline/dataset_adapter.py`,
  `app/realtime/event_mapper.py`, `app/api/webhook_listener.py`,
  `app/orchestration/recovery_orchestrator.py` (`process_and_execute`)
- **Tests:** `tests/realtime/test_webhook_ingestion.py` (25), `tests/pipeline/` (opportunity
  construction, Stage 0), `tests/experiment/` (batch generation through the same boundary)

> **Why this document is dated four days after the decision.** The decision was made and
> implemented on 2026-09-01 — `app/domain/models.py:43` has carried the docstring
> `"""Provider-neutral event contract (ADR-0012)."""` since then — but the ADR itself was
> never written, and `ADR_INDEX.md` linked a file that did not exist. This is that file. The
> decision is reconstructed from the code that implements it, not invented after the fact.

## Context

The engine ingests from two paths that have nothing in common at the wire level:

1. **Razorpay Test Mode** — real webhook deliveries. Provider-shaped payloads: the entity is
   nested under a different key per event family (`payload.payment.entity`,
   `payload.subscription.entity`, `payload.invoice.entity`), amounts arrive as `amount` or
   `amount_due`, and times arrive as Unix epoch integers.
2. **The deterministic simulator** — the sandbox event factory and the experiment batch
   generator, which must be reproducible from a seed.

The obvious failure mode is a forked engine: a `process_webhook()` alongside a
`process_simulated()`, each with its own Stage 0, its own validation, its own drift. Two code
paths means the demo path and the real path diverge, and the reproducible one is the only one
anybody ever tests. A judge would then be watching a simulator that shares a name with the
product but not its logic.

Two further constraints made an ad-hoc mapping unacceptable:

- **Point-in-time discipline (INV-7).** The model may only use facts available at decision
  time. That requires *two* distinct timestamps — when the event happened, and when we learned
  of it — kept separate from the moment of ingestion onward. A single `timestamp` field
  collapses them and the leakage guard has nothing to check.
- **Money is integer paise.** Provider payloads carry paise as ints, dataset rows carry rupees
  as strings and floats. Whatever crosses the boundary must already be `Money`.

## Decision

One boundary, crossed at two levels, with **exactly one engine entrypoint**.

```
Razorpay webhook ──► event_mapper.map_webhook() ──┐
                                                  │
                                                  ├──► raw event dict
                                                  │        │
Simulator / batch / dataset row ──────────────────┘        │
                                                           ▼
                            orchestrator.process_and_execute(raw_event=…)
                                                           │
                                       DatasetAdapter.adapt_raw_event()
                                                           │
                                                           ▼
                                                  CanonicalEvent  (frozen)
                                                           │
                                            Stage 0 ─► Stage 1 ─► candidates ─► …
```

**Level 1 — the raw event dict.** Provider-specific unwrapping stops here. `map_webhook()`
owns everything Razorpay-shaped: which key the entity hides under, `amount` vs `amount_due`,
epoch-to-ISO conversion, and the pseudonymous customer key. It emits a plain dict in the same
shape a dataset row or a simulated event uses. The simulator produces that dict directly.

**Level 2 — `CanonicalEvent`.** `DatasetAdapter.adapt_raw_event()` normalises the dict into a
frozen dataclass, and nothing downstream of it can tell which path the event came from:

| Field | Contract |
|---|---|
| `event_id` | engine-assigned identity |
| `merchant_id` | tenant scope — every read and write below is scoped by it (INV-1) |
| `customer_id` | pseudonymous key; never a raw email (ADR-0019) |
| `source_event_id` | the provider's own id, retained for reconciliation |
| `event_type` | one of the four streams — provider vocabulary is already gone |
| `amount` | `Money`, integer paise, always |
| `currency` | ISO code |
| `source` | `RAZORPAY_TEST` or `SIMULATED` |
| `idempotency_key` | deduplication key; `(merchant_id, idempotency_key)` is unique |
| `occurred_at` | when the money was lost |
| `observed_at` | when we learned of it — the point-in-time cut |
| `raw_payload` | the untouched original, for the audit trail |

### Rules that keep the boundary honest

1. **Frozen.** `CanonicalEvent` is `@dataclass(frozen=True)`. An ingested event is a fact. No
   stage may edit history; derived state lives on `RecoveryOpportunity`.
2. **An unmapped event is dropped, never guessed.** `resolve_stream()` returns `None` for an
   unrecognised event name and the listener acknowledges and discards it. Mapping is an
   explicit table, never a family prefix — the code this replaced read
   `"FAILED_PAYMENT" if "payment" in event_name else "ABANDONED_CHECKOUT"`, which filed
   `subscription.halted` as a failed payment and made three of four streams unreachable from
   real traffic. A misfiled event is recovered under the wrong policy, which is worse than
   not acting.
3. **No money at risk, no event.** A non-positive amount returns `None` before an opportunity
   exists, rather than letting Stage 0 reject it later.
4. **Two timestamps, never one.** `occurred_at` and `observed_at` are separate at the boundary
   so the leakage guard has something to enforce (INV-7).
5. **`raw_payload` is retained verbatim.** Every decision can be traced back to the bytes that
   caused it without re-reading the provider.
6. **The boundary is the only entrypoint.** The live listener, the retry queue, the follow-up
   scheduler, the batch runner and the dashboard's Live Test tab all call
   `process_and_execute(raw_event=…)`. There is no second engine path to drift.

## Known gap — recorded, not hidden

`source` is set from the `provenance` argument, which the live path leaves at its default, so a
`CanonicalEvent` built from a real webhook is tagged `SIMULATED`. The live/test distinction is
carried by the `webhook_events` ingest store and the provider's own provenance reporting
instead (`tests/realtime/test_webhook_ingestion.py::test_the_live_provider_reports_real_provenance`).

This is a labelling gap, not a behavioural one: `source` is written to the database and copied
onto the opportunity, and is read by no policy, feature builder, or safety check — verified by
grep, `.source` appears only in `dal.py`, `models.py` and one field copy in
`recovery_pipeline.py`. Worth fixing; not worth claiming is already right.

## Consequences

**Positive**
- One engine, one Stage 0, one audit format for both paths. The demo cannot diverge from the
  real path because there is no second path.
- Adding a provider is a new Level-1 mapper and nothing else.
- Reproducibility survives: the simulator hits the same entrypoint, so a seeded batch exercises
  production code rather than a parallel implementation.

**Negative / accepted cost**
- The intermediate raw dict is untyped, so Level-1 mapper bugs surface at Level 2 rather than
  at a type check. Mitigated by 25 ingestion tests, four of which pin one stream each.
- Two hops where a single typed mapper would do — the cost of accepting both provider payloads
  and dataset rows through one door.

## Alternatives considered

- **Map webhooks straight to `RecoveryOpportunity`.** Rejected: skips Stage 0's own
  construction path and gives the live path a shortcut the simulator does not have — precisely
  the fork this ADR exists to prevent.
- **A provider SDK type as the internal contract.** Rejected: couples every stage to Razorpay's
  payload shape and makes the simulator synthesise fake provider payloads to test policy.
- **Pydantic models at the boundary.** Rejected under ADR-0007's minimal-dependency posture;
  a frozen dataclass plus `Money`'s own validation covers what is actually enforced here.


