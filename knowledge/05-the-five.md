# 5. The Five — told as stories

Five projects survived. Here's each one as a story about a person with a problem.

---

## #1 — The Reconciliation Exception Resolver ⭐ *our recommendation*

**Track 4 · AI Finance Controller**

### The story

Priya does the books for an online clothing brand. They take payments through Razorpay and one other
provider, because using two means fewer failed checkouts.

Every month she downloads settlement files from both. Each line has a sale amount, the provider's
fee, GST charged on that fee, any refunds deducted, any chargebacks deducted, the net amount paid,
and a bank reference number.

Her job: match every line to the orders behind it.

Most match in minutes. Then there's the tail. A ₹4,300 deduction with no obvious source — it turns
out to be a chargeback from a sale *three settlement cycles ago*, for a different amount, because a
partial refund happened in between. Twelve more like it. She spends two days on them.

**Razorpay says merchants spend 20-40 hours a month on this.**

### Why nobody has fixed it

Razorpay actually has **three** tools that touch reconciliation, and it's worth knowing all three
because a judge will:

- **Single View Recon** (June 2022) — puts settlement data on one screen. **Shows** mismatches,
  doesn't **resolve** them.
- **Smart Collect** — gives each of your customers a unique bank identifier, so when money arrives
  you know who sent it. That's *preventing* confusion on money coming in — not fixing a broken
  settlement line.
- **Source to Pay** — matches supplier invoices against purchase orders for money going *out*.
  Opposite direction entirely.

None of them resolves Priya's problem: a payout that doesn't match the orders behind it once fees,
GST on those fees, refunds and old chargebacks are subtracted.

Four years, no resolver. And there's a genuinely good reason.

> If Razorpay says *"these two lines match"*, that claim goes into Priya's audited financial
> statements. If it's wrong, Razorpay has corrupted a legal document.

Showing data is safe. Asserting a match is not. That's why they built a viewer.

### What you build

An agent that does the easy matching in plain code, then reasons about the leftovers — and **never
claims certainty**. It writes *proposals*, each with a confidence score and the evidence behind it,
and for anything it can't crack it produces an exception entry saying which candidates it weighed
and what was missing.

**You sidestep the exact liability that stopped Razorpay** — because you propose and a human decides.

### The demo that wins

Terminal, live, 500 records. Counter running: matched, proposed, abstained.

Then the move most people won't make: **open the exceptions file and walk through one it couldn't
solve.** Show the two candidates it weighed and the missing bank reference that made it stop.

Track 4's bar literally asks for "the exceptions it could not resolve." You'd be answering it directly.

### Why it's our pick

Best data of anything we found — Razorpay publishes the schema *and* the list of failure modes, and
Track 4's instructions explicitly say to use synthetic data. Least crowded track. Simplest version
builds in 4-5 days, leaving real time for the writeup and video.

And crucially: its claim to be different rests on *global tools not handling Indian settlement lines*
— which stays true no matter what Razorpay shipped last month.

### What could go wrong

Matching is easy; **being right is hard**. You could hit 95% matching with 70% proposal accuracy and
have built something no accountant would trust. Measure accuracy, not coverage.

**Honest objection:** this saves cost, it doesn't make money. A company called Ledge does it better
globally with 150+ integrations, and Razorpay has three adjacent tools. **Why it still wins:** every
objection is about a *different* reconciliation problem — money in, money out, or just displaying it.
Nobody resolves the Indian settlement line itself.

---

## #2 — The Recovery Sequencer That Knows When To Stop

**Track 3 · AI Revenue Recovery**

### The story

Arjun runs a subscription fitness app. Every month, mandates fire and a large share simply fail —
the money isn't in the account at that moment. At SBI, roughly 70% fail.

So he retries. Fixed schedule: try again in 24 hours, then 48.

What he doesn't see: some customers are getting hit repeatedly, getting annoyed, and calling their
bank to dispute the charge. **"Cancelled recurring" is 8.5% of all chargebacks.**

His chargeback rate creeps up. It crosses 1%. **Razorpay freezes his settlements.**

His recovery effort caused a worse problem than the one it solved.

### What you build

An agent that classifies *why* each payment failed using Razorpay's published error codes, learns
*when* each customer's money is actually available, chooses a response — and then does the thing
nobody does:

> **It watches the merchant's chargeback headroom and stops before pushing them into a freeze.**

That's the centrepiece. When the bar asks "what are your stopping rules?", you answer with
**Razorpay's own published 1% threshold** instead of an arbitrary retry limit.

### The demo

Two runs side by side, same random seed: fixed retries vs timing-aware. Then the moment — **the agent
halts mid-campaign** because projected chargeback rate hit 0.9%, with the trace showing the veto.

Close with honesty: *"Gross, we recovered ₹X. But the holdout group says ₹Y of that would have
arrived on its own. Our real number is the difference."*

Almost nobody measures that.

### What could go wrong

**Its clever bit already exists commercially.** Revaly ships decline-code retry timing today. And
this is the most crowded space in the buildathon — 88 competing repos.

Simulating customer balances over time is a project inside the project, and it's where 11-day
schedules break.

**Why it still survives:** it's the highest-priority problem we found, and the stopping rule is the
single most defensible design decision in this research.

---

## #3 — The Invoice Chaser That Knows The Law

**Track 3 · AI Revenue Recovery**

### The story

Meera supplies components to three factories. Her invoices say "pay within 30 days." She gets paid
in 73. She has ₹40 lakh outstanding and no time to chase it.

