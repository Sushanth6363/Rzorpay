# problem_graph.md — Phase 4: Connected Problems

Compiled 2026-08-25 over the 20 evidenced problems in [problems.md](problems.md), using priorities
from [problems_priority.md](problems_priority.md) and track mappings from
[problems_track_mapping.md](problems_track_mapping.md).

## How an edge earns its place

Two problems sounding related is not a connection. Every candidate edge was tested four ways:

| Test | Question |
|---|---|
| **Causal** | Does solving A actually change B's outcome? |
| **Data** | Do they share transaction, customer, merchant, risk, financial or event data? |
| **Workflow** | Would they appear in the same business workflow, owned by the same person? |
| **Outcome** | Does improving A improve the measured result of B? |

| Grade | Rule | Kept? |
|---|---|---|
| **STRONG** | Passes all 4, and at least one is a *physical* link (a shared field, a documented trigger) | ✅ Primary graph |
| **MODERATE** | Passes 3 of 4 | ✅ Primary graph |
| **WEAK** | Passes 2 or fewer | ❌ Removed |
| **ARTIFICIAL** | Related only by topic or vocabulary | ❌ Removed |

**A note on direction.** Not every edge is synergistic. One pair (§4) is a genuine **trade-off** —
solving A makes B worse. Those are marked ⚡ and matter more than the friendly edges, because they
are where a naive submission gets caught.

---

## 1. The chains

### ⭐ Chain A — "Money owed didn't arrive" (the recovery chain)

**P2 payment failure → root-cause classification → intervention → bounded retry → P1 mandate
failure → recovery → P6 reconciliation of the outcome**

| Field | Detail |
|---|---|
| **Connected problems** | P2 (success-rate leakage) · P1 (AutoPay/mandate failure) · P9 (refund failures) · P18 (overdue receivables) |
| **Why connected** | All four are the same event wearing different clothes: *an expected movement of money did not happen.* Each needs the identical loop — detect, classify why, choose an intervention, act within bounds, stop when told, reconcile the result. The nouns differ (payment, mandate, refund, invoice); the machinery does not |
| **Shared data** | Razorpay's published error taxonomy: `bank_technical_error`, `insufficient_funds`, `payment_declined`, `payment_timed_out`, `vpa_resolution_failed` etc., plus the **`source` attribution field** (bank / gateway / customer / issuer) and the reason → next-best-action mapping. Payment ID, order ID, customer VPA, UTR, timestamps |
| **Shared AI capability** | Failure classification over a fixed ontology → intervention selection → bounded execution with stopping rules → outcome verification. One agent architecture, four instantiations |
| **Business outcome** | ₹ recovered per batch; recovery rate; cost per recovery attempt |
| **Grade** | **STRONG** — causal ✅ data ✅ (literally the same error codes) workflow ✅ outcome ✅ |

> **This is the single most important structural finding in Phase 4.** P1, P9 and P18 are *not three
> projects*. They are one agent pointed at three ledgers. A submission that builds the loop once and
> demonstrates it across two of them is strictly stronger than one that builds a bespoke solution to
> one — and it is the honest way to claim breadth without scope creep.

### ⭐ Chain B — "Recovery pressure becomes a frozen account" (the escalation chain)

**P1 mandate failure → aggressive dunning → customer disputes the charge → P8 chargeback ratio rises
→ crosses 1% → P4 merchant funds frozen → P10 support ticket**

| Field | Detail |
|---|---|
| **Connected problems** | P1 → P8 → P4 → P10 |
| **Why connected** | Each link is documented, not inferred. **Visa reason code 13.2 "cancelled recurring" accounts for 8.5% of all chargebacks** — failed and re-attempted subscriptions *produce* disputes. **Razorpay's own published freeze trigger is a chargeback ratio above 1%.** A freeze then generates the support contact. The chain converts a 0.26%-rate nuisance into a total revenue stop |
| **Shared data** | Subscription/mandate ID → payment ID → dispute record → merchant chargeback ratio → risk flag → ticket. The merchant identifier threads all four |
| **Shared AI capability** | Cross-domain risk propagation: modelling how an action in recovery changes exposure in risk. Requires reasoning about *second-order consequences of your own agent's actions* |
| **Business outcome** | Chargeback ratio held below the freeze trigger; frozen-capital days avoided; support contacts deflected |
| **Grade** | **STRONG** — causal ✅ (documented reason code + documented trigger) data ✅ workflow ✅ outcome ✅ |

