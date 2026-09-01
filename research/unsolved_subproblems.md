# unsolved_subproblems.md — Phase 6: What Remains Difficult

Compiled 2026-08-25 over the clusters in [problem_clusters.md](problem_clusters.md), using the
current-methods and constraint analysis in [problems_priority.md](problems_priority.md) §6.

## The test applied

For every candidate subproblem: *does Razorpay already have a product or feature for this?* Checked
against product pages, the Agent Studio roster, developer docs, the MCP tool list, newsroom and
blog. Then classified:

| Verdict | Meaning |
|---|---|
| **OPEN** | No Razorpay product addresses it |
| **PARTIALLY SOLVED** | A product exists but a specific, nameable gap remains |
| **SOLVED** | Razorpay addresses it substantially — **downgrade, do not build** |
| **UNKNOWN** | Insufficient evidence either way |

**Skepticism rule applied throughout:** a shipped product that *displays* or *scores* something is
not a solution to *acting* on it — but neither is "they only have a dashboard" an automatic gap. The
question is always whether the remaining work is **specific and nameable**. "Fraud detection is still
hard" is not a subproblem. "Nobody prices a false positive in frozen-capital days" is.

---

## 1. Cluster C2 — Settlement Truth / Finance Close

**What Razorpay already does:** *Single View Recon* (Optimizer, June 2022) consolidates transaction
status, UTRs, Settlement IDs and processing aggregator into one view. *Settlement Insights*
(Agent Studio) sends a daily WhatsApp settlement summary. `fetch_settlement_recon_details` exposes
the recon report via API. The Dashboard carries a first-class "settlements on hold" state.

**What these appear to solve:** **visibility.** Every shipped capability shows you data in one place.
By Razorpay's own account, merchants still spend **20–40 work-hours/month** downloading files from
each aggregator and matching by hand.

| Existing Capability | Remaining Pain Point | Why Existing Approach Isn't Enough | Potential AI Opportunity | Verdict |
|---|---|---|---|---|
| Single View Recon (consolidated view) | **The unmatched tail.** Bulk matching on amount/date/UTR is trivial; the residual few percent consumes the time | A viewer surfaces mismatches for a human to resolve. It never proposes a resolution, because **asserting a match writes into the merchant's statutory books** — a liability Razorpay rationally declines | Agent that proposes candidate matches **with confidence scores**, ranks the exception queue by materiality, and escalates rather than asserts | **OPEN** |
| `fetch_settlement_recon_details` | **Cross-period deductions.** A chargeback deduction or refund offset lands in a *later* settlement than the original sale, so the sale and its reversal never appear in the same cycle | The API returns a cycle at a time. Linking a deduction back to a transaction from three cycles ago is manual archaeology | Temporal linking agent that reconstructs the transaction↔deduction chain across settlement periods | **OPEN** |
| Settlement report schema (11 named fields) | **Net-only reporting and missing UTRs.** Razorpay itself names these as failure modes that make payouts impossible to match to bank credits | Razorpay documents the failure mode but ships no remediation — when the UTR is absent the trail simply ends | Agent that infers the missing linkage from amount/date/counterparty patterns and flags irreducible cases honestly | **OPEN** |
| Optimizer (multi-gateway routing) | **Multi-gateway normalisation.** Optimizer exists *because* merchants run 100+ providers — which fragments settlement across schemas Razorpay does not control | Normalising a competitor's settlement file reduces switching costs away from Razorpay (commercial disincentive) and there is no industry schema | Schema-inference agent that maps arbitrary PSP settlement exports onto a canonical model | **OPEN** |
| — (no product) | **Tax-line matching.** GST-on-MDR and TDS treatment vary by merchant and state | "Tax-line matcher" is an official example direction with **no Razorpay product behind it**, because a generic engine would produce tax-wrong results for some merchants | Agent that proposes tax treatment per line with jurisdiction reasoning and abstains where ambiguous | **OPEN** but ⚠️ *no magnitude was ever found for this* |
| — (no product) | **Materiality judgement at close.** Which exceptions block the books and which can be carried? | Purely human judgement today; no product attempts it | Exception triage ranked by materiality and audit risk | **OPEN** |
| Late-authorisation handling | **Provisional status.** Payment status finalises minutes-to-hours after the transaction, forcing repeated re-checks before books balance | Razorpay documents the behaviour; the delay originates at the bank, so Razorpay cannot promise finalisation timing | Provisional-state agent that holds, re-checks and emits a corrected line with a confidence trail | **PARTIALLY SOLVED** — documented but unremediated |

