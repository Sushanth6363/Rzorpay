# problems_track_mapping.md — Phase 3: Business Problems → Buildathon Tracks

Compiled 2026-08-25. Maps the 20 evidenced problems in [problems.md](problems.md) onto the official
buildathon tracks, using the Phase-2 priorities from [problems_priority.md](problems_priority.md).

> ## ⚠️ There are no "official problem statements" to map to
>
> Verified against the raw page capture in `phase0/`: Razorpay published **5 track mandates + 5 build
> specs + 5 "The bar" statements + 22 example directions** (19 named across Tracks 1–4, plus 3 Open
> Track prompts). **It published no numbered problem statements.** Blogs that present the example
> directions as "problem statements" are adding a framing Razorpay did not use.
>
> So the *Official Problem Statement* column below quotes **either the track's build spec or a named
> example direction, verbatim** — and says which. A mapping to a *build spec* is stronger than one to
> an *example direction*, because the spec is the mandate and the directions are explicitly optional.
>
> *(Correction: earlier files in this repo said "24 example directions". The verbatim count is 22 —
> T1:4, T2:4, T3:7, T4:4, Open:3. Corrected across the repo.)*

### Relationship scale

| Grade | Meaning |
|---|---|
| **DIRECT** | The build spec or a named example direction literally describes this problem |
| **RELATED** | Clearly inside the track mandate, but not a named direction |
| **INDIRECT** | Reaches the mandate only through a chain of reasoning |
| **FORCED** | Only fits if you stretch the wording — **removed from the mapping, listed separately** |

---

## 1. Master mapping (many-to-many)

| Razorpay Business Problem | Official Track | Official Problem Statement (verbatim) | Relationship | Priority | Business Value |
|---|---|---|---|---|---|
| **P1** UPI AutoPay / e-mandate execution failure | **Track 3** AI Revenue Recovery | *"Failed-subscription recovery"* and *"Mandate retry sequencer"* (example directions) — plus the spec: *"detects revenue at risk, determines the right intervention, and executes a bounded recovery workflow"* | **DIRECT** ×2 | 🔴 P0 (8.36) | ₹ recovered per mandate cycle; mandate execution success rate; involuntary churn averted |
| **P1** (secondary) | **Track 4** AI Finance Controller | *"Forward cash forecaster"* | INDIRECT | 🔴 P0 | Failed mandates distort cash forecasts |
| **P2** Payment success-rate leakage | **Track 3** | *"Payment degradation → root cause → recovery action"* | **DIRECT** | 🔴 P0 (8.02) | Success-rate points recovered × TPV. **But Vulcan owns this — see §4** |
| **P4** Merchant fund holds / freezes | **Track 4** | Mandate: *"Run the books and the cash position."* | RELATED | 🟡 P2 (6.87) | Days of frozen working capital released; hold resolution time |
| **P4** (secondary) | **Open Track** | *"Solve a problem you deeply understand"* | **DIRECT** (as Open) | 🟡 P2 | Same — see §3, this is the better home |
| **P5** Agentic commerce trust & liability | **Track 1** AI Growth & Agentic Commerce | Build spec: *"…or that makes a merchant transactable by an AI buyer end to end."* Directions: *"Conversational in-app checkout"*, *"Agent-readable catalog"* | **DIRECT** (spec-level) | 🟠 P1 (7.57) | New transaction rail; agent-attributable GMV |
| **P6** Reconciliation exception handling | **Track 4** | Build spec: *"closes one finance-ops loop across a 50+ record batch of synthetic data, reporting its match rate and the exceptions it could not resolve."* Direction: *"Multi-source reconciliation"* | **DIRECT** (spec **and** direction) | 🟠 P1 (7.16) | 20–40 finance work-hours/month recovered; match rate; exception count |
| **P7** Settlement timing / working capital | **Track 4** | *"Settlement Q&A agent"* | RELATED | 🟡 P2 (5.65) | Working-capital days; settlement query deflection |
| **P8** Disputes & chargebacks | **Track 2** AI Risk Manager | *"Chargeback evidence responder"* | **DIRECT** | 🟠 P1 (7.34) | Dispute win-rate; ₹ retained per dispute; freeze risk avoided |
| **P9** Refund failures | **Track 4** | Mandate: *"Run the books…"* (refund/settlement state reconciliation) | RELATED | ⚪ P3 (5.16) | Refund completion rate; support ticket deflection |
| **P9** (secondary) | **Open Track** | *"Solve a problem you deeply understand"* | RELATED | ⚪ P3 | Same |
| **P10** Support cost & quality | **Open Track** | *"Build something we haven't thought of"* | RELATED | 🟡 P2 (6.44) | Cost per ticket; first-contact resolution |
| **P11** RTO / COD returns | **Track 2** | *"Return-risk scorer"* | **DIRECT** | 🟡 P2 (6.78) | ₹200–250 saved per RTO prevented; RTO rate vs 23.18% baseline |
| **P12** Cross-border | **Track 1** | Mandate: *"Grow the merchant's revenue…"* | INDIRECT | 🟡 P2 (5.78) | International revenue enabled; ~5% failure rate closed |
| **P15** Fraud detection coverage | **Track 2** | *"Fraud-spike detector"*, *"Abuse-ring sentinel"* | **DIRECT** ×2 | 🟡 P2 (6.74) | Fraud ₹ prevented at a stated false-positive cost |
| **P16** Checkout abandonment | **Track 3** | *"Checkout drop-off recovery"* | **DIRECT** | 🟡 P2 (6.68) | Recovered carts; conversion vs ~2% D2C baseline |
| **P16** (secondary) | **Track 1** | *"Conversational in-app checkout"* | RELATED | 🟡 P2 | Conversion uplift |
| **P17** Merchant onboarding friction | **Track 1** | Build spec: *"…makes a merchant transactable…"* | INDIRECT | ⚪ P3 (5.08) | Time-to-first-transaction |
| **P18** B2B receivables / collections | **Track 3** | *"B2B receivables chaser"* and *"Promise-to-pay tracker"* | **DIRECT** ×2 | 🟠 P1 (7.00) | ₹ collected vs ₹ overdue; DSO reduction from 73 days |
| **P19** Late-authorisation recon exceptions | **Track 4** | Build spec: *"…the exceptions it could not resolve."* | **DIRECT** (spec-level) | 🟡 P2 (5.59) | Exceptions auto-cleared; month-end close time |
| **P20** COD outside the regulated rail | **Track 2** | Mandate: *"…losing money to fraud, returns and chargebacks."* | INDIRECT | ⚪ P3 (5.00) | Context for RTO work; not independently buildable |

