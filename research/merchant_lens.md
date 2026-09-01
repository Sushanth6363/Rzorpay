# merchant_lens.md — Three Merchants, and Where Razorpay Fails Them

Compiled 2026-08-25. Every prior phase reasoned **downward** from Razorpay's strategy. This one
reasons **upward** from the merchant, and **backwards** from failure.

It surfaced four problems the top-down research missed. One of them is the strongest single finding
in this project.

> **UPDATE 2026-08-25 — personas now grounded in official data.** The three merchants were originally
> invented. They have since been re-anchored to **Udyam registration data (Ministry of MSME)**, the
> **statutory MSME turnover thresholds** (Notification S.O. 1364(E), effective 1 Apr 2025) and
> **NPCI UPI ticket-size data**. See the new §0 below. The stories remain illustrative; the tier
> definitions and the N1 arithmetic are now built on published figures.

---

## §0 — The real distribution [B, official]

| Source | Figure |
|---|---|
| **Udyam portal, Ministry of MSME (June 2026)** | **4,71,55,579 registered MSMEs** across 36 states/UTs and 783 districts |
| Composition | **98.9% micro** · ~4.9 lakh small (1.04%) · **37,042 medium (0.079%)** |
| **Statutory turnover ceilings** (S.O. 1364(E), 1 Apr 2025) | Micro **≤₹10 cr** · Small **≤₹100 cr** · Medium **≤₹500 cr** (investment: ₹2.5 cr / ₹25 cr / ₹125 cr) |
| **NPCI UPI** | Avg ticket ~**₹1,300**; **P2M = 63% of volume**; **~86% of P2M transactions are under ₹500** |
| NPCI scale | 23.2bn transactions worth ₹29.9 trillion (May 2026) |

**Read together: 98.9% of India's formal enterprise base is micro, and the payments they accept are
overwhelmingly small-ticket — 86% of merchant-facing UPI transactions are under ₹500.**

### ⭐ Two independent routes converge on the same merchant

**Route A — from Razorpay's own economics.** Revenue per merchant ~₹3,150/yr ÷ take rate 0.253%
= **~₹12.45 lakh of annual TPV**, i.e. ~₹1.04 lakh/month.

**Route B — from NPCI ticket data.** At a ₹500 P2M ticket, ₹1.04 lakh/month = **~208 transactions
per month.**

Both routes, from unrelated sources, describe a merchant doing roughly **₹12 lakh a year and ~200
transactions a month.** That is the *average* Razorpay merchant — and by the 98.9%-micro
distribution, the *median* is smaller still.

---

## The distribution nobody mentions

Razorpay earns roughly **₹3,150 per merchant per year** across 12M+ merchants.

Work backwards from that. At a ~2% take on cards and 0% on UPI, ₹3,150 of annual revenue implies a
merchant processing on the order of **₹1.5–2 lakh a year** — a few thousand rupees a day.

**The typical Razorpay merchant is tiny.** The mid-market and enterprise accounts everyone designs
for are a thin slice of a very long tail. Hold that thought — it comes back at the end and it is
uncomfortable for my own recommendations.

---

# Merchant 1 — Anjali · "Poorly established"

Handmade candles, sells on Instagram and a Shopify store. **~150 orders/month, ~₹2.5 lakh GMV.**
70% cash on delivery. No GST registration yet. No accountant — she does everything at 11pm.

**Uses:** Payment Gateway, a payment link she pastes into DMs. That's it.

### Where Razorpay fails her

**🔴 The 1% chargeback threshold is statistically brutal at her scale.** *(See the new finding below
— this is the big one.)*

**🔴 A fund hold is an extinction event.** She has no working-capital buffer. Razorpay's published
bands — 2-5 days for KYC, 1-3 weeks for chargeback review, **30+ days** for fraud — are survivable
for a company with reserves. For Anjali, 30 days without settlements means she cannot buy wax.

**🔴 Her success looks like fraud.** One of the documented freeze triggers is a **~10x volume
spike**. A reel goes viral, orders jump from 150 to 1,500, and the system that protects the
ecosystem flags her at the exact moment she finally has momentum.

