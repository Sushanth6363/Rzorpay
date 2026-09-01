# company_direction.md — Razorpay's Goals, Direction and a Metrics Framework

Compiled 2026-08-25. Grading as elsewhere: **[A]** official Razorpay · **[A-mkt]** Razorpay
marketing · **[B]** primary external · **[C]** credible secondary · **[E]** inference/derived here.

> **Razorpay publishes no OKRs, no scorecard and no strategy deck.** Part 1 is what executives have
> said on the record. Part 2 is arithmetic on reported figures. Part 3 is my reading of direction —
> inference, labelled as such. Part 4 is a metrics framework I built; it is **not** Razorpay's.

---

## Part 1 — What they actually say

### The vision, in the CEO's own words [C]

> **"Idea is to evolve Razorpay beyond a payments provider into a financial operating system for
> businesses"** — Harshil Mathur, Business Today, **12 March 2026**

Note the date: that is **the same day Agent Studio launched**. The positioning and the product
landed together.

> **"Businesses don't just need more software anymore — they need intelligence that can act."**
> — Harshil Mathur, Agent Studio launch [A]

> **"The system has to allow for a certain level of mistakes so that you can learn from them and
> correct them."** — Shashank Kumar, on agentic AI liability, Business Standard, 12 March 2026 [C]

### The stated five-year target [C]

> Triple end users to **1 billion**, and revenue to **₹8,400 crore**.

### The volume ambition [B/C]

**~$400 billion TPV by 2030**, from ~$180bn today.

### The IPO [C]

Confidential DRHP filed with SEBI **12 June 2026**. Raising ~**₹5,700 crore** (₹2,700 cr fresh
issue + offer for sale), targeting a listing by **end-2026**, at a reported **$5–6bn** valuation —
**down 20–33% from the $7.5bn peak** of December 2021.

**Reported use of proceeds** — this is the clearest published statement of where money is going:

1. **International expansion**
2. **Offline POS**
3. **RazorpayX** (business banking)
4. **AI-powered payment solutions and technology infrastructure**
5. Acquisitions and general corporate purposes

---

## Part 2 — What the numbers say

**Assumption:** ₹83/USD throughout. **[E]** — all conversions below inherit it.

⚠️ **A data conflict to know about:** FY24 revenue appears in sources as both **₹2,475 crore** and
**₹2,296 crore** (likely different definitions or a restatement). The widely-quoted "+65% growth"
uses the ₹2,296 cr base; against ₹2,475 cr the growth is +53%. **Both are in circulation. Cite the
base you use.**

| Metric | FY24 | FY25 | Change |
|---|---|---|---|
| Revenue | ₹2,475 cr *(or ₹2,296 cr)* | **₹3,783 cr** | **+53% or +65%** |
| TPV | $150bn (~₹12.45 lakh cr) | **$180bn (~₹14.94 lakh cr)** | **+20%** |
| **Implied take rate** [E] | **0.199%** | **0.253%** | **+27% relative** |
| Gross profit | — | ₹1,277 cr | — |
| **Gross margin** [E] | — | **33.8%** | — |
| Net result | **+₹34 cr profit** | **−₹1,209 cr loss** | one-off driven |
| **Revenue per merchant/yr** [E] | — | **~₹3,150** | — |

### Four things this reveals

**1. They are monetising, not just growing.** Revenue grew ~2.7× faster than volume. The take rate
expanded 27% in a single year. **Growth is coming from selling more per merchant, not from moving
more money** — exactly what you'd expect from a company whose dominant rail earns 0% MDR.

**2. Revenue per merchant is ~₹3,150 a year.** Across 12 million merchants. That is a *very* long
tail of tiny accounts — which explains why almost everything Razorpay ships must be self-serve.
Human-touch solutions don't survive that arithmetic.

**3. The FY25 loss is not an operating story.** FY24 was profitable. The ₹1,209 cr loss is ESOP
expense plus roughly $150M (₹1,245 cr) of tax from moving the parent company from the US to India.
Anyone citing "Razorpay is loss-making" as a business problem is reading a one-off as a trend.

**4. ⭐ The two public targets are exactly consistent with a flat take rate.**

```
$400bn TPV × ₹83  =  ₹33.2 lakh crore
₹8,400 cr ÷ ₹33.2 lakh cr  =  0.253%
Current take rate           =  0.253%
```