> **Why this chain is worth more than its parts.** It contains the best answer to *"what are the
> stopping rules?"* — Track 3's bar demands "compliant escalation, stopping rules, and an audit
> trail," and this chain tells you **what the stopping rule is protecting against**: your own
> recovery agent pushing the merchant's chargeback ratio past 1% and freezing their funds. A
> submission that models this is answering the bar's real question rather than adding an arbitrary
> retry cap.

### Chain C — The finance convergence chain

**P2/P8/P9/P11 transaction outcomes → P7 settlement → P6 reconciliation → P19 late-auth exceptions →
cash position → forecast**

| Field | Detail |
|---|---|
| **Connected problems** | P8 · P9 · P7 · P6 · P19 (and P2 upstream) |
| **Why connected** | **Physical, not conceptual.** Razorpay's own settlement report itemises *MDR, GST on MDR, **refund offsets**, **chargeback deductions**, net settled and bank UTR.* Disputes and refunds are literally line items inside the reconciliation artefact. You cannot reconcile without resolving them; a late authorisation (P19) leaves the line provisional |
| **Shared data** | The settlement report's 11 fields; UTR; Settlement ID; transaction ID; the processing aggregator |
| **Shared AI capability** | Multi-source matching under uncertainty + exception triage + provisional-state handling. The hard part is the unmatched tail, not the match |
| **Business outcome** | Match rate; exceptions cleared; 20–40 finance work-hours/month recovered; month-end close time |
| **Grade** | **STRONG** — the shared-field evidence makes the data test unusually literal |

### Chain D — The risk-to-freeze convergence

**P15 fraud detection (false positives) + P8 chargebacks + P17 stale KYC + P13 PA compliance flags →
P4 fund holds**

| Field | Detail |
|---|---|
| **Connected problems** | P15 · P8 · P17 · P13 → P4 |
| **Why connected** | Razorpay publishes the four freeze triggers, and each is the terminal state of a different upstream problem: chargeback ratio >1%, ~10x volume spikes, stale KYC/GST/PAN, and PA compliance flags. **P4 is not an independent problem — it is where four other problems land** |
| **Shared data** | Merchant risk profile, chargeback ratio, volume time-series, KYC document state, transaction anomaly flags |
| **Shared AI capability** | Risk-signal fusion, and — critically — **false-positive cost modelling**. Track 2's bar demands "honest metrics including false-positive cost"; this chain shows what a false positive actually costs: a frozen merchant, 30+ days |
| **Business outcome** | Freezes avoided; false-positive cost quantified in frozen-capital days rather than in abstract precision |
| **Grade** | **STRONG** (P8→P4, P15→P4) · **MODERATE** (P17→P4, P13→P4) |

> This chain gives Track 2 submissions their best available answer to "what is your false-positive
> cost?" — a number in rupees and days, not a confusion matrix.

### Chain E — The agentic commerce chain

**P5 agent identity/trust → discovery → P16 checkout → authorization → P15 risk decision → P2
payment → confirmation → *dispute with no defined path* → back to P5**

| Field | Detail |
|---|---|
| **Connected problems** | P5 · P16 · P15 · P2 · P8 |
| **Why connected** | The loop closes badly: an AI-initiated purchase runs through checkout, risk and payment like any other, **but the evidenced gap is that chargebacks and dispute resolution for AI-led transactions have no defined liability or recourse path.** So the chain terminates in an unresolved state that feeds back into the trust problem it started with |
| **Shared data** | Agent identity/consent token, spending caps, merchant catalog, transaction context, risk signals |
| **Shared AI capability** | Bounded autonomy: scoped consent, cap enforcement, auditable action trail, and graceful handling of "the agent was wrong" |
| **Business outcome** | Agent-attributable GMV; disputed-agent-transaction rate; consent revocations |
| **Grade** | **STRONG** on P5↔P8 (the liability void is evidenced) · **MODERATE** elsewhere |

### Chain F — The RTO / merchant-loss chain

**P11 RTO risk → COD order → delivery failure → merchant loss → P20 no escrow protection**

