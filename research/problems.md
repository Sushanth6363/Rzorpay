# problems.md — Razorpay's Real Business Problems (Phase 1, v2.1)

**v1** compiled 2026-08-24 from 109 claims / 42 verification votes.
**v2** compiled 2026-08-24 from a second adversarial pass: **109 agents, 26 sources fetched,
120 claims extracted, 25 adversarially verified (6 confirmed, 19 killed), 1,049 tool calls.**
Both raw agent journals are archived in this folder.

**v2.1 (same day): capture audit.** A check of my own coverage found that **16 of the 120 claims
from the second run had never been read** — my extraction filters skipped them. Six were material
and are now incorporated, marked *v2.1*: card-network chargeback thresholds, the Visa dispute
reason-code mix, Razorpay's own India checkout-abandonment figures, the absence of any first-party
Magic Checkout benchmark, the RBI Ombudsman scope exclusion, and a Shashank Kumar leadership quote
that partially fills what v2 reported as an empty Gap E. **All 120 claims from run 2 and all 109
from run 1 have now been read.**

Grading: **[A]** official Razorpay · **[A-mkt]** Razorpay marketing/launch publicity ·
**[B]** primary external (RBI/NPCI/SEBI/government) · **[C]** high-quality secondary ·
**[D]** weak/vendor blog · **[E]** inference by this document.

---

## ⚠️ How to read the verification verdicts

**A 0-3 vote means verifiers did not confirm a claim. It does NOT mean the fact is false.** The
verification round had a hard budget: **only 25 of 120 extracted claims were ever voted on.**
Several down-voted claims failed because a URL 403'd to direct fetch, or because a single source
carried them — not because they were disproven.

This document therefore uses four states:

| State | Meaning |
|---|---|
| **VERIFIED** | Survived 3-vote adversarial verification |
| **FALSIFIED** | Actively disproven against a better source |
| **UNVERIFIED** | Extracted from a fetched source but never voted, or voted down for sourcing rather than substance. Usable with the source named — **not** established fact |
| **CONTESTED** | Two credible sources disagree |

Three fetch failures distorted coverage and must be disclosed: **business-standard.com and
medianama.com both 403 direct fetch** (quotes recovered via search-index extraction are
near-verbatim at best); **razorpay.com/agent-studio/ is client-side rendered and returned zero
agent cards**, so the *live* Aug 2026 roster is unconfirmed; **razorpay.com/blog/razorpay-vulcan-ai-model/
returns 404.** The Vulcan search thread exhausted its 200-query budget, so "no independent audit
exists" is a **non-exhaustive negative**.

---

## What v2 changed

**One hard falsification.** v1's P1.7 claimed a T+2-practice-versus-T+1-mandate compliance gap.
**There is no RBI T+1 settlement mandate.** See P-F1 below. My v1 confidence of 8/10 on that
problem was wrong.

**One hard confirmation, now properly cited.** Vulcan's numbers are unaudited vendor self-report —
MediaNama asked Razorpay directly for baseline, sample size and timeframe and **received none**.

**Six of seven missing magnitudes are now filled** — RTO rate and cost, SME DSO, MSME receivables,
reconciliation hours, chargeback benchmarks, cart abandonment. Most are UNVERIFIED (budget, not
substance), and each is labelled with its source quality.

**Several v1 confidence scores were too high** and are cut below. The AutoPay 20M figure in
particular rests on a source that 403s.

---

## Master table — every problem