**Coverage:** 16 of 20 problems map to a track. **20 mappings are DIRECT or RELATED**, 5 INDIRECT.

---

## 2. Removed as FORCED

These were considered and **cut**, because the mapping only works by stretching the wording. Naming
them is the point of the exercise — a forced mapping is exactly what a judge spots.

| Problem | Track it was forced into | Why it was cut |
|---|---|---|
| **P3** Take-rate compression | Track 1 — "grow the merchant's revenue" | The revenue at stake is **Razorpay's**, not the merchant's. The track is explicitly about merchant revenue. Resolves in Parliament, not in code |
| **P13** Regulatory / compliance burden | Track 2 — "risk" | The track's risk is *merchant loss to fraud and returns*, not *the aggregator's licensing exposure*. Different meaning of "risk" entirely. Also not Razorpay-specific |
| **P14** IPO / valuation compression | Track 1 or Open | Not a product problem in any sense. Nothing to build |
| **P10** Support cost | Track 1 — "campaign orchestrator" | Support automation is not growth. Kept as an **Open Track** mapping instead, where it is honest |
| **P2** Payment success | Track 1 — "grow revenue" | Higher success rate does grow revenue, but the mechanism is payment reliability, which is Track 3's territory. Kept as Track 3 DIRECT only |

**Not mapped anywhere:** P3, P13, P14. All three are real, well-evidenced problems that belong in
your *pitch context* — the "why Razorpay is investing in agents" framing — and in no track.

---

## 3. Open Track opportunities

The Open Track's bar is explicit: *"Open doesn't mean easier… The same bar for execution,
reliability, and depth applies here."* So Open is not a refuge for a weak fit — it is the right home
for a **strong problem with no track**.

