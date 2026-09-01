# economics.md — Phase 8: The Business Metric That Matters

Compiled 2026-08-25 for the strong opportunities in
[agentic_opportunities.md](agentic_opportunities.md).

## Rules applied

**FACT** — sourced, with the source quality named.
**INFERENCE** — derived from facts by stated reasoning.
**ASSUMPTION** — a value I chose because none exists publicly. Always labelled, always a range.

**No invented rupee totals.** Where a monetary figure would require a number nobody publishes, this
file gives **the formula and the missing input** rather than a fabricated total. A formula a merchant
can populate with their own data is more useful — and more defensible in a panel — than a made-up
crore figure.

> ### ⚠️ The honesty constraint that governs this entire phase
>
> **On synthetic data you measure the mechanism, not the market.** A batch run proves your agent
> resolves X% of exceptions or recovers Y% of at-risk value *against a generator you wrote*. It does
> not prove the real-world rate. Every claim below is therefore split into:
>
> - **What the demo can measure** (a rate, on your batch — legitimate)
> - **What the merchant computes** (rate × their own volume — their arithmetic, not your claim)
> - **What you must never assert** (a market-wide rupee total)
>
> A submission that states this distinction explicitly is doing the thing every track bar asks for.
> One that multiplies its demo rate by ₹180bn TPV has disqualified itself on honesty.

---

## A1 — Reconciliation Exception Resolver

**Primary KPI: auto-resolution rate on the exception tail** — the percentage of unmatched settlement
lines the agent resolves correctly without human input.
**Secondary:** match precision (a wrong proposal accepted is the real failure), throughput
(records/min), exception composition, close-readiness time.

| Grade | Statement |
|---|---|
| **FACT** | Razorpay states multi-gateway merchants spend **20–40 work-hours/month** on reconciliation *(Razorpay blog — unaudited vendor figure, no methodology)* |
| **FACT** | Razorpay describes the process as manual: finance teams "download and manually reconcile payments and settlements" |
| **FACT** | Single View Recon (June 2022) is a **viewing** dashboard; no auto-matching or resolution |
| **FACT** | Razorpay names *net-only reporting* and *missing UTRs* as failure modes that make payouts impossible to match |
| **INFERENCE** | Bulk matching on amount/date/UTR is near-trivial; the 20–40 hours is concentrated in the unmatched tail and in cross-period deductions, not in the bulk |
| **ASSUMPTION** | The exception tail is **2–8%** of settlement lines. No source publishes this. Chosen from the general shape of reconciliation problems; **flagged as the weakest input in this section** |

**The economics, as a formula rather than a number:**

```
Hours saved / month  =  H_manual × (share of hours in the tail) × (auto-resolution rate)
₹ saved / month      =  Hours saved × (merchant's fully-loaded analyst cost per hour)
```

`H_manual` = 20–40 **[FACT, unaudited]** · tail share **[ASSUMPTION]** · **auto-resolution rate is
what your demo measures** · analyst cost is the merchant's own number, which you should not supply.

| Scenario | Auto-resolution rate | Hours saved/month (on H=30) | Label |
|---|---|---|---|
| Conservative | 40% of the tail | ~8–10 | ASSUMPTION-driven |
| Central | 60% | ~14–18 | ASSUMPTION-driven |
| Optimistic | 80% | ~19–24 | ASSUMPTION-driven |

**Measurable in a hackathon: ✅ Yes — better than any other opportunity here.** Track 4's build spec
*sanctions synthetic data outright* ("50+ record batch of synthetic data"), so a seeded generator
producing realistic settlement lines with known ground truth gives you exact match rate, exact
precision, and an exact exception list. **This is the only opportunity where the demo metric and the
business metric are almost the same thing.**

**Never claim:** a rupee saving for Razorpay's merchant base, or that 20–40 hours is an audited
figure.

---

## A2 — Headroom-Aware Recovery Sequencer

