# problems_priority.md — Phase 2: Research-Derived Priority Ranking

Compiled 2026-08-25. Scores every problem in [problems.md](problems.md) (v2.1) across the ten
Phase-2 criteria.

> ## ⚠️ These are NOT Razorpay's priorities
>
> **Razorpay publishes no P0/P1/P2 ranking for any of these problems, and nothing in this file was
> obtained from Razorpay.** Every score below is **research-derived** — my judgement applied to the
> evidence base in `problems.md`, using a stated formula so you can disagree with any individual
> number and recompute. Do not present these labels as Razorpay's own assessment in any submission,
> pitch or interview. The correct phrasing is *"on our own scoring of public evidence…"*.

---

## 1. Scoring methodology

### 1.1 The ten criteria

Each problem is scored **1–10** on each criterion. Anchors are fixed so scores mean the same thing
across problems:

| # | Criterion | 1–3 | 4–6 | 7–8 | 9–10 |
|---|---|---|---|---|---|
| 1 | **Direct financial impact** | Indirect/soft cost | Measurable cost, modest | Large quantified loss | Existential to P&L |
| 2 | **Merchants/customers affected** | Niche segment | A vertical or tier | Most merchants | Every merchant + consumers |
| 3 | **Strategic importance to Razorpay** | Peripheral | Adjacent to strategy | Named in product strategy | Core to company direction |
| 4 | **Frequency of occurrence** | Rare/episodic | Periodic | Weekly–daily | Continuous, every transaction |
| 5 | **Operational cost** | Little manual work | Some ops load | Heavy manual labour | Dedicated teams |
| 6 | **Revenue upside** | Cost saving only | Retention | Recoverable revenue | New revenue line |
| 7 | **Regulatory / risk importance** | No regulatory angle | Indirect | Named in RBI/NPCI rules | Licence or legislative exposure |
| 8 | **Razorpay's current investment/activity** | Nothing shipped | Blog/docs only | A shipped product | Multiple products + exec airtime |
| 9 | **AI suitability** | Rules engine suffices | ML classification | Multi-step reasoning + tools | Genuinely agentic: plan, act, handle exceptions |
| 10 | **Buildathon relevance** | Not a track fit | Loose fit | Named track direction | Named direction + room left to build |

### 1.2 Weights, and why

An unweighted mean would treat *AI suitability* as equal in importance to *direct financial impact*,
which is wrong for a priority ranking. Weights:

| Criterion | Weight | Rationale |
|---|---|---|
| 1 Direct financial impact | **15%** | Money lost or recovered is the primary definition of priority |
| 3 Strategic importance | **15%** | What Razorpay is actually steering toward |
| 2 Merchants affected | **10%** | Scale multiplies impact |
| 6 Revenue upside | **10%** | Upside is weighted alongside loss-prevention |
| 9 AI suitability | **10%** | Determines whether the problem is addressable at all by this kind of work |
| 10 Buildathon relevance | **10%** | This ranking exists to support a build decision |
| 4 Frequency | **8%** | Recurrence compounds magnitude |
| 7 Regulatory/risk | **8%** | Regulatory exposure forces action regardless of ROI |
| 5 Operational cost | **7%** | Real but usually smaller than revenue effects |
| 8 Razorpay's investment | **7%** | Strong *signal* of priority, but partly redundant with #3 |

**Overall score = Σ(criterion × weight) ÷ 100.** Both weighted and unweighted means are published
below so you can see where weighting changed a classification. It changed exactly two: **P2 rises to
P0** and **P18 rises to P1**.

### 1.3 Classification bands

| Band | Score | Meaning |
|---|---|---|
| 🔴 **P0** | ≥ 8.0 | Extremely important — large, current, strategically central |
| 🟠 **P1** | 7.0 – 7.9 | Highly important |
| 🟡 **P2** | 5.5 – 6.9 | Meaningful but lower priority |
| ⚪ **P3** | < 5.5 | Weak or indirect |

### 1.4 The two things this score deliberately does NOT do

**It does not blend in evidence quality.** A problem can score highly on a magnitude that is
unverified. Blending confidence into the score would hide that, so **evidence confidence is carried
as a separate column** (inherited from `problems.md`). Read the two together: *a high score on
weak evidence is a research task, not a conclusion.*

**Criterion 8 is a priority signal, not a buildability signal.** Heavy Razorpay investment means the
problem matters — *and* that there is less room for you. Those pull in opposite directions.
Criterion 8 captures only the first; the second is handled separately in §4.

---

## 2. Full score matrix

Criteria in column order: 1 financial · 2 affected · 3 strategic · 4 frequency · 5 op-cost ·
6 revenue · 7 regulatory · 8 RZP investment · 9 AI fit · 10 buildathon.

| Problem | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | **Wtd** | Unwtd | Class | Evid |
|---|--|--|--|--|--|--|--|--|--|--|---|---|---|---|
| **P1** UPI AutoPay / e-mandate failure | 9 | 9 | 8 | 10 | 7 | 9 | 7 | 8 | 8 | 8 | **8.36** | 8.30 | 🔴 P0 | 7/10 |
| **P2** Payment success-rate leakage | 9 | 10 | 9 | 10 | 6 | 9 | 5 | 10 | 7 | 4 | **8.02** | 7.90 | 🔴 P0 | 6/10 |
| **P5** Agentic commerce trust & liability | 6 | 7 | 10 | 3 | 4 | 9 | 9 | 9 | 9 | 8 | **7.57** | 7.40 | 🟠 P1 | 8/10 |
| **P3** Take-rate compression (zero-MDR) | 10 | 10 | 10 | 10 | 5 | 10 | 9 | 6 | 1 | 1 | **7.49** | 7.20 | 🟠 P1 | 9/10 |
| **P8** Disputes & chargebacks | 8 | 7 | 8 | 6 | 8 | 6 | 8 | 8 | 9 | 5 | **7.34** | 7.30 | 🟠 P1 | 7/10 |
| **P6** Reconciliation exception handling | 7 | 8 | 6 | 9 | 9 | 4 | 6 | 4 | 9 | 10 | **7.16** | 7.20 | 🟠 P1 | 8/10 |
| **P18** B2B receivables / collections | 8 | 7 | 5 | 8 | 6 | 8 | 6 | 3 | 9 | 9 | **7.00** | 6.90 | 🟠 P1 | 7/10 |
| **P4** Merchant fund holds / freezes | 8 | 6 | 6 | 6 | 8 | 5 | 9 | 3 | 8 | 9 | **6.87** | 6.80 | 🟡 P2 | 8/10 |
| **P11** RTO / COD returns | 8 | 7 | 8 | 8 | 6 | 7 | 4 | 10 | 6 | 3 | **6.78** | 6.70 | 🟡 P2 | 7/10 |
| **P15** Fraud detection coverage | 7 | 7 | 9 | 5 | 6 | 5 | 9 | 10 | 6 | 3 | **6.74** | 6.70 | 🟡 P2 | 6/10 |
| **P16** Checkout abandonment | 8 | 8 | 7 | 10 | 3 | 9 | 2 | 8 | 6 | 4 | **6.68** | 6.50 | 🟡 P2 | 6/10 |
| **P10** Support cost & quality | 5 | 8 | 7 | 9 | 9 | 3 | 5 | 7 | 8 | 5 | **6.44** | 6.60 | 🟡 P2 | 8/10 |
| **P13** Regulatory / compliance burden | 7 | 10 | 8 | 4 | 8 | 2 | 10 | 7 | 3 | 2 | **6.12** | 6.10 | 🟡 P2 | 8/10 |
| **P12** Cross-border | 6 | 4 | 7 | 5 | 4 | 8 | 7 | 7 | 5 | 4 | **5.78** | 5.70 | 🟡 P2 | 7/10 |
| **P7** Settlement timing / working capital | 6 | 9 | 5 | 10 | 4 | 5 | 5 | 6 | 4 | 3 | **5.65** | 5.70 | 🟡 P2 | 7/10 |
| **P19** Late-authorisation recon exceptions | 5 | 7 | 4 | 8 | 7 | 3 | 5 | 3 | 8 | 7 | **5.59** | 5.70 | 🟡 P2 | 7/10 |
| **P14** IPO / valuation compression | 10 | 1 | 10 | 2 | 3 | 6 | 7 | 8 | 1 | 1 | **5.39** | 4.90 | ⚪ P3 | 7/10 |
| **P9** Refund failures | 5 | 6 | 4 | 5 | 7 | 3 | 6 | 2 | 7 | 7 | **5.16** | 5.20 | ⚪ P3 | 5/10 |
| **P17** Merchant onboarding friction | 4 | 6 | 6 | 4 | 6 | 4 | 6 | 8 | 6 | 2 | **5.08** | 5.20 | ⚪ P3 | 4/10 |
| **P20** COD outside the regulated rail | 6 | 6 | 4 | 7 | 4 | 3 | 9 | 2 | 5 | 4 | **5.00** | 5.00 | ⚪ P3 | 8/10 |