| # | Problem | Evidence | Business impact | Who suffers | Current Razorpay solution | Remaining gap | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | UPI AutoPay/e-mandate executions fail at debit | NPCI-derived press [C] | ~70% of SBI auto-debits fail; e-mandate volume ~1.6bn/mo (May 26) | Merchants, customers | Subscription Recovery (early access) | Retry timing vs balance availability; no cross-app mandate view | **OPEN** |
| 2 | Payment success-rate leakage | Blog/industry [D] + NPCI targets [B] | 92–96% blended UPI SR | Merchants | Optimizer, Vulcan | Business declines unaddressable by routing | **PARTIALLY SOLVED** |
| 3 | Take-rate compression under zero-MDR | Press/policy [B/C] | ₹15–20k cr ecosystem cost; ~96% of txns stay zero-MDR | Razorpay | None possible | Resolves in Parliament | **OPEN (not buildable)** |
| 4 | Merchant fund holds / account freezes | Razorpay blog [A] + reviews [C] | 120-day hold documented; 14-day reversal with full appeal | Merchants | **None** — manual ticket + escalation | Entire resolution path manual | **OPEN** |
| 5 | Agentic-commerce trust & agent liability | Press [B/C] | UPI P2M 63.5% of 22.71bn txns (Jun 26) | Razorpay, merchants | Claude pilot on UPI Reserve Pay | UAP unlaunched; **no chargeback path for AI-led txns** | **OPEN** |
| 6 | Reconciliation exception handling | **Razorpay blog [A]** | **20–40 finance work-hours/month** on multi-gateway recon | Merchants | Single View Recon (2022) — a *viewing* dashboard | No auto-matching or exception resolution, 4 yrs on | **OPEN** |
| 7 | Settlement timing / working capital | Razorpay docs [A] | T+2 cards, T+1 UPI | Merchants | Instant Settlements (**paid, manual ticket to enable**) | Not self-serve; not a compliance breach (see P-F1) | **PARTIALLY SOLVED / MONETISED** |
| 8 | Disputes & chargebacks | Razorpay [A] + vendor [D] | Global avg 0.26% (Q3 25, +24% YoY); RZP freeze trigger 1% is **stricter than Visa VAMP 1.5%/Mastercard ECM 1.5%** | Merchants | Dispute Responder | No published win-rate; support latency unchanged | **PARTIALLY SOLVED** |
| 9 | Refund failures | Reviews [C] — **CONTESTED** | No rate published | Customers, merchants | **None** — no refund agent | Three-way state recon RZP↔merchant↔bank | **OPEN** |
| 10 | Support cost & quality | Reviews [C] | 94% of negative reviews get an identical templated reply | Merchants | Slash, Call-E (internal) | Templated escalation, not resolution | **OPEN** |
| 11 | RTO / COD returns | GoKwik [D], Unicommerce [D] | **23.18% national avg; ₹200–250 lost per RTO** | Merchants | RTO Shield, RTO Insights, Vulcan RTO Intelligence | Merchant delivery-data coverage <100% gates accuracy | **SOLVED to data limit** |
| 12 | Cross-border | Razorpay [A/B] | ~5% of international txns fail | Merchants | PA-CB licence, Intl Payments | No public cross-border settlement benchmark | **PARTIALLY SOLVED** |
| 13 | Regulatory/compliance burden | RBI [B] | ~1-yr onboarding ban 2022–23 | Razorpay | Compliance function | Structural; **not Razorpay-specific** | **CONTEXT** |
| 14 | IPO / valuation compression | Press [C] | $5–6bn vs $7.5bn peak; FY25 −₹1,209 cr | Razorpay | — | DRHP confidential | **OPEN (not buildable)** |
| 15 | Fraud detection coverage | TransUnion [C] | **Retail 2.5%, txn-stage 1.2%** — at/below global | Merchants | Vulcan, Thirdwatch | No India merchant-side rate; Vulcan unaudited | **UNKNOWN MAGNITUDE** |
| 16 | Checkout abandonment | Baymard [B] | 70.22% global; **mobile 80.02% vs desktop 66.41%, >60% of India traffic mobile; Indian D2C converts ~2% vs ~10% for Amazon/Flipkart** | Merchants | Magic Checkout, Abandoned Cart agent | **Razorpay publishes no first-party Magic Checkout effect** | **PARTIALLY SOLVED** |
| 17 | Merchant onboarding friction | Razorpay [A-mkt] | 30–45 min → 5 min (contradicted internally) | Merchants | Agentic Onboarding | Two Razorpay sources disagree | **SOLVED** |
| 18 | **B2B receivables / collections** | **MSME Samadhaan [B]** | **₹55,244 cr claimed, ₹20,979 cr pending; SME DSO 73 days** | Merchants (SMEs) | **None** — no agent | Entire collections loop uncovered | **OPEN** |
| 19 | Late authorisation recon exceptions | Razorpay blog [A] | Status finalises minutes–hours late | Merchants | None | Finance staff re-check pending txns manually | **OPEN** |
| 20 | COD sits outside the regulated rail | **RBI MD [B]** | COD barred from PA escrow | Merchants | None | No PA-side protection on COD; RTO loss is merchant's | **OPEN** |

---

## P-F1 — FALSIFIED: there is no RBI T+1 settlement mandate

**This is the single most important correction in v2, and it overturns a v1 finding.**

- **Source [B, primary]:** RBI Master Direction **RBI/DPSS/2025-26/141**,
  CO.DPSS.POLC.No.S-633/02-14-008/2025-26, dated **15 Sep 2025**, effective immediately, applying to
  all bank and non-bank PAs.
- **Chapter V, Table 1, verbatim:** *"Credit to merchant's a/c: As per the agreement between the PA
  and the merchant. Such an agreement should be fair, equitable and must transparently mention the
  settlement timelines."*
- **Method:** a verifier extracted the full **44,787-character PDF** and ran regex across it —
  **zero matches** for "T+1", "Ts+1", "Td+1", "+1 day", "one working day", or even "working day".
  All 19 occurrences of "settl*" were inspected individually; **none imposes a day-count.** The 2025
  Directions **expressly repeal** the 2020 circular that carried Ts+1/Tp+1.
- **Verdict: VERIFIED 3-0.** v1's "regulation-vs-practice gap" framing was wrong.

> **Contradiction worth knowing.** **Razorpay's own blog asserts the opposite** — that "RBI Payment
> Aggregator Directions 2025 impose a hard T+1 credit obligation," citing penalties up to ₹1 crore
> under the PSS Act 2007 [A-mkt]. The primary regulator text does not support this. **Razorpay's
> marketing content misstates the regulation it cites.** If you build anything touching settlement
> timing, cite the Master Direction, not Razorpay's blog — and this is a genuinely impressive detail
> to have caught if it comes up in a panel.