**Cluster verdict: OPEN, and it is the cleanest gap in the corpus.** Four years after Single View
Recon shipped, the *resolution* half is untouched — and §6's audit-liability analysis explains why
that is a rational choice for Razorpay rather than an oversight.

---

## 2. Cluster C1 — The Money-Didn't-Arrive Engine

**What Razorpay already does:** *Subscription Recovery* (analyses failed subscription payments,
applies smarter retry logic, triggers targeted nudges; voice by ElevenLabs). *Optimizer* routing.
*Vulcan* (routing, fraud, conversion). Payment links, registration links, mandate APIs. Published
error taxonomy with `source` attribution and a reason → next-best-action mapping.

**What these appear to solve:** **retrying and nudging after a failure.**

| Existing Capability | Remaining Pain Point | Why Existing Approach Isn't Enough | Potential AI Opportunity | Verdict |
|---|---|---|---|---|
| Subscription Recovery (retry logic) | **Retry *timing* against funds availability.** The dominant failure cause is insufficient balance at the trigger moment — a timing problem, not a retry-count problem | "Smarter retry logic" reschedules attempts; it does not model *when the money will be there*. Razorpay cannot see the balance, so it cannot check — but a predictive approach never needs to | Sequencer learning per-customer success timing from failure history, salary-cycle patterns and the mandatory 24h notification window | **PARTIALLY SOLVED** — strongest remaining gap in the cluster |
| Reason → next-best-action mapping (published) | **Nothing executes it.** Razorpay publishes a downloadable spreadsheet mapping each failure reason to a recommended action, and ships no agent that performs the action | A documented mapping is a lookup table, not a workflow. The merchant still decides and acts | Classifier over the published taxonomy driving a bounded intervention policy — the graph's bottleneck component | **OPEN** |
| Subscription Recovery + Dispute Responder (separate agents) | **Nobody models the interaction.** Aggressive recovery raises disputes (Visa 13.2 = 8.5% of chargebacks); disputes past 1% trigger a freeze | Two agents optimising separate metrics, with no shared view of the merchant's chargeback headroom. The recovery agent can cause the worst outcome in the graph while improving its own number | Stopping rule derived from live chargeback-ratio headroom against the documented 1% freeze trigger | **OPEN** ⭐ |
| — (no product) | **Promise-to-pay state.** No system records "the customer said they'd pay on the 5th" and reconciles against it | "Promise-to-pay tracker" is an official example direction with no product behind it | Commitment-tracking agent with escalation ladders and compliant contact rules | **OPEN** |
| — (no product) | **Self-cure attribution.** A large share of failed payments recover on their own. Any recovery agent without a holdout is claiming credit for money that would have arrived anyway | Razorpay publishes no recovery baseline. Neither does any competitor repo sampled | Counterfactual evaluation — treated vs holdout — reporting *incremental* recovery | **OPEN** ⭐⭐ |
| Agent Studio (merchant-facing agents) | **Compliant collections communication.** What may be said, to whom, how often, at what hour | Collections conduct is regulated (recovery-agent guidelines, harassment rules), which is exactly why Razorpay ships nothing here | Draft-and-escalate agent operating in the *merchant's* name with rule-bounded cadence | **OPEN** |

> ⭐⭐ **Self-cure attribution is the highest-leverage unsolved item in this cluster, and almost
> nobody will do it.** It is simultaneously (a) a real unsolved measurement problem, (b) the honest
> way to report "money recovered", and (c) a literal reading of Track 2's *"held-out test set"* and
> Track 3's *"measured money recovered across a batch"*. A submission that reports **incremental**
> recovery against a holdout is doing something that neither Razorpay nor the 88 competing recovery
> repos appear to be doing.

**Cluster verdict: PARTIALLY SOLVED**, with three genuinely OPEN subproblems (timing, cross-agent
stopping rules, attribution).

---

## 3. Cluster C6 — Merchant Operations Navigator