**Distribution:** 🔴 P0 × 2 · 🟠 P1 × 5 · 🟡 P2 × 9 · ⚪ P3 × 4

---

## 3. P0 validation — the four tests

Per the Phase-2 rule, **a P0 must show strong evidence on at least 3 of 4 tests** or be downgraded.

### 🔴 P1 — UPI AutoPay / e-mandate execution failure · **8.36**

| Test | Verdict | Evidence |
|---|---|---|
| **Financial** — prevents loss / recovers money? | ✅ PASS | ~70% of SBI auto-debit executions fail; every failure is unrecognised recurring revenue |
| **Strategic** — is Razorpay investing? | ✅ PASS | Subscription Recovery agent shipped in Agent Studio (voice by ElevenLabs); Vulcan's launch copy names "a subscription that silently lapses" |
| **Scale** — many merchants, large volume? | ✅ PASS | UPI e-mandate volume ~1.6bn transactions/month at the top ten remitter banks (May 2026) |
| **Urgency** — current, recurring, growing? | ✅ PASS | Volume ~3x YoY (577M → 1.6bn); RBI E-Mandate Framework 2026 notified April 2026 |

**4/4 — P0 confirmed.** *Caveat:* the widely cited ">20M monthly revocations" figure rests on a
source that 403s to direct fetch. The SBI ~70% leg survived and was re-reported on May-2026 data.
Evidence confidence 7/10, so cite the SBI figure, not the 20M one.

### 🔴 P2 — Payment success-rate leakage · **8.02**

| Test | Verdict | Evidence |
|---|---|---|
| **Financial** | ✅ PASS | 4–8% of UPI attempts fail against ~$180bn TPV |
| **Strategic** | ✅ PASS | The single most-invested problem: Optimizer (150+ parameters, 600M data points) **and** Vulcan's headline purpose |
| **Scale** | ✅ PASS | Every merchant, every transaction |
| **Urgency** | ✅ PASS | Continuous; Vulcan launched 18 Aug 2026 |

**4/4 — P0 confirmed as a Razorpay priority.** ⚠️ **But see §4: this is simultaneously the worst
buildathon choice in the entire set.** High priority and good project are different questions.

### Near-miss checks

**P3 take-rate compression (7.49)** passes financial, strategic, scale and urgency at maximum — it
would be the #1 P0 on business merit alone. It sits at P1 only because criteria 9 and 10 score 1/10:
it is not an AI problem and resolves in Parliament. **Recorded explicitly so the ranking isn't
mistaken for a claim that Razorpay cares less about it.**

**P4 fund holds (6.87)** lands in P2 despite being the best *gap*, because frequency (6) and revenue
upside (5) are genuinely lower — it is severe for those affected, not universal.

---

## 4. Priority ≠ buildability

The ranking above answers *"what matters most to Razorpay?"* It does **not** answer *"what should
you build?"* — because the more Razorpay has already invested, the less room remains.

**Openness (1–10)** = how much of the problem is still unaddressed, combining Razorpay's shipped
coverage with competitor density from `requirements.md` §4.5.
**Build score = 0.5 × priority + 0.5 × openness.**

| Rank | Problem | Build | Priority | Openness | Evid | Why |
|---|---|---|---|---|---|---|
| 1 | **P6** Reconciliation exceptions | **8.08** | 7.16 | 9 | 8/10 | Razorpay supplies the magnitude (20–40 hrs/mo), admits the process is manual, and its answer is a 2022 *viewing* dashboard. Track 4 is the least crowded (24 repos vs 88) |
| 2 | **P18** B2B receivables | **8.00** | 7.00 | 9 | 7/10 | Government-portal magnitude (₹20,979 cr pending), fresh Aug-2026 legislation, **no Razorpay agent**, ~3–4 competitor repos |
| 3 | **P4** Fund holds / freezes | **7.94** | 6.87 | 9 | 8/10 | Razorpay documents triggers, bands and a wholly manual remedy. No agent. Freeze trigger (>1%) is stricter than Visa VAMP (1.5%) |
| 4 | **P1** UPI AutoPay failure | **7.68** | 8.36 | 7 | 7/10 | Highest priority with real room left — Subscription Recovery doesn't touch retry *timing* against balance availability |
| 5 | P19 Late-auth recon exceptions | 6.79 | 5.59 | 8 | 7/10 | Sub-problem of P6; fold in rather than build separately |
| 6 | P9 Refund failures | 6.58 | 5.16 | 8 | 5/10 | Genuine gap, but the weakest evidence in the set |
| 7 | P5 Agentic commerce | 6.29 | 7.57 | 5 | 8/10 | Strategically central, but Razorpay's flagship *and* ~100 competitor repos |
| … | | | | | | |
| 19 | P2 Payment success-rate | **5.01** | 8.02 | 2 | 6/10 | 🔴 P0 for Razorpay, near-worst to build — you would be competing against Vulcan with public data |
| 20 | P14 IPO / valuation | 3.19 | 5.39 | 1 | 7/10 | Not buildable |

**The headline tension:** the two P0s split cleanly. **P1 (AutoPay) is high priority *and* buildable
— it is the only problem in the top 4 of both lists.** **P2 (payment success) is high priority and
nearly unbuildable.** A submission that "improves payment success rates" is picking a fight with a
foundation model trained on ~4 billion transactions a year.

---