**What survives:** a weaker but real **disclosure** argument. The 2025 MD retains a fairness-and-
transparency obligation, so "does Razorpay's merchant agreement disclose its timeline fairly and
transparently?" is still open. **Scope limit:** only the RBI MD was examined — NPCI rules,
card-scheme rules, nodal-account rules and Razorpay's actual merchant agreement were not.

---

## Newly filled magnitudes (JOB 2)

### RTO / COD returns — **filled** [D, vendor networks]
- **GoKwik network data (180M+ shoppers): national RTO average 23.18%**; worst state Bihar
  **34.06%** — a >10 percentage-point geographic spread. General COD RTO band **20–25%**, up to
  ~40% for some brands. `UNVERIFIED`
- **Cost per RTO: ₹200–250 on a ₹1,000 COD order** (forward shipping/handling ~₹200 + reverse
  logistics ~₹85) **with zero offsetting revenue**, versus ~₹100 total cost on a prepaid order.
  `UNVERIFIED` — the only cost-per-RTO figure found anywhere.
- **60–70% of RTOs stem from low buying intent; only 20–25% from logistics issues** → the
  addressable lever is **checkout-time risk scoring**, not delivery ops. `UNVERIFIED`
- Unicommerce D2C report (6,000+ brands, 410M shipments): festive-quarter **COD RTO 58% vs prepaid
  under 15%**; blended peak **39.2%**; one brand cut RTO **39% → 21%** in four months with prepaid
  incentives, pincode-based courier routing and address verification. `voted 0-3` — the report
  itself failed verification; treat as indicative only.

### B2B receivables — **filled, and this is the best-sourced new magnitude** [B, government]
- **MSME Samadhaan portal: 2,56,892 delayed-payment applications worth ₹55,244 crore, of which
  ₹20,979 crore still pending.** **40,580 applications (16%) unresolved for more than a year.**
  `UNVERIFIED` — **caveat:** the identical totals are elsewhere reported as the position at
  31 Dec 2025, so the "14 Aug 2026" as-of date is likely a restatement of a stale snapshot. Cite as
  cumulative, not current-year.
- **Recordent Indian SME Receivables Report 2026 (27 Jun 2026): SMEs take an average 73 days to
  settle invoices** against a 45-day statutory norm; **the average SME carries ~₹3.83 crore in
  receivables unpaid beyond 360 days**; **82.6% of invoices carry 0–30 day terms**, so the 73-day
  reality is a **43+ day collection-discipline failure**, not lax credit policy. Mumbai is fastest
  at 59 days. `UNVERIFIED` — **vendor-generated data from a collections platform whose CEO uses it
  to sell receivables software; sample self-selects toward businesses with collection problems.**
- **August 2026: Parliament legislated time-bound machinery** (mediation concluded within 90 days,
  arbitration referral within 30, award within 90 days of pleadings), which implies the existing
  45-day rule and MSEFC process **were not working**. Crisil Intelligence calls it a potential
  "IBC moment" for delayed payments, **conditional on implementation**. `UNVERIFIED`

### Reconciliation effort — **filled from Razorpay's own content** [A]
- **Razorpay states multi-gateway merchants spend 20–40 work-hours per month on reconciliation.**
  Unaudited vendor-marketing figure with no stated methodology — but it is *Razorpay's own number*
  for the problem, which is exactly what a Track 4 project needs. `UNVERIFIED`
- **Razorpay describes the process as explicitly manual:** finance teams "download and manually
  reconcile payments and settlements" from each aggregator by hand.
- **Late authorisation is a named exception class:** payment status can finalise "minutes to several
  hours" after the transaction, forcing repeated re-checks before books balance.
- **Single View Recon (shipped June 2022) is a consolidated *viewing* dashboard** — transaction
  status, UTRs, Settlement IDs, processing aggregator. **It surfaces mismatches for humans rather
  than resolving them.** Four years on, exception resolution is still unautomated. **This is the
  cleanest OPEN gap in the finance domain.**
- Razorpay separately enumerates the fields a settlement report must itemise (MDR, GST on MDR,
  refund offsets, chargeback deductions, net settled, bank UTR) and flags **"net-only reporting" and
  missing UTRs** as failure modes that make payouts impossible to match to bank credits.

### Chargeback rates — **filled, global only** [D]
- **Global all-industry average 0.26% of transactions (Q3 2025), up 24% YoY from 0.21%.**
- **Rates vary ~8.5x by vertical:** restaurants ~0.12%, software/SaaS 0.66%, education/training
  1.02% — so any single blended benchmark is invalid without vertical segmentation, and
  subscription-heavy verticals sit closest to freeze-trigger levels.
- Razorpay's own numbers [A]: freeze trigger **1%**, global average "near 0.60%", recommended
  internal alert **0.5%**, and "up to 40% of disputes avoidable."
- **No India-specific chargeback rate exists in any source found.** `UNVERIFIED`

### Cart abandonment — **filled, and the finding is that India cannot be measured** [B]
- **Baymard global average 70.22%**, derived from **50 studies spanning 2006–2025**. **VERIFIED 3-0.**
- **Baymard's dataset contains ZERO India-specific studies and ZERO mobile-vs-desktop splits.** Its
  scope note covers "leading ecommerce sites in US and Europe"; its 344-site benchmark contains no
  Indian sites. **The widely circulated ~80% India abandonment figure is unverified vendor data.**