Their stated revenue target is what you get by holding today's take rate constant and growing volume
to $400bn. **Both targets imply the same 17.3% CAGR.**

Two readings, and I can't distinguish them from public data: either the targets were set
independently and coincide, or **Razorpay's plan does not assume MDR reform rescues them** — it
assumes new-product monetisation merely offsets continued zero-MDR pressure on the core.

Either way it's a useful thing to know: **their public plan is a volume plan.** [E — arithmetic on
two separately-reported targets under an assumed FX rate. Treat as an observation, not a disclosure.]

---

## Part 3 — Seven directions of travel

Each is an inference, with the evidence that supports it.

### 1. Payments → Financial operating system
**Evidence:** the CEO says it explicitly. IPO proceeds name RazorpayX, POS and international.
Product surface has grown to ~40 products spanning banking, payroll, lending, AP automation,
company registration.
**Why:** UPI earns zero MDR. If your dominant rail is free, you must sell something else.

### 2. Software → Agents that act
**Evidence:** Agent Studio (Mar 2026), Vulcan (Aug 2026), agentic payments with NPCI (Feb 2026),
"intelligence that can act", and **this buildathon** — hiring AI builders in the same six months.
**Why:** it is both a product bet and a cost bet — agents reduce the human cost of serving 12M
merchants at ₹3,150 each.

### 3. Volume → Monetisation per merchant
**Evidence:** take rate 0.199% → 0.253%; revenue growing 2.7× faster than TPV.
**Implication for you:** projects that help a merchant *earn or keep more* align better than
projects that move more volume.

### 4. India → Cross-border
**Evidence:** PA-CB licence (Dec 2025), Curlec in Malaysia, Replit partnership, international named
first in IPO proceeds.
**Caveat:** ~5% of international transactions still fail, and the segment isn't yet EBITDA-positive.

### 5. Growth → Profitability discipline
**Evidence:** IPO at a 20–33% valuation markdown; only the online payments segment is EBITDA-
positive; India-level profitability targeted FY26, consolidated 2–3 quarters later.
**Implication:** cost-saving stories are more saleable in 2026 than they'd have been in 2021.

### 6. Renting AI → Owning the model
**Evidence:** Vulcan is proprietary, built with NVIDIA and AWS, trained on ~3 trillion data points.
**Implication:** don't propose to out-model them. Compete on workflow, verification and action.

### 7. Product → Platform / ecosystem
**Evidence:** Agent Studio ships **partner-built agents** (SuperU, Nugget by Zomato), states
*"Third-party builders will be able to create and publish specialized agents"*, plus an App Store and
"onboard as an AI partner".
**⭐ Implication for you:** a strong external agent is a **business-development target**, not just a
competitor. This is the most under-appreciated route into the company.

---

## Part 4 — The metrics framework

**This is my construction, not Razorpay's.** Three tiers: what the board sees, what a strategy owner
sees, what a product team sees.

### Tier 1 — Company scorecard

| Metric | Latest known | Direction | Source |
|---|---|---|---|
| Revenue | ₹3,783 cr (FY25) | → ₹8,400 cr in 5y | [C] |
| TPV | $180bn | → $400bn by 2030 | [B/C] |
| **Take rate** | **0.253%** | flat in plan; MDR reform is upside | [E] |
| Gross margin | 33.8% | ↑ with product mix | [E] |
| Merchants | 12M+ | → 1bn *end users* | [C] |
| Revenue/merchant | ~₹3,150/yr | ↑ = the whole strategy | [E] |
| Segment EBITDA | only online payments positive | → RazorpayX, POS, intl positive | [C] |
| Valuation | $5–6bn at IPO | vs $7.5bn peak | [C] |

### Tier 2 — Strategic vector metrics

| Vector | Metric that proves it | Known? |
|---|---|---|
| Financial OS | % revenue from non-payment-gateway lines | ❌ not disclosed |
| Agents | Merchants with ≥1 agent deployed; agent-attributable outcome value | ❌ |
| Monetisation | Products per merchant; take rate by segment | ❌ |
| Cross-border | International % of TPV and revenue | ❌ |
| Profitability | Months to consolidated EBITDA positive | partially |
| Own the model | Vulcan-attributable success-rate lift | ⚠️ claimed 8–10%, **unaudited** |
| Ecosystem | Third-party agents published; partner-built share | ❌ |

