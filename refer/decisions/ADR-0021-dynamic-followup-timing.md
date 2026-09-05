# ADR-0021 — Follow-up timing derived from diagnosis, channel and attempt

- **Status:** ACCEPTED
- **Date:** 2026-09-05 *(recorded retrospectively; the decision was made when the modules were written)*
- **Affects:** recovery workflow, contact policy, copy
- **Code:** `app/realtime/followup.py`, `app/dispatch/copy.py`
- **Related:** ADR-0015 (escalation ladder), ADR-0023 (durable case), ADR-0026 (agent loop)

## Context

An engine that contacts a customer once and stops is not a recovery product. Most of the
money in receivables arrives on the second or third touch, so the question "when do we ask
again" is not an implementation detail; it is most of the product.

The obvious answer is a constant. Chase every case every 48 hours. That is wrong in both
directions at once, and the two failures are asymmetric:

- A **gateway failure** is our fault and is usually over in hours. Waiting two days to
  re-offer a payment link wastes intent that was there at the moment of failure.
- An **overdue B2B invoice** sits with a finance team on a payment run. Chasing it every
  48 hours does not accelerate anything; it gets the sender's domain filtered, which
  destroys the channel for every other customer too.

The channel matters independently of the reason. Silence after an SMS is a real signal
within a day. Silence after an email is mostly unread mail. Silence after a **phone call**
is not silence at all, and following a call quickly reads as pressure rather than service.

## Decision

The delay to the next review is derived per case, from three factors:

```
delay = base(diagnosis) x multiplier(action) x backoff(attempt)
```

**Base, by diagnosis** — how long until asking again is reasonable rather than rude:

| Diagnosis | Base |
|---|---:|
| Customer abandonment | 6h |
| Gateway failure | 8h |
| Card declined | 24h |
| Subscription renewal failure | 48h |
| Insufficient funds | 72h |
| Customer unresponsive | 120h |
| Invoice overdue | 168h |
| Unknown | 48h |

**Multiplier, by channel** — how long until silence can fairly be called silence. This is a
read-latency judgement, not an urgency one: `RECOMMEND_RETRY` 0.5 (no human is involved),
SMS 0.8, WhatsApp 0.9, email 1.2, IVR 1.5, agent dial 2.0.

**Backoff, by attempt** — 1.0, 1.5, 2.5, 4.0. Someone who ignored three messages is not
more likely to answer the fourth sooner.

Bounded by `MIN_DELAY_HOURS = 1`, `MAX_FOLLOWUPS = 4` and `RECOVERY_WINDOW_DAYS = 30`.

Message copy is selected on the same two axes: **tone by rung** (a first email and a fifth
contact should not read the same) and **ask by diagnosis** (a failed card needs a different
instrument; an overdue invoice needs a person to schedule a payment). Neither is generated
by a language model, which keeps the outbound text reviewable and identical across runs.

## Consequences

- A gateway blip is retried in about 4 hours; an overdue invoice is followed up in about
  8 days. Same engine, no rules written per case, no per-merchant configuration.
- Adding a diagnosis means adding one row to a table, not a new branch in a scheduler.
- The timing is deterministic and therefore testable. Given a diagnosis, an action and an
  attempt number, the next touch time is a pure function.

## A defect this decision exposed

The live path could not read `decision_features` off `AIRecoveryDecision`, so the diagnosis
never reached `followup.schedule()`. Every live case silently fell back to the 48-hour
default and the generic copy — the entire mechanism above was inert in exactly the path
that matters, while remaining correct in tests that passed the diagnosis explicitly.

Fixed by carrying `diagnosis_code` on `EndToEndRecoveryResult`. Proven by observation: an
overdue invoice on 8 Sept scheduled its next review for 14 Sept (168h base x 1.2 email
multiplier), and the copy changed from "The payment did not complete." to "This invoice is
showing as outstanding on our ledger."

The general lesson, which recurs in ADR-0023: a value that is *available* to a function is
not the same as a value that *reaches* it.

## Alternatives considered

- **Fixed interval.** Simplest, and wrong for the reasons above.
- **Learned timing.** Requires outcome data per (diagnosis, channel, delay) cell that this
  project does not have. Inventing it in the simulator would make the result circular.
- **Merchant-configured schedules.** Pushes the judgement onto someone with less
  information than the engine, and produces a support burden rather than a product.