**What Razorpay already does:** **nothing productised.** A June 2026 blog naming freeze triggers and
resolution bands; a support-ticket path; a "settlements on hold" dashboard state; advice to
*negotiate hold triggers into your gateway contract*.

| Existing Capability | Remaining Pain Point | Why Existing Approach Isn't Enough | Potential AI Opportunity | Verdict |
|---|---|---|---|---|
| Blog guidance + support tickets | **Document pack assembly.** KYC-gap holds clear in 2–5 days and are largely document-shuffling | Razorpay's own remedy is "raise a ticket, request the reason in writing, assemble documents, escalate, then go to the Ombudsman" — a wholly manual runbook | Case agent that assembles the required pack, tracks the case against published bands and drafts each escalation | **OPEN** |
| Dashboard chargeback metrics | **Pre-threshold self-monitoring.** Razorpay recommends merchants alert at 0.5% against a 1% trigger — but ships no alerting | Razorpay is constrained from warning merchants (warning a fraudulent merchant lets them cash out). **The merchant is not constrained from monitoring themselves** | Merchant-side exposure monitor computing headroom to the freeze trigger from the merchant's own data | **OPEN** ⭐ |
| — | **Cash-flow replanning during a hold** — 30+ day holds with no ability to model the consequences | Cashflow Forecaster predicts 3–7 days ahead and does not model a freeze scenario | Scenario agent: "if this hold runs 30 days, here is payroll risk and here are the levers" | **OPEN** |
| — | **Reason discovery** | ❌ **HARD-BLOCKED.** AML "tipping off" means a regulated entity often *may not* disclose why an account is under review | — | **SOLVED-BY-CONSTRAINT** — do not build |

**Cluster verdict: OPEN**, with one sub-item explicitly off-limits. The distinction between "help the
merchant respond" (open) and "explain the risk decision" (blocked) is the whole design.

---

## 4. Cluster C4 — Agentic Commerce Trust

**What Razorpay already does:** UPI Reserve Pay pilot with Claude (one-time scoped consent,
per-merchant cap, instant revoke, ~₹10,000 block), Agent Studio as an emerging open ecosystem, the
official MCP server (45 tools), Magic Checkout, and piloted conversational and voice checkout.

| Existing Capability | Remaining Pain Point | Why Existing Approach Isn't Enough | Potential AI Opportunity | Verdict |
|---|---|---|---|---|
| UPI Reserve Pay consent model | **Intent verification.** Consent and caps prove the human authorised *a merchant and an amount* — not that the agent bought *what they meant* | Rail-level consent is amount-scoped, not intent-scoped. A cap does not catch "right price, wrong product" | Intent-attestation layer: capture the instruction, verify the cart against it, gate on divergence | **OPEN** |
| — (no standard) | **Agent-readable catalog** | The one official Track 1 direction with **no Razorpay product and no evidenced problem** — genuinely unoccupied territory | Machine-readable catalog + availability/price attestation for AI buyers | **OPEN** but ⚠️ *you must establish the problem yourself* |
| Dispute Responder | **Disputes for AI-led transactions.** No defined liability or recourse path when an agent transacts wrongly | Evidenced void: UAP is unlaunched and NPCI will authenticate agents but **not track purchase specifics**, leaving intent-level trust to intermediaries | Agent-transaction dispute record: what was instructed, what was bought, what diverged | **OPEN** ⭐ |
| — | **Agent error handling.** Razorpay's MD publicly concedes agents will make mistakes and "the system has to allow for a certain level of mistakes so that you can learn from them and correct them" | Nothing productised implements that tolerance | Error-taxonomy + correction loop for agent actions, with human escalation | **OPEN** |
| Conversational in-app checkout | — | ✅ Razorpay has **already piloted this** with Vodafone, and voice with Gnani.ai and SuperU | — | **SOLVED — downgrade** |

**Cluster verdict: PARTIALLY SOLVED.** The rail is handled; intent and liability are not.

---

## 5. Cluster C3 — Risk Exposure → Freeze Prevention

**What Razorpay already does:** Dispute Responder, Thirdwatch, Vulcan fraud detection, RTO Shield.

