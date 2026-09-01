# 4. The Funnel — how 20 problems became 5

Here's the whole narrowing, stage by stage, with the reason each idea died.

```
   20 real business problems found
        ↓  (is it big, current, and actually Razorpay's?)
   16 mapped to a buildathon track
        ↓  (does Razorpay already sell this?)
   10 still genuinely unsolved
        ↓  (does this really need an AI agent?)
    6 genuinely agentic
        ↓  (can we get the data in 11 days?)
    5 with obtainable data
        ↓  (can one student build it?)
    5 worth building
```

---

## Stage 1 — Find the real problems

We looked for problems with **evidence**, not problems that sounded plausible. Each one needed a
number attached, a Razorpay source showing they care, and an independent source confirming it's real.

That produced 20. The strongest were mandate failures, payment failures, reconciliation, fund
freezes, and B2B receivables.

Three were dropped immediately as not-real-problems: RBI's bank fraud statistics (they measure
large-value loan fraud, not payments — using them would have been badly wrong), a stale revenue
figure two years out of date, and a claim that Razorpay is unprofitable that turned out to depend
entirely on which year you cite.

---

## Stage 2 — Which are worth caring about?

We scored all 20 on ten dimensions — money at stake, how many merchants, how much Razorpay is
investing, how well it suits AI, and so on.

Two came out top: **mandate failures** and **payment success rates**.

But we also scored something separate: **how much room is left?** And that produced the first
genuinely surprising result.

> **Payment success rate is Razorpay's #1 problem and one of the *worst* things you could build.**

They have a routing product using 150+ parameters over 600 million data points, *and* a foundation
model trained on 3 trillion data points. Building a payment success optimiser means competing with
that using public data.

**High priority and good project are different questions.** That distinction shaped everything after.

---

## Stage 3 — Which track does each belong to?

Mostly straightforward. But we cut five "forced" mappings — ideas we could only fit into a track by
stretching the words.

The clearest: we tried putting Razorpay's fee-margin problem into Track 1, "grow the merchant's
revenue." But the revenue at stake there is **Razorpay's**, not the merchant's. Different problem
wearing a similar word.

Then we checked the *reverse* direction, and found something worth knowing:

> **Six of the 19 example directions on the buildathon page have no evidenced problem behind them.**

Upsell agent, campaign orchestrator, conversational checkout, Hinglish voice recovery — two full
research passes found no citable problem for any of them. Conversational checkout is worse than
unevidenced: Razorpay has already piloted it with Vodafone.

They look inviting because they're on the official page. You'd be inventing the problem *and* its
size, against a bar demanding measured results.

---

## Stage 4 — Which problems feed into each other?

We stopped treating problems as separate and drew the connections — but only kept an edge if it
passed four tests: is there a real cause-and-effect, do they share data, do they occur in the same
workflow, and does fixing one improve the other?

Seven "connections" were removed as fake. Fee margins and reconciliation both contain the word
"revenue" — that's a shared word, not a connection.

Two real chains changed our thinking.

**Chain one: four problems are secretly one problem.** Failed mandates, failed payments, failed
refunds, unpaid invoices — all four are *"money that was supposed to move and didn't."* All four need
the same machinery: work out why, pick a response, act within limits, check it worked. They even
share the same published error codes.

**They're not four projects. They're one engine pointed at four different ledgers.**

**Chain two: a recovery agent can freeze its own merchant.** Failed subscriptions get retried →
retries annoy customers → customers dispute the charges (remember, "cancelled recurring" is 8.5% of
all chargebacks) → the chargeback rate crosses 1% → **Razorpay freezes the merchant's funds.**

Every link there is documented, not guessed. Which means an AI agent doing its job well could
trigger the worst outcome in the entire system.

That gave us the best answer to a question the bars explicitly ask — *what are your stopping rules?*
Not "stop after 3 retries." **Stop before you freeze your own merchant.**

---

## Stage 5 — Group them into clusters

Six clusters. The one that mattered was the recognition that reconciliation is held together by a
**physical object**: Razorpay's settlement report. Chargebacks and refunds aren't merely *related*
to reconciliation — they're literally columns inside it.

