# ADR-0025 — The merchant CSV carries no reason column, and nothing is silently dropped

- **Status:** ACCEPTED
- **Date:** 2026-09-05 *(recorded retrospectively; the decision was made when the module was written)*
- **Affects:** ingestion, domain, claims
- **Code:** `app/cases/csv_ingest.py`
- **Related:** ADR-0012 (canonical event), ADR-0023 (durable case), ADR-0024 (email content)

## Context

The receivables path needs an entry point a merchant can actually use, which in practice
means a spreadsheet export. An early version of the template accepted `event_type` and
`failure_reason` columns.

That was a mistake, and a self-serving one. A merchant with a list of overdue invoices knows
**what** is owed and **by whom**. They do not know **why** it is unpaid — that is precisely
the question they are paying an engine to answer. Asking them to type a reason into a
spreadsheet would have meant Stage 1 diagnosis appeared to work brilliantly while doing
nothing at all: the answer would have been supplied in the input and read back out.

Any demo built that way is a demo of the merchant's typing.

Separately, a receivables export is messy: blank phone columns, three date formats, the same
customer twice, an amount written as `"25,000.00"`. The tempting default is to skip rows
that do not parse and process the rest.

That default is wrong here in a way it is not wrong elsewhere. **A silently dropped row is
revenue the merchant believes is being chased and which nothing is chasing.** The failure is
invisible and it compounds every month.

## Decision

**Six columns, all of them things a merchant can actually know:**

```
customer_id, name, email, phone, amount, due_date
```

No `event_type`, no `failure_reason`. The stream is derived structurally instead of asked
for: a merchant-uploaded debt had no charge attempt, therefore there is no stored
instrument, therefore `RECOMMEND_RETRY` is not a legal action for it. That is a fact about
the world, not an opinion to collect. Every row enters as `OVERDUE_B2B_INVOICE` and the
engine diagnoses it per case.

**Nothing is silently dropped.** Every rejected row is returned with its line number and a
reason written for a human, and the UI shows them:

> `Line 3 rejected: malformed email 'not-an-email' - sending to it would hard-bounce`

**A row with no route to the customer is rejected**, not accepted-and-skipped. An email or a
phone is required; a case that can never be contacted is a data-quality ticket, not a
recovery opportunity.

**Validation is strict where being wrong is expensive.** A malformed email that is accepted
becomes a hard bounce, and hard bounces damage the sending domain's reputation for every
subsequent customer. A phone number that cannot be normalised to E.164 is rejected rather
than guessed, because a wrong number is a message to a stranger and it also burns a contact
slot belonging to the real customer.

**Amounts convert to integer paise exactly once**, here, using `round()` rather than `int()`
so float representation error cannot shave a paisa off every amount.

The CSV is then the single source of truth: the `Case` and `Customer` created from a row are
what the email subject, the greeting and the payment link amount are read back from. Nothing
downstream re-enters a number by hand.

## Consequences

- Stage 1 diagnosis is genuinely exercised on this path, because the answer is not in the
  input. A judge can verify this by reading the template: there is no reason field to fill.
- A merchant sees exactly which rows were refused and why, and can fix and re-upload.
- The demo CSV deliberately includes a malformed row, so rejection is visible rather than
  described.

## Alternatives considered

- **Accept a reason column as optional.** Sounds harmless, and it makes every claim about
  diagnosis conditional on which columns a given file happened to contain. Worse, the
  optional path would be the one demonstrated.
- **Best-effort parsing, skip bad rows.** Standard practice, and it converts a data-quality
  problem into invisible lost revenue.
- **Reject the whole file on any bad row.** Safe and unusable: a 500-row export with one
  typo would be refused entirely.
