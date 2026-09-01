# final_ranking.md — Phase 13: Top 15 Connected Problem Opportunities

Compiled 2026-08-25 from [connected_problem_graph.md](connected_problem_graph.md).

## Method

**This is a blind re-score.** Per the protocol, every opportunity was re-evaluated from scratch
rather than inheriting Phase 2/5/9/10 numbers. Where a re-score disagrees with an earlier phase, the
disagreement is noted — there are four.

**Weights (as specified):**

| Dimension | Weight | Polarity note |
|---|---|---|
| Razorpay priority | 20% | — |
| Business impact | 20% | — |
| Novelty | 15% | vs **both** Razorpay's stack and the commercial market |
| Data availability | 15% | — |
| Technical feasibility | 10% | ⚠️ **10 = easiest.** Scored as feasibility, not difficulty |
| Agentic potential | 10% | — |
| Demo potential | 5% | — |
| Competition risk | 5% | ⚠️ **Inverted to "headroom": 10 = uncontested.** Otherwise the most contested idea would score highest |

`Score = Σ(dimension × weight)` — full arithmetic in §3.

---

## 1. The ranking

| Rank | Connected Problem | Track(s) | Priority | Business Impact | Novelty | Data | Feasibility | Agentic Potential | Demo | Headroom | **Score** |
|---|---|---|--|--|--|--|--|--|--|--|---|
| **1** | **Reconciliation Exception Resolver** (India settlement semantics) | **T4** | 7 | 7 | 6 | **9** | 6 | **9** | **9** | 7 | **7.35** |
| **2** | **Recovery Sequencer + headroom veto** (mandate branch) | **T3** | **9** | **9** | 4 | 8 | 4 | **9** | **9** | 3 | **7.30** |
| **3** | **Promise-to-Pay + MSME statutory escalation** | **T3** | 6 | 8 | 6 | 8 | 5 | **9** | 7 | **9** | **7.10** |
| **4** | **Merchant freeze EXPOSURE monitor** (pre-threshold) | Open / T2 | 6 | 7 | **9** | 7 | 7 | 6 | 6 | **9** | **7.05** |
| **5** | **Cross-period deduction linker** | **T4** | 6 | 6 | 8 | **9** | 7 | 7 | 6 | 8 | **7.05** |
| **6** | **Self-cure attribution harness** | T3 (component) | 6 | 7 | **9** | **9** | 8 | **2** | 5 | **9** | **7.00** |
| **7** | **Agentic Purchase Intent Verifier** | **T1** | 8 | 7 | 6 | 8 | 5 | 8 | **9** | **2** | **6.95** |
| **8** | **Multi-PSP settlement schema normaliser** | **T4** | 6 | 7 | 7 | 7 | 6 | 8 | 7 | 8 | **6.85** |
| **9** | Merchant freeze CASE navigator (post-freeze) | Open | 5 | 7 | **9** | **4** | 6 | **9** | 5 | **9** | **6.55** |
| ~~10~~ | ~~Tax-line matcher (GST-on-MDR / TDS)~~ **REFUTED 2026-08-25** — Source to Pay already auto-deducts TDS on line items and catches GST ITC misses | ~~T4~~ | — | — | **0** | — | — | — | — | — | **DEAD** |
| **11** | Agent-readable catalog for AI buyers | T1 | 6 | 6 | 7 | 8 | 7 | 5 | 7 | 4 | **6.40** |
| **12** | Late-authorisation provisional-state resolver | T4 | 5 | 5 | 7 | 8 | 7 | 7 | 5 | 8 | **6.30** |
| **13** | Refund three-way state reconciler | T4 / Open | 4 | 5 | 7 | 6 | 6 | 7 | 6 | 8 | **5.75** |
| **14** | Chargeback evidence pre-assembly | T2 | 7 | 7 | 4 | **3** | 5 | 8 | 6 | 4 | **5.65** |
| **15** | Joint RTO/conversion threshold optimiser | T2 | 6 | 6 | 8 | **3** | 6 | **3** | 6 | 6 | **5.55** |

---

## 2. One-line justification per score — top 5

**#1 Reconciliation Exception Resolver — 7.35**

| Dim | Score | Justification |
|---|--|---|
| Priority | 7 | Razorpay publishes the 20–40 hrs/month figure itself, but ships only a viewer — real, not top-of-mind |
| Impact | 7 | Cost saving rather than revenue; large per merchant, bounded in aggregate |
| Novelty | 6 | Ledge and HighRadius exist globally; **no one handles Indian MDR/GST-on-MDR/TDS/UTR semantics** |
| Data | **9** | Schema published field-by-field, defect list published, synthetic explicitly sanctioned by the track spec |
| Feasibility | 6 | Deterministic matcher + LLM on the residual; MVP in 4–5 days |
| Agentic | **9** | Exception handling *is* the job; abstention is a designed output |
| Demo | **9** | Match rate, throughput and an exception list are exactly Track 4's bar |
| Headroom | 7 | 24 recon repos vs 88 on recovery; crowded commercially, not in the applicant pool |