---

## Stage 6 — What's genuinely unsolved? (the big cull)

For every remaining idea we asked: *does Razorpay already sell this?*

**Nine ideas died here** — including nine of Razorpay's own example directions:

| Killed | Because |
|---|---|
| Generic fraud detection | Vulcan, trained on 3 trillion data points. Unwinnable with public data |
| Chargeback auto-response | Dispute Responder already ships |
| RTO / return-risk scoring | *Three* products: RTO Shield, RTO Insights, Vulcan RTO Intelligence |
| Abandoned cart recovery | Two partner-built agents already ship |
| Conversational / voice checkout | Already piloted with real partners |
| Payment routing | Optimizer plus Vulcan |
| Settlement summaries | Settlement Insights ships a daily WhatsApp digest |
| Cash-flow forecasting | Cashflow Forecaster ships |
| Merchant onboarding | Agentic Onboarding ships |

We also separated a category people conflate: **things nobody has done because nobody legitimately
can.** Sharing a customer blacklist across merchants breaks privacy law. Warning a merchant before
freezing them defeats the purpose of the freeze. These look like open gaps. They're traps.

---

## Stage 7 — Does this actually need an *agent*?

This is where we had to downgrade our own favourites.

Three of our top ten weren't agent problems at all:

- Measuring what would have recovered anyway — that's **statistics**
- Pricing the cost of a false alarm — that's **cost modelling**
- Balancing returns against conversion — that's **optimisation**

They're valuable — they're the *measurement layer* that makes an agent's claims believable — but
calling them agents would have been exactly the buzzword-inflation the bars punish.

The test we settled on: **if "I don't know — here's what I checked and what a human should look at"
is a legitimate output, it's an agent problem.** A classifier can't abstain into a document pack.

---

## Stage 8 — Can we get the data? (the second big cull)

The single most important technical fact we found:

> **You cannot create a dispute in Razorpay's test environment.** Disputes are raised by banks and
> card networks, not merchants. There is no test API for it.

That kills chargeback projects. And six competitor repos are building exactly that right now — they
haven't hit the wall yet.

This stage also killed **our own highest-novelty idea**. The freeze navigator — helping merchants
whose funds are frozen — had the best novelty score of anything we found and almost no competition.
And you can't create a freeze in test mode, there's no API, and you can never see whether it worked.
Simulating the event, the trigger *and* the outcome is three layers of invention.

Meanwhile reconciliation scored highest, because Razorpay **publishes the settlement schema and the
list of things that go wrong with it** — so synthetic data isn't faking anything, it's rebuilding a
documented structure. And Track 4's own instructions say to use synthetic data.

---

## Stage 9 — Can one student build it in 11 days?

About **40% of the work is identical whichever you pick** — a data generator, an evaluation harness,
a trace log, a limits layer. Roughly three days of shared foundation.

One casualty: the recovery agent's *ambitious* version. Simulating customer balances over time,
plus two agents negotiating, doesn't fit. Its simpler version does, and is strong.

---

## Stage 10 — Who else already does this?

The sobering stage. **None of the five finalists is a new idea.** All five have funded companies
selling them — Ledge for reconciliation, Butter and Revaly for recovery, HighRadius for collections.

But two different things were being confused:

- **Market competition** — does a company sell this? (affects how you pitch)
- **Buildathon competition** — are other applicants building it? (affects whether you're noticed)

Reconciliation and collections are **crowded commercially but nearly empty in the applicant pool**.
Recovery and agentic commerce are crowded in both.

And the differentiator survived: every one of those companies is built for US and European payment
rails. **None of them handles an Indian settlement line** — with its MDR, GST charged on that MDR,
TDS deduction and UTR reference. That's not a temporary gap; it's structural.

---

## What came out

Five projects. Two are robust under every assumption we tested. Two depend on that five-month-old
product list being accurate. One is the best demo but the most crowded track.

**Next:** [The five, told as stories →](05-the-five.md)