Nationally: **₹20,979 crore of unpaid claims sit unresolved** on the government's MSME portal, 16%
of them open more than a year. In August 2026 Parliament passed new laws forcing time-bound
resolution — proof the old rules failed.

### What you build

An agent that ranks who to chase, drafts compliant reminders **in Meera's name**, records when
someone promises to pay, notices when they break it — and escalates into **India's statutory
machinery**: the 45-day rule, the MSEFC, a Samadhaan filing.

### Why the legal part is the whole idea

HighRadius already runs 15 AI collections agents and tracks promise-to-pay. **What no global tool
does is escalate into Indian statutory process.**

And Razorpay can't build this themselves — debt collection is regulated conduct with harassment
rules. But a tool that helps *the merchant* collect, in the merchant's own name, avoids all of it.

### The demo

The DSO curve dropping. Then the broken promise: agent recorded "will pay on the 5th", detects the
miss on the 6th, escalates one step — **and stops**, handing to statutory process rather than
hounding. Show the guardrails: quiet hours, contact caps, merchant's name on everything.

### What could go wrong

If it looks like harassment automation, it fails on judgement not engineering. And this has the
weakest signal that Razorpay cares — they mention it, they've built nothing.

**But:** it's the emptiest space we found — roughly 3-4 competing repos.

---

## #4 — The Freeze Early-Warning System

**Track: Open**

### The story

Kabir's payments stop. No warning. Support says documents are needed but won't say why. Two weeks
pass. Payroll is due.

Razorpay publishes the triggers: chargebacks above 1%, sudden volume spikes, expired KYC documents,
compliance flags. They publish how long it takes: 2-5 days, 1-3 weeks, **30+ days**. One documented
case ran 120 days.

They even recommend merchants watch their own chargeback rate at 0.5%.

**And they ship no alert.**

### The asymmetry that makes this possible

Razorpay **cannot** warn Kabir. Anti-money-laundering rules often forbid telling someone they're
under review, and warning a genuinely fraudulent merchant would let them cash out first.

**Kabir is under no such restriction.** He can watch his own numbers all he likes.

So you build the monitor **on his side of the fence**, using only his own transaction data,
targeting Razorpay's own published 0.5% recommendation.

### The demo

Chargeback rate climbing across a simulated quarter. The monitor flags at 0.5%, projects when it'll
cross 1%, and models what a 30-day freeze does to payroll. Then the counterfactual: with
intervention, the curve turns before the trigger.

### What could go wrong

**A judge might read it as helping merchants dodge Razorpay's risk controls** — and we've since found
this is more than a perception issue. Razorpay's merchant contract explicitly says risk management is
*their* job (clause 2.23) and that they're legally required to monitor merchants (2.31).

Nothing stops a merchant watching their own numbers — Razorpay literally recommends it. But the
difference between these two framings decides everything:

- ✅ *"Your dispute rate is climbing — here's the cause, fix it"*
- 🔴 *"You're near 1% — here's how to stay under"*

One reduces real risk. The other hides it. Say which one you're building, out loud, in the pitch.
**After this check, this became the riskiest of the five, not the boldest.**

And it's fragile — if Razorpay's product list has grown since March, its novelty claim weakens.

**Note the distinction:** *warning before a freeze* is buildable, because the numbers come from the
merchant. *Helping after a freeze* is not, because you can't create a freeze to test against and
can never see if it worked. Same problem, opposite feasibility.

---

## #5 — The AI Shopper's Chaperone

**Track 1 · AI Growth & Agentic Commerce**

### The story

You tell an AI assistant: *"Order my usual coffee beans, the dark roast, 1kg."*

It comes back with 1kg of beans at the right price. Correct amount. Correct merchant. Payment
approved.

**Wrong roast.**

Every check passed, because consent covers *a merchant and an amount* — not *what you meant*.

This is not hypothetical. OpenAI's shopping checkout publicly stumbled on exactly this class of
problem with Etsy, Walmart and Shopify.

### What you build

A gate that sits between the AI agent and the payment. It reads the original instruction, compares
it to what's actually in the cart, and **blocks the payment when they diverge** — showing the human
the difference and asking.

### Why Razorpay cares

They're live on agentic payments with NPCI, Claude, and Zomato/Swiggy/Zepto. And their MD said
publicly:

> *"The system has to allow for a certain level of mistakes so that you can learn from them and
> correct them."*

Track 1's bar asks for *"one failure handled gracefully."* This project is entirely about the
failure case.

### The demo

The agent shops correctly — you approve. Then the adversarial run: subtly wrong item, right price.
**The gate blocks payment, shows the diff, asks.** Close on the audit chain: instruction → consent →
cart → decision → payment.

Best demo of the five, by some distance.

### What could go wrong

**~100 competing repos** — the most crowded track. It's honestly a verification checkpoint rather
than a fully autonomous agent, and claiming otherwise would be the buzzword-inflation the bars
punish. Latency matters: a gate that takes 5 seconds ruins the experience.

---

## Side by side

| | Safest | Highest impact | Emptiest | Most novel | Best demo |
|---|---|---|---|---|---|
| | **#1 Recon** | **#2 Recovery** | **#3 Invoices** | **#4 Freeze** | **#5 Chaperone** |
| Track | 4 | 3 | 3 | Open | 1 |
| Competing repos | ~24 | ~88 | **~3-4** | very few | ~100 |
| Build difficulty | Moderate | **Hardest** | Moderate | Moderate | Moderate |
| Data | **Best** | Good | Good | OK | Good |
| Risk | Accuracy | Schedule + crowding | Tone | Perception | Crowding |

---

**Next:** [Which one is yours? →](06-choose-yours.md)