| Existing Capability | Remaining Pain Point | Why Existing Approach Isn't Enough | Potential AI Opportunity | Verdict |
|---|---|---|---|---|
| Dispute Responder | **Evidence assembly across merchant systems.** The decisive evidence — delivery proof, customer comms, T&C acceptance — sits with the merchant and its courier | Razorpay can auto-respond with what it holds; it cannot compel what it does not | Merchant-side evidence collator assembling the pack at transaction time, before it decays | **PARTIALLY SOLVED** |
| Vulcan fraud detection | **False-positive cost accounting.** Nobody prices a false positive in the currency that matters — frozen-capital days for the merchant | Detection is optimised on precision/recall; the downstream freeze is a different team's metric | FP-cost model expressing risk thresholds in rupees and frozen days | **OPEN** ⭐ |
| — | **Cross-merchant fraud rings** | ❌ **HARD-BLOCKED** by DPDP purpose limitation and competition-law exposure on shared negative lists | — | **BLOCKED — do not build** |
| — | **Pre-threshold warning to merchants** | ❌ **HARD-BLOCKED** — warning a fraudulent merchant enables cash-out | — | **BLOCKED for Razorpay** (but see C6: the *merchant* may monitor themselves) |
| Vulcan (8x fraud detection claim) | Generic fraud detection | ✅ **Downgrade.** Vulcan trains on ~3 trillion data points from ~4bn payments/year. You cannot beat this on public data | — | **SOLVED — downgrade** |

**Cluster verdict: PARTIALLY SOLVED, with the two most attractive subproblems hard-blocked.** Only
FP-cost accounting is genuinely open, and it is an *analysis* contribution more than a product.

---

## 6. Cluster C5 — Physical-Goods Loss

**What Razorpay already does:** RTO Shield (pre-dispatch COD risk via LLM address validation and
bad-pincode intelligence), RTO Insights (pattern analysis), Vulcan RTO Risk Intelligence, and an RTO
Analytics Dashboard with COD-vs-prepaid split.

| Existing Capability | Remaining Pain Point | Why Existing Approach Isn't Enough | Potential AI Opportunity | Verdict |
|---|---|---|---|---|
| RTO Shield / Insights / Vulcan | Pre-dispatch COD risk scoring | ✅ **Three products against one problem.** Downgrade aggressively | — | **SOLVED — downgrade** |
| RTO Analytics Dashboard | **Merchant delivery-data coverage below 100%**, which gates model accuracy | Razorpay's own dashboard exposes a "Delivery Data" coverage widget — it knows coverage is short. The data belongs to the merchant's courier | — | **BLOCKED (C4 data ownership)** |
| RTO Shield + Magic Checkout (separate) | ⚡ **The RTO↔conversion trade-off is unmanaged.** The proven RTO lever is pushing prepaid — which raises abandonment | Two products optimise opposed metrics with no joint objective. **No one publishes a joint operating curve** | Threshold optimiser on the joint RTO/conversion curve, reporting both sides | **OPEN** ⭐ — *the one real gap in a heavily solved area* |

**Cluster verdict: SOLVED — downgrade the cluster**, except the trade-off curve.

---

## 7. Ranked open subproblems

Filtered to OPEN or PARTIALLY-SOLVED-with-a-nameable-gap, and not hard-blocked.

| # | Subproblem | Cluster | Why it survives skepticism |
|---|---|---|---|
| **1** | **Reconciliation exception *resolution* with confidence scores and materiality triage** | C2 | Four years of a viewer and no resolver; the audit-liability reason is specific and it does not bind a student |
| **2** | **Self-cure attribution for recovery** | C1 | No baseline published by anyone; it *is* the honest reading of "measured money recovered" |
| **3** | **Retry timing against predicted funds availability** | C1 | "Smarter retry logic" ships; timing intelligence does not |
| **4** | **Stopping rules tied to chargeback-ratio headroom** | C1/C3 | Two shipped agents optimise opposed metrics with no shared view |
| **5** | **Merchant-side freeze exposure monitor and case navigator** | C6 | Razorpay is constrained from warning; the merchant is not constrained from monitoring |
| **6** | **Cross-period deduction linking** | C2 | Chargebacks and refunds land in later cycles than the sale; the API returns one cycle |
| **7** | **Promise-to-pay commitment tracking** | C1 | Official example direction, no product |
| **8** | **Intent verification for agentic purchases** | C4 | Consent is amount-scoped, not intent-scoped |
| **9** | **False-positive cost in frozen-capital days** | C3 | Detection and freeze are different teams' metrics |
| **10** | **Joint RTO/conversion threshold optimisation** | C5 | The only unmanaged surface in a heavily solved area |