**Six of seven are undisclosed.** That's normal pre-IPO — and it means anyone claiming to know
Razorpay's strategic KPIs is guessing.

### Tier 3 — Operating metrics (where your project actually lands)

| Metric | Known value | Whose number |
|---|---|---|
| UPI payment success rate | 92–96% blended | merchant |
| UPI technical decline | ~0.7–0.8% | ecosystem |
| **Mandate execution success** | **~30% at SBI** | merchant |
| E-mandate volume | ~1.6bn/mo (top 10 banks) | ecosystem |
| Chargeback ratio | 0.26% global avg; **1% = Razorpay freeze** | merchant |
| RTO rate | ~23.18% of COD | merchant |
| Cost per RTO | ₹200–250 | merchant |
| **Reconciliation effort** | **20–40 hrs/month** | merchant |
| Settlement cycle | T+2 (cards), T+1 (UPI) | Razorpay |
| Freeze resolution | 2–5 days / 1–3 wks / 30+ days | Razorpay |
| SME DSO | 73 days vs 45-day norm | merchant |
| Cart abandonment | 70.22% global; mobile 80.02% | merchant |

---

## Part 5 — Which project moves which metric

The pitch-relevant mapping. **Ladder your KPI up to a company goal and you're speaking their
language.**

| Project | Tier 3 metric it moves | Tier 2 vector | Tier 1 goal |
|---|---|---|---|
| **#1 Reconciliation resolver** | Recon hours 20–40 → lower; match rate; exceptions | Financial OS · Agents | **Revenue per merchant** — a stickier finance product raises products-per-merchant |
| **#2 Recovery sequencer** | Mandate success ~30% → higher; chargeback ratio held < 1% | Agents · Monetisation | **Take rate** — recovered volume is billable volume |
| **#3 Promise-to-pay** | DSO 73 days → lower | Financial OS | **Revenue per merchant** — opens an AR line that doesn't exist |
| **#4 Freeze monitor** | Freeze incidence; frozen-capital days | Profitability | **Merchant retention** — a frozen merchant is a churning merchant |
| **#5 Intent verifier** | Agent-attributable GMV; disputed-agent-txn rate | Agents · Ecosystem | **TPV** — new rail, new volume |

### The strongest framings available

- **#1:** *"Razorpay earns ~₹3,150 per merchant per year. That arithmetic only works if products are
  self-serve. Reconciliation is the least self-serve thing a merchant does — 20 to 40 hours a month
  of it."*
- **#2:** *"Recovered payments are billable payments. At a 0.253% take rate, every rupee recovered
  is revenue for the merchant and margin for Razorpay — and the stopping rule protects the merchant
  account that generates both."*
- **#5:** *"Your public plan is a volume plan — $400bn TPV at a flat take rate. Agentic commerce is
  the only genuinely new volume source in it."*

---

## Part 6 — What we cannot see

- **No public OKRs.** Everything in Part 3 is inference from products, quotes and spending.
- **The DRHP is confidential.** SEBI does not publish pre-filed drafts, so there is **no
  company-authored risk-factor list** — the single best source for "what Razorpay is worried about"
  does not exist publicly.
- **Six of seven strategic-vector metrics are undisclosed.**
- **Vulcan's performance numbers are unaudited** — a journalist asked for baseline, sample size and
  timeframe on 18 Aug 2026 and received none.
- **Segment-level revenue and margin are not broken out**, so "is RazorpayX working?" is unanswerable
  from outside.
- **The ₹83/USD assumption** runs through every derived figure here.

---

## Summary in five lines

1. **Goal:** stop being a payments company; become the financial operating system for Indian
   businesses — 1 billion end users, ₹8,400 cr revenue, ~$400bn TPV.
2. **Constraint:** the dominant rail earns zero MDR, and revenue per merchant is ~₹3,150/year.
3. **Strategy:** sell more products per merchant, expand abroad, and use agents to serve a
   12-million-merchant long tail without adding humans.
4. **The 2026 bet:** own the AI stack (Vulcan), ship agents (Agent Studio), open it to third-party
   builders — and hire the builders (this buildathon).
5. **The pressure:** an IPO by end-2026 at a marked-down valuation, with only one segment
   EBITDA-positive.
