# ADR-0016 — TDS position is derived from the invoice, never read off a flag

- **Status:** ACCEPTED
- **Date:** 2026-09-03
- **Affects:** Stage 0, attribution, money reporting, B2B stream
- **Code:** `app/pipeline/tds.py`, `app/pipeline/stage0.py`
- **Tests:** `tests/pipeline/test_tds_derivation.py` (14)

## Context

Stage 0's TDS exclusion was a passthrough:

```python
if context.get("is_tds_withheld", False):
    return NOT_RECOVERABLE
```

That is not a capability. It is the engine being *told* the answer by whoever built the
event, and then taking credit for knowing it. The distinguishing claim of this project —
that it declines to chase revenue that was never chaseable — cannot rest on a boolean
somebody else computed.

The underlying problem is real and specific to Indian B2B receivables. An invoice for
₹1,00,000 settled with a remittance of ₹90,000 looks like a ₹10,000 shortfall to every
naive receivables system, which starts chasing the customer. If the invoice falls under
s.194J, that ₹10,000 **is** the statutory withholding: the payer already remitted it to the
government on the payee's behalf. The customer owes nothing. Chasing them is a demand for
money the law required them to withhold.

The inverse matters just as much. A ₹1,00,000 invoice under s.194C (company, 2%) settled at
₹85,000 has a ₹15,000 shortfall of which ₹2,000 is statutory. The recoverable debt is
₹13,000. An engine that chases ₹15,000 is asking for money it cannot lawfully collect —
**and its "recovered" figure is inflated by an amount it never could have recovered.**

## Decision

Derive the withholding position from the invoice's own facts — gross amount, section, payee
constitution, PAN availability, amount actually remitted — and classify into one of five
positions:

| Position | Meaning | Recoverable |
|---|---|---|
| `NO_SHORTFALL` | settled in full | 0 |
| `STATUTORY_WITHHOLDING` | shortfall == expected TDS | 0 — not customer debt |
| `PARTIAL_WITH_TDS` | shortfall > expected TDS | shortfall − TDS |
| `UNDER_WITHHELD` | shortfall < expected TDS | full shortfall |
| `UNDETERMINED` | facts incomplete | full amount |

Stage 0 then:
- declines to chase `STATUTORY_WITHHOLDING` and `NO_SHORTFALL`, attaching the **full
  working** to the evidence record, not just the verdict;
- **restates** the chaseable amount on `PARTIAL_WITH_TDS` via a new
  `Stage0Result.recoverable_amount_paise`, which the orchestrator uses as
  `amount_at_risk_paise`. The restatement can only ever reduce.

### Rules that keep this honest

1. **Integer paise only.** Rates are basis points (integers); `expected = gross * bps // 10000`.
   No float touches a money value.
2. **Conservative on ambiguity.** An unrecognised section or an absent remittance figure
   yields `UNDETERMINED` and the opportunity stays **fully recoverable**. This module may
   never invent a withholding that suppresses a legitimate recovery.
3. **Derivation beats a contradicting flag.** The legacy `is_tds_withheld` passthrough is
   retained but fires **only** where the derivation reached no conclusion. A flag may fill a
   silence; it may never contradict the invoice's own numbers. Otherwise any caller could
   suppress any recovery by asserting a withholding the arithmetic does not support.
4. **Scope-gated.** The derivation runs only for `OVERDUE_B2B_INVOICE` or where a section is
   explicitly supplied, so a stray `amount_received_paise` on an unrelated stream cannot
   suppress it.
5. **s.206AA handled.** No PAN raises withholding to the higher of the section rate or 20% —
   the most common cause of a shortfall that looks like a large underpayment and is in fact
   compliant withholding.
6. **Rounding tolerance.** s.288B rounds to the nearest rupee and payers round independently
   at line and invoice level, so an exact-paise match is unachievable. One rupee of slack
   per invoice absorbs that without absorbing a real shortfall.

## Limitation — stated, not hidden

**The rate table is authored and approximate.** It uses commonly-cited resident-payee rates
to demonstrate the derivation. It has **not** been verified against the current Finance Act.
Rates change annually and vary by payee constitution, threshold, and lower-deduction
certificate.

Before any production use the table must be replaced by a finance-owned, versioned source
with an effective-from date per row. The table carries a `TDS_RATE_TABLE_VERSION` which is
written into every evidence record, so any decision can be traced to the vintage that
produced it.

This module derives a **recovery decision**, not a tax position. It does not compute a
liability, file anything, or replace a finance team's determination.

## Consequences

**Positive**
- The claim "this engine declines to chase revenue that was never chaseable" is now
  demonstrable on the invoice's own numbers, with the working in the audit trail.
- Money reporting is materially more honest: `Rs at risk` is the derived recoverable
  balance, so the engine never counts the exchequer's share as money it could have collected.
- Makes the D3 (Stage 0) ablation act on something structural rather than on a flag.

**Negative / accepted cost**
- Reported rupees recovered fall on the B2B stream, because a portion of what was previously
  counted was never collectable. That reduction is the correction, not a regression.
- The rate table is a maintenance liability with a real expiry date.

## Alternatives considered

- **Keep the flag, document it as a stub.** Rejected: it is the project's headline
  differentiator and a judge would reasonably ask where the intelligence is.
- **Chase the full shortfall and reconcile later.** Rejected: it makes a demand for money
  the customer was legally required to withhold, which is the exact harm this engine claims
  to prevent.
- **Call an external tax API.** Rejected under ADR-0007 (no external services on the
  decision path) and unnecessary — the arithmetic is a rate lookup and a subtraction.