## 8. Explicitly downgraded — Razorpay solves these well

| Do not build | Because |
|---|---|
| Generic fraud detection | Vulcan: ~3tn data points, ~4bn payments/year. Unwinnable on public data |
| Chargeback auto-response | Dispute Responder ships it — **and disputes cannot be created in test mode** |
| RTO / COD risk scoring | Three products: RTO Shield, RTO Insights, Vulcan RTO Intelligence |
| Abandoned-cart recovery | Agent Studio ships two partner-built variants (SuperU, Nugget by Zomato) |
| Conversational / voice checkout | Already piloted: Vodafone, Gnani.ai, SuperU; ElevenLabs powers Subscription Recovery |
| Payment routing / success-rate optimisation | Optimizer + Vulcan; NPCI and bank dependencies block the rest |
| Settlement summaries | Settlement Insights ships a daily WhatsApp digest |
| Cash-flow forecasting (3–7 day) | Cashflow Forecaster ships it |
| Merchant onboarding | Agentic Onboarding ships it |
| Cross-merchant fraud rings / shared blacklists | Hard-blocked: DPDP purpose limitation + competition law |
| Explaining why an account was frozen | Hard-blocked: AML tipping-off |

---

```
PHASE 6 VALIDATION

Open problems: 10        (the ranked list in section 7)
Partially solved: 5      (retry timing, evidence assembly, late-auth provisional states,
                          agentic rail vs intent, dispute response)
Solved: 9                (section 8 downgrade list)
Blocked by constraint: 4 (cross-merchant rings, pre-threshold warning, reason disclosure,
                          delivery-data coverage) - distinct from "solved": nobody has done
                          them and nobody legitimately can
Unknown: 2               (tax-line matching magnitude; whether Agent Studio's roster has grown
                          since 12 Mar 2026 - the product page is client-side rendered and
                          defeated every fetch attempt)

Ideas eliminated because Razorpay already solves them:
  generic fraud detection, chargeback auto-response, RTO scoring, abandoned-cart recovery,
  conversational/voice checkout, payment routing, settlement summaries, cash-flow forecasting,
  merchant onboarding. Nine of the buildathon's own example directions are on this list.

Most promising remaining gaps:
  1. Reconciliation exception RESOLUTION (C2) - a viewer has shipped since June 2022 and the
     resolver has not, for a reason (audit liability) that is specific, defensible, and does
     not apply to a student project.
  2. Self-cure attribution (C1) - the only way to report recovery honestly, and neither
     Razorpay nor any sampled competitor repo appears to do it.
  3. Merchant-side freeze exposure monitoring (C6) - Razorpay is constrained from warning
     merchants; merchants are not constrained from monitoring themselves.

Evidence:
  - Razorpay states merchants spend 20-40 work-hours/month on multi-gateway reconciliation and
    describes the process as manual "download and reconcile by hand" [Razorpay blog].
  - Single View Recon (June 2022) is documented as a consolidated VIEW - status, UTRs,
    Settlement IDs, aggregator - with no matching or resolution capability.
  - Razorpay publishes a reason -> next-best-action mapping and ships no agent that executes it.
  - Razorpay recommends merchants self-monitor chargebacks at 0.5% against its own 1% freeze
    trigger, while shipping no alerting.
  - Agent Studio's launch page names refunds in the pain surface it targets and ships no refund
    agent; it contains nothing on fund holds, B2B receivables or reconciliation exceptions.
  - Shashank Kumar (Business Standard, 12 Mar 2026): "The system has to allow for a certain
    level of mistakes so that you can learn from them and correct them."

Confidence: 8/10

READY FOR PHASE 7: YES
```

**Why 8/10.** Every OPEN verdict was checked against a named product surface rather than assumed,
and nine candidate ideas were eliminated as already-solved — including nine of Razorpay's own
example directions, which is the strongest evidence the skepticism was applied rather than
performed. It is not 9/10 because the Agent Studio roster could not be verified as current (the
product page defeated fetching, and the launch blog is five months old and promises third-party
agents), so any "no product exists" claim carries that risk. The tax-line magnitude also remains
unknown.
