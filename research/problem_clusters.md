# problem_clusters.md — Phase 5: Problem Clusters

Compiled 2026-08-25 from the edges in [problem_graph.md](problem_graph.md), priorities in
[problems_priority.md](problems_priority.md) and evidence in [problems.md](problems.md).

## Clusters were derived, not adopted

Your example clusters were tested and **three of the five did not survive contact with the graph.**
The disagreement is the useful part, so it is stated up front:

| Your example cluster | Verdict | Why |
|---|---|---|
| A: Payment Failure + Routing + Recovery | **Split and re-formed** | Routing (Optimizer/Vulcan) is HARD-blocked by bank and NPCI dependencies and is Razorpay-owned. Recovery is not. Grouping them inherits the blocked half |
| B: Fraud + Chargeback + Evidence + Recovery | **Re-cut** | The graph shows chargebacks flowing to **two different destinations** — into reconciliation as a *settlement line item*, and into the freeze trigger as a *risk threshold*. Those are different workflows with different owners |
| C: Reconciliation + Investigation + Cash Flow | ✅ **Survives essentially intact** | Becomes C2 |
| D: Collections + Revenue Recovery + Forecasting | **Merged upward** | Collections and revenue recovery are *the same loop over different ledgers* (Phase 4, Chain A). Keeping them apart hides the strongest structural finding in the research |
| E: Agentic Commerce + Payments + Risk | **Narrowed** | Payments and risk appear in every cluster; including them makes E unfalsifiable. Narrowed to the trust/consent/liability layer that is actually unique to it |

**The load-bearing change:** P1 failed mandates, P9 failed refunds and P18 overdue invoices are one
engine over three ledgers. Your Clusters A and D split that engine in half. C1 below re-joins it.

---

## 1. The six clusters

### 🥇 C2 — Settlement Truth / Finance Close · **composite 7.90**
**Problems:** P6 reconciliation · P19 late-authorisation exceptions · P7 settlement timing ·
P9 refunds *(as settlement line items)* · P8 chargebacks *(as settlement line items)*
**Track:** 4 · **Graph basis:** Chain C

The cluster is held together by a **physical artefact**: Razorpay's settlement report, which
itemises MDR, GST on MDR, **refund offsets**, **chargeback deductions**, net settled and bank UTR.
Disputes and refunds are not *related to* reconciliation — they are fields inside it. Late
authorisation is the named exception class that leaves lines provisional.

**Economic outcome:** 20–40 finance work-hours/month recovered; match rate; exceptions cleared.

### 🥈 C1 — The Money-Didn't-Arrive Engine · **composite 7.60**
**Problems:** P1 mandate failure · P2 payment failure · P9 refund failure · P18 overdue receivables
· P19 *(shared exception handling)*
**Track:** 3 · **Graph basis:** Chain A

One loop — detect → classify over Razorpay's published error taxonomy → select intervention → act
within bounds → verify → reconcile — pointed at four different ledgers. The classification stage is
literally the same code; only the intervention policy changes.

**Economic outcome:** ₹ recovered per batch; recovery rate; cost per recovery attempt.

### 🥉 C6 — Merchant Operations Navigator · **composite 7.20**
**Problems:** P4 fund holds · P10 support · P9 refunds *(merchant-facing)* · P17 KYC currency
**Track:** Open · **Graph basis:** Chains B (tail) and G

The merchant's side of everything that goes wrong: a frozen account, an unexplained hold, a refund
that never landed, a stale KYC document. Razorpay is HARD-blocked from automating the *decision*
(AML tipping-off, licence exposure) but nothing blocks automating the *merchant's response* —
document assembly, band tracking, escalation drafting.

**Economic outcome:** frozen-capital days released; hold resolution time; tickets deflected.

### C4 — Agentic Commerce Trust Layer · **composite 6.90**
**Problems:** P5 agent trust/liability · P16 conversational checkout · P2 *(authorization step)* ·
P8 *(the AI-transaction dispute void)*
**Track:** 1 · **Graph basis:** Chain E

Bounded autonomy for AI buyers: scoped consent, cap enforcement, auditable action trails, and the
unresolved question of what happens when the agent is wrong — which Razorpay's own MD has publicly
conceded is unsolved.

**Economic outcome:** agent-attributable GMV; disputed-agent-transaction rate; consent revocations.

### C3 — Risk Exposure → Freeze Prevention · **composite 6.40**
**Problems:** P8 chargebacks · P15 fraud · P17 KYC · P13 compliance → P4 freeze
**Track:** 2 · **Graph basis:** Chain D

Model the merchant's total exposure across four documented freeze triggers and act before the
terminal state. Its distinctive asset: it expresses **false-positive cost in frozen-capital days**
rather than as an abstract precision penalty.

**Economic outcome:** freezes avoided; FP cost in rupees and days.

### C5 — Physical-Goods Loss · **composite 5.30**
**Problems:** P11 RTO/COD · P20 COD-outside-escrow · P15 *(return abuse)*
**Track:** 2 · **Graph basis:** Chain F