**Primary KPI: ⭐ incremental ₹ recovered against a holdout** — never gross recovery.
**Secondary:** recovery rate by failure class, cost per recovery attempt, and **chargeback ratio held
below the freeze trigger** (a constraint metric, not an outcome metric).

| Grade | Statement |
|---|---|
| **FACT** | For SBI, the largest remitter bank, **~30% of UPI AutoPay auto-debits are approved — ~70% fail**, predominantly on insufficient funds *(press, re-reported on May-2026 data)* |
| **FACT** | UPI e-mandate volume at the top-ten remitter banks reached **~1.6bn transactions in May 2026**, up from 577M in May 2025 — roughly **3× year on year** *(press, unverified)* |
| **FACT** | Merchant-observed blended UPI success is **92–96%**; failure mix is bank timeout **35–45%**, wrong PIN **20–30%**, insufficient funds **15–25%** *(industry blog)* |
| **FACT** | **Smart retry recovers 20–30% of timeout failures**; in-app UPI SDKs add **2–4 percentage points** *(industry blog, unaudited)* |
| **FACT** | Visa reason code 13.2 "cancelled recurring" is **8.5% of all chargebacks**; Razorpay's freeze trigger is a **>1%** chargeback ratio |
| **INFERENCE** | Absolute failed auto-debits are growing even if the failure *rate* is flat, because the denominator tripled year on year |
| **ASSUMPTION** | ⭐ **The self-cure rate is unknown.** Nobody — not Razorpay, not any sampled competitor repo — publishes what share of failed payments recover with no intervention. This is the single largest uncertainty in recovery economics |

**Why the self-cure gap dominates everything:**

```
Gross recovery       = payments that succeeded after your agent acted
Self-cure            = payments that would have succeeded anyway
Incremental recovery = Gross − Self-cure          ← the only honest number
```

**If self-cure is 40% and you report gross, you have overstated your effect by roughly two-thirds.**
Reporting incremental recovery against a holdout is simultaneously the correct economics, a literal
reading of Track 3's *"measured money recovered across a batch"*, and a differentiator against 88
competing recovery repos.

| Scenario | Incremental lift over no-intervention | Label |
|---|---|---|
| Conservative | Recovery concentrated in timeouts only; most funding failures self-cure | ASSUMPTION |
| Central | Timing-aware retries add materially over fixed-interval retries | ASSUMPTION |
| Optimistic | Timing + rail choice + nudge compound | ASSUMPTION |

I have deliberately **not** attached percentages to these rows. The only defensible number is the
one your holdout produces.

**Measurable in a hackathon: ✅ Yes, with a caveat.** A holdout design on synthetic data measures the
*method* cleanly — but the self-cure process is one you modelled, so the magnitude reflects your
generator's assumptions. **Say this out loud in the video.** It converts a weakness into evidence of
judgement.

**Never claim:** a rupee figure extrapolated to India's e-mandate volume, or gross recovery as if it
were incremental.

---

## A3 — Merchant Freeze Navigator

**Primary KPI: time-to-complete-submission** versus the manual runbook.
**Secondary:** first-submission completeness (rework is the real cost), predicted-trigger accuracy
**including misses**, frozen-capital days modelled.

| Grade | Statement |
|---|---|
| **FACT** | Razorpay publishes resolution bands: **KYC gaps 2–5 business days · chargeback reviews 1–3 weeks · fraud/legal holds 30+ days** |
| **FACT** | Razorpay publishes the four triggers: chargeback ratio >1%, ~10× volume spikes, stale KYC/GST/PAN, PA compliance flags |
| **FACT** | Merchant reviews document a **120-day settlement hold** followed by termination, and **~14 days to reverse a suspension** with a complete appeal (first substantive response on day 3) |
| **FACT** | Razorpay's own remedy is a manual runbook ending at the RBI Ombudsman |
| **FACT** | Razorpay cites **44% of merchants globally** reporting severe cash-flow stress from unexpected holds — *uncited within the source; treat as [D]* |
| **INFERENCE** | Most of the elapsed time in the fastest band (KYC, 2–5 days) is document assembly and rework, not Razorpay's review |
| **ASSUMPTION** | Incomplete first submissions cause **one additional round trip** in a meaningful share of cases. No source quantifies rework |