**🟠 RTO eats her margin entirely.** 70% COD at ~23% RTO means roughly 24 parcels a month coming
back, at ₹200-250 each — **₹5,000-6,000/month**, against a business doing ₹2.5 lakh. And RTO Shield
requires enabling COD Intelligence and **sharing delivery data back to Razorpay**, which needs a
courier integration she doesn't have.

**🟠 Every fix costs money she doesn't have.** Instant Settlements is a paid add-on that
**requires raising a support ticket** to activate. Optimizer is for merchants running multiple
gateways. The tools that would help her are gated behind spend she can't justify.

**🟠 She gets template support.** Razorpay replies to 94% of negative reviews with an identical
script. She has no account manager and never will — at ₹3,150/year, she can't fund one.

**🟢 What works:** onboarding is genuinely fast, payment links need no website, UPI is free.

### Backwards: what would actually help Anjali?

Not an AI agent. **An early warning that she is two disputes from a freeze**, and a way to prove
she's legitimate *before* the volume spike gets her flagged.

---

# Merchant 2 — Rohan · "Mid established"

D2C skincare, 4 years old. **~8,000 orders/month, ~₹1.2 crore GMV.** Runs Razorpay **and** a second
gateway for redundancy. A ₹400/month subscription box (~2,000 active mandates). Sells wholesale to
40 stockists on 30-day terms. **One finance person, Divya.**

**Uses:** Payment Gateway ×2, Magic Checkout, Subscriptions/UPI AutoPay, Invoices, RazorpayX for
payouts, an accountant on Tally.

### Where Razorpay fails him

**🔴 Reconciliation is Divya's whole month.** Two gateways, two settlement formats, neither matching
the other. Every line carries MDR, GST on that MDR, refund offsets and chargeback deductions, and
deductions arrive in a *different* cycle from the sale. **20-40 hours a month**, by Razorpay's own
estimate.

**🔴 Mandates fail and nobody tells him why.** ~2,000 mandates; at SBI-like execution rates a large
share fail monthly on insufficient funds. Subscription Recovery exists but is in early access and
retries on logic, not on when Divya's customers actually get paid.

**🔴 Nothing exists for his ₹18 lakh of stockist receivables.** Razorpay creates the invoice. It has
no product to collect it. His realised DSO drifts toward the national 73 days against 30-day terms.

**🟠 He's in the no-man's-land.** Too big for self-serve — his problems are genuinely complex now.
Too small for enterprise treatment — no CSM, no custom terms, no negotiated MDR.

**🟠 Agent Studio doesn't fit his shape.** Seven prebuilt agents, one configuration each. His
subscription box needs different retry behaviour from his one-off orders, and there's no policy layer
to express that.

**🟠 T+2 on cards vs T+1 on UPI** means two different cash-flow rhythms to plan against, for no
reason he can see.

### Backwards: what would help Rohan?

**Exactly the top of our list.** Reconciliation that resolves, mandate recovery that understands
timing, a collections tool for stockists. **Rohan is the merchant our five projects were designed
for**, though nobody said so out loud until now.

---

# Merchant 3 — Meridian Retail · "Highly established"

Omnichannel fashion. **~1.2M transactions/month, ~₹180 crore GMV.** Three PSPs deliberately —
pricing leverage and failover. SAP. A 12-person finance team, a payments PM, a risk analyst.
Negotiated MDR. A named account manager.

**Uses:** Payment Gateway, Optimizer, POS, Route, Instant Settlements, RazorpayX, custom APIs.

### Where Razorpay fails them

**🔴 Razorpay is one of three, and every tool assumes it's the only one.** Optimizer routes across
providers, but reconciliation, reporting and agents are Razorpay-centric. Meridian's actual question
— *"what is my blended success rate and true cost across all three PSPs?"* — has no owner.