```
PHASE 2 VALIDATION

P0 problems:
  P1  UPI AutoPay / e-mandate execution failure ....... 8.36  (4/4 tests passed)
  P2  Payment success-rate leakage .................... 8.02  (4/4 tests passed)

P1 problems:
  P5  Agentic commerce trust & liability .............. 7.57
  P3  Take-rate compression (zero-MDR) ................ 7.49
  P8  Disputes & chargebacks .......................... 7.34
  P6  Reconciliation exception handling ............... 7.16
  P18 B2B receivables / collections ................... 7.00

P2 problems:
  P4 (6.87), P11 (6.78), P15 (6.74), P16 (6.68), P10 (6.44),
  P13 (6.12), P12 (5.78), P7 (5.65), P19 (5.59)

P3 problems:
  P14 (5.39), P9 (5.16), P17 (5.08), P20 (5.00)

Problems downgraded (vs the implicit v1/v2 ordering in problems.md):
  P4  fund holds  9/10 confidence -> P2 priority. Severity is high but frequency and revenue
      upside are not. It remains the best GAP; it is not the biggest PROBLEM.
  P9  refund failures -> P3. Primacy contested three ways and no rate exists anywhere.
  P7  settlement timing -> P2. The T+1 compliance framing was falsified, which removed its
      regulatory weight (criterion 7 fell from ~8 to 5).
  P20 COD-outside-escrow -> P3. A sharp regulator-grounded insight, but it is context for a
      pitch rather than a problem with its own build.

Problems upgraded:
  P18 B2B receivables -> P1 (was the weakest problem in v1 at 4/10 confidence). The MSME
      Samadhaan and Recordent magnitudes plus August 2026 legislation moved it decisively.
  P6  reconciliation -> P1 and #1 on build attractiveness, on Razorpay's own 20-40 hrs/month
      figure and the discovery that Single View Recon only VIEWS.
  P1  AutoPay -> the top-ranked problem overall, on the ~1.6bn/month e-mandate denominator.

Why:
  The upgrades all come from magnitudes discovered in the v2 pass that did not exist in v1.
  The downgrades all come from evidence being contested, falsified, or found to be severity
  without scale. No score moved on opinion alone.

Biggest uncertainty in our ranking:
  Criterion 8 (Razorpay's current investment) is measured from marketing surfaces, because
  that is all Razorpay publishes. If Agent Studio's roster has grown since the 12 Mar 2026
  launch blog - and Razorpay has said it will open to third-party builders - then openness
  scores for P4, P9 and P18 are overstated and their build ranking falls. The live product
  page is client-side rendered and defeated every fetch attempt, so this is unresolved.

  Second: five of the ten criteria (3, 5, 8, 9, 10) are judgement calls with no public
  measurement behind them. They carry 49% of the total weight. A reasonable person could
  move any single problem by roughly +/-1.0 points, which is enough to cross one band
  boundary but not two.

Confidence: 8/10

READY FOR PHASE 3: YES
```

**Why 8/10.** The band assignments are stable: re-running with equal weights moved only two problems
by one band each (P2 and P18), and both are documented above. Scores rest on the `problems.md`
evidence base, whose own confidence is carried per-row. It is not 9/10 because half the criterion
weight is judgement rather than measurement, and because criterion 8 depends on a product roster I
could not verify as current.

**Why READY: YES.** Phase 3 maps problems to buildathon tracks, and every problem now carries both a
priority score and a buildathon-relevance sub-score, which is the input that mapping needs.

---

## 5. What this implies

1. **P1 (UPI AutoPay) is the standout** — the only problem in the top four of *both* the priority
   and buildability rankings. Highest priority overall, with real room left, because Subscription
   Recovery attacks retry logic while the actual failure is funding *timing*.
2. **P6 (reconciliation) is the safest high-yield choice** — #1 on buildability, Razorpay-supplied
   magnitude, and the least crowded track.
3. **P18 (B2B receivables) is the biggest mover** — from the weakest problem in v1 to P1, and the
   only one with a government-sourced magnitude and no Razorpay agent.
4. **Avoid P2, P11, P15, P16** despite respectable priority scores. Each is a problem Razorpay has
   already attacked with a shipped product or a foundation model.
5. **P3 and P14 are pitch context, not projects.** Cite them to show you understand why Razorpay is
   investing in agents; do not propose to solve them.

---

# 6. Current methods, roads not taken, and why

> **Epistemic warning — read this first.** Section 6 is the **most inferential** part of this entire
> research corpus. *What Razorpay currently does* is evidence-grounded and cited. ***Why* Razorpay
> chose not to do something else is almost never published.** Every "why they didn't" reason below
> is a **reasoned hypothesis**, not a finding. They are tagged:
>
> - **[HARD]** — a structural constraint with evidence behind it (regulation, escrow rules, data
>   access, counterparty control). Very likely a real blocker.
> - **[SOFT]** — a commercial, organisational or prioritisation reason. Plausible, unverifiable, and
>   **the kind of constraint that does not bind a hackathon submission.**
>
> Never assert any of these to Razorpay as fact. Phrase them as questions — *"I assumed you didn't
> do X because of Y; is that right?"* — which is a far stronger move in a panel anyway.

## 6.1 The constraint taxonomy — why big companies leave obvious things unbuilt

The same ten reasons recur across all twenty problems. Naming them once beats repeating them.

| # | Constraint | Type | What it means |
|---|---|---|---|
| **C1** | **Regulatory/licensing bar** | HARD | RBI PA Directions, escrow rules, KYC/CKYCR, AML. Razorpay's licence is the company; nothing that risks it gets shipped |
| **C2** | **Liability transfer** | HARD | The moment Razorpay *asserts* an outcome (this match is correct, this order is safe, this refund is due), it owns the consequence of being wrong |
| **C3** | **Counterparty control** | HARD | Banks, NPCI and card networks own the failure. Razorpay can route around them, not fix them |
| **C4** | **Data access** | HARD | The signal needed sits with the merchant or the bank. Delivery data coverage is below 100%; account balance is invisible pre-debit |
| **C5** | **Tipping-off / evasion** | HARD | Explaining a risk decision in detail teaches bad actors to evade it. AML rules can also *prohibit* disclosure |
| **C6** | **Commercial incentive conflict** | SOFT | Fixing it free cannibalises something Razorpay sells (Instant Settlements) |
| **C7** | **Zero-MDR unit economics** | SOFT→HARD | At 0% on UPI and ~2% on cards, per-merchant handholding across 12M+ merchants is unfundable |
| **C8** | **Blast radius** | SOFT | At ~4bn payments/year, an autonomous bug is a national incident. Prefer "surface it to a human" over "act" |
| **C9** | **Merchant adoption cost** | SOFT | Requires merchants to integrate, share data or change behaviour. Adoption, not engineering, is the bottleneck |
| **C10** | **Precedent and fairness at scale** | SOFT | A bespoke exception for one merchant becomes an obligation to 12 million |

### ⭐ The payoff — and it is the whole reason this section exists

**C6, C7, C8, C9 and C10 do not bind you.** You have no P&L to cannibalise, no 12M merchants to be
fair to, no licence at risk, and a demo blast radius of zero. **A workaround Razorpay rationally
declined for a SOFT reason is precisely the project you should build** — it is genuinely valuable,
visibly unbuilt, and you can explain *why* it is unbuilt without implying Razorpay is stupid.

Conversely, **a workaround blocked by C1–C5 is a trap.** You will build a demo that could never
ship, and the first panel question will expose it.

---

## 6.2 🔴 P1 — UPI AutoPay / e-mandate execution failure