**The economics, as a formula:**

```
Frozen-capital cost = (held amount) × (days held) × (merchant's cost of capital / 365)
Days saved          = (rework rounds avoided) × (band length)
```

Every input except *days saved* belongs to the merchant. **Days saved is what your demo measures.**

**Measurable in a hackathon: ⚠️ Partially.** You can measure submission completeness and
time-to-assemble against a manual baseline you run yourself. You **cannot** measure whether Razorpay
actually released funds faster — no feedback loop exists. **This is the weakest opportunity on
measurability, and that is a real strike against it** despite its excellent novelty score.

**Never claim:** that the agent shortens Razorpay's review, or that it can determine why an account
was frozen.

---

## A4 — Promise-to-Pay Collections Agent

**Primary KPI: DSO reduction in days** on a batch.
**Secondary:** ₹ collected ÷ ₹ overdue, promise-kept rate, contacts per rupee collected, and —
reported honestly — **opt-outs and complaints**.

| Grade | Statement |
|---|---|
| **FACT** | **MSME Samadhaan: 2,56,892 delayed-payment applications worth ₹55,244 crore, ₹20,979 crore still pending; 40,580 (16%) unresolved beyond a year** *(government portal — but the same totals appear elsewhere as the 31 Dec 2025 position, so treat as cumulative)* |
| **FACT** | Indian SMEs take an average **73 days** to settle invoices against a 45-day statutory norm; the average SME carries **~₹3.83 crore** unpaid beyond 360 days *(Recordent — vendor data, sample self-selects toward businesses with collection problems)* |
| **FACT** | **82.6% of invoices carry 0–30 day terms** — so the 73-day reality is a ~43-day collection-discipline failure, not lax credit policy |
| **FACT** | August 2026 legislation introduced time-bound MSME dispute machinery, implying the 45-day rule was not working |
| **INFERENCE** | Because terms are short and realised payment is long, the addressable gap is *follow-up discipline*, which is exactly what an agent supplies |
| **ASSUMPTION** | Systematic follow-up compresses DSO by some days. **No source quantifies the effect of dunning discipline on Indian SME DSO** |

**Measurable in a hackathon: ✅ Yes** — a synthetic invoice ledger with a modelled payer-response
process gives DSO movement, promise-kept rate and collection curves. Same caveat as A2: **you are
measuring against your own behavioural model.**

**Never claim:** that your agent would recover any portion of the ₹20,979 crore pending. That figure
sizes *the problem*, not your solution.

---

## Cross-cutting: metrics to reject

The protocol's rule — reject vague outcomes — applied:

| ❌ Rejected | ✅ Required instead |
|---|---|
| "Improves user experience" | Time-to-complete-submission, in minutes, versus a manual baseline |
| "Reduces fraud" | Precision and recall on a held-out set **plus false-positive cost in frozen-capital days** |
| "Saves time" | Hours saved = manual hours × tail share × auto-resolution rate, each input named |
| "Recovers revenue" | **Incremental** ₹ recovered against a holdout |
| "Increases conversion" | Conversion delta **and** its RTO cost — the two are opposed (Phase 4, trade-off edge) |
| "Improves cash flow" | Days of frozen capital released, or DSO days compressed |
| "More efficient reconciliation" | Match rate, precision, throughput, exception count |

---

## Ranking on economic strength