**Economic outcome:** RTO rate vs the 23.18% baseline; ₹200–250 saved per prevented RTO.

---

## 2. Scores

**Polarity warning — two columns are inverted.** *Technical difficulty* is scored 10 = hardest and
*competition risk* 10 = most contested, so **higher is worse** on both. The composite uses
`feasibility = 11 − difficulty` and `headroom = 11 − competition risk` so that every input points
the same way. The composite is the plain mean of the ten aligned values.

| Cluster | Business impact | Razorpay priority | Connected problems | Data availability | AI suitability | Agentic suitability | Technical difficulty ⚠️ | Novelty potential | Competition risk ⚠️ | Demo potential | **Composite** |
|---|--|--|--|--|--|--|--|--|--|--|---|
| **C2** Settlement Truth | 7 | 7 | 7 *(5)* | **9** | **9** | **9** | 5 | 8 | **3** | **9** | **7.90** |
| **C1** Money-Didn't-Arrive | **9** | **9** | **9** *(5)* | 8 | 8 | **9** | 6 | 7 | 8 | **9** | **7.60** |
| **C6** Merchant Ops Navigator | 7 | 5 | 7 *(4)* | 6 | 8 | **9** | 6 | **9** | **2** | 7 | **7.20** |
| **C4** Agentic Commerce Trust | 7 | 8 | 7 *(4)* | 8 | **9** | **10** | 7 | 5 | **9** | **9** | **6.90** |
| **C3** Risk → Freeze Prevention | 8 | 7 | **9** *(5)* | **4** | 8 | 7 | 7 | 6 | 7 | 7 | **6.40** |
| **C5** Physical-Goods Loss | 7 | 6 | 5 *(3)* | 5 | 6 | **4** | 5 | **2** | 5 | 6 | **5.30** |

### Why the notable scores are what they are

- **C2 data 9 / competition 3** — Track 4's build spec *sanctions synthetic data outright* ("50+
  record batch of synthetic data"), the settlement report's fields are published, and the track is
  the least crowded at 24 recon repos against 88 on recovery.
- **C1 priority 9, competition 8** — contains both P0s, and sits in the most contested track. High
  value, hard to stand out, unless you go where the crowd isn't (mandate ×~6 repos, receivables ×3–4).
- **C6 novelty 9 / competition 2 / priority 5** — the cleanest gap in the corpus and essentially
  uncontested, but Razorpay's *demonstrated* priority is low precisely because it ships nothing here.
  That is the cluster's opportunity and its risk in the same number.
- **C3 data 4** — the binding constraint: **disputes cannot be created in Razorpay test mode**, and
  no India merchant-side fraud rate is publicly obtainable. Everything must be synthesised.
- **C4 agentic 10, novelty 5** — definitionally the most agentic cluster, but Razorpay has already
  piloted conversational checkout and voice payments, and ~100 competitor repos are here.
- **C5 novelty 2 / agentic 4** — three shipped Razorpay products, and a risk *scorer* is an ML model,
  not an agent.

---

## 3. Cluster validation

### Cohesion — would a Razorpay product team see one workflow?

| Cluster | Verdict |
|---|---|
| C2 | ✅ Finance ops owns the settlement-to-close workflow end to end |
| C1 | ✅ Revenue ops owns "money owed didn't arrive" across ledgers |
| C6 | ✅ A merchant's finance/ops person experiences all four as one bad week |
| C4 | ✅ The agentic-payments team owns consent, caps and agent errors |
| C3 | ⚠️ **Partly.** Risk owns fraud and chargebacks; *compliance* owns KYC and PA flags. Two owners |
| C5 | ✅ RTO/COD is a single owned surface |

### Shared infrastructure — can they share data, models, tools and workflows?

| Cluster | Shared substrate |
|---|---|
| C2 | The settlement report schema, UTR, Settlement ID — one matching engine, one exception queue |
| C1 | The published error taxonomy + `source` field — **one classifier, four intervention policies** |
| C6 | Merchant case state, document pack, published bands — one case-tracking agent |
| C4 | Consent token, cap ledger, action audit trail |
| C3 | Merchant risk profile and exposure time-series |
| C5 | Order, address, pincode, delivery outcome |

### Economic test — do the members drive the same outcome?

✅ C1 (rupees recovered) · ✅ C2 (hours saved + match rate) · ✅ C6 (frozen days released) ·
✅ C5 (rupees per prevented RTO) · ⚠️ **C4 mixes two outcomes** — conversion uplift (P16) and risk
containment (P5/P8), which are different P&L lines · ⚠️ **C3 mixes** loss prevented (P8/P15) with
capital released (P4).

### Overlap test

**C3 and C6 share node P4 — deliberately, and they are not duplicates.** C3 is *Razorpay-side*:
predict exposure, prevent the freeze, own the risk decision — which §6 of `problems_priority.md`
shows is HARD-blocked for an outsider by AML and licensing. C6 is *merchant-side*: respond to a
freeze that has already happened. Different actor, different data, different capability, opposite
buildability. **Kept separate, with the shared node declared.**