**Current method [A]:** *Subscription Recovery* agent in Agent Studio (early access) — "analyses
failed subscription payments, applies smarter retry logic, triggers targeted customer nudges", with
voice by ElevenLabs. Plus standard mandate APIs and registration links. **That is retry logic after
the fact. Nothing addresses when the money will actually be there.**

### W1.1 — Balance-aware debit scheduling (predict *when* funds land, then debit)
**Could have, because:** (1) Razorpay already sees historical success/failure timing per customer
across merchants; (2) Indian salary credits cluster on predictable dates (1st–7th); (3) the RBI 2026
framework's mandatory 24h pre-debit notification creates a natural scheduling window; (4) mandate
execution date is merchant-configurable within the mandate terms; (5) it converts a ~70% failure
rate into a timing problem, which is tractable.
**Didn't, plausibly because:** (1) **[HARD, C4]** Razorpay cannot see the customer's bank balance —
UPI gives no balance-inquiry to a PSP for a third-party mandate; (2) **[HARD, C3]** the debit is
executed by the remitter bank on NPCI's schedule, not Razorpay's; (3) **[HARD, C1]** mandate terms
(amount, frequency, date) are fixed at registration and altering them requires fresh AFA; (4)
**[SOFT, C8]** mis-timing a debit for millions of mandates creates mass duplicate-debit risk; (5)
**[SOFT, C9]** merchants own the billing calendar and resist Razorpay moving their revenue
recognition dates.

### W1.2 — Cross-rail fallback ladder (UPI mandate → card → netbanking → payment link)
**Could have:** (1) Razorpay owns every one of those rails already; (2) Optimizer proves it can route
across 100+ providers; (3) recovering a subscription is worth far more than the MDR on the retry;
(4) tokenised cards are already on file for many subscribers; (5) it needs no new regulation — each
rail is separately mandated.
**Didn't:** (1) **[HARD, C1]** each rail requires its *own* mandate with its own AFA — a UPI AutoPay
consent does not authorise a card debit; (2) **[HARD, C1]** RBI's 2026 framework requires
pre-transaction notification per mandate, so a silent fallback is non-compliant; (3) **[HARD, C2]**
debiting a rail the customer didn't authorise for that purpose is an unauthorised transaction; (4)
**[SOFT, C9]** merchants would need to register duplicate mandates, doubling onboarding friction;
(5) **[SOFT]** consumer-harm optics — the PissedConsumer corpus already contains "cutting money
without my permission" complaints.

### W1.3 — Partial / split collection (take what's available now, the rest later)
**Could have:** (1) something beats nothing on a failed EMI or SIP; (2) lenders already do partial
recovery; (3) reduces mandate revocation, which is the expensive outcome; (4) UPI supports
variable-amount mandates up to a cap; (5) directly attacks the stated cause (insufficient funds).
**Didn't:** (1) **[HARD, C1]** variable-amount mandates cap the *maximum*; a partial debit against a
fixed-amount mandate breaches its terms; (2) **[HARD, C2]** partial payment against an invoice
creates accounting and legal ambiguity about whether the obligation is discharged; (3) **[HARD, C3]**
NPCI's mandate execution is all-or-nothing; (4) **[SOFT, C9]** merchants' billing systems generally
cannot represent a part-paid subscription; (5) **[SOFT]** multiple partial debits multiply
notification obligations and support contacts.

### W1.4 — Mandate health score, surfaced to the merchant at registration
**Could have:** (1) Razorpay has cross-merchant history on the same VPAs; (2) it is a pure
prediction problem with clean labels; (3) it needs no new consent, being an aggregate merchant
insight; (4) mirrors RTO Shield's pre-dispatch scoring exactly; (5) it lets merchants ask for a
different rail *before* failure rather than dunning after.
**Didn't:** (1) **[HARD, C4]** cross-merchant behavioural scoring of consumers raises DPDP Act
purpose-limitation issues; (2) **[HARD, C5]** exposing "this customer will fail" invites merchants
to deny service, creating discrimination exposure; (3) **[SOFT, C10]** a wrong score that costs a
merchant a legitimate customer is a support and trust problem across 12M merchants; (4)
**[SOFT, C7]** subscriptions are a minority of TPV — the modelling spend competes with Vulcan's
routing work; (5) **[SOFT]** it makes Razorpay visibly responsible for a signal it cannot guarantee.

### W1.5 — Consumer-side top-up nudge inside the 24h notification window
**Could have:** (1) RBI *mandates* a 24h pre-debit notification, so the touchpoint already exists and
is free; (2) the failure cause is literally an empty account; (3) Razorpay has UPI consumer
distribution via the POP acquisition; (4) a UPI collect request to top up is one API call; (5) it
turns a compliance obligation into a recovery channel.
**Didn't:** (1) **[HARD, C3]** the notification is sent by the *issuer bank*, not by Razorpay or the
merchant — Razorpay does not control that message; (2) **[HARD, C1]** the notification's contents are
prescribed and must carry an opt-out; (3) **[HARD, C4]** Razorpay does not know the customer is short
until the debit fails; (4) **[SOFT]** nudging a consumer to move money to cover a debit edges toward
credit-like behaviour; (5) **[SOFT, C9]** merchants own the customer relationship and guard it.

> **Where the gap is:** W1.1 and W1.4 are blocked mainly by **C4 (no balance visibility)** — but a
> *predictive* approach never needs the balance. It needs failure history, which Razorpay has and a
> student can synthesise. **The buildable project is a retry *sequencer* that learns per-customer
> timing from failure history, not a balance checker.** That is exactly the buildathon's own
> "mandate retry sequencer" example direction, and only ~4–6 competitor repos are on it.

---

## 6.3 🔴 P2 — Payment success-rate leakage

**Current method [A]:** Optimizer (ML routing across 100+ providers, 150+ parameters, 600M data
points, bank downtime as an input) and **Vulcan** (foundation model; routing, fraud, conversion;
claimed 8–10% success lift, unaudited).

### W2.1 — Publish per-bank real-time health, and let merchants route on it
**Could have:** (1) Razorpay sees bank downtime across the whole network; (2) NPCI already publishes
TD/BD/uptime data; (3) it would build enormous developer goodwill; (4) transparency pressures banks
to improve; (5) it is a differentiator no competitor offers.
**Didn't:** (1) **[HARD, C3]** publicly naming underperforming partner banks damages the commercial
relationships Razorpay depends on; (2) **[HARD, C1]** NPCI and RBI govern what network performance
data may be published; (3) **[HARD, C2]** a "bank is down" signal that is wrong causes merchants to
misroute and lose money; (4) **[SOFT]** it exposes Razorpay's own comparative performance; (5)
**[SOFT, C6]** routing intelligence *is* the Optimizer product — giving it away is cannibalisation.

### W2.2 — Deterministic customer-side retry with rail switching at checkout
**Could have:** (1) 35–45% of failures are bank timeouts, which are transient and retryable; (2)
smart retry is documented to recover 20–30% of timeout failures; (3) the customer is still present
at checkout; (4) Magic Checkout already controls that surface; (5) no new consent needed for a fresh
attempt.
**Didn't:** (1) **[HARD, C3]** retrying into a bank that is already timing out worsens congestion —
NPCI penalises aggressive retry behaviour; (2) **[HARD, C2]** double-debit risk when the first
attempt was actually successful but unacknowledged; (3) **[HARD, C1]** retry limits are set by NPCI
circulars, not by the PSP; (4) **[SOFT, C8]** at 4bn payments/year a retry storm is systemic; (5)
**[SOFT]** it inflates attempt counts, which degrades the very success-rate metric being optimised.

