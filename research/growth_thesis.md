# growth_thesis.md — Where Razorpay Could Enter to Make Weak Businesses *Profitable*

Compiled 2026-08-25, in response to a direct question: *had I looked for ways Razorpay could help
weak businesses **gain profits**, not merely lose less?*

## The honest answer: no, and it was a systematic bias

Of the nine ideas in [micro_merchant_thesis.md](micro_merchant_thesis.md) §6, **seven reduce harm** —
freeze risk, RTO loss, KYC lapses, cash-flow gaps. Only one or two touch revenue.

Every phase of this research asked *"where does the merchant lose money?"* and never
*"where could the merchant make more?"* That bias also caused me to under-rate **Track 1 — which is
literally titled "Grow the merchant's revenue."** I dismissed it as crowded and largely solved,
which was true of *agentic commerce as a technology* and false of *merchant growth as a problem*.

This file corrects that.

---

## 1. The finding: paid growth is now structurally unprofitable at micro scale

### The inputs [B/C]

| Figure | Value | Source |
|---|---|---|
| Average P2M ticket | **~₹500** (86% of P2M transactions are under ₹500) | NPCI |
| Meta CAC, Indian D2C | **₹380 (2025) → ₹502 (2026), +32% in one year** | industry reporting |
| Blended CAC | **+35% YoY** | industry reporting |
| Fashion/beauty CAC | **₹800–1,200**, up from ₹200–500 | industry reporting |
| Quick-commerce ad rate cards | **₹10–20 lakh/month** | industry reporting |
| Organic discovery | *"nearly impossible without paid promotion"* | industry reporting |

### The arithmetic

**A ₹502 customer acquisition cost against a ₹500 average order value.**

| Gross margin | Contribution/order | After RTO drag¹ | **Orders per customer to break even on CAC** |
|---|---|---|---|
| 30% | ₹140 | ₹104 | **4.8** |
| 40% | ₹190 | ₹154 | **3.3** |
| 50% | ₹240 | ₹204 | **2.5** |

¹ 70% COD × 23% RTO × ₹225 loss = ₹36/order of drag.

**A micro merchant must get a customer to return three to five times just to recover the cost of
acquiring them** — and they have no CRM, no retention tooling, and no way to know who their repeat
customers are.

At the average Razorpay merchant's scale (₹12.45 lakh/year, ~2,490 orders), acquiring just **10% of
orders as new customers costs ₹1.25 lakh — 10% of total revenue, spent on acquisition alone.**

**Conclusion: the micro merchant cannot buy growth.** Paid acquisition is a losing trade at their
AOV. They need distribution they don't have to pay for.

---

## 2. What this does to the earlier analysis

In Phase 3 I wrote that **"agent-readable catalog"** was one of six official example directions with
**no evidenced problem** behind it, and warned against building there.

**That was wrong, and this is the correction.** The problem is now evidenced:

> Micro merchants have no organic discovery, cannot afford paid acquisition at ₹502 CAC against a
> ₹500 AOV, and **agentic commerce is the first genuinely new distribution channel to appear in
> years.** Being machine-readable is the entry ticket to it. A micro merchant cannot build that
> alone. Razorpay already owns their checkout and catalog surface — and is already live on agentic
> payments with NPCI.

That is the strongest growth-side thesis in this entire research, and I missed it because I was
looking for losses rather than for gains.

---

## 3. Eight entry points, ordered by fit

All are **[E]** — my proposals. Each is tested against the four structural constraints from
`micro_merchant_thesis.md` §4: **R1** unit economics (₹3,150/merchant/yr), **R2** risk asymmetry,
**R3** AML disclosure limits, **R4** data access.

### 🥇 G1 — Make every merchant agent-readable by default

**The idea:** Razorpay auto-generates a machine-readable catalog, availability and price feed for
every merchant from data it already processes, and exposes it to AI shopping agents through the
agentic-payments rail it already operates.

**Why it beats the constraints:** zero marginal cost (R1 ✅) · uses data Razorpay already holds
(R4 ✅) · no risk disclosure (R3 ✅).

**Why Razorpay specifically:** they are the only party sitting on **both** the catalog surface *and*
the payment rail, and they already run the NPCI agentic pilot. A micro merchant with no SEO, no
marketplace ranking and no ad budget gets a distribution channel for free.

**Why now:** the channel is forming *this year*. Whoever makes Indian long-tail inventory
machine-readable first defines the standard — and Razorpay has said Agent Studio will open to
third-party builders.

**Revenue for Razorpay:** new TPV on a rail they own. Their public plan is a volume plan
(`company_direction.md` §2) and **this is the only genuinely new volume source in it.**

### 🥈 G2 — Repeat-purchase engine built from payment data

**The idea:** the micro merchant's break-even needs 3–5 repeat purchases. They have no CRM. But
**Razorpay knows who paid, how often, how much and when** — that *is* the customer database.
Automated repeat-purchase prompts, replenishment reminders, lapsed-customer win-backs, all
merchant-branded.

**Why it beats the constraints:** zero marginal cost (R1 ✅) · uses existing data (R4 ✅).
**Constraint to respect:** DPDP purpose limitation — this must be *the merchant's own customers*,
per-merchant, never cross-merchant.

**Why it matters:** it attacks the exact number that decides survival. Moving repeat rate from 1.5
to 3 orders per customer flips a loss-making acquisition into a profitable one.

### 🥉 G3 — Cash-flow-based working capital, underwritten on transaction history

**The evidenced gap:** India's MSME **credit gap is ₹20–30 lakh crore**; formal credit penetration
is **14%**, against China's 37% and the US's 50%. Micro firms *"lack the assets or formal
documentation needed to qualify"*.