| Field | Detail |
|---|---|
| **Connected problems** | P11 · P20 · P15 (return abuse) |
| **Why connected** | RTO costs ₹200–250 per incident at a ~23% rate — and **RBI's PA Directions expressly bar COD from the escrow account**, so the loss falls wholly on the merchant with no PA-side protection. The structural rule explains why the commercial problem is the merchant's alone |
| **Shared data** | Order, address, pincode, COD flag, delivery outcome, customer return history |
| **Shared AI capability** | Pre-dispatch risk scoring; address normalisation |
| **Business outcome** | RTO rate vs 23.18% baseline; ₹ saved per prevented RTO |
| **Grade** | **MODERATE** — causal ✅ data ✅ outcome ✅, workflow ⚠️ (P20 is a regulatory fact, not an operational step) |

### Chain G — The support sink

**Every unresolved problem → P10 support**

P4 freezes, P9 refunds, P6 reconciliation queries and P8 disputes all terminate in a support contact.
**P10 has the highest in-degree in the graph and is a poor build target** — it is a symptom node.
Fixing any upstream problem reduces it; attacking it directly treats the symptom.
**Grade: MODERATE** as edges, but flagged as a **structural sink**.

---

## 2. Master connection table

| Connected Problems | Why They Are Connected | Shared Data | Shared AI Capability | Business Outcome | Grade |
|---|---|---|---|---|---|
| **P2 ↔ P1** | Same failure event, one-shot vs mandated | Error codes + `source` field | Failure classification → retry policy | ₹ recovered | **STRONG** |
| **P1 ↔ P18** | Both are "money owed, chase it within rules" | Obligation, promise, escalation state | Promise-to-pay tracking, compliant escalation | ₹ collected | **STRONG** |
| **P1 ↔ P9** | Both are money that failed to move, opposite directions | Payment/refund state, bank response codes | Three-way state reconciliation | Completion rate | **MODERATE** |
| **P1 → P8** | Failed recurring debits generate disputes — Visa 13.2 = 8.5% of chargebacks | Subscription → payment → dispute IDs | Second-order risk of your own actions | Chargeback ratio | **STRONG** |
| **P8 → P4** | Chargeback ratio >1% is a documented freeze trigger | Merchant chargeback ratio | Threshold-aware action planning | Freezes avoided | **STRONG** |
| **P15 → P4** | Fraud flags are a documented freeze trigger | Risk flags, anomaly scores | FP-cost modelling | FP cost in frozen days | **STRONG** |
| **P17 → P4** | Stale KYC/GST/PAN is a documented freeze trigger | KYC document state | Document currency monitoring | Freezes avoided | **MODERATE** |
| **P13 → P4** | PA compliance flags are a documented freeze trigger | Compliance state | — | Freezes avoided | **MODERATE** |
| **P8 → P6** | Chargeback deductions are a **named field** in the settlement report | Settlement report fields | Multi-source matching | Match rate | **STRONG** |
| **P9 → P6** | Refund offsets are a **named field** in the settlement report | Settlement report fields | Multi-source matching | Match rate | **STRONG** |
| **P19 → P6** | Late authorisation is the named exception class inside reconciliation | Provisional status, timestamps | Provisional-state handling | Exceptions cleared | **STRONG** |
| **P6 ↔ P7** | Reconciliation produces the cash position; settlement timing determines when | UTR, settlement date, net settled | Matching → forecasting | Cash-position accuracy | **STRONG** |
| **P18 → P7** | Collections outcomes drive the cash forecast | Invoice, promise date, receipt | Probability-weighted forecasting | Forecast accuracy | **MODERATE** |
| **P5 ↔ P8** | AI-led transactions have **no defined dispute/liability path** | Agent consent token, transaction context | Bounded autonomy + error handling | Disputed-agent-txn rate | **STRONG** |
| **P5 → P16** | Agentic checkout is a checkout | Session, cart, catalog | Conversational conversion | Conversion | **MODERATE** |
| **P11 → P20** | COD loss falls on the merchant because COD is barred from escrow | COD flag, order value | — | ₹ per RTO | **MODERATE** |
| **P11 ↔ P15** | Return abuse is fraud-adjacent | Customer return history | Abuse-pattern detection | Abuse rings caught | **MODERATE** |
| **P4 → P10**, **P9 → P10**, **P6 → P10**, **P8 → P10** | Unresolved problems become tickets | Ticket ↔ merchant ID | Triage | Cost per ticket | **MODERATE** (sink) |

---

## 3. Removed edges

Cut because they failed the tests, not because they were inconvenient.