- Dataset last refreshed **22 Sep 2025**, so it is ~11 months stale and carries no 2026 datapoint.
- Baymard's own research: the average large site has **39 checkout improvement areas** and can gain
  **35.26% conversion uplift** from checkout design alone.
- Stated abandonment causes excluding "just browsing" (42%): extra costs too high **40%**, delivery
  too slow **20%**, card distrust **19%**, forced account creation **18%**, checkout too long **17%**.
- **Caveat the verifiers raised:** Baymard's 70.22% is a *meta-average of studies published by
  cart-recovery vendors*, not primary research. Do not call it a gold standard.

### Merchant-side fraud — **filled as a misuse warning** [C]
- **TransUnion H1 2026 report (16 Jun 2026): 7.1% of attempted transactions involving Indian
  consumers were suspected fraud in 2025, ~1.87x the global 3.8%.** **VERIFIED 3-0.**
- **But that headline is economy-wide and dominated by logistics (16.3%) and telecom (14.7%).**
  The sectors a payment aggregator actually serves: **retail 2.5%, financial services 2.6%** —
  *below* the global average. By attack stage: login 3.9%, account creation 3.1%, and **the
  financial-transaction stage — the moment Razorpay controls — is the LOWEST at 1.2%.**
- **Using 7.1% to size Razorpay-relevant fraud overstates it by roughly 3–6x.** `sector splits
  UNVERIFIED — they failed as standalone claims even though they appear inside the verified parent`
- "Suspected fraud" includes policy-violation denials, not confirmed loss.

### Refund failure rate — **STILL EMPTY**
No rate found in any source. The PissedConsumer extraction **explicitly returned nothing** on
resolution times or resolution rate. See P9 below, which is now **CONTESTED**.

### Card-network chargeback thresholds — **filled** [D] · *added in v2.1*
- **Visa VAMP:** a merchant is flagged "Excessive" at a **2.2%** dispute-and-fraud ratio, tightening
  to **1.5% effective 1 April 2026**.
- **Mastercard ECM:** flagged at **100 monthly chargebacks or a 1.5% rate**; HECM escalation at
  **300 chargebacks or 3%**.
- **Therefore Razorpay's >1% fund-hold trigger is STRICTER than the card networks' own excessive-
  chargeback thresholds** — the aggregator withholds merchant funds *before* the network would
  penalise it. That is a sharp, checkable asymmetry and one of the best arguments that P4 (fund
  holds) is a genuine merchant-side problem rather than pure regulatory necessity. `UNVERIFIED`

### Dispute reason-code mix — **filled** [D] · *added in v2.1*
Visa reason-code distribution: **10.4 card-absent fraud 11.1%**, **13.2 cancelled recurring 8.5%**,
**13.7 cancelled merchandise 8.2%**. **Subscription/recurring-billing disputes are a top-three
chargeback driver globally** — hard reason-code corroboration that mandate-lifecycle failure (P1)
produces measurable downstream dispute cost, not just churn. `UNVERIFIED`

### India checkout abandonment — **partially filled from Razorpay's own Learn page** [A] · *v2.1*
This qualifies the "no India benchmark exists" finding above. Razorpay Learn publishes:
- **Mobile abandonment 80.02% vs desktop 66.41%**, and **over 60% of Indian e-commerce traffic is
  mobile** — so India's effective blended rate sits **nearer the mobile figure than the 70.22%
  global average**. (Baymard's own dataset carries no device split, so this split comes from
  elsewhere — treat as Razorpay-cited, not Baymard-verified.)
- **Razorpay's stated benchmark for a well-performing Indian D2C brand: abandonment below 65%.**
- **Indian D2C brands convert at ~2% versus ~10% for Amazon and Flipkart — a 5x conversion gap**
  Razorpay attributes partly to checkout friction. This is the closest thing to an India-specific
  magnitude found in either pass.
- **Critical negative:** the page publishes **no measured effect of Magic Checkout** on abandonment
  or conversion — only qualitative positioning via a "100 million+ shopper" prefill network. Its
  sole quantified upside (35.26% conversion lift) is **sourced to Baymard, not to Razorpay merchant
  data.** *Razorpay processes the transactions and still publishes no first-party checkout-recovery
  benchmark.* The widely repeated "22% cart-abandonment reduction via Magic Checkout" is not
  supported by Razorpay's own page. `UNVERIFIED`

---

## Problem records by domain

### PAYMENTS