### W2.3 — In-app UPI SDK / intent deep-linking as default
**Could have:** (1) documented +2–4 percentage points on success; (2) Vulcan already predicts
preferred UPI app; (3) removes app-switching failure entirely; (4) Razorpay controls the checkout
SDK; (5) mobile is >60% of Indian traffic.
**Didn't:** (1) **[HARD, C9]** requires merchants to upgrade their SDK — a long tail that never
updates; (2) **[HARD, C3]** deep-link behaviour is controlled by the UPI apps and the OS; (3)
**[SOFT, C7]** integration support cost across 12M merchants; (4) **[SOFT]** fragmentation across
Android/iOS versions; (5) **[SOFT]** it is incremental, not a step change, so it loses to Vulcan for
engineering attention.

> **Verdict: do not build here.** Every meaningful workaround is blocked by C1–C3 (NPCI, banks,
> retry rules) — the HARD constraints. This is the trap case: high priority, near-zero room.

---

## 6.4 🟠 P6 — Reconciliation exception handling *(best build candidate)*

**Current method [A]:** *Single View Recon* (Optimizer, shipped **June 2022**) — a consolidated
**viewing** dashboard showing transaction status, UTRs, Settlement IDs and processing aggregator.
*Settlement Insights* (Agent Studio) sends a **daily WhatsApp summary**. `fetch_settlement_recon_details`
exposes the report via API. **Razorpay states merchants still spend 20–40 work-hours/month
reconciling, downloading files from each aggregator and matching by hand.**

### W6.1 — Automated matching engine that *resolves* rather than displays
**Could have:** (1) Razorpay holds both sides of the data for its own rail; (2) fuzzy matching on
amount/date/UTR is a solved engineering problem; (3) it already itemises the 11 fields needed
(MDR, GST on MDR, refund offsets, chargeback deductions, net settled, UTR); (4) it would make
Optimizer far stickier; (5) four years have passed since Single View Recon shipped.
**Didn't:** (1) ⭐ **[HARD, C2]** **an asserted match writes into the merchant's statutory books.**
If Razorpay says "these reconcile" and they don't, it has contaminated an audited financial
statement — that is a categorically different liability from showing data and letting the merchant
decide. *This single reason best explains why a viewer shipped instead of a resolver;* (2)
**[HARD, C4]** the other side of a multi-gateway reconciliation is a **competitor's** settlement
file, in a format Razorpay neither controls nor is entitled to normalise; (3) **[HARD, C1]** GST
input-credit and TDS treatment vary by merchant and state — a generic engine would produce tax-wrong
results; (4) **[SOFT, C6]** reconciliation is a cost centre, not a revenue line; (5) **[SOFT, C10]**
every merchant's chart of accounts differs, so "correct" is merchant-specific.

### W6.2 — Late-authorisation exception queue with automated follow-up
**Could have:** (1) Razorpay documents late authorisation as a named exception class (status
finalises minutes-to-hours late); (2) it knows exactly which transactions are pending; (3) it could
simply hold and re-emit a corrected line; (4) webhooks already exist for status change; (5) it
removes the "re-check before books balance" loop Razorpay itself describes.
**Didn't:** (1) **[HARD, C3]** the delay originates at the bank/issuer, so the finalisation time is
not Razorpay's to promise; (2) **[HARD, C2]** re-emitting a corrected financial line implies a
guarantee of finality; (3) **[SOFT, C9]** merchants' ERPs would need to consume amendments, which
most cannot; (4) **[SOFT]** it exposes how often status is provisional; (5) **[SOFT, C7]** low
visibility means low internal priority relative to Vulcan.

### W6.3 — Publish an open multi-gateway reconciliation schema
**Could have:** (1) Razorpay is the market leader and could set the standard; (2) it already defines
the 11 fields; (3) standards work builds developer mindshare; (4) it would make Optimizer the
natural hub; (5) merchants overwhelmingly run multiple PSPs.
**Didn't:** (1) **[HARD]** it requires competitors to adopt it — no unilateral path; (2)
**[SOFT, C6]** normalising competitors' data reduces switching costs *away* from Razorpay; (3)
**[HARD, C1]** any industry-wide standard-setting among competitors invites CCI scrutiny; (4)
**[SOFT]** standards take years and produce no quarterly revenue; (5) **[SOFT]** NPCI/RBI would be
the natural convenor, not a private PA.

### W6.4 — Direct bank-statement ingestion via Account Aggregator
**Could have:** (1) the AA framework exists and is regulated; (2) it closes the loop from settlement
to actual bank credit; (3) Razorpay already knows the UTR to match against; (4) it would eliminate
the biggest manual step; (5) it complements RazorpayX current accounts.
**Didn't:** (1) **[HARD, C1]** AA consent architecture for business accounts is thinner than for
individuals and consent must be per-merchant, per-purpose; (2) **[HARD, C1]** ingesting full bank
statements pulls Razorpay into a much larger data-protection perimeter under DPDP; (3)
**[HARD, C4]** merchants bank across dozens of institutions with uneven AA coverage; (4)
**[SOFT, C9]** merchant consent friction; (5) **[SOFT]** it competes with RazorpayX's own account
proposition.

> **Where the gap is:** C2 (audit liability) explains the *viewer*, and it constrains Razorpay far
> more than it constrains you. **A student agent that proposes matches with confidence scores,
> escalates an honest exception list, and never asserts finality sidesteps the exact liability that
> stopped Razorpay** — and it matches Track 4's bar (match rate + throughput + honest exception
> list) almost word for word.

---

## 6.5 🟡 P4 — Merchant fund holds and freezes *(best pure gap)*

**Current method [A]:** No product. Razorpay's published remedy is **entirely manual**: raise a
support ticket, request the reason in writing, assemble documents, escalate to a named risk contact,
and if unresolved **file an RBI Ombudsman complaint**. Its other advice is to *negotiate hold
triggers into the gateway contract*. Resolution bands: 2–5 days (KYC), 1–3 weeks (chargeback), 30+
days (fraud/legal). Its freeze trigger (>1% chargebacks) is **stricter than Visa VAMP (1.5%)**.

### W4.1 — Graduated/partial holds (withhold only the at-risk exposure)
**Could have:** (1) exposure is calculable — chargeback ratio × volume × window; (2) it preserves
merchant solvency and therefore Razorpay's revenue; (3) card networks already think in rolling
reserves; (4) it is strictly less blunt than a total freeze; (5) it would defuse the loudest
complaint category in the review corpus.
**Didn't:** (1) **[HARD, C1]** during an AML/fraud investigation the regulatory expectation is to
freeze, not to meter; (2) **[HARD, C2]** releasing 80% of funds from an account later proven
fraudulent means Razorpay eats the loss; (3) **[HARD, C5]** a partial hold signals the threshold and
teaches structuring beneath it; (4) **[SOFT, C10]** any published formula becomes a negotiating
position for 12M merchants; (5) **[SOFT, C8]** a mis-set parameter releases funds at scale.