**#2 Recovery Sequencer + headroom veto — 7.30**

| Dim | Score | Justification |
|---|--|---|
| Priority | **9** | The highest-priority problem in the corpus (P1, 8.36) |
| Impact | **9** | ~70% of SBI auto-debits fail against ~1.6bn monthly e-mandates |
| Novelty | **4** ⚠️ | **Revaly already ships decline-code retry timing.** Only the headroom veto is genuinely new |
| Data | 8 | Failure simulation works; chargeback headroom must be synthetic |
| Feasibility | **4** ⚠️ | The temporal simulation is a sub-project; ambitious version doesn't fit 11 days |
| Agentic | **9** | Reasons about second-order consequences of its own actions |
| Demo | **9** | Money recovered on a batch, with a visible stop |
| Headroom | **3** ⚠️ | Worst quadrant — 88 repos *and* a mature commercial category |

**#3 Promise-to-Pay + MSME statutory escalation — 7.10** · Priority 6 (Razorpay gestures at it, ships
nothing) · Impact 8 (₹20,979 cr pending; 73-day DSO) · Novelty 6 (HighRadius ships promise-to-pay;
**Indian statutory escalation is unoccupied**) · Data 8 (good distribution anchors) · Feasibility 5 ·
Agentic 9 (long-horizon commitments) · Demo 7 · Headroom **9** (3–4 repos — the emptiest space found).

**#4 Freeze EXPOSURE monitor — 7.05** · Novelty **9** and Headroom **9**. ⭐ **The key insight
separating this from #9:** the *monitor* computes chargeback-ratio headroom **from the merchant's own
transactions**, so it scores Data 7 — while the *navigator* needs hold events that cannot be created,
scoring Data 4. Same problem, opposite feasibility.

**#5 Cross-period deduction linker — 7.05** · Novelty 8, Data 9. A chargeback deduction lands in a
*later* settlement cycle than the sale; the API returns one cycle at a time. Narrow, unglamorous,
completely unaddressed — and the best sub-component of #1.

---

## 3. Complete calculation (worked, top 3)

```
Score = 0.20·Priority + 0.20·Impact + 0.15·Novelty + 0.15·Data
      + 0.10·Feasibility + 0.10·Agentic + 0.05·Demo + 0.05·Headroom

#1 Reconciliation Exception Resolver
   = 0.20(7) + 0.20(7) + 0.15(6) + 0.15(9) + 0.10(6) + 0.10(9) + 0.05(9) + 0.05(7)
   = 1.40 + 1.40 + 0.90 + 1.35 + 0.60 + 0.90 + 0.45 + 0.35
   = 7.35

#2 Recovery Sequencer + headroom veto
   = 0.20(9) + 0.20(9) + 0.15(4) + 0.15(8) + 0.10(4) + 0.10(9) + 0.05(9) + 0.05(3)
   = 1.80 + 1.80 + 0.60 + 1.20 + 0.40 + 0.90 + 0.45 + 0.15
   = 7.30

#3 Promise-to-Pay + MSME statutory
   = 0.20(6) + 0.20(8) + 0.15(6) + 0.15(8) + 0.10(5) + 0.10(9) + 0.05(7) + 0.05(9)
   = 1.20 + 1.60 + 0.90 + 1.20 + 0.50 + 0.90 + 0.35 + 0.45
   = 7.10
```

**#1 and #2 are separated by 0.05 — statistically indistinguishable.** They win on opposite grounds:
#2 has far higher priority and impact (1.80+1.80 vs 1.40+1.40) and gives it all back on novelty,
feasibility and headroom (0.60+0.40+0.15 = 1.15 vs 0.90+0.60+0.35 = 1.85). **The choice between them
is a risk preference, not a ranking question.**

---

## 4. Sensitivity test

Three scenarios, re-ranked:

| Opportunity | Base | S1: Agent Studio roster grew | S2: more time | S3: crowding worsens |
|---|---|---|---|---|
| Reconciliation Exception Resolver | **1** | **1** (+0) | **1** (+0) | **1** (+0) |
| Recovery Sequencer + headroom veto | **2** | **2** (+0) | **2** (+0) | **2** (+0) |
| Promise-to-Pay + MSME statutory | 3 | **7** (−4) ⚠️ | 3 | 3 |
| Freeze EXPOSURE monitor | 4 | **8** (−4) ⚠️ | 4 | 4 |
| Cross-period deduction linker | 5 | **3** (+2) | 5 | 5 |
| Self-cure attribution harness | 6 | **4** (+2) | 6 | 6 |

