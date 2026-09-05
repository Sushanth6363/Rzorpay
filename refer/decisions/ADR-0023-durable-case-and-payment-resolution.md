# ADR-0023 — A durable case, and payment always wins

- **Status:** ACCEPTED
- **Date:** 2026-09-05 *(recorded retrospectively; the decision was made when the modules were written)*
- **Affects:** domain, persistence, dispatch, payments
- **Code:** `app/cases/models.py`, `app/cases/repository.py`, `app/payments/link_service.py`, `app/api/webhook_listener.py`
- **Related:** ADR-0012 (adapter boundary), ADR-0021 (follow-up timing), ADR-0026 (agent loop)

## Context

The engine was built around a **decision**: an event arrives, a decision is produced,
an action is taken. That is the right unit for an experiment and the wrong unit for a
product, because recovery is a process that runs for days across multiple attempts and
several channels.

Nothing owned the sentence "this customer, this debt, across every attempt". Consequently:

- The second contact had no memory of the first beyond a ledger row.
- A payment could arrive and the engine had no object to mark as settled.
- A payment link had no owner, so nothing could cancel it when the debt was paid.

There is a specific hazard hiding in the third point. Recovery systems send links. If the
customer pays through one link while another is still live, a second payment can be taken
for a debt that no longer exists. That is not a bug report; it is a refund, an apology, and
a merchant who stops using the product.

## Decision

Introduce a durable spine that outlives any individual decision:

- **`Customer`** — who we may contact, and how.
- **`Case`** — one debt, one lifecycle: `OPEN`, `IN_PROGRESS`, `PROMISED`, `PAID`, `CLOSED`.
- **`PaymentLink`** — a provider link bound to a case, with its own status.
- **`CaseEvent`** — an append-only timeline: created, decided, link created, message sent,
  follow-up scheduled, payment received, closed. Provider-neutral by construction, per
  ADR-0012.

`Case.may_contact` is the **single question** the dispatcher asks. Not a combination of
flags evaluated at each call site, because a rule expressed in five places is five chances
to express it differently.

### Payment always wins

`ChannelDispatcher.precheck()` **re-reads the case from storage** and deliberately ignores
any case object passed in by the caller, which is stale by construction: it was loaded when
the action was queued, and the interesting event — payment — happens after that.

On a verified payment the case is marked `PAID`, every other open link on it is cancelled,
and every scheduled follow-up is stopped. A customer who has paid cannot be contacted by
something already in flight.

### Refusing simulated links

`PaymentLinkService` refuses to attach a simulated link to a live case. A simulated link
fires no webhook, so a case holding one could never close, and would sit in the board
looking active forever. Failing at creation is better than a case that can only ever be
wrong.

## A defect this decision exposed

A real Rs 25,000 payment was made through a real recovery link. Razorpay delivered
`payment.captured` and `order.paid`. Both passed HMAC verification. Both were recorded. The
case stayed `IN_PROGRESS` with a follow-up still scheduled against it.

The engine was about to chase a customer who had already paid — the exact failure this ADR
exists to prevent — and it survived 395 passing tests.

The cause was resolution, not policy. The listener read `reference_id` from the top level of
the entity. A **payment link** entity carries it there; a **payment** or **order** entity
does not — ours is echoed inside `notes`, and the originating link appears in `description`
as `#<id without the plink_ prefix>`. The repository could already map a reference to a
case; it was simply never handed one.

Two corrections followed:

1. Resolution now collects **every** identifier the event offers, most authoritative first,
   and tries each. `payment.captured`, `order.paid` and `payment_link.paid` all close the
   case, so correctness no longer depends on which events a merchant happened to tick in a
   dashboard.
2. `cancel_for_entity` matched only `origin_event_id`, while the webhook path cancels by
   `case_id`. The update matched zero rows and returned 0, and no caller checked. Nothing
   reached the customer, because the dispatcher re-read the case and would have refused —
   but relying on the last line of defence for what the first line was supposed to do is
   luck, not design. It now matches either identifier.

The regression test uses the **actual payload Razorpay sent**, contact details scrubbed. A
hand-written fixture would have encoded the same wrong assumption that caused the bug.

## Consequences

- Recovery state survives process restarts, which the previous decision-shaped design did
  not.
- The board (ADR-0027) and the handoff report (ADR-0022) both become possible, because
  there is finally an object to report on.
- Double-payment is prevented at two independent layers: link cancellation on settlement,
  and a re-read at dispatch time.

## Alternatives considered

- **Keep the decision as the unit and reconstruct state by replaying events.** Correct in
  principle, and it makes the single most common query — "may we contact this person now" —
  a fold over history at dispatch time. Too slow and too easy to get wrong in the one place
  it must never be wrong.
- **Trust the provider's entity as the case identity.** Fails immediately: one case can have
  several links, and a payment names none of them directly.