**P1 — UPI AutoPay / e-mandate execution failure** · **OPEN** · confidence **7/10** (was 9)
Impact: **~70% of SBI auto-debit executions fail**, still being reported on May-2026 data in
June 2026 — so the freshness challenge failed and the figure survives a year on `UNVERIFIED, 0-3`.
**UPI e-mandate volume at the top ten remitter banks reached ~1.6bn transactions in May 2026, up
~3x from 577M in May 2025** — a new denominator: even at a flat failure rate, absolute failures are
tripling `UNVERIFIED, 0-3`. Failure cause is **business decline (insufficient funds at trigger)**,
not infrastructure. **The >20M monthly revocations figure could not be re-fetched** (Business
Standard 403s) and one 2026 source explicitly does not contain it — **downgraded from v1's 9/10.**
Additional gap: **as of June 2026 there is no unified view of a user's active AutoPay mandates
across apps; NPCI is only now building a centralised API** — mandate visibility is an
infrastructure-level hole.
Solution: Subscription Recovery (early access, voice by ElevenLabs). Gap: retry timing against
predicted balance, and the new mandatory 24h pre-debit notification creates an opt-out churn path
nobody manages.

**P2 — Payment success-rate leakage** · **PARTIALLY SOLVED** · confidence **6/10** (was 9) ·
**CONTESTED**
92–96% merchant-observed blended UPI success; system TD ~0.7–0.8% vs 8–10% in 2016; NPCI OC-149
targets TD <1%, BD <5%. **But v1's "residual failure is mostly business decline" is contested by
its own source:** the same page puts **bank server timeout at 35–45% of failures** — larger than
insufficient balance at 15–25%. Combining buckets, **technical/infrastructure causes may dominate
merchant-observed failures even though system-wide TD is low.** v1 overstated this.
Also: **no officially published per-PSP success benchmark exists** — Razorpay 93–96%, PayU 91–94%,
Cashfree 92–95%, direct NPCI 95–97% are all self-described as directional.
Recovery magnitude found: **smart retry recovers 20–30% of timeout failures; in-app UPI SDKs add
2–4 percentage points** `UNVERIFIED [D]`.

**P16 — Checkout abandonment** · **PARTIALLY SOLVED** · confidence **6/10** — see magnitudes above.

**P12 — Cross-border** · **PARTIALLY SOLVED** · confidence **7/10**. New: **Razorpay publishes no
fixed settlement cycle for international payments**, deferring to "applicable law" and the merchant
Dashboard — so no public cross-border settlement benchmark exists [A].

### RISK

**P8 — Disputes & chargebacks** · **PARTIALLY SOLVED** · confidence **7/10**. Dispute Responder
ships with **zero published performance metrics**. Merchant reviews specifically name slow dispute
support as of Aug 2026 — the agent has not measurably reduced dispute latency. **Regulatory
constraint [B]:** RBI MD 2025 — *"The chargeback rights of customers, as applicable, shall remain
unaffected"*, and refunds/reversals must route through escrow, so **a PA cannot contractually limit
chargeback exposure**; the funding and reconciliation burden sits structurally on PA and merchant.

**P11 — RTO / COD** · **SOLVED to the data limit** · confidence **7/10** (was 6, raised — magnitude
now exists). Most heavily productised problem here. Remaining gap is **merchant delivery-data
coverage below 100%**, which gates model accuracy.

**P20 — COD sits outside the regulated rail** · **OPEN** · confidence **8/10** · **NEW in v2** [B]
RBI MD 2025 verbatim: *"The escrow account shall not be operated for 'Cash-on-Delivery'
transactions."* COD flows — precisely where RTO loss occurs — sit **entirely outside the regulated
PA settlement rail**, so no PA-side settlement or escrow protection applies and RTO cost falls
wholly on the merchant. A structural, regulator-grounded reason COD risk is the merchant's problem
alone.

**P15 — Fraud detection coverage** · **UNKNOWN MAGNITUDE** · confidence **6/10** (was 5). The
negative finding is now well-evidenced: no valid India merchant-side rate exists, RBI's dataset is
invalid as a proxy, and the TransUnion headline would overstate by 3–6x. Razorpay's own 2026 blog
recycles **stale FY2022-23 figures** (9,000+ digital fraud cases, 0.0011% of transaction value) —
weak evidence for present-day conditions.

### REVENUE

**P18 — B2B receivables / collections** · **OPEN** · confidence **7/10** (was 4, **raised sharply**)
Now the best-evidenced *uncovered* problem in the set: a **government portal magnitude**
(₹55,244 cr claimed / ₹20,979 cr pending / 16% unresolved >1yr), an independent DSO figure
(73 days vs 45-day norm), fresh **Aug 2026 legislation** confirming the problem is live and
unsolved, and **no Razorpay agent covering it.** Buildathon fit: Track 3 "B2B receivables chaser"
and "promise-to-pay tracker", both nearly uncontested in the competitor field.

