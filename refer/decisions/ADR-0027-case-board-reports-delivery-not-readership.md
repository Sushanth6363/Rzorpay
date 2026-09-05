# ADR-0027 — The case board reports delivery and payment, never readership

- **Status:** ACCEPTED
- **Date:** 2026-09-05 *(recorded retrospectively; the decision was made when the module was written)*
- **Affects:** UI, claims, operations
- **Code:** `app/cases/board.py`, `app/ui/dashboard.py`
- **Related:** ADR-0010 (Streamlit), ADR-0022 (handoff report), ADR-0023 (durable case)

## Context

A merchant uploads fifty rows and needs one screen that answers, per person: what did the
agent decide, did it reach them, have they paid, and if not, is anything still going to
happen. All of that already existed, spread across `cases`, `case_events`, `payment_links`
and `followup_queue`. It just had nowhere to be read.

Two traps sit in the middle of building that screen.

**The first is inventing a Response column.** Every recovery dashboard has one, and it is
almost always a lie. This system has **no open tracking, no click tracking and no read
receipts anywhere**. It knows exactly two things about a customer: whether a contact was
confirmed delivered, and whether money arrived. Anything else on that screen would be
inferred and presented as observed.

The distinction is not pedantic. "Ignored us" and "never saw it" produce identical data and
call for opposite responses — escalate versus fix the channel — and a column that conflates
them will confidently recommend the wrong one.

**The second is that a table is not a board.** The first version rendered as a dataframe:
twelve columns of wrapped text, sorted by upload order. It was accurate and unusable. It
looked exactly like the CSV the merchant had just uploaded, which is what a board is
supposed to save them from reading.

## Decision

**One card per customer**, carrying what a merchant scans for: who, how much, how overdue,
how far up the escalation ladder, and what happens next. Ordered by **urgency then
exposure**, so the row needing a human is never below the fold.

**Four flags, and only four:**

| Flag | Meaning |
|---|---|
| `PAID` | money verified by a provider webhook |
| `ACTIVE` | contacted, still inside the follow-up sequence |
| `WAITING` | not yet contacted, or the engine chose not to |
| `STALLED` | contacted, no payment, and **nothing further is scheduled** |

`STALLED` is the reason the board exists. It is the only state that needs a person, and
everything else on the screen exists to make it stand out.

**The escalation ladder is drawn, all four rungs, always.** The unused rungs are what make
it legible as a ladder. A rung lights **only** when a contact was confirmed sent; an action
that was decided but not yet dispatched is drawn dashed, never lit, because a lit rung is a
claim that a message went out.

**No column may claim knowledge we do not have.** No Opened, no Read, no Response, no
Ignored. The note beside an unpaid case is a fact about *us* — "no payment since contact 6d
ago" — never a claim about them.

**A settled case never advertises a future contact.** If a case is terminal, `next_review`
renders empty regardless of what the queue says. "Next review" beside `PAID` reads as
though the engine intends to chase someone who has already paid, which is the one thing
this product must never appear to do.

**A settled case is never aged.** A paid card shows "settled", not "17d overdue". The debt
stopped ageing when the payment was verified, and one visibly wrong number on a screen
discredits every other number on it.

## Consequences

- The screen answers "who needs me" in about two seconds, which a sortable grid did not.
- The honesty constraint is enforced by test, not by intention: the suite asserts that no
  card contains the words opened, read, ignored, declined or seen.
- The board is also the demo surface. Clicking a row expands that case's full decision
  trail, so the audit-trail claim is something a judge can click rather than something they
  are told.

## A consequence worth naming

Refusing to invent a Response column makes the board look **less** capable than competing
dashboards, which show open rates and click-through. That is the correct trade: those
numbers are available to products that embed tracking pixels and rewrite links, and this
one does neither. Showing an empty Opened column would be worse than showing none, and
showing a populated one would require becoming a different kind of product.

## Alternatives considered

- **A sortable dataframe.** What existed. Honest, and unreadable at fifty rows.
- **Adding open/click tracking so the column could be real.** A significant privacy change,
  requiring pixel embedding and link rewriting, made to populate a column nobody asked for.
- **Inferring engagement from time-to-payment.** Presenting a guess as an observation, which
  is the exact failure this ADR is written to prevent.
