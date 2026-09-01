# 7. Glossary

Every term used in this research, explained as if you've never seen it.

---

## The payment journey

**Payment gateway** — The plumbing between a shopper and a shop. Razorpay is one.

**Merchant** — The shop. Razorpay's customer. When you read "merchant", picture a small business
owner, not a corporation.

**Payment aggregator (PA)** — A company licensed by RBI to collect money on behalf of many
merchants. Razorpay holds this licence. It's the licence that makes them careful about everything.

**Settlement** — Payday for the shop. Razorpay collects money from shoppers, holds it briefly, then
pays the shop. Usually 2 working days.

**T+2** — Settlement two working days after the sale. "T" is the transaction day.

**MDR (Merchant Discount Rate)** — Razorpay's cut. Around 2% on cards. **Zero on UPI**, by law — a
huge deal for their business.

**UTR** — The bank's reference number for a transfer. The thing you match against to prove money
actually arrived. When it's missing, the trail dies.

**TPV (Total Payment Volume)** — Money flowing through, roughly $180 billion a year for Razorpay.
Not their revenue — the river, not the toll.

---

## Payment methods

**UPI** — India's instant bank-to-bank payment system. Free to use, which is why it dominates and
why Razorpay earns nothing on it.

**NPCI** — The organisation that runs UPI. Sets the rules Razorpay must follow.

**RBI** — India's central bank and the regulator. When RBI issues a rule, everyone re-implements.

**COD (Cash on Delivery)** — Pay the delivery person in cash. Huge in India because of trust
deficit. Also the source of the RTO problem.

**Mandate / UPI AutoPay / e-mandate / e-NACH** — A standing instruction. Approve once, money gets
pulled automatically. Like a gym direct debit. **Setting them up works; executing them often
doesn't.**

**AFA (Additional Factor of Authentication)** — The extra step: OTP, PIN, biometric. RBI rules say
when it's required and when it can be skipped.

**Tokenisation** — Replacing a real card number with a stand-in, so shops never store the real one.

---

## Things that go wrong

**Failed payment** — Didn't go through. Roughly 4-8% of UPI attempts.

**Technical decline (TD)** — The system broke: bank server down, timeout. Now under 1% nationally.

**Business decline (BD)** — Nothing broke; the payment was correctly refused. No money, wrong PIN,
limit exceeded.

**Decline codes / error codes** — Standard labels for why a payment failed. Razorpay publishes
theirs: `insufficient_funds`, `payment_timed_out`, `bank_technical_error` and so on. **These matter
a lot in this research** — they're a published, machine-readable vocabulary you can build on.

**`source` field** — Razorpay's label for *who* caused a failure: the bank, the gateway, the
customer, or the card issuer. Precisely the distinction a diagnosis agent needs.

**Chargeback / dispute** — A customer tells their bank "I didn't authorise this." The bank claws the
money back. The shop must prove otherwise, on a deadline, with evidence.

**Chargeback ratio** — Disputes as a percentage of transactions. **Razorpay freezes merchants above
1%** — stricter than Visa's own 1.5% threshold.

**Reason code** — The specific dispute category. **Visa 13.2 "cancelled recurring" = 8.5% of all
chargebacks**, which is how failed subscriptions become disputes.

**RTO (Return To Origin)** — A COD parcel that comes back. Roughly 23% of COD orders. Costs the
shop about ₹200-250 each with no revenue.

**Involuntary churn** — A subscriber lost because payment failed, not because they quit. 20-40% of
all subscription churn.

**Self-cure** — A failed payment that succeeds later with no help. **Nobody publishes how often this
happens** — which means any recovery tool without a control group is taking credit for it.

---

## Money and books

**Reconciliation** — Matching what you were paid against what you sold. Like balancing a bank
statement, but with 11 columns and three parties. Razorpay says merchants spend 20-40 hours a month
on it.

**Exception** — A line that won't match. The whole job is the exceptions; the rest is easy.

**Late authorisation** — A payment whose final status arrives hours after the transaction, so books
won't balance until you re-check.

**DSO (Days Sales Outstanding)** — Average days to get paid. Indian SMEs: 73 days against 30-day
terms.

**Receivables** — Money owed to you but not yet received.

**MSME Samadhaan** — Government portal where small businesses report late payment. Holds ₹55,244
crore of claims, ₹20,979 crore unresolved.

**Escrow** — A ring-fenced account holding money in transit. RBI controls what it can be used for —
and **explicitly bans COD from it**, which is why COD losses land entirely on the merchant.

**GST on MDR** — Tax charged on Razorpay's fee, itemised separately in the settlement line. A small
detail that makes Indian reconciliation different from anywhere else.

**TDS** — Tax deducted at source. Another Indian-specific line item.

---

## AI terms

**Agent** — Software that decides what to do next, uses tools, acts, and handles what goes wrong.
Not just a model that predicts.

**LLM** — Large language model. Claude, GPT and similar.

**MCP (Model Context Protocol)** — A standard way to give an AI model tools. **Razorpay ships an
official MCP server with 45 tools** — so an AI agent can call Razorpay's APIs directly. Test keys
work.

**Structured output** — Forcing the model to return a fixed shape (JSON) rather than prose. Essential
for anything you'll measure.

**Held-out test set** — Data the system never saw while being built, used to measure honestly.
Track 2's bar asks for one by name.

**Holdout / control group** — A slice you deliberately *don't* treat, so you can tell what your
system actually caused versus what would have happened anyway.

**Precision and recall** — Of the things you flagged, how many were right (precision); of the things
you should have flagged, how many did you catch (recall). Usually a trade-off.

**False positive** — A false alarm. In payments these are expensive: flag a good merchant and you
freeze their money.

**Abstain** — The system says "I don't know" instead of guessing. **In this research, abstention is
a feature, not a failure.**

**Trace** — A replayable log of what an agent saw, decided and did. Every buildathon bar asks for
an audit trail; this is it.

**Idempotency** — Making sure that doing the same operation twice has the same effect as doing it
once. In payments, this is what stops a retry becoming a double charge.

**AI washing** — Calling something an "AI agent" when a simple rule would do. The bars punish it.

---

## Razorpay's products

**Agent Studio** — Their AI agent platform, launched March 2026, built on Claude. Seven prebuilt
agents. Still early access.

**Vulcan** — Their own payments AI model, launched 18 August 2026. Trained on ~3 trillion data
points. Handles routing, fraud, conversion.

**Optimizer** — Routes payments across 100+ providers to improve success rates.

**Magic Checkout** — Their fast checkout with pre-filled details.

**Single View Recon** — Their reconciliation tool from June 2022. **Shows mismatches; doesn't
resolve them.** That gap is project #1.

**RazorpayX** — Business banking: current accounts, payouts, payroll.

**Instant Settlements** — Get paid faster than T+2, for a fee.

**UPI Reserve Pay** — NPCI's mechanism behind Razorpay's AI shopping pilot. One-time consent with a
spending cap per merchant, revocable instantly. Worth copying as a safety model.

---

## Test mode facts worth memorising

- `success@razorpay` and `failure@razorpay` — test UPI IDs that force each outcome
- OTP of 4-10 digits succeeds; under 4 digits fails
- **Disputes cannot be created in test mode** — kills chargeback projects
- **UPI cancellation returns SUCCESS in test mode** — passes in test, breaks in production
- Card tokens last only 3 days — constrains subscription demos