**🔴 The agents have no governance layer.** Meridian cannot let a vendor's agent contact its
customers without approval workflows, tone control, brand rules, audit and role-based access. Agent
Studio ships agents; it doesn't ship the controls an enterprise needs to permit them.

**🔴 Dispute volume is industrial.** At 1.2M transactions and a 0.26% rate, that's **~3,100 disputes
a month**. Evidence lives in SAP, the WMS and the courier's system — none of which Razorpay can
reach. Dispute Responder can only answer with what Razorpay holds.

**🟠 They want raw data, not dashboards.** Every product Razorpay ships as a UI, Meridian wants as an
export into SAP. Settlement Insights sending a daily WhatsApp summary is, to them, noise.

**🟠 Vulcan is invisible and uncontrollable.** An 8-10% success-rate lift is claimed. Meridian cannot
verify it, segment it, A/B it, or turn parts of it off. For a team with its own payments PM, an
unauditable black box on the critical path is a governance problem, not a feature.

**🟢 What works:** negotiated pricing, an account manager, Optimizer's failover, POS.

### Backwards: what would help Meridian?

Not another agent. **A control plane** — policy, approval, audit and evaluation over agents, plus
cross-PSP truth. Notably, **the "propose, never assert" design in project #1 is exactly the shape an
enterprise wants.**

---

# The backwards view: which product fails whom?

| Razorpay product | Fails Anjali (micro) | Fails Rohan (mid) | Fails Meridian (large) |
|---|---|---|---|
| Payment Gateway | 🟢 works | 🟢 works | 🟢 works |
| **Freeze / risk process** | 🔴 **existential** — no buffer, 30+ day bands, spike = flag | 🟠 painful | 🟢 has an AM to call |
| **Single View Recon** | 🔴 an Optimizer feature — she has no access **[E]** | 🟠 helps, but only *views* | 🟠 wants an export, not a view |
| Instant Settlements | 🔴 paid + **support ticket to enable** | 🟠 cost | 🟢 has it |
| RTO Shield | 🔴 needs COD Intelligence + courier data | 🟠 partial coverage | 🟢 has the data |
| Agent Studio | 🔴 early access, not for her | 🟠 no policy control | 🔴 no governance layer |
| Subscription Recovery | 🟢 N/A | 🔴 retries on logic, not timing | 🟠 wants own policy |
| Vulcan | 🟢 invisible benefit | 🟢 invisible benefit | 🔴 unauditable black box |
| Support | 🔴 templated | 🟠 templated | 🟢 account manager |
| **Receivables/collections** | 🟢 N/A | 🔴 **nothing exists** | 🟠 uses a separate AR tool |
| Smart Collect | 🟠 needs RazorpayX | 🟢 works | 🟢 works |

**The pattern:** Razorpay's products are built for a merchant who is **big enough to have complexity
and small enough to accept defaults.** Rohan. Anjali is too small to reach the tools; Meridian is too
big to accept them as shipped.

---

# Four problems this lens found that the top-down research missed

### ⭐ N1 — The 1% chargeback threshold is scale-blind

Razorpay freezes above a **1%** chargeback ratio. That is a *ratio*, applied identically to a merchant
doing 150 transactions and one doing 1.2 million.

**Now grounded in the §0 figures rather than invented volumes.** Assuming a ₹500 P2M ticket and a
*true* dispute rate exactly at the global average of **0.26%** — i.e. a perfectly well-behaved
merchant — Poisson variance gives:

| Annual turnover | Txns/month | 2 disputes = | **P(breach 1% in a month)** | **P(breach in a year)** |
|---|---|---|---|---|
| **₹5 lakh** | 83 | 2.40% | **19.5%** | near-certain |
| **₹12.45 lakh ← the average Razorpay merchant** | **208** | 0.96% | **1.8%** | **19%** |
| ₹25 lakh | 417 | 0.48% | 0.5% | ~6% |
| ₹50 lakh | 833 | 0.24% | ~0% | ~0% |
| ₹3 crore | 5,000 | 0.04% | ~0% | ~0% |