**P9 — Refund failures** · **OPEN** · confidence **5/10** (was 7) · **CONTESTED**
v1 called refunds the single most frequent complaint category. **Two sources now contradict that:**
Trustpilot's own AI topic taxonomy names Payment, Service, Customer service, Response time and
Website — **refunds do not appear**; and an aggregated review analysis names payment holds, disputes
and unresponsive support **with no mention of refunds at all**. Trustpilot's sample is also
**449 reviews, 72% one-star, only 65 in the last 12 months** — too small and too self-selected to
rank complaint categories. RBI Ombudsman data cuts the same way: **Loans & Advances 29.25% and
Credit Cards 20.04% lead**, and mobile/electronic banking complaints **fell 12.74% YoY**.
**Counter-evidence in the other direction** [C]: the PissedConsumer extraction does name refund
non-processing and delay as **the single most prevalent theme in that corpus** as of Aug 2026 — but
that establishes rank-order *among complainers*, not a population failure rate, and its sample is
**444 registered-user reviews, not the "1.8K" the page headline implies** (a prior citation of
~1.8K would overstate the base ~4x).
**Why the RBI Ombudsman data cannot settle it** [B]: that dataset covers **13,34,244 complaints in
FY25 (+13.55% YoY)** but is attributed **81.53% to banks and 14.80% to NBFCs** — it contains **no
payment-aggregator or merchant-side category and no UPI-specific statistic at all.** It cannot
proxy for Razorpay merchant refund, settlement or fund-hold complaints in either direction.
**Refund failure is real but its primacy is not established, and no rate exists.** Razorpay's Agent
Studio blog does name refunds in the pain surface it targets while shipping no refund agent
`0-3`. Downgrade accordingly.

### FINANCE

**P6 — Reconciliation exception handling** · **OPEN** · confidence **8/10** (was 8, now much better
evidenced). See magnitudes. **The strongest Track 4 position:** Razorpay's own content supplies the
magnitude (20–40 hrs/month), admits the process is manual, names the exception class (late
authorisation), and its shipped answer is a *viewing* dashboard from 2022.

**P19 — Late authorisation recon exceptions** · **OPEN** · confidence **7/10** · **NEW in v2** [A]

**P7 — Settlement timing** · **PARTIALLY SOLVED / MONETISED** · confidence **7/10**, reframed after
P-F1. Razorpay's own docs: **T+2 standard domestic**, T+1 UPI. **Instant Settlements is on-demand
and requires a manual support ticket to activate** — so the default merchant experience stays T+2
unless they discover and request a paid add-on `1-2`. Docs also enumerate **settlement failure
causes** (frozen/inactive merchant bank account, incorrect bank details, bank-side rejection) with
no frequency attached, and expose a **"settlements placed on hold"** state with **no triggers, no
timeline and no automated remediation path** [A].

**P3 — Take-rate compression** · **OPEN, not buildable** · confidence **9/10**.

### GROWTH

**P5 — Agentic-commerce trust & liability** · **OPEN** · confidence **8/10**. Unchanged from v1;
the chargeback/liability void for AI-led transactions remains the sharpest sub-problem. Note
Agent Studio is explicitly becoming an **open ecosystem** — *"Third-party builders will be able to
create and publish specialized agents"* [A]. **That is a direct route in: build the agent that
belongs in their marketplace.**

**Leadership statement — Gap E, partially filled** [C] · *added in v2.1*
**Shashank Kumar (Razorpay MD/co-founder), Business Standard, 12 Mar 2026**, on agentic-AI
liability: ***"The system has to allow for a certain level of mistakes so that you can learn from
them and correct them."*** This is a Razorpay leader conceding that **autonomous financial agents
will make errors and the system must tolerate them** — i.e. agent accuracy and error handling are
unresolved for high-stakes flows like disputes.

> **Read this against the buildathon bar.** Track 1 asks for *"one failure handled gracefully."*
> Razorpay's own MD frames error tolerance and correction as the open problem in agentic finance.
> A submission whose centrepiece is *how the agent behaves when it is wrong* is answering the
> question its leadership is publicly asking. This is the single best quote in the corpus to open
> a pitch with. (Hard paywall: only ~1,680 characters of the article were retrievable, so no
> success-rate, TPV or hiring detail was reachable.)

**Domains with NO credible problem evidence found** (reported as required): **AI-readable catalogs,
upsell/cross-sell, campaign optimisation, conversational commerce.** No source in either pass
produced a citable, quantified Razorpay-relevant problem in these four areas. They appear in the
buildathon's example directions but not in any evidence base — treat as **unevidenced**, and if you
build there, expect to supply the problem statement yourself.

### OPERATIONS

**P4 — Merchant fund holds / freezes** · **OPEN** · confidence **8/10** (was 9)
Razorpay's June 2026 blog confirms the trigger set (**chargeback ratio >1%, ~10x volume spikes,
stale KYC/GST/PAN, PA compliance flags**) and the resolution bands (**2–5 business days / 1–3 weeks
/ 30+ days**) `voted 0-3 on sourcing, but the page is Razorpay's own` [A]. **Razorpay's prescribed
remedy is entirely manual:** open a support ticket, request the reason in writing, assemble
documents, escalate to a named risk contact, and **if unresolved, file an RBI Ombudsman complaint.**
Its other advice is that merchants should **negotiate hold triggers and escalation paths into the
gateway contract** — an admission there is no product answer.
New concrete magnitudes from merchant reviews [C]: a documented **120-day settlement hold** after a
"compliance review" followed by service termination; and **account suspension without prior warning
taking ~14 days to reverse** even with a complete documented appeal, first substantive response on
day 3.
**Still no Agent Studio agent covers this.**

**P10 — Support cost & quality** · **OPEN** · confidence **8/10** (was 7)
New and damning [C]: Razorpay **replies to 94% of negative reviews with an identical copy-pasted
script** — *"This appears to be an isolated setup issue"* — across unrelated complaints spanning
fund holds, KYC rejection, refunds and spam. Templated acknowledgement, not resolution.