### W4.2 — Transparent reason codes and a countdown timer in the dashboard
**Could have:** (1) it is the single most-requested thing in the complaint corpus; (2) Razorpay
already knows the trigger and the band; (3) it would collapse support volume; (4) it costs almost
nothing to build; (5) settlement holds are *already* a first-class state in the dashboard.
**Didn't:** (1) ⭐ **[HARD, C5]** **AML/PMLA "tipping off" — a regulated entity often may not tell a
customer they are under suspicion, let alone why.** This is the strongest single explanation for the
opacity merchants experience, and it is not a UX failure; (2) **[HARD, C5]** publishing exact
triggers is an evasion manual; (3) **[HARD, C2]** a stated reason becomes a legal admission if the
freeze is later challenged; (4) **[SOFT]** a countdown implies an SLA Razorpay cannot honour when a
bank or law-enforcement request is in the loop; (5) **[SOFT, C10]** disclosure precedent.

### W4.3 — Pre-emptive warning before a threshold is breached
**Could have:** (1) chargeback ratio is observable in real time; (2) Razorpay recommends merchants
self-monitor at 0.5% — so it clearly believes early warning helps; (3) it converts a freeze into a
correction; (4) legitimate merchants would fix the underlying issue; (5) it needs no reason-code
disclosure at all, only a metric.
**Didn't:** (1) **[HARD, C5]** warning a fraudulent merchant lets them cash out before the freeze;
(2) **[SOFT, C2]** a warning implies that absence of warning means safety; (3) **[SOFT, C10]** it
creates an expectation of warning in every case, including those where law prohibits it; (4)
**[SOFT]** thresholds are dynamic and risk-model-driven, so a "warning" would be noisy; (5)
**[SOFT, C7]** proactive merchant risk-coaching does not scale at 12M merchants.

### W4.4 — Self-serve document upload with automated verification
**Could have:** (1) KYC gaps are the *fastest* band (2–5 days), i.e. mostly document-shuffling; (2)
CKYCR retrieval is now mandated at onboarding anyway; (3) OCR/validation of GST and PAN is
commodity; (4) it removes the ticket round-trip entirely; (5) it is the least risk-sensitive of the
four triggers.
**Didn't:** (1) **[HARD, C1]** KYC verification carries personal regulatory liability for the
compliance officer — automation is scrutinised; (2) **[HARD, C2]** an automated accept of forged
documents is an onboarding failure with licence consequences; (3) **[SOFT, C9]** long-tail merchants
submit poor-quality scans; (4) **[SOFT]** it partially exists inside onboarding but was not extended
to remediation; (5) **[SOFT, C7]** engineering attention went to onboarding acquisition, not
remediation.

### W4.5 — Hold insurance / bridge financing during a freeze
**Could have:** (1) Razorpay Capital already lends to merchants; (2) it directly answers the
cash-flow stress; (3) it turns a cost centre into a revenue line; (4) exposure is collateralised by
the held funds themselves; (5) 44% of merchants report severe cash-flow stress from holds.
**Didn't:** (1) **[HARD, C1]** lending against funds frozen for suspected fraud is close to
facilitating the suspected activity; (2) **[HARD, C1]** RBI would view financing one's own escrow
holds poorly; (3) **[HARD, C2]** it creates an incentive conflict in Razorpay's own risk decisions;
(4) **[SOFT]** balance-sheet intensity; (5) **[SOFT]** reputationally grotesque — charging interest
to unfreeze a merchant's own money.

> **Where the gap is:** the *risk decision* is HARD-blocked (C1, C5). **The merchant's side of it is
> not.** A "hold navigator" that assembles the required document pack, tracks the case against the
> published bands, drafts the written-reason request and the Ombudsman escalation, and tells the
> merchant what to expect **never touches Razorpay's risk logic** — and every reason Razorpay didn't
> build it is a reason about *Razorpay's* position, not about the merchant's need.

---

## 6.6 🟠 P18 — B2B receivables and collections

**Current method [A]:** **None.** "Following up on unpaid invoices until they're paid" appears in
Agent Studio's "what others are automating" list — an aspiration, not a product. RazorpayX and
Invoices handle issuance, not collection.

### W18.1 — Automated dunning/collections agent for merchants
**Could have:** (1) Razorpay already sends payment links, SMS, email and WhatsApp; (2) it knows
which invoices are unpaid; (3) MSME Samadhaan shows ₹20,979 cr in pending claims; (4) collections is
the natural extension of Invoices; (5) Track 3's own example directions name "B2B receivables
chaser" and "promise-to-pay tracker".
**Didn't:** (1) ⭐ **[HARD, C1]** **debt collection in India is regulated conduct** — RBI's recovery-
agent guidelines, harassment prohibitions, and time-of-contact restrictions create real legal
exposure for automated chasing; (2) **[HARD, C3]** the debtor is the *merchant's* customer, with no
relationship or leverage of Razorpay's own; (3) **[HARD, C2]** an over-aggressive automated message
sent in Razorpay's name is a reputational and legal event; (4) **[SOFT, C7]** collections is
high-touch and cannot be funded at payment-processing margins; (5) **[SOFT]** it drags a neutral
infrastructure provider into adversarial commercial disputes between its own customers.

### W18.2 — Invoice financing / factoring via Razorpay Capital
**Could have:** (1) Capital exists and already underwrites merchants; (2) receivables are
self-collateralising; (3) it solves cash flow immediately rather than chasing; (4) Razorpay sees the
transaction history that underwrites it; (5) TReDS proves the model works in India.
**Didn't:** (1) **[HARD, C1]** factoring requires specific licensing and NBFC structure; (2)
**[HARD, C4]** underwriting requires the *buyer's* credit quality, which Razorpay cannot see; (3)
**[SOFT]** balance-sheet intensity ahead of an IPO with a ₹1,209 cr FY25 loss; (4) **[SOFT, C2]**
credit losses land on Razorpay, not the merchant; (5) **[SOFT]** TReDS already occupies the
regulated version of this niche.

### W18.3 — Buyer credit scoring / payment-behaviour network
**Could have:** (1) Razorpay sees payment behaviour across 12M merchants; (2) it would price and
prevent, not chase; (3) Recordent shows demand for exactly this; (4) it is a data-network effect
only an aggregator can build; (5) it needs no collections conduct at all.
**Didn't:** (1) **[HARD, C1]** credit information sharing is CIC-regulated territory (CICRA); (2)
**[HARD, C1]** DPDP purpose limitation on repurposing transaction data into credit assessment; (3)
**[HARD, C5]** a "this buyer pays late" score is defamatory if wrong; (4) **[SOFT, C10]** merchants
would object to their own payment behaviour being scored and shared; (5) **[SOFT]** it makes
Razorpay a credit bureau, which is a different regulated business.

### W18.4 — Escrow-backed B2B terms (funds held until delivery/acceptance)
**Could have:** (1) Razorpay operates escrow infrastructure already; (2) it removes the trust gap
that causes late payment; (3) Escrow+ is an existing RazorpayX product; (4) it fits marketplace
flows via Route; (5) it prevents the dispute rather than resolving it.
**Didn't:** (1) **[HARD, C1]** PA escrow accounts are ring-fenced for payment settlement — RBI
prohibits general commercial use, and **explicitly bars COD from escrow**; (2) **[HARD, C2]**
adjudicating "was delivery acceptable?" makes Razorpay an arbiter; (3) **[SOFT, C9]** both buyer and
seller must adopt it; (4) **[SOFT]** it lengthens the merchant's own cash cycle; (5) **[SOFT, C7]**
B2B terms negotiation is high-touch.

