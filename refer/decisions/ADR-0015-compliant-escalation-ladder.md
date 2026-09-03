# ADR-0015 — Compliant escalation: one rung, on evidence, after a quiet period

- **Status:** ACCEPTED
- **Date:** 2026-09-03
- **Affects:** policy, actions, pipeline, audit trail, INV-4 ordering
- **Supersedes:** nothing
- **Code:** `app/pipeline/escalation.py`, `app/pipeline/recovery_pipeline.py`
- **Tests:** `tests/pipeline/test_escalation.py` (15)

## Context

The Track 3 bar names **"compliant escalation"** verbatim, alongside stopping rules and an
audit trail. Before this decision the engine had no concept of escalation at all:
`grep -rin "escalat" app/` returned nothing. The scorer ranked all eligible channels by
expected value and could select `AGENT_DIAL` — a human being telephoning a customer — as a
**first** contact, purely because a model scored it highest.

That is not a scoring bug. It is a missing constraint. Recovery outreach has an intensity
ladder, and an engine with no notion of that ladder cannot claim to escalate compliantly,
however good its rankings are.

An earlier plan (F30 in `final.md`) specified "escalate ONE rung" and was never built.

## Decision

Introduce an explicit intensity ladder and bound every decision by a **ceiling** computed
before scoring runs:

```
EMAIL_LINK → SMS_LINK → WHATSAPP_LINK → IVR_CALL → AGENT_DIAL
   rung 0      rung 1       rung 2         rung 3      rung 4
```

Four rules, all enforced in `EscalationPolicy`:

1. **One rung.** `ceiling = highest_confirmed_rung + 1`. Never +2, whatever the score says.
2. **Evidence-gated.** Only a ledger entry in `EXECUTED` or `RECONCILED_DELIVERED` raises
   the ceiling. `EXECUTION_UNKNOWN` does **not** — you may not escalate on a message you
   cannot prove reached anyone.
3. **Quiet period.** No escalation within 24h of the last confirmed contact. The current
   rung stays available; a repeat at the same intensity is not an escalation.
4. **Entry cap.** A customer with no history is met at their stream's entry rung, hard
   capped at `MAX_ENTRY_RUNG = 1` (SMS). `IVR_CALL` and `AGENT_DIAL` are unreachable
   without an earned escalation. **The engine never opens a relationship with a phone call.**

The entry rung is stream-aware within that cap: `FAILED_PAYMENT` and
`FAILED_SUBSCRIPTION_RENEWAL` open at SMS (the customer was transacting seconds ago and an
SMS retry link is the expected medium); `ABANDONED_CHECKOUT` and `OVERDUE_B2B_INVOICE` open
at email. A blanket "always open with email" would not be more compliant, only less useful,
and the property that matters — the ceiling on first-touch loudness — is enforced
regardless by `MAX_ENTRY_RUNG`.

## Ordering: escalation is layered UNDER safety, never over it

The single most important property, and the one most likely to be got wrong:

> **The escalation policy is SUBTRACTIVE ONLY. It can remove eligibility. It can never
> grant it.**

A candidate already `SAFETY_REJECTED` by the hard safety filter — gateway outage (INV-4),
exhausted contact budget (ADR-0003) — passes through untouched and rejected, even when it
sits well below the ceiling. Escalation is a **VALUE** control in the sense of ADR-0004;
safety controls are never overridable by it. `test_escalation_can_never_revive_a_safety_rejected_candidate`
pins this.

Escalation also creates no capacity: an escalated contact still reserves a slot against the
same per-customer budget. It changes *which* action may be taken, never *how many*.

## Consequences

**Positive**
- The bar's "compliant escalation" clause is answered by running code with 15 tests, not by
  a claim.
- The audit trail gains the full working per decision: the ladder, the ceiling, the highest
  confirmed rung, whether the quiet period was active, and which actions were suppressed.
- Suppression reasons are explicit (`ESCALATION_CEILING`, `ESCALATION_COOLDOWN`) rather
  than folded into a generic policy rejection.

**Negative / accepted cost**
- Recovery rate falls slightly. Loud channels score higher under the simulator, and the
  ceiling prevents reaching for them. This is the intended trade and is reported honestly
  rather than tuned away.
- The ladder only advances when contact history is visible, which makes escalation
  **structurally impossible** for arms without a shared contact ledger (see below).

## A consequence worth reporting as a finding

In the 200×20 evaluation, arm **A1** (independent per-stream agents, no shared ledger) sent
1,500 contacts and earned **zero** escalations. Every arm with a shared ledger earned
around 120.

That is not a defect in A1's implementation. An agent with no shared record that this
customer was already reached can never satisfy the evidence test the ladder requires, so it
does not escalate — it repeats the first touch, at full volume, forever. **Compliant
escalation is not a feature that can be bolted onto uncoordinated agents; it presupposes
the shared memory they lack.** This is the strongest single piece of evidence for the
unified-ledger thesis produced so far, and it emerged from building the compliance control
rather than from arguing for the architecture.

## A defect this decision exposed

Wiring escalation revealed that the contact ledger stamped `resolved_at` from the **wall
clock** while decisions ran on the batch's time axis. Every prior contact therefore appeared
to belong to a different epoch, the quiet period was permanently active, and the ladder
never advanced in any run. The control was present in code and dead in every execution.

Fixed in `RecoveryOrchestrator.process_and_execute`: when a caller supplies a
`decision_timestamp`, that is the engine's "now" for that decision, and the ledger and DAL
are stamped from it. In a replay or backtest the audit trail must sit on the batch's own
time axis. Guarded by
`test_ladder_advances_one_rung_per_contact_through_the_full_engine`, which no unit test of
the policy object could have caught.

The evaluation batch also now carries a real time axis (45-day window, chronologically
sorted) — without elapsed time between a customer's opportunities, any quiet-period rule is
vacuous.

## Alternatives considered

- **Let the scorer handle it via cost.** Rejected: `AGENT_DIAL` at ₹15 is still cheap
  against a ₹50,000 invoice, so EV ranking alone will reach for the loudest channel on
  high-value cases — exactly where restraint matters most. Compliance cannot be a price.
- **Fixed rung-0 entry for every stream.** Rejected as less useful without being more
  compliant; `MAX_ENTRY_RUNG` provides the guarantee instead.
- **Advance the ladder on any execution attempt.** Rejected: escalating on an
  `EXECUTION_UNKNOWN` risks a louder second message to someone who received nothing at all,
  which is precisely the harm escalation rules exist to prevent.