**P17 — Onboarding friction** · **SOLVED** · confidence **4/10** — two Razorpay sources disagree.

**P13 — Regulatory burden** · **CONTEXT, not Razorpay-specific** · confidence **8/10**.
New [B]: RBI MD 2025 sets a **KYC cliff** — merchants onboarded up to **31 Dec 2025** must be
brought into compliance within a year, and from **1 Jan 2026** due diligence must happen at
onboarding with the PA retrieving the merchant's record from **CKYCR** `0-3`.

**P14 — IPO / valuation compression** · **OPEN, not buildable** · confidence **7/10**. Phase-1
finding #7 (DRHP confidential) **was never tested in this round — status unknown, not confirmed.**

---

## Killed in v2

| Claim | Why |
|---|---|
| RBI mandates T+1 settlement for PAs | **FALSIFIED** against the primary Master Direction. Razorpay's own blog asserts it and is wrong. |
| Refunds are the single most frequent complaint category | **CONTESTED** by Trustpilot's own taxonomy, an aggregated review analysis, and RBI Ombudsman category data. |
| Residual UPI failure is *mostly* business decline | **CONTESTED** — bank server timeouts are 35–45% of merchant-observed failures vs 15–25% for insufficient funds. |
| India cart abandonment ≈ 80% | Unverified vendor figure; **no India benchmark exists at all.** |
| India suspected fraud 7.1% sizes Razorpay's exposure | **Misuse** — economy-wide, logistics/telecom-dominated; retail is 2.5%, txn-stage 1.2%. |
| Vulcan's performance figures evidence solved problems | **CONFIRMED as unaudited self-report.** MediaNama asked for baseline, sample and timeframe; Razorpay did not supply them (as at 18 Aug 2026 — a living article). |

*(v1's three removals — RBI bank-fraud as proxy, the 9% growth deceleration, and the
unprofitability overreach — all still stand.)*

---

## Open questions

1. **What is the live Agent Studio roster today?** The product page is client-side rendered and
   defeated fetching; the roster we have is from a **5-month-old** launch blog, and Razorpay says
   the studio will open to third-party builders. Needs a rendered-browser check.
2. **Did Razorpay ever answer MediaNama on Vulcan's baseline?** The search budget was exhausted, so
   "no independent audit exists" is non-exhaustive.
3. **Where is an India-specific refund failure rate?** Still the one genuinely empty cell.
4. **Does Razorpay's merchant agreement disclose settlement timelines "fairly, equitably and
   transparently"** as the 2025 MD requires — and do NPCI or card-scheme rules impose a day-count
   the RBI no longer does? This is the only surviving form of the settlement question.
5. **Are the fund-hold triggers and bands traceable to a durable Razorpay-official page**, and can
   refund grievance volume be documented from NCH/consumer-forum data rather than review corpora?

---

```
PHASE 1 VALIDATION (v2)

Problems identified: 20 retained + 3 removed in v1 + 1 falsified framing = 24 examined
Problems with strong evidence: 12  (P1 partial, P2 partial, P3, P4, P5, P6, P7, P8, P10, P11,
                                    P13, P18, P20 — see confidence table)
Problems with weak evidence: 6     (P9, P12, P15, P16, P17, P19 magnitude)
Problems removed: 3 (v1: RBI-fraud-proxy, 9%-growth, unprofitability-overreach)
Problems falsified: 1 (the T+1 settlement mandate framing of P7)
Problems merged: 3 merges collapsing 6 candidate entries (unchanged from v1)
Problems added in v2: 3 (P18 promoted to strong, P19 late-auth exceptions, P20 COD-outside-escrow)

Top questionable assumptions:
1. That a 0-3 adversarial vote means a fact is false. It does not - only 25 of 120 claims were
   ever voted on, and several failed because a URL 403'd, not because they were disproven. Most
   of the magnitudes in this document are UNVERIFIED in exactly that sense.
2. That Razorpay's own content is reliable on regulation. It asserts an RBI T+1 mandate that the
   primary Master Direction does not contain. If it is wrong about the rule it cites, its
   unaudited performance numbers deserve no more trust.
3. That merchant review sites can rank complaint categories. Trustpilot carries 449 reviews, 72%
   one-star, only 65 in the past year, and its own topic taxonomy contradicts v1's refund finding.
   The complaint THEMES are corroborated by Razorpay's own blog; the RANKINGS are not measurement.

Contradictory evidence:
- Razorpay blog says RBI PA Directions 2025 impose a hard T+1 credit obligation; the Master
  Direction contains zero day-count references and repeals the circular that carried one.
- Bank server timeouts (35-45% of failures) vs insufficient funds (15-25%) contradicts the
  "residual failure is mostly business decline" framing drawn from the same page.
- Trustpilot's topic taxonomy (no refunds) vs v1's "refunds are the top complaint".
- TransUnion's parent claim passed 3-0 while its own sector breakdown failed as standalone claims,
  despite those figures appearing inside the passing claim's evidence.
- Razorpay describes Agent Studio agents as launching/production-ready in press while the product
  page says "Get early access" and badges the builder Beta.
- MSME Samadhaan totals dated 14 Aug 2026 appear elsewhere as the 31 Dec 2025 position.

Problems requiring additional research:
- Refund failure/delay rate - the only JOB-2 cell still completely empty.
- Live Agent Studio roster (client-side rendering defeated all fetch attempts).
- Whether NPCI or card-scheme rules impose a settlement day-count the RBI MD does not.
- Direct NPCI monthly AutoPay statistics to replace the 403'd Business Standard source.
- Razorpay engineering blog, RazorpayX product surfaces and the 2026 newsroom - requested and
  unyielding. CORRECTED IN v2.1: the leadership-interview source type DID yield something (Shashank
  Kumar on agent error tolerance, Business Standard 12 Mar 2026), though hard-paywalled at ~1,680
  retrievable characters. v2's blanket "none of the six source types yielded anything" was wrong.

Confidence by problem:
P3  Take-rate compression / zero-MDR ............ 9/10
P4  Merchant fund holds and freezes ............. 8/10
P5  Agentic trust / protocol fragmentation ...... 8/10
P6  Reconciliation exception handling ........... 8/10
P10 Support cost and quality .................... 8/10
P13 Regulatory burden (not RZP-specific) ........ 8/10
P20 COD outside the regulated rail .............. 8/10
P1  UPI AutoPay / e-mandate failure ............. 7/10  (was 9 - source 403s)
P7  Settlement timing (reframed) ................ 7/10  (T+1 framing falsified)
P8  Disputes and chargebacks .................... 7/10
P11 RTO / COD ................................... 7/10  (was 6 - magnitude now exists)
P12 Cross-border ................................ 7/10
P14 IPO / valuation compression ................. 7/10
P18 B2B receivables / collections ............... 7/10  (was 4 - government magnitude found)
P19 Late-authorisation recon exceptions ......... 7/10
P2  Payment success-rate leakage ................ 6/10  (was 9 - internally contested)
P15 Fraud detection coverage .................... 6/10
P16 Checkout abandonment ........................ 6/10
P9  Refund failures ............................. 5/10  (was 7 - primacy contested)
P17 Onboarding friction ......................... 4/10

Overall Phase 1 confidence: 8/10

READY FOR PHASE 2: YES
```