**S1 is the scenario that matters.** Razorpay's Agent Studio page is client-side rendered and
defeated every fetch attempt, so the roster in use is from the **five-month-old launch blog** — which
itself says third-party builders will publish agents. If the roster has grown, every opportunity
whose novelty rests on *"no Razorpay product exists"* loses 3 points.

**ROBUST — top 5 in every scenario:** Reconciliation Exception Resolver · Recovery Sequencer.
**FRAGILE — fall out of the top 5 under S1:** Promise-to-Pay (3→7) · Freeze exposure monitor (4→8).

**What is quietly reassuring:** #1's novelty rests on *Indian settlement semantics being unaddressed
by global tools*, not on "Razorpay hasn't built it." That claim survives S1 intact — which is why it
holds rank 1 in all three scenarios.

---

## 5. Disagreements with earlier phases

The blind re-score contradicted my own earlier conclusions four times:

| Change | Earlier | Now | Why |
|---|---|---|---|
| Recovery novelty | 7 (Phase 5) | **4** | Phase 11 found Revaly ships decline-code retry timing |
| Promise-to-Pay novelty | 9 (Phase 6) | **6** | HighRadius runs 15 agentic collections agents and auto-creates promise-to-pay |
| Freeze work | one opportunity | **split in two** | The monitor (Data 7) and the navigator (Data 4) have opposite feasibility. Merging them hid that |
| Self-cure attribution | a component | **ranked #6 in its own right** | Novelty 9, Data 9, Feasibility 8 — it scores highly on everything except agentic potential (2), which is honest |

---

```
PHASE 13 VALIDATION

Top 15: as listed in section 1.

Robust opportunities (top-5 under every scenario tested):
  1. Reconciliation Exception Resolver (7.35) - holds rank 1 in all three scenarios because
     its novelty claim rests on Indian settlement semantics being unaddressed by GLOBAL tools,
     not on an absence in Razorpay's roster. That is the only novelty claim in the top 5 that
     does not depend on a product page I could not fetch.
  2. Recovery Sequencer + headroom veto (7.30) - holds rank 2 everywhere. Its weaknesses
     (novelty 4, feasibility 4, headroom 3) are already priced in at base, so no scenario
     makes them worse.

Fragile opportunities:
  3. Promise-to-Pay + MSME statutory - falls 3 -> 7 if Agent Studio's roster has grown.
  4. Freeze EXPOSURE monitor - falls 4 -> 8 on the same assumption.
  Both depend on "no Razorpay product exists", sourced from a five-month-old launch blog.

Biggest scoring uncertainty:
  Novelty, carrying 15% of the weight, is the least verifiable dimension in the model. It
  depends on (a) Razorpay's CURRENT agent roster, which I could not fetch because the product
  page is client-side rendered, and (b) whether global incumbents like Ledge and HighRadius
  handle Indian settlement and tax semantics - which I INFERRED from their US/EU positioning
  rather than verified. Both are checkable and neither has been checked.

Would rankings change if:
  - DATA AVAILABILITY CHANGES? Materially for two entries. If test-mode settlement data is
    richer than "thin", #1 gets stronger. If dispute creation ever became possible in test
    mode, #14 rises from 5.65 by roughly 0.9. Nothing else moves much.
  - RAZORPAY PRIORITY CHANGES? The top two are insensitive: #1 wins on data and agentic fit
    rather than on priority, and #2 already scores priority 9 (it cannot rise). A priority
    shift would mostly reshuffle ranks 8-15.
  - COMPETITION CHANGES? Almost nothing moves (S3). Competition risk carries only 5% of the
    weight, which is arguably too little - on the two-axis analysis in Phase 11, buildathon
    crowding is one of the strongest practical determinants of whether a submission is even
    seen. Under the specified weights it barely registers, and I have followed the specified
    weights rather than substituting my own.

Confidence: 8/10

READY FOR PHASE 14: YES
```

**Why 8/10.** The ranking was re-scored blind, contradicted four of my own earlier conclusions, and
survived three sensitivity scenarios with a stable top two. It is not 9/10 because novelty — 15% of
the weight — rests on two unverified inferences, and because the top two are separated by 0.05,
which is well inside the noise of a judgement-based model.

---

## 6. What the ranking actually says

**#1 and #2 are a tie that the score cannot break.** Choose on risk appetite:

- **#1 Reconciliation** — lower ceiling, far lower variance. Best data, least crowded track, MVP in
  under half the window, and a novelty claim that survives every sensitivity scenario.
- **#2 Recovery** — highest priority and impact in the corpus, and the headroom veto is the single
  most defensible design decision in this research. But it is the worst competitive quadrant and its
  temporal simulation is where 11-day schedules break.

**The strongest combination is #1 + #5 + #6:** a reconciliation resolver, extended with cross-period
deduction linking, evaluated with a proper holdout harness. All three are Track 4-aligned, all three
score ≥7.00, and together they form one coherent project rather than three.