| Edge | Grade | Why removed |
|---|---|---|
| P3 take-rate ↔ any operational problem | **ARTIFICIAL** | Economic backdrop, not a causal input to any operational loop. Sharing the word "revenue" is not a connection |
| P14 IPO ↔ anything | **ARTIFICIAL** | Corporate finance. No shared data, workflow or event |
| P12 cross-border ↔ P2 | **WEAK** | Both concern "success rates", but different rails, different failure taxonomy, different counterparties. Vocabulary overlap only |
| P16 abandonment ↔ P6 reconciliation | **ARTIFICIAL** | An abandoned cart never becomes a settlement line. There is nothing to reconcile |
| P10 support ↔ P5 agentic | **WEAK** | Plausible ("agents could do support") but no shared data or workflow in the evidence base |
| P17 onboarding ↔ P2 success rate | **WEAK** | Passes only the vaguest causal test |
| P11 RTO ↔ P1 mandates | **ARTIFICIAL** | Physical goods vs recurring digital billing. No shared field, no shared workflow |

---

## 4. ⚡ The trade-off edge — the one that catches people out

### P11 (RTO reduction) ⚡ P16 (checkout abandonment)

These pull **against** each other, and almost every naive submission misses it.

- The dominant lever for reducing RTO is **pushing customers from COD to prepaid** — and the
  evidence supports it: one brand cut RTO from 39% to 21% using prepaid incentives, pincode routing
  and address verification.
- But **forcing prepaid raises checkout abandonment.** Baymard's stated abandonment causes are led by
  "extra costs too high" (40%) and card distrust (19%). In an Indian market where COD exists
  precisely because of trust deficit, removing it removes conversions.

| Test | Result |
|---|---|
| Causal | ✅ — but **negatively**. Solving P11 by the obvious lever worsens P16 |
| Data | ✅ Same checkout session, same COD flag, same customer |
| Workflow | ✅ Both decisions are made at the same moment, on the same screen |
| Outcome | ⚡ **Opposed**: RTO rate down, conversion down |

**Grade: STRONG (negative).** Kept in the primary graph precisely *because* it is negative.

> **How to use it.** If you build in Track 2 on return-risk, a judge can ask: *"what did this cost
> you in conversion?"* A submission that reports **both** RTO reduction and abandonment impact —
> and picks a threshold on the joint curve — is demonstrating the honest-metrics behaviour every
> bar demands. One that reports only RTO reduction has optimised one number by damaging another and
> not noticed.

**A second, milder tension: P1 ⚡ P8.** Recovering aggressively raises disputes. Recovery rate and
chargeback ratio are opposed beyond some intensity. The stopping rule is where you place yourself
on that curve.

---

## 5. Graph properties

### Critical nodes (highest in-degree — where problems converge)

| Node | In-degree | Significance |
|---|---|---|
| **P4 fund holds** | 4 (P8, P15, P17, P13) | **The terminal severity node.** Four upstream problems all end here, and here the merchant's entire revenue stops rather than degrades |
| **P6 reconciliation** | 4 (P8, P9, P19, P2) | **The convergence node.** Every transaction outcome must eventually appear as a settlement line. Chargebacks and refunds are literally fields in the artefact |
| **P10 support** | 4+ | **Sink.** Symptom of everything upstream; poor build target |

### The bottleneck — solve this and several problems unlock

**Failure classification over Razorpay's published error taxonomy.**

P2, P1, P9 and P19 all begin with the same unanswered question: *why didn't this money move?*
Razorpay publishes the ontology to answer it — per-method error codes, an enumerated `source`
attribution field, and a reason → next-best-action mapping. **Whoever builds a good classifier over
that taxonomy has the first stage of four different agents.** It is the highest-leverage single
component in the graph, and it is buildable from public documentation.

### Most valuable edge

**P8 → P4 (chargeback ratio → fund freeze).** It converts a low-rate, low-severity problem (0.26% of
transactions) into a catastrophic one (all funds, 1–3 weeks). Any agent acting in the recovery or
dispute domain that ignores this edge can *cause* the worst outcome in the graph while optimising
its own metric.

### Most powerful end-to-end workflow

**Detect → classify (shared taxonomy) → decide intervention → act within bounds → verify → reconcile
→ update cash position.**

Spans P1, P2, P9, P18 (chain A) and P6, P19, P7 (chain C), joined at the reconciliation step. This
is one coherent workflow that a single finance-ops or revenue-ops owner would recognise — and it is
the spine of both Track 3 and Track 4.

---