**Why still 8/10 after a falsification and four downgrades.** The falsification *raises* confidence
in the process: a wrong finding was caught against a primary regulator source before it reached a
submission. Six of seven magnitude gaps are now filled, three problems were added, and the two
best-evidenced gaps (P4 fund holds, P6 reconciliation) both improved. It is not 9/10 because the
verification budget covered only 25 of 120 claims, six prioritised Razorpay source types yielded
nothing that survived, and one cell is still empty.

**Why READY: YES.** Phase 2 ranks by financial, strategic, scale and urgency tests, and every
problem now carries either a magnitude or an explicit "no magnitude found" — which is precisely the
input a priority ranking needs. The weak entries (P9, P15, P16, P17) will fail Phase 2's tests on
their own merits.

---

## Implications for track selection

1. **P6 reconciliation is the strongest Track 4 position** — Razorpay supplies the magnitude
   (20–40 hrs/month), admits the process is manual, names the exception class, and its shipped
   answer is a 2022 viewing dashboard. Track 4 is also the least crowded (24 repos vs 88).
2. **P18 B2B receivables is the strongest Track 3 position** — a government-portal magnitude, fresh
   legislation, no Razorpay agent, and near-zero competitor density.
3. **P4 fund holds remains the best pure gap** — but note it is a *risk-operations* problem and may
   read as Track 2 or Open rather than a clean track fit.
4. **P20 (COD outside escrow) and the Agent Studio open-ecosystem note are the two best
   "shows you did the reading" details** for a pitch or panel.
5. **Avoid** AI-readable catalogs, upsell/cross-sell, campaign optimisation and conversational
   commerce unless you bring your own problem evidence — two full research passes found none.

## Sources

RBI Master Direction RBI/DPSS/2025-26/141 (rbi.org.in) · razorpay.com/docs/payments/settlements ·
razorpay.com/blog/agent-studio-ai-agents-by-razorpay · razorpay.com/blog/single-view-recon ·
razorpay.com/blog/what-to-do-when-your-payment-gateway-account-is-frozen ·
razorpay.com/blog/settlement-transparency-the-complete-merchant-playbook… ·
razorpay.com/learn/cart-abandonment-rate-101 · medianama.com (Vulcan, 18 Aug 2026) ·
baymard.com/lists/cart-abandonment-rate · newsroom.transunion.in + business-standard.com
(TransUnion H1 2026) · unicommerce.com/india-d2c-report-2026-april · gokwik.co (RTO) ·
chargeback.io · samadhaan.msme.gov.in + indiagazette.com (MSME/Crisil) · smestreet.in (Recordent) ·
the420.in (NPCI e-mandate) · business-standard.com (UPI AutoPay revocations; Shashank Kumar
interview) · productgrowth.in (UPI success rates) · trustpilot.com · razorpay.pissedconsumer.com ·
voxya.com · xflowpay.com · affairscloud.com (RBI Ombudsman FY25)