C1 and C2 join at reconciliation (P9, P19 appear in both). A project spanning both is coherent but
doubles scope — see §5.

---

## 4. Merges and removals

**Merged:** *Collections* + *Revenue Recovery* → **C1**. They are one loop over different ledgers;
separating them would have hidden the strongest structural finding in the research.

**Split:** *Fraud + Chargeback + Evidence + Recovery* → **C2** (chargebacks as settlement line items)
and **C3** (chargebacks as a risk threshold). Same problem, two destinations, two owners.

**Removed as a cluster:** *Support automation as a standalone*. P10 is a **sink** — the terminal
symptom of every other cluster, with the highest in-degree in the graph and almost no independent
data of its own. Folded into C6, where it belongs to a real workflow.

**Not clustered at all:** P3 take-rate, P13 regulatory burden, P14 IPO/valuation. They connect to
nothing operationally (Phase 4 removed those edges as artificial) and belong in pitch context.

---

```
PHASE 5 VALIDATION

Clusters validated: 6
Clusters merged: 1  (Collections + Revenue Recovery -> C1, on the shared-loop finding)
Clusters split:  1  (Fraud/Chargeback -> C2 line-item view + C3 risk-threshold view)
Clusters removed: 1 (standalone Support automation -> folded into C6 as a sink, not a cluster)

Strongest cluster: C2 Settlement Truth / Finance Close (7.90)
  Cohesion, shared infrastructure and economic tests all pass cleanly. Its substrate is a
  PUBLISHED ARTEFACT - the settlement report's named fields - so the members are joined by a
  schema rather than by resemblance. Data availability is the highest of any cluster because
  Track 4's own build spec sanctions synthetic data, and competition risk is the lowest of the
  four viable clusters. It also maps DIRECT to a build spec rather than to an optional example
  direction.

Runner-up: C1 Money-Didn't-Arrive Engine (7.60)
  Highest business impact and Razorpay priority of any cluster (contains both P0s) and the most
  intellectually interesting - one classifier, four ledgers. Loses to C2 only on competition
  risk (8 vs 3) in the most crowded track in the buildathon.

Weakest cluster: C5 Physical-Goods Loss (5.30)
Why:
  Novelty 2 - Razorpay ships RTO Shield, RTO Insights AND Vulcan RTO Risk Intelligence against
  it. Agentic suitability 4 - a pre-dispatch risk scorer is an ML model, not an agent, so it
  fails the anti-AI-washing test before it starts. Data availability 5 - no public India RTO
  dataset, and the delivery data that gates model accuracy belongs to the merchant's courier.
  It is a real problem that is already solved to the edge of available data.

Second-weakest: C3 Risk -> Freeze Prevention (6.40)
  Fails the cohesion test partially (two owners: risk and compliance), mixes two economic
  outcomes, and carries the hardest data constraint in the entire corpus - disputes CANNOT be
  created in Razorpay test mode, so every input must be synthesised.

Biggest uncertainty:
  C6's Razorpay-priority score of 5. It scores low precisely BECAUSE Razorpay ships nothing
  there - the same fact that makes its novelty score 9. If the absence reflects deliberate
  strategic avoidance (AML exposure, not wanting to appear to coach merchants around its own
  risk controls) rather than an unexploited gap, then C6's real priority is lower still and
  judges may read it as off-strategy. This is the one cluster where the gap could be a moat
  rather than an opening.

Confidence: 8/10

READY FOR PHASE 6: YES
```

**Why 8/10.** Cluster membership is derived from graph edges that each passed four tests, and the
two strongest clusters are held together by published artefacts — an error taxonomy and a settlement
schema — rather than by theme. It is not 9/10 because the ten scores are judgement calls (as in
Phase 2, roughly ±1 each), C3 fails part of the cohesion test yet was retained for completeness, and
C6's priority score rests on interpreting an absence.

---

## 5. What this means for the build

1. **C2 is the recommendation.** Best composite, lowest competition, highest data availability,
   maps to a *build spec* rather than an example direction, and its bar (match rate + throughput +
   honest exception list) is the most objectively satisfiable in the buildathon.
2. **C1 is the higher-ceiling, higher-variance choice.** It contains both P0s and the best story —
   *one classifier, four ledgers* — but sits in a track with 88 competing repos. Choose it only if
   you go where the crowd is not: mandate retry sequencing or B2B receivables, not generic
   "failed payment recovery".
3. **The C1 ∩ C2 overlap is the sweet spot, if scope allows.** A recovery agent whose outcomes
   *reconcile* — i.e. it recovers money and then proves the recovery landed in the settlement
   report — spans both clusters through P9/P19 and demonstrates the full loop. It is more work, but
   it is the only shape that satisfies two tracks' bars at once. Pick one track to submit under.
4. **C6 is the contrarian pick.** Near-zero competition, the cleanest gap, and a genuinely good
   explanation of why nobody has built it. The risk is that judges read a merchant-side
   hold-navigator as working around Razorpay's own risk controls — worth pre-empting explicitly in
   the pitch.
5. **Avoid C5.** Three shipped products and a scorer that is not an agent.