```
PHASE 4 VALIDATION

Strong connections:
  P2 <-> P1     same failure event, shared error taxonomy
  P1 <-> P18    same "money owed" loop, shared escalation machinery
  P1 -> P8      failed recurring debits generate disputes (Visa 13.2 = 8.5% of chargebacks)
  P8 -> P4      chargeback ratio >1% is a documented Razorpay freeze trigger
  P15 -> P4     fraud flags are a documented freeze trigger
  P8 -> P6      chargeback deductions are a named settlement-report field
  P9 -> P6      refund offsets are a named settlement-report field
  P19 -> P6     late authorisation is the named exception class
  P6 <-> P7     reconciliation produces the cash position
  P5 <-> P8     AI-led transactions have no defined dispute/liability path
  P11 <-> P16   NEGATIVE/trade-off edge (see below)

Moderate connections:
  P1 <-> P9, P17 -> P4, P13 -> P4, P18 -> P7, P5 -> P16, P11 -> P20, P11 <-> P15,
  and the four support-sink edges into P10

Weak connections removed:
  P12 <-> P2 (vocabulary overlap: "success rate", different rails entirely)
  P10 <-> P5 (plausible, no shared data or workflow)
  P17 <-> P2 (vaguest causal test only)

Artificial connections removed:
  P3 <-> anything operational (shares the word "revenue", nothing else)
  P14 <-> anything (corporate finance)
  P16 <-> P6 (an abandoned cart never becomes a settlement line)
  P11 <-> P1 (physical goods vs recurring digital billing)

Most important connected chain:
  Chain A - "money owed didn't arrive": P2 / P1 / P9 / P18 share one detect-classify-intervene-
  verify loop over one published error taxonomy. P1, P9 and P18 are not three problems; they
  are one agent pointed at three ledgers.

Why this chain is genuinely connected:
  It is not a conceptual grouping. The four problems share the SAME PUBLISHED DATA STRUCTURE -
  Razorpay's per-method error codes, the enumerated `source` attribution field (bank / gateway /
  customer / issuer), and the reason -> next-best-action mapping. The classification stage is
  literally identical code across all four; only the intervention policy differs. Causal test
  passes (better classification improves every downstream recovery), data test passes at the
  level of shared field definitions, workflow test passes (one revenue-ops owner), outcome test
  passes (rupees recovered is the metric in all four).

Runner-up chain, and the one with the sharpest insight:
  Chain B - P1 -> P8 -> P4. Both links are documented rather than inferred, and together they
  explain what Track 3's required "stopping rules" are actually protecting against: your own
  recovery agent pushing the merchant's chargeback ratio past the 1% freeze trigger.

Confidence: 8/10

READY FOR PHASE 5: YES
```

**Why 8/10.** The STRONG edges rest on physical links — a named field in a settlement report, a
published freeze trigger, a Visa reason-code share — rather than on resemblance, and four candidate
edges were removed as artificial. It is not 9/10 because the MODERATE edges (P17→P4, P13→P4,
P18→P7) are reasoned rather than documented, and because chain B's first link (P1→P8) infers from a
*global* reason-code distribution that Indian recurring-payment failures produce disputes at a
similar rate — plausible and directionally supported, but not measured for India.

---

## 6. What this means for the build

1. **Chain A is a project, not four projects.** Build the classify-decide-act-verify loop once, run
   it over two ledgers (e.g. failed mandates **and** overdue invoices), and you have breadth without
   scope creep. Both are Track 3 named directions.
2. **Chain B gives you your stopping rule.** Not an arbitrary "max 3 retries", but "stop before the
   merchant's chargeback ratio crosses the freeze trigger" — a rule derived from Razorpay's own
   published threshold. That is exactly what "compliant escalation, stopping rules, and an audit
   trail" is asking for.
3. **Chain C is Track 4's spine**, and the settlement report's named fields mean disputes and refunds
   are already inside the reconciliation problem. You do not need to invent the exception classes.
4. **The trade-off edge is a differentiator.** Reporting both sides of an opposed pair is the single
   clearest demonstration of the honest-metrics behaviour every track bar demands.
5. **Build the failure classifier first** whatever you choose. It is the graph's bottleneck, it is
   reusable across four problems, and it is fully specified by Razorpay's public error documentation.

---

*Phase 5 note: your message ended with the header "PHASE 5 — Identify Problem Clusters" but no
instructions beneath it. The clusters follow directly from this graph, and the original protocol's
Phase 5 validation criteria (cohesion, shared infrastructure, economic, overlap tests) are on file.
Say the word and I will run it.*