**The average Razorpay merchant has roughly a 1-in-5 chance each year of tripping the freeze
trigger through statistical noise alone**, while behaving exactly like the global average. A
merchant at ₹5 lakh turnover is in that position most months.

And it gets worse with *larger* tickets, because the denominator shrinks: at a ₹1,300 ticket, the
same ₹12.45 lakh merchant does only ~80 transactions a month and faces a **92% annual** chance of a
noise-driven breach.

**Above roughly ₹25-50 lakh of annual turnover the problem disappears entirely.**

The same rule is a meaningful signal for a large merchant and **a coin-flip for a small one**. The
metric isn't wrong; applying it scale-blind is.

**This reframes project #4 completely.** It isn't "help merchants avoid risk controls" — it's
**"the control has a statistical blind spot at low volume, and here's a volume-aware exposure model."**
That framing is defensible, technically interesting, and sidesteps the compliance problem entirely,
because you're improving the signal rather than evading it. [E — my arithmetic on sourced thresholds]

### N2 — The reconciliation tool is gated behind the multi-gateway product

Single View Recon appears to be an **Optimizer** feature. Optimizer is for merchants running multiple
providers. So a merchant with two gateways who hasn't bought Optimizer gets **no consolidated view at
all** — and they are exactly the merchants with the worst reconciliation pain. **[E — needs
verification; inferred from Razorpay's own blog describing it as Optimizer's Single View Recon]**

### N3 — The mid-market has no service model

Rohan is too complex for self-serve and too small for an account manager. At ₹3,150 average revenue
per merchant, human support is unfundable — which is *precisely* why Razorpay is betting on agents.
**The mid-market gap is the strategic reason Agent Studio exists.** Useful framing for a pitch.

### N4 — Agent Studio ships agents but no governance

Meridian cannot deploy an agent that contacts its customers without approval workflows, tone control,
audit trails and role-based access. Razorpay ships the agents. **Nobody ships the control plane** —
and Razorpay has said third-party builders will be able to publish to the studio.

---

# What this does to the five recommendations

### The uncomfortable finding

| Project | Serves | Share of Razorpay's merchant base |
|---|---|---|
| #1 Reconciliation | Rohan, Meridian | small minority |
| #2 Recovery | Rohan | small minority |
| #3 Collections | Rohan | small minority |
| #4 Freeze monitor | **Anjali** | **the vast majority** |
| #5 Intent verifier | Meridian | tiny minority |

**Four of five serve the merchant tier that is a thin slice of the base.** Only #4 serves the typical
Razorpay merchant.

That doesn't invalidate them — mid-market merchants generate disproportionate revenue, and Razorpay's
own strategy is to raise revenue *per merchant*, which means selling deeper to Rohan. But it is worth
knowing that **"most Razorpay merchants" and "the merchants our projects help" are almost disjoint
sets**, and I hadn't noticed until reasoning upward.

### Changes I'd make

**#4 is rehabilitated — with a new framing.** N1 turns it from a compliance-risk idea into a
statistical-fairness one: *volume-aware chargeback exposure, because a ratio threshold behaves
differently at 150 transactions than at 1.2 million.* That is a better project than the one I
described in Phase 14, and it serves the largest merchant tier. **It still has the Phase 9 data
problem** — you can't create freezes in test mode — but the *monitor* only needs the merchant's own
transactions, which you can generate.

**#1 gets a sharper target.** Build for Rohan explicitly — two gateways, one finance person,
month-end. Not an abstract "merchant."

**#5 gets a better angle for large merchants:** the governance layer (N4) is more valuable to
Meridian than another agent.

---

## Honest limits

The personas are constructed. Their transaction volumes, and therefore N1's arithmetic, are
**illustrative** — I have no data on Razorpay's actual merchant size distribution beyond the ₹3,150
average, which is itself derived rather than published.

The N1 finding holds directionally for **any** low-volume merchant regardless of the exact numbers —
the mathematics of small denominators is not in doubt. But if you use it, present it as *"a merchant
doing ~150 transactions a month"*, not as a claim about Razorpay's real portfolio.