| Rank | Opportunity | Primary KPI | Measurable in a hackathon? | Weakest input |
|---|---|---|---|---|
| **1** | **A1 Reconciliation** | Auto-resolution rate on the exception tail | ✅ **Best** — synthetic data is sanctioned by the track spec, ground truth is exact | Tail share (2–8%) is pure ASSUMPTION |
| **2** | **A4 Collections** | DSO days compressed | ✅ Good — government-sourced problem magnitude | Dunning-effect size unquantified anywhere |
| **3** | **A2 Recovery** | Incremental ₹ vs holdout | ✅ Good, with the self-cure caveat stated | Self-cure rate unknown — the largest single uncertainty |
| **4** | **A3 Freeze Navigator** | Time-to-submission | ⚠️ **Partial — no feedback loop exists** | Cannot observe the outcome you care about |

---

```
PHASE 8 VALIDATION

Measurable opportunities: 3   (A1, A2, A4 - each produces a defensible number on a synthetic
                               batch with ground truth you control)
Poorly measurable: 1          (A3 Freeze Navigator - you can measure submission quality and
                               speed, but never whether Razorpay released funds faster. No
                               feedback loop exists, and none can be built from outside)

Primary KPI for each:
  A1 Reconciliation  -> auto-resolution rate on the exception tail (+ match precision)
  A2 Recovery        -> INCREMENTAL rupees recovered against a holdout (never gross)
  A3 Freeze          -> time-to-complete-submission and first-submission completeness
  A4 Collections     -> DSO days compressed (+ promise-kept rate)

Unsupported economic claims - identified and refused:
  - Any rupee total extrapolated from a demo rate to Razorpay's 12M merchants or $180bn TPV.
  - Any claim that an agent recovers a share of the Rs 20,979 crore MSME pending figure. That
    number sizes the PROBLEM, not any solution.
  - Vulcan's 8-10% success lift, 8x fraud detection and 40% UPI-app match as baselines for
    comparison. Confirmed unaudited vendor self-report with no published methodology, baseline
    or sample period; MediaNama asked Razorpay directly and received nothing.
  - Razorpay's "44% of merchants report severe cash-flow stress" - uncited within its own
    source, so it may be used as colour but not as a load-bearing input.
  - Gross recovery presented as if it were incremental. This is the most likely honest-looking
    error in the entire competitive field.

Assumptions, stated:
  A1 - exception tail is 2-8% of settlement lines. NO SOURCE. Weakest input in this file.
  A2 - self-cure rate is unknown. Largest single uncertainty in recovery economics anywhere
       in this research.
  A3 - incomplete first submissions cause one extra round trip in a meaningful share of cases.
       Unquantified.
  A4 - systematic follow-up compresses DSO by some number of days. Unquantified for India.
  All four - the merchant's cost of capital and analyst cost are deliberately NOT supplied.
       Formulas are given so a merchant substitutes their own.

The governing caveat:
  On synthetic data you measure the MECHANISM, not the MARKET. Every rate below is measured
  against a generator we wrote. Stating this explicitly is required, not optional - and it is
  itself evidence of the judgement the track bars are testing for.

Confidence: 8/10

READY FOR PHASE 9: YES
```

**Why 8/10.** Every headline magnitude traces to a named source with its quality declared, four
assumptions are isolated and labelled rather than buried in a total, and five categories of
unsupported claim were identified and refused — including two I could easily have used. It is not
9/10 because the two most decision-relevant inputs (the exception tail share for A1, the self-cure
rate for A2) have **no public source at all**, and both sit directly under the primary KPI of the
top two opportunities.

---

## What to do about the two missing inputs

Neither gap blocks a build, and both convert into a strength if handled openly:

- **A1's tail share:** measure it on your own generator and state it as a parameter, not a finding.
  *"At a 5% exception rate the agent resolves 62% of the tail; the curve across 2–10% is in the
  README."* A sensitivity curve is a stronger artefact than a point estimate.
- **A2's self-cure rate:** make it the experiment. Run the holdout, report the self-cure rate **you
  observed on your data**, and present incremental recovery. You will be one of very few submissions
  that even acknowledges the problem exists.