> **Where the gap is:** **C1 blocks Razorpay from *doing* the collecting. It does not block a tool
> that helps the merchant collect.** A promise-to-pay tracker that drafts compliant reminders, tracks
> commitments, escalates through statutory MSME machinery and never sends anything in Razorpay's own
> name avoids every HARD constraint above.

---

## 6.7 🟠 P8 — Disputes and chargebacks

**Current method [A]:** *Dispute Responder* (Agent Studio) — "auto-responds to chargebacks with
optimized evidence to maximise win rates". **No published win-rate, baseline or methodology.**
Thirdwatch for fraud flagging. Merchant reviews still name dispute support as slow as of Aug 2026.

### W8.1 — Assemble evidence at transaction time, not at dispute time
**Could have:** (1) the evidence (device, IP, AVS, delivery, comms) exists at authorisation and
decays afterwards; (2) it converts a scramble into a lookup; (3) Razorpay already stores much of it;
(4) representment deadlines are tight, so pre-assembly is decisive; (5) up to 40% of disputes are
avoidable, by Razorpay's own claim.
**Didn't:** (1) **[HARD, C4]** the decisive evidence — delivery proof, customer comms, T&C
acceptance — sits with the **merchant and its logistics partner**, not with Razorpay; (2)
**[HARD, C1]** storing richer transaction-linked personal data expands the DPDP perimeter; (3)
**[HARD, C3]** each network prescribes its own representment format and compelling-evidence rules;
(4) **[SOFT]** storage cost across ~4bn transactions/year for an event affecting ~0.26%; (5)
**[SOFT, C9]** requires merchants to push delivery and comms data back — the same coverage problem
that limits RTO models.

### W8.2 — Chargeback guarantee / underwriting ("we pay if we lose")
**Could have:** (1) competitors sell exactly this; (2) it aligns incentives perfectly; (3) Razorpay
has the loss data to price it; (4) it monetises the Dispute Responder; (5) it removes the merchant's
tail risk entirely.
**Didn't:** (1) **[HARD, C1]** guaranteeing an outcome is insurance and is separately regulated;
(2) **[HARD, C2]** Razorpay would absorb losses driven by *merchant* behaviour it does not control;
(3) **[HARD, C1]** RBI PA Directions preserve customer chargeback rights and require refunds through
escrow, so a PA cannot contract around exposure; (4) **[SOFT]** adverse selection — the merchants
who buy it are the ones who need it; (5) **[SOFT]** capital requirements pre-IPO.

### W8.3 — Merchant coaching: prevent the dispute upstream
**Could have:** (1) Razorpay says up to 40% are avoidable with better communication; (2) it sees
which descriptors and refund policies correlate with disputes; (3) prevention is cheaper than
representment; (4) it lowers freeze risk, which merchants care about; (5) it requires no network
cooperation.
**Didn't:** (1) **[SOFT, C7]** advisory work does not scale at 12M merchants; (2) **[SOFT, C2]**
prescribing refund policy edges into telling merchants how to run their business; (3) **[SOFT]**
benefits accrue slowly and are hard to attribute; (4) **[HARD, C4]** descriptor and policy changes
must be made in the merchant's own systems; (5) **[SOFT]** no revenue line attaches to it.

> **Trap warning:** disputes **cannot be created in Razorpay test mode** (§3.6 of `requirements.md`),
> so any Track 2 chargeback build needs a synthetic dispute corpus. Six competitor repos are already
> here, and Agent Studio ships the obvious version.

---

## 6.8 🟠 P5 — Agentic commerce trust and liability

**Current method [A]:** Agentic Payments on Claude via **NPCI UPI Reserve Pay** — one-time scoped
consent, per-merchant cap (~₹10,000 block), no per-transaction PIN, full visibility, instant
revoke. Closed pilot with Zomato, Swiggy, Zepto. Agent Studio on the merchant side, becoming an open
ecosystem for third-party agents.

### W5.1 — Define its own agent-identity and liability standard ahead of UAP
**Could have:** (1) Razorpay is first mover with a live pilot; (2) NPCI's UAP is unlaunched and
awaits RBI approval; (3) standards leadership is strategically valuable; (4) it already operates the
consent model in production; (5) global protocols (ACP, AP2, x402) are fragmenting anyway.
**Didn't:** (1) **[HARD, C1]** NPCI owns UPI's rails and agent authentication — a PA cannot
unilaterally define national payment identity; (2) **[HARD, C1]** liability allocation for
unauthorised transactions is set by RBI, not by contract; (3) **[HARD, C3]** interoperability is
worthless if only one PA implements it; (4) **[SOFT]** betting against the eventual UAP standard
risks a costly rewrite; (5) **[SOFT]** regulatory goodwill matters more pre-IPO than protocol
ownership.

### W5.2 — Agent-transaction escrow / reversible settlement window
**Could have:** (1) it directly answers the "no chargeback path for AI-led transactions" void; (2)
Razorpay runs escrow infrastructure; (3) a short reversal window would build consumer trust in
agentic payments; (4) it is the natural analogue of card chargebacks; (5) Shashank Kumar publicly
concedes agents will make mistakes.
**Didn't:** (1) **[HARD, C1]** PA escrow is ring-fenced by RBI for settlement, not for dispute
buffering; (2) **[HARD, C1]** UPI is designed as irrevocable push — a reversal window contradicts the
rail; (3) **[HARD, C3]** NPCI would have to define it; (4) **[SOFT, C9]** merchants would resist
delayed settlement; (5) **[SOFT]** it implies agentic payments are unsafe, undercutting the launch
narrative.

> **Where the gap is:** the *rail* is HARD-blocked, but **the merchant-side controls are not.** An
> agent that enforces caps, logs an auditable consent trail, and handles the "the agent was wrong"
> case is exactly what Kumar describes as unsolved — and it is buildable entirely on test-mode APIs.

---

## 6.9 🟡 P11 — RTO / COD returns

**Current method [A]:** The most heavily productised problem: **RTO Shield** (pre-dispatch COD risk
using LLM address validation and bad-pincode intelligence), **RTO Insights** (pattern analysis),
**Vulcan RTO Risk Intelligence**, and an **RTO Analytics Dashboard** (90-day retention, COD vs
prepaid split). Magnitude: ~23.18% national RTO; ₹200–250 lost per RTO.

### W11.1 — A shared cross-merchant RTO blacklist
**Could have:** (1) Razorpay sees the same consumers across many merchants; (2) 60–70% of RTO is
low buying intent, i.e. consumer-attributable; (3) network effects would make it uniquely accurate;
(4) GoKwik-style networks already do a version of this; (5) it would step-change model performance.
**Didn't:** (1) ⭐ **[HARD, C1]** **DPDP Act purpose limitation** — repurposing one merchant's
customer data to deny service at another is hard to consent-justify; (2) **[HARD, C1]** a shared
negative list among competing merchants raises **CCI/competition** concerns; (3) **[HARD, C5]** a
wrongly blacklisted consumer has a discrimination and defamation claim; (4) **[SOFT, C10]** merchants
would object to contributing their customer base to a shared asset; (5) **[SOFT]** no appeal
mechanism exists for a consumer scored by an invisible network.

