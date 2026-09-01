# 2. Razorpay in Plain English

## What the company actually is

When you buy something online in India and tap "Pay", your money doesn't go straight to the shop.
It goes through plumbing. Razorpay is that plumbing.

They sit between **you**, **your bank**, and **the shop**, and they make the payment happen. They
handle around **4 billion payments a year** for **12 million-plus businesses**.

Think of a toll booth on a very busy road. Every car passing through pays a tiny fee. Razorpay's
entire business is being that toll booth — and then selling the shopkeeper extra services on top:
a business bank account, payroll, loans, a card machine.

---

## Follow one payment, end to end

This matters because **every problem in this research lives somewhere on this journey.**

```
1. You're on a shop's website. You add a shirt to your cart.
2. You tap Pay. Razorpay's checkout appears.
3. You choose UPI. Your bank app opens. You enter your PIN.
4. Your bank moves the money.
5. Razorpay receives it and holds it briefly.
6. Two working days later, Razorpay pays the shop — minus its fee.
7. The shop's accountant tries to match that payout to the orders it came from.
```

Simple enough. Now here's where it goes wrong.

---

## The six places money leaks

### Leak 1 — The payment just fails

Roughly **4 to 8 out of every 100 UPI payment attempts fail.**

You'd assume it's Razorpay's technology breaking. It mostly isn't — that kind of failure has fallen
from about 8-10% in 2016 to under 1% today. The failures now are things like:

- the bank's server times out (the biggest single cause, 35-45% of failures)
- you type your PIN wrong (20-30%)
- there isn't enough money in your account (15-25%)

The shop just sees a lost sale.

### Leak 2 — The standing instruction fails

This is the big one, and it's worth understanding properly.

A **mandate** (Razorpay calls it UPI AutoPay) is a standing instruction — like a gym direct debit.
You approve it once, and money gets pulled automatically each month for your Netflix, your loan
EMI, your SIP.

Setting them up works fine. **Executing them doesn't.**

At **SBI, India's largest bank, only about 30% of these automatic debits succeed. Around 70% fail.**
Overwhelmingly because the money isn't in the account at the exact moment the debit fires.

And this is growing fast: mandate volume at the top ten banks went from roughly 577 million a month
to **around 1.6 billion a month in a year.**

Nobody chose to cancel. The subscription just quietly dies. The industry calls it *involuntary
churn*, and it's 20-40% of all subscription churn.

### Leak 3 — The customer disputes the charge

A **chargeback** is when a customer tells their bank "I didn't authorise this" and the bank claws
the money back from the shop. The shop has to prove otherwise, with evidence, on a deadline.

Two facts that matter enormously later:

- **Visa reason code 13.2 — "cancelled recurring" — is 8.5% of all chargebacks.** So failed
  subscriptions *cause* disputes. Leak 2 feeds Leak 3.
- **Razorpay freezes a merchant's funds if their chargeback rate crosses 1%.** That's *stricter*
  than Visa's own threshold of 1.5%.

### Leak 4 — The parcel comes back

**RTO** — Return To Origin. Someone orders cash-on-delivery, then refuses the package or isn't
home. The parcel travels out and back and the shop pays for both journeys.

About **23% of COD orders in India come back.** Each one costs the shop roughly **₹200-250** on a
₹1,000 order, with zero revenue against it.

The interesting bit: **60-70% of RTOs come from low buying intent** — people who never really meant
to buy — not from delivery problems. So the fix is at checkout, not in the warehouse.

### Leak 5 — The books don't match

The shop's accountant gets a settlement report. Each line carries: the sale amount, Razorpay's fee
(MDR), **GST charged on that fee**, any refunds deducted, any chargebacks deducted, the net amount
paid, and a bank reference number (UTR).

Their job is to match every line to the orders it came from. Mostly this is easy. But a stubborn
few percent won't match — and that tail eats the month.

**Razorpay says merchants spend 20 to 40 working hours a month on this.** Their own words describe
teams who *"download and manually reconcile payments and settlements"* by hand.

### Leak 6 — Nobody pays their invoices

For businesses selling to other businesses: **Indian SMEs invoice on 0-30 day terms and get paid in
73 days on average.** 82.6% of invoices say "pay within 30 days." Reality is 73.

The government runs a complaints portal for this. It's sitting on **₹55,244 crore of claims, with
₹20,979 crore still unresolved** — and 16% of cases have been open more than a year. In August 2026
Parliament passed new laws to force faster resolution, which tells you the old rules weren't working.

---

## What Razorpay has already built

This is the part most applicants skip, and it's where most project ideas die.

**Agent Studio** (launched March 2026, built on Anthropic's Claude Agent SDK) ships seven ready-made
AI agents:

| Agent | What it does |
|---|---|
| Dispute Responder | Auto-answers chargebacks with evidence |
| Subscription Recovery | Retries failed subscription payments |
| Abandoned Cart Conversion | Chases people who didn't finish checkout |
| RTO Shield | Flags risky COD orders before dispatch |
| RTO Insights | Analyses return patterns |
| Settlement Insights | Daily settlement summary on WhatsApp |
| Cashflow Forecaster | Predicts cash 3-7 days ahead |

**Vulcan** (launched 18 August 2026 — six days before we started) is their own AI model for
payments, trained on roughly 3 trillion data points from those 4 billion yearly payments. It handles
routing, fraud detection and checkout conversion.

**Agentic payments** are live: AI shopping via Claude with Zomato, Swiggy and Zepto, done with NPCI.

**And there's more than we first counted.** Razorpay's site lists around **40 products**. Ones worth
knowing about because they're close to our ideas: **Smart Collect** (auto-matches incoming bank
transfers by giving each customer a unique identifier), **Source to Pay** (reads supplier invoices
with OCR, does 3-way matching, auto-deducts TDS, checks GST credits), and **Invoices** (GST billing).
We missed these on the first pass and had to correct two conclusions — see
`research/razorpay-product-audit.md`.

Now compare that list of seven agents against the examples on the buildathon page. Chargeback
responder. Return-risk scorer. Failed-subscription recovery. Checkout drop-off recovery. Settlement
Q&A. Cash forecaster.

**They're the same list.**

Which leads to the single most important rule in this whole project:

> **The "example directions" on the buildathon page are largely a description of products Razorpay
> already sells.** Build one naively and you're demoing a worse version of their own product to the
> team that built it.

---

## And one thing they can't build

Here's the asymmetry that makes several of our ideas possible.

Razorpay is a regulated company. That blocks them from doing things that would otherwise be obvious:

- They **can't tell you why they froze your account** — anti-money-laundering rules often forbid
  warning someone they're under review.
- They **can't chase your customers for unpaid invoices** — debt collection is regulated conduct
  with harassment rules.
- They **can't say "these accounts reconcile"** — that would put their claim inside your audited
  books, and they'd own being wrong.

**You have none of these constraints.** You don't have a licence to protect or 12 million customers
to be consistent with.

That's not a loophole. It's the actual shape of the opportunity — and it's why the best ideas in
this research are all the *merchant's half* of a problem whose *Razorpay half* is genuinely,
defensibly closed.

---

**Next:** [How we investigated — and what we got wrong →](03-how-we-investigated.md)