**The idea:** Razorpay's transaction history **is** the underwriting file — no collateral, no
documentation, no bank statement needed. Inventory finance sized to observed sales, repaid
automatically from settlements.

**Why it beats the constraints:** underwriting is data Razorpay already has (R4 ✅) and is fully
automatable (R1 ✅).
**The real obstacle is balance sheet, not capability** — and it is pre-IPO. So the realistic shape
is *origination and underwriting-as-a-service to lending partners*, not lending off Razorpay's own
book. Razorpay Capital exists; the question is whether it reaches a ₹12 lakh/year merchant.

### G4 — Close the conversion gap Razorpay itself measured

Razorpay publishes that **Indian D2C converts at ~2% versus ~10% for Amazon and Flipkart** — a **5×
gap** it attributes partly to checkout friction. For a merchant who cannot afford more traffic,
converting more of the traffic they already have is the only free growth available. Magic Checkout
exists; the question is whether it reaches the micro tier and what its *measured* effect is —
Razorpay publishes no first-party number.

### G5 — Merchant standing passport
A clean two-year payment history is an asset locked inside Razorpay. Made portable and verifiable, it
unlocks credit, marketplace trust and better terms elsewhere. Zero marginal cost; also a retention
mechanism, because the passport lives where the history is.

### G6 — Export-in-a-box for micro sellers
Razorpay holds a **PA-CB licence** (Dec 2025) and supports 130+ currencies. A micro seller reaching
overseas buyers escapes the domestic CAC spiral entirely. The hard parts — compliance, FX,
documentation — are exactly what Razorpay already does and the merchant cannot.

### G7 — Pooled demand from the merchant network
12M merchants and their payment histories constitute a demand graph nobody has activated.
⚠️ **Heavy DPDP constraint** — cross-merchant customer data is purpose-limited. Likely only viable
in aggregate or opt-in form. Listed because it is the largest latent asset, not because it is easy.

### G8 — Category benchmarking as a growth product
*"Merchants like you convert at 2.8%; you are at 1.9%. Your repeat rate is half the category
median."* Free, zero marginal cost, and gives a merchant with no analyst the diagnosis they cannot
otherwise buy.

---

## 4. Ranking against the buildathon

| Idea | Track | Reach | Buildable in 11 days? | Competitor repos |
|---|---|---|---|---|
| **G1 Agent-readable catalog** | **T1** | 98.9% | ✅ Yes | ~few — it was the *one* Track 1 direction with no Razorpay product |
| **G2 Repeat-purchase engine** | T1/T3 | 98.9% | ✅ Yes | moderate |
| G4 Conversion gap | T1 | high | ⚠️ Magic Checkout occupies it | ~100 |
| G8 Benchmarking | T1 | 98.9% | ✅ Yes, but shallow | low |
| G3 Credit | — | 98.9% | ❌ Not a hackathon project | — |
| G5 Passport | Open | 98.9% | ⚠️ Abstract to demo | low |
| G6 Export | T1 | low | ❌ Compliance-heavy | low |
| G7 Demand graph | T1 | 98.9% | ❌ DPDP-blocked | low |

**G1 is the standout**, and it reverses my Phase 3 advice. It is the only official Track 1 example
direction with **no Razorpay product**, it now has an evidenced problem behind it, it serves 98.9% of
merchants, it is growth rather than harm-reduction, and it aligns with Razorpay's stated volume plan.

---

## 5. So which problem statement is now the most useful?

Three candidates, honestly compared:

| | **Reconciliation** | **Volume-blind risk** | **Agent-readable catalog (G1)** |
|---|---|---|---|
| Track | 4 | Open/2 | **1** |
| Reach | 1.1% | 98.9% | 98.9% |
| Type | Cost saving | Harm prevention | **Revenue creation** |
| Evidence | Razorpay's 20–40 hrs | Razorpay's 1% + NPCI/Udyam | **NPCI ticket + CAC data** |
| Razorpay product? | 3 adjacent | none | **none** |
| Build risk | 🟢 Low | 🟠 Medium | 🟠 Medium |
| Strategic fit | Financial OS | Merchant retention | **Their #1 bet + their volume plan** |
| Weakness | Small reach | Assumes rule is naive | Must prove buyers exist |

**My read:** for *usefulness to weak businesses*, **G1 is now the strongest** — it is the only one of
the three that makes a struggling merchant *money* rather than saving them from a loss.

For *safety of execution*, reconciliation still wins.

**The killer objection to G1, which you must answer:** *"Where are the AI buyers today?"* Agentic
commerce is a pilot with three merchants. You would be building distribution infrastructure for a
channel that barely exists.

**The answer:** that is precisely why it is unoccupied, and Razorpay is the party betting the company
on that channel existing. Being early is the thesis, not a flaw — but say it out loud rather than
pretending the demand is already there.

---

## 6. Honest limits

- **CAC figures come from industry blogs**, not audited research. Directionally consistent across
  several sources but not primary.
- **A data conflict on merchant counts:** my earlier Udyam figure was 4.72 crore (June 2026); this
  search returned **6.19 crore as of 31 March 2025**, over 99% micro. The difference is likely the
  Udyam Assist Platform, which registers informal micro units. **Both are in circulation — say which
  you're using.** The 99%-micro conclusion holds either way.
- **I have not verified whether Razorpay Capital already serves the micro tier**, which would weaken
  G3.
- **G1's demand side is unproven.** No public data exists on Indian AI-agent shopping volume, because
  it barely exists yet.
- **The ₹500 AOV is an ecosystem average**, not a per-merchant figure. A merchant with a ₹2,000 AOV
  has very different acquisition maths.