### W11.2 — Mandatory delivery-data feedback loop
**Could have:** (1) Razorpay's own dashboard exposes a "Delivery Data" coverage widget, so it knows
coverage is short; (2) model accuracy is directly gated on it; (3) merchants benefit from their own
contribution; (4) logistics APIs are standardised enough; (5) it is the single highest-leverage fix.
**Didn't:** (1) **[HARD, C4]** the data sits with the merchant's **courier**, under the courier's
contract; (2) **[HARD, C9]** Razorpay cannot compel it without making RTO Shield conditional; (3)
**[SOFT, C10]** mandating data sharing as a condition of a paid product invites backlash; (4)
**[SOFT]** integration burden across dozens of couriers; (5) **[SOFT]** it would expose how much of
the model's accuracy is merchant-supplied.

> **Verdict: weakest build target.** Three shipped products, and the residual gap is HARD-blocked by
> data ownership and DPDP.

---

## 6.10 🟡 P7 · P10 · P16 — the monetisation and scale-cost cluster

**P7 settlement timing.** *Current:* T+2 standard; **Instant Settlements is a paid, on-demand
add-on requiring a manual support ticket to activate.** *Workarounds not taken:* self-serve instant
settlement toggle; risk-scored automatic early settlement for clean merchants; tiered settlement by
merchant vintage. *Why not:* ⭐ **[SOFT, C6] the delay is the product** — free early settlement
cannibalises a revenue line; **[HARD, C2]** early settlement is effectively unsecured credit against
unsettled transactions; **[HARD, C1]** escrow rules govern the timing of releases; **[SOFT, C8]**
automatic early release at scale concentrates risk; **[SOFT, C10]** a published risk formula becomes
negotiable. *Note the falsification:* there is **no RBI T+1 mandate**, so this is a commercial
choice, not a compliance gap — which makes C6 the honest explanation.

**P10 support quality.** *Current:* Slash and Call-E internally; a templated reply on **94% of
negative reviews**. *Workarounds not taken:* tiered human support by merchant value; public status
and case tracking; AI triage with guaranteed human escalation; published SLAs. *Why not:*
**[SOFT, C7]** support cost per merchant is unfundable at zero-MDR across 12M merchants;
**[SOFT, C10]** published SLAs become contractual expectations; **[HARD, C5]** risk and freeze cases
*cannot* be explained even by a human; **[SOFT]** support is a cost centre measured on deflection,
not satisfaction; **[SOFT, C8]** an AI agent giving wrong guidance on money movement is worse than
slow guidance.

**P16 checkout abandonment.** *Current:* Magic Checkout (prefill across a claimed 100M+ shopper
network), Abandoned Cart Conversion agents (partner-built by SuperU and Nugget by Zomato), Vulcan
preferred-UPI-app prediction. **Razorpay publishes no first-party measured effect for any of it.**
*Workarounds not taken:* publish measured conversion uplift; guarantee conversion; one-click network
identity across merchants. *Why not:* **[SOFT, C2]** publishing a baseline invites comparison and
underperformance claims; **[HARD, C1]** a cross-merchant identity network raises DPDP consent
issues; **[HARD, C4]** conversion depends on merchant pricing, delivery and trust, which Razorpay
does not control; **[SOFT]** attribution between Magic Checkout and everything else is genuinely
hard; **[SOFT, C6]** partner-built agents mean the uplift story belongs partly to partners.

---

## 6.11 ⚪ Remaining problems — condensed

| Problem | Current method | Workarounds not taken | Dominant reason not taken |
|---|---|---|---|
| **P3** Take-rate compression | Lobbying; diversification into RazorpayX/Payroll/Capital | Surcharge UPI to consumers; platform subscription fees; vertical SaaS bundling; interchange-style fee on large merchants | **[HARD, C1]** surcharging UPI is prohibited; zero-MDR was statutory until the Aug 2026 Bill. Not solvable by product |
| **P9** Refund failures | Refund APIs; no agent | Refund status tracker with bank-side follow-up; auto-reissue on failure; refund guarantee; proactive customer notification | **[HARD, C3]** the failure is at the issuing bank; **[HARD, C2]** re-issuing risks double refund; **[SOFT]** weak evidence base means low internal visibility |
| **P12** Cross-border | PA-CB licence; Intl Payments; Replit partnership | Local-entity-as-a-service; published FX and success benchmarks; multi-currency settlement guarantees | **[HARD, C1]** FEMA and PA-CB scope limits; **[HARD, C3]** correspondent-bank dependency; **[SOFT]** newest vertical, still scaling |
| **P13** Regulatory burden | Compliance function; licence maintenance | Compliance-as-a-product for merchants; shared KYC utility; automated CKYCR remediation | **[HARD, C1]** regulated activity cannot be resold; **[HARD, C2]** assuming merchants' compliance liability |
| **P14** IPO/valuation | Diversification; cost discipline; reverse flip completed | — | Not a product problem |
| **P15** Fraud coverage | Vulcan; Thirdwatch | Publish an India merchant-side fraud benchmark; shared fraud-ring graph across merchants; open-source detection tooling | **[HARD, C5]** publishing detection performance aids evasion; **[HARD, C1]** DPDP and CCI on shared graphs; **[SOFT, C6]** detection quality is the moat |
| **P17** Onboarding | Agentic Onboarding | — | Largely solved |
| **P19** Late-auth exceptions | None (see P6) | Provisional-status flagging; amended settlement lines; hold-and-emit | **[HARD, C3]** bank-side finalisation timing |
| **P20** COD outside escrow | None — structural | COD escrow product; delivery-linked release; COD insurance | **[HARD, C1]** RBI expressly bars COD from PA escrow accounts. Legally closed |

---

## 6.12 Summary — where the SOFT constraints leave room

| Problem | Best unbuilt workaround | Blocked by | Open to you? |
|---|---|---|---|
| **P6** Reconciliation | Matching engine that proposes, scores and escalates without asserting finality | C2 audit liability (HARD **for Razorpay**) | ✅ **Yes** — confidence scores + exception list sidestep the liability |
| **P18** Receivables | Promise-to-pay tracker drafting compliant reminders in the *merchant's* name | C1 collections conduct (HARD for Razorpay as collector) | ✅ **Yes** — as a merchant tool, not a collector |
| **P4** Fund holds | Merchant-side "hold navigator": document pack, band tracking, escalation drafting | C1/C5 bind the *risk decision*, not the merchant's response | ✅ **Yes** — build the merchant's half |
| **P1** AutoPay | Retry sequencer learning per-customer timing from failure history | C4 balance invisibility — but prediction never needs the balance | ✅ **Yes** |
| **P5** Agentic | Merchant-side caps, consent audit trail, agent-error handling | C1/C3 bind the rail, not the merchant controls | ⚠️ Partly — crowded |
| **P8** Disputes | Transaction-time evidence pre-assembly | C4 merchant data + can't simulate disputes in test mode | ⚠️ Risky |
| **P2** Success rate | — | C1/C3 NPCI, banks, retry rules | ❌ **No** |
| **P11** RTO | Shared blacklist | C1 DPDP + CCI | ❌ **No** |
| **P3/P14/P20** | — | Statute | ❌ **No** |

**The one-sentence version:** *Razorpay is blocked from asserting, deciding and collecting; you are
not blocked from proposing, explaining and drafting.* Every top build candidate above is the
merchant-facing half of a problem whose Razorpay-facing half is genuinely, defensibly closed.