| Candidate | Why Open rather than a numbered track | Strength |
|---|---|---|
| **P4 Merchant fund holds / freezes** ⭐ | It spans risk (Track 2's domain), cash position (Track 4's) and revenue interruption (Track 3's) without sitting inside any of them. It is a **merchant-operations navigation** problem, and no track covers merchant ops. Forcing it into Track 4 costs you the freeze/AML framing that makes it interesting | **Strongest Open candidate.** Best pure gap in the corpus; no Razorpay agent; documented triggers and 30+ day bands |
| **P10 Support cost & quality** | No track covers operations or support | Medium — real, but generic and hard to differentiate |
| **P9 Refund failures** | Sits between Track 4's books and nobody's revenue | Weak — 5/10 evidence, no rate exists |
| **Cross-cutting: merchant-side agent governance** | An audit/observability layer for *any* Razorpay agent — bounded actions, consent trails, error handling. Directly answers Shashank Kumar's public concession that agents will make mistakes | Medium-strong, novel, but abstract to demo |

**Recommendation on Open:** only P4 clears the bar. Note the trade-off — Open Track has no example
directions to anchor against, so **you supply the problem statement and the judge's frame of
reference**. That is more freedom and more risk. If you take P4, the pitch must spend its first 20
seconds establishing that the problem is real, using Razorpay's own published trigger list and
resolution bands.

---

## 4. Reverse mapping — official directions with no evidenced problem behind them

Read this before choosing. Six of the 19 named directions have **no evidenced problem** in two full
research passes.

| Official example direction | Evidenced problem? | Note |
|---|---|---|
| Failed-subscription recovery · Mandate retry sequencer | ✅ P1 | Best-evidenced pairing in the set |
| B2B receivables chaser · Promise-to-pay tracker | ✅ P18 | Government-sourced magnitude, no Razorpay agent |
| Multi-source reconciliation | ✅ P6 | Razorpay-supplied magnitude |
| Payment degradation → root cause → recovery | ✅ P2 | Evidenced, but Vulcan-owned |
| Checkout drop-off recovery | ✅ P16 | Agent Studio already ships this |
| Chargeback evidence responder | ✅ P8 | Agent Studio already ships this; **cannot be simulated in test mode** |
| Return-risk scorer | ✅ P11 | RTO Shield + RTO Insights + Vulcan already ship this |
| Fraud-spike detector · Abuse-ring sentinel | ⚠️ P15 partial | Magnitude unknowable from public data |
| Settlement Q&A agent | ⚠️ P7 partial | Settlement Insights ships a WhatsApp summary |
| Forward cash forecaster | ⚠️ partial | Cashflow Forecaster already ships |
| Tax-line matcher | ⚠️ thin | GST/TDS line matching is named as uncovered by any agent, but **no magnitude was found** |
| **Conversational in-app checkout** | ❌ | Razorpay has **already piloted this** with Vodafone and voice partners |
| **Agent-readable catalog** | ❌ | No evidenced problem — but also **no Razorpay product**, so it is unbuilt rather than disproven |
| **Upsell & cross-sell agent** | ❌ | Two passes found no citable problem |
| **Campaign orchestrator** | ❌ | Two passes found no citable problem |
| **Hinglish voice recovery** | ❌ | A *modality*, not a problem. Razorpay already pilots voice payments (Gnani.ai, SuperU) and Subscription Recovery is voice-powered by ElevenLabs |

**The trap:** four directions (upsell, campaign orchestrator, conversational checkout, Hinglish
voice) look inviting and have **no evidence base you can cite**. You would be inventing the problem
and the magnitude, against a bar that demands measured outcomes on a batch.

**The exception worth noting:** *Agent-readable catalog* has no evidenced problem **and** no Razorpay
product. That is the only direction in Track 1 that is genuinely unoccupied — but you would have to
establish the problem yourself.

---

## 5. Per-track view, with competitive density

Density from `requirements.md` §4.5 (300 competitor repos sampled 2026-08-24).

| Track | Problems mapped | Repos | Best problem | Verdict |
|---|---|---|---|---|
| **Track 1** Growth & Agentic Commerce | P5 (D), P12 (I), P16 (R), P17 (I) | ~100 (commerce 57 + agentic 43) | **P5** | Strategically central, heavily contested, and Razorpay is already live with pilots |
| **Track 2** AI Risk Manager | P8 (D), P11 (D), P15 (D), P20 (I) | ~64 (risk 46 + fraud 18) | **P8** | Every direction is already an Agent Studio product; disputes can't be simulated in test mode |
| **Track 3** AI Revenue Recovery | P1 (D×2), P2 (D), P16 (D), P18 (D×2) | **88** — most crowded | **P1**, then **P18** | Highest-value problems, worst crowding. Survive it by going where the crowd isn't: mandate ×6 repos, receivables ×3–4, vs 88 on generic recovery |
| **Track 4** AI Finance Controller | P6 (D), P19 (D), P7 (R), P4 (R), P9 (R) | **24 recon + 9 settlement** — least crowded | **P6** | Best ratio of evidence to competition. Build spec reads like a description of P6 |
| **Open Track** | P4 ⭐, P10, P9 | Not separately measurable | **P4** | Only viable if the problem is self-evidently real |

---

## 6. Where priority, evidence, mapping and openness all agree

Combining Phase 2's priority and build scores with this mapping:

| Rank | Problem → Track | Relationship | Priority | Build | Crowding | Razorpay agent? |
|---|---|---|---|---|---|---|
| **1** | **P6 → Track 4** | DIRECT (spec + direction) | 🟠 7.16 | **8.08** | Lowest | Viewer only (2022) |
| **2** | **P18 → Track 3** | DIRECT ×2 | 🟠 7.00 | **8.00** | ~3–4 repos | **None** |
| **3** | **P1 → Track 3** | DIRECT ×2 | 🔴 **8.36** | 7.68 | ~4–6 repos | Retry logic only |
| **4** | **P4 → Open** | DIRECT (as Open) | 🟡 6.87 | 7.94 | Unmeasured | **None** |

**P6 and P1 are the two strongest cases, for different reasons.** P6 wins on evidence-to-competition
ratio and on the build spec practically describing it. P1 wins on being the top-priority problem in
the corpus with two named directions pointing at it and real room left. P18 sits between them —
almost no competition, no Razorpay agent, government-sourced magnitude, but the weakest of the three
on Razorpay's own demonstrated interest (criterion 3 scored 5/10).

---

```
PHASE 3 VALIDATION

Direct mappings: 12
  P1->T3 (x2 directions), P2->T3, P5->T1 (spec), P6->T4 (spec + direction), P8->T2,
  P11->T2, P15->T2 (x2 directions), P16->T3, P18->T3 (x2 directions), P19->T4 (spec),
  P4->Open, P9->Open(related)

Related mappings: 5
  P4->T4, P7->T4, P9->T4, P10->Open, P16->T1

Indirect mappings: 5
  P1->T4, P12->T1, P17->T1, P20->T2, P2->T1 (dropped in favour of the T3 direct)

Forced mappings removed: 5
  P3->T1, P13->T2, P14->T1/Open, P10->T1, P2->T1
  Reason in every case: the track's words were being stretched past their plain meaning.
  P3/P13/P14 map to NO track and are recorded as pitch context only.

Problems that don't fit existing tracks:
  P3  Take-rate compression - Razorpay's own P&L, resolves in Parliament
  P13 Regulatory/compliance burden - not Razorpay-specific, and "risk" here means something
      different from Track 2's merchant-loss risk
  P14 IPO/valuation compression - not a product problem
  P10 Support cost - no track covers operations (mapped to Open instead)

Potential Open Track opportunities:
  P4  Merchant fund holds/freezes  <- STRONGEST. Spans three tracks without belonging to any;
      no Razorpay agent; Razorpay-published triggers and resolution bands; AML "tipping off"
      explains the opacity, which makes the merchant-side half legitimately unbuilt.
  P10 Support cost & quality - real but generic
  P9  Refund failures - weakest evidence in the corpus (5/10)
  Cross-cutting: merchant-side agent governance/audit layer - answers Shashank Kumar's public
      concession that agents will make mistakes, but is abstract to demo.

Coverage test - "does the track give us permission to solve this?":
  PASS for all 16 mapped problems. The strongest permissions are P6 and P19, where Track 4's
  BUILD SPEC (not merely an example direction) describes the work almost verbatim: "closes one
  finance-ops loop across a 50+ record batch... reporting its match rate and the exceptions it
  could not resolve."

Track test - "would Razorpay judges consider this relevant to this track?":
  PASS for all mapped problems. Two carry a caveat:
  - P4 in Open Track requires you to establish the problem yourself, since Open has no
    example directions to anchor judge expectations.
  - P2 in Track 3 is relevant but competes directly with Vulcan.

Six of the 19 named example directions have NO evidenced problem behind them (upsell,
campaign orchestrator, conversational checkout, Hinglish voice, and partially tax-line
matcher and agent-readable catalog). Building those means inventing the problem statement.

Mapping confidence: 9/10

READY FOR PHASE 4: YES
```

**Why 9/10.** The mapping rests on verbatim track text captured from the page and re-verified this
session (the 22-vs-24 count was corrected in the process), and the relationship grades are
defensible from the wording alone. It is not 10/10 because "DIRECT versus RELATED" is a judgement on
some rows — P4→Track 4 and P16→Track 1 could each be argued one grade either way — and because the
Open Track has no published directions, so any Open mapping is inherently a claim about how a judge
will read it.
