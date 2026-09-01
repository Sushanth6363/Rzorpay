# agentic_opportunities.md — Phase 7: What Genuinely Needs an Agent

Compiled 2026-08-25 over the ten open subproblems in
[unsolved_subproblems.md](unsolved_subproblems.md).

## The anti-AI-washing test

Before any candidate is called agentic it must survive three questions:

1. **Could a rules engine do this?** If a `CASE WHEN` resolves it, it is a rules problem.
2. **Could a single ML model do this?** If one prediction ends the job, it is an ML problem.
3. **Does it genuinely need reasoning, multi-step decisions, tool calls, external actions,
   dynamic adaptation and exception handling?** If not, downgrade the level.

Track 2's bar demands *"measured precision and recall on a held-out test set"* — which is ML
language. Track 3's demands *"executes a bounded recovery workflow… with compliant escalation,
stopping rules, and an audit trail"* — which is agent language. **Razorpay is not asking for agents
everywhere, and pretending otherwise is the fastest way to fail a panel.**

| Level | System type |
|---|---|
| **1** | Prediction only |
| **2** | Prediction + recommendation |
| **3** | Recommendation + tool execution |
| **4** | Autonomous multi-step agent |
| **5** | Multi-agent workflow |

---

## 1. Classification of all ten open subproblems

| # | Subproblem | Level | Honest verdict |
|---|---|---|---|
| 1 | Reconciliation exception resolution | **4** | ✅ Genuinely agentic — multi-source, iterative, exception-dominated |
| 2 | **Self-cure attribution** | **1** | ❌ **Not an agent.** This is experiment design and statistics |
| 3 | Retry timing against funds availability | **2 → 4** | ⚠️ The *prediction* is Level 2; it becomes Level 4 only when it executes and adapts |
| 4 | Stopping rules from chargeback headroom | **3** | ⚠️ A *constraint layer* on another agent, not an agent itself |
| 5 | Merchant freeze exposure + case navigator | **4** | ✅ Genuinely agentic — document assembly, drafting, escalation over time |
| 6 | Cross-period deduction linking | **3** | ⚠️ Mostly retrieval + matching; agentic only in the ambiguous tail |
| 7 | Promise-to-pay commitment tracking | **4** | ✅ Genuinely agentic — long-horizon state, negotiation, compliant escalation |
| 8 | Intent verification for agentic purchases | **3** | ⚠️ Verification + gate. Real, but a checkpoint rather than an autonomous loop |
| 9 | False-positive cost in frozen-capital days | **1** | ❌ **Not an agent.** This is cost modelling |
| 10 | Joint RTO/conversion threshold | **1** | ❌ **Not an agent.** This is constrained optimisation |

**Three of my own top-ten are not agentic at all, and one more is a constraint layer.** Saying so is
the point of this phase.

> **But they are not worthless — they are the evidence layer.** Self-cure attribution (#2) is the
> *evaluation harness* that makes a recovery agent's numbers honest. FP-cost-in-frozen-days (#9) is
> what converts a confusion matrix into a business claim. The joint RTO curve (#10) is what proves
> you did not optimise one metric by wrecking another. **Pair a Level-4 agent with one of these
> Level-1 components and you have exactly what every track bar asks for:** an agent that acts, and
> a measurement that is honest about whether the acting worked.

---

## 2. Full specifications — the four genuine Level-4 candidates

Tool names below are **real tools from Razorpay's official MCP server** (45 tools, test-mode keys
auto-detected by prefix). Note `create_refund` is unavailable on the hosted remote server — run
locally if a loop needs it.

### 🥇 A1 — Reconciliation Exception Resolver · **Level 4** · Cluster C2 · Track 4

**Observes:** settlement reports (`fetch_all_settlements`, `fetch_settlement_with_id`,
`fetch_settlement_recon_details`), the payment ledger (`fetch_all_payments`, `fetch_order_payments`),
refunds (`fetch_all_refunds`, `fetch_multiple_refunds_for_payment`), and a merchant-supplied bank
statement or ERP export. The 11 named settlement fields — MDR, GST on MDR, refund offsets, chargeback
deductions, net settled, UTR — are the join keys.

**Reasons about:** which candidate pairing explains an unmatched line; whether a discrepancy is a
fee, a tax component, a cross-period deduction, a late authorisation, or a genuine break; how
material the break is; and whether the evidence is sufficient to propose a resolution or only to
escalate.

**Tools:** the recon and payment fetch tools above; a bank-statement parser; a fuzzy-matcher over
amount/date/counterparty; a ledger writer that only ever writes to a **proposal** table.

**Actions:** propose a match with a confidence score; link a deduction to its originating transaction
across settlement cycles; classify an exception; rank the exception queue by materiality; produce a
close-readiness report.

**Constraints:** ⭐ **never asserts finality.** Writes proposals, never the books — this is the exact
liability that stopped Razorpay from shipping a resolver, and respecting it is the design. Read-only
against Razorpay. Deterministic re-runs on a fixed seed. Every proposal carries its evidence chain.

**Low confidence:** below threshold it does not guess — it emits the exception with the candidates it
considered, the discriminating evidence it lacked, and what a human should check. **The exception
list is a first-class output, not a failure log.**

**Human intervention:** every proposal is accept/reject/amend; rejections become training signal;
materiality ranking decides what a human sees first. A human can always run the batch unattended and
review only the tail.

**Success:** match rate on a held-out batch of ≥500 synthetic records; throughput in records/minute;
**exception count and its composition**; precision of proposed matches (a wrong proposal accepted is
the real failure mode); hours saved against the 20–40/month Razorpay cites.

**Why not a rules engine:** rules match the easy 95%. The residual tail is where the fields
disagree — a rules engine has nothing to say about a deduction that appeared three cycles later with
a different amount because a partial refund intervened.
**Why not one ML model:** the output is not a class, it is a *linked explanation* assembled from
several retrievals, with an abstain option.

---

### 🥈 A2 — Headroom-Aware Recovery Sequencer · **Level 4** (Level 5 only if genuinely warranted, §3) · Cluster C1 · Track 3

**Observes:** failed payments and mandates (`fetch_all_payments` filtered on failure, `fetch_payment`),
Razorpay's published error taxonomy — `bank_technical_error`, `insufficient_funds`,
`payment_declined`, `payment_timed_out`, `vpa_resolution_failed` and the **`source` attribution
field** (bank / gateway / customer / issuer) — plus per-customer failure history and the merchant's
current chargeback ratio.

**Reasons about:** *why* this payment failed, using the published ontology; whether the cause is
transient (bank timeout → retry) or funding (insufficient balance → time it); **when** funds are
likely present, from that customer's own historical success timing; which intervention the reason →
next-best-action mapping recommends; and ⭐ **how much chargeback headroom the merchant has before the
documented 1% freeze trigger.**

**Tools:** payment and order fetches; `create_payment_link` / `create_payment_link_upi` /
`send_payment_link`; `create_registration_link` for re-mandating; `fetch_tokens` for saved methods;
a scheduler; a notification client.

**Actions:** schedule a retry at a predicted-good time; send a payment link; propose a re-mandate;
escalate to the merchant; **stop**.

**Constraints:** hard cap on attempts per customer per window; quiet hours; no rail switching without
a mandate for that rail (a UPI AutoPay consent does not authorise a card debit); ⭐ **halt when the
merchant's projected chargeback ratio approaches the freeze trigger** — the stopping rule is derived
from Razorpay's own published threshold rather than invented; full audit trail per money action.

**Low confidence:** if the failure reason is unclassifiable or the timing model is uncertain, it
defaults to the *least intrusive* action — one payment link, no repeated contact — and flags for
merchant review rather than escalating blind.

**Human intervention:** merchant sets caps, quiet hours and the headroom threshold; every scheduled
action is visible before execution; a kill switch halts the campaign and the audit trail explains
what had already been sent.

**Success:** ⭐ **incremental** ₹ recovered against a **holdout** — never gross recovery, because a
share of failures self-cure; recovery rate by failure class; cost per recovery; **and chargeback
ratio held below the trigger throughout**, which is the constraint the whole design exists to honour.

**Why not a rules engine:** "retry 3 times at 24h intervals" is the rules-engine answer and is
precisely what fails — the dominant cause is funds timing, which is customer-specific.
**Why not one ML model:** a model predicts recovery probability. It does not choose among rails,
respect quiet hours, halt on a risk threshold owned by a different system, or explain itself
afterwards.

---

### 🥉 A3 — Merchant Freeze Navigator · **Level 4** · Cluster C6 · Open Track

**Observes:** the merchant's own settlement state (`fetch_all_settlements`, on-hold state),
chargeback ratio trend, KYC/GST document currency, volume time-series against baseline, and the
merchant's document store.

**Reasons about:** which of the four documented triggers most likely applies (chargeback ratio >1%,
~10x volume spike, stale KYC/GST/PAN, PA compliance flag); which documents the case will require;
where the case sits against the published resolution bands (2–5 days / 1–3 weeks / 30+ days); what
the cash-flow consequence is if it runs long; and what the next escalation step should be.

**Tools:** settlement and payment fetches; a document checker (expiry, completeness); a template
drafter; a case tracker; a cash-flow projector.

**Actions:** assemble the document pack; draft the written-reason request; track elapsed time against
the band; draft the escalation, and — if unresolved — the RBI Ombudsman complaint; project payroll
risk under an extended hold.

**Constraints:** ⭐ **never claims to know why Razorpay froze the account.** It reasons about
*likelihood* from the merchant's own observable data. This respects the AML tipping-off constraint
that legitimately prevents Razorpay from explaining, and it is the line that keeps the project on the
right side of "helping a merchant respond" rather than "coaching evasion of risk controls."
Merchant-side data only. Drafts, never sends, without approval.

**Low confidence:** where the trigger is ambiguous it prepares for the *most likely two* and says so,
rather than committing to one narrative that could mislead the merchant's own submission.

**Human intervention:** every document and draft is reviewed before submission; the merchant owns
all outbound communication.

**Success:** time-to-complete-submission versus manual baseline; document-pack completeness on first
submission (rework is the cost); frozen-capital days modelled; and — the honest metric — **how often
the predicted trigger matched the actual reason**, reported including misses.

**Why not a rules engine:** the case is a moving state over days, with branching evidence and drafting.
**Why not one ML model:** the output is a document pack and a sequence of correspondence, not a class.

---

### A4 — Promise-to-Pay Collections Agent · **Level 4** · Cluster C1 / P18 · Track 3

**Observes:** invoice ledger, ageing buckets, payment history per buyer, prior commitments and
whether they were honoured, contact log.

**Reasons about:** probability of payment by bucket and buyer; prioritisation under limited contact
budget; whether a commitment was made, is pending, or was broken; the compliant next step and its
timing; when to stop and hand to statutory MSME machinery.

**Tools:** invoice/ledger reads; `create_payment_link` and `send_payment_link`; a commitment store;
a template drafter; a calendar.

**Actions:** prioritise the chase list; send a payment link; record a promise; follow up on a broken
promise; escalate; stop.

**Constraints:** ⭐ **operates in the merchant's name, never Razorpay's** — debt collection is
regulated conduct with harassment and contact-hour rules, which is exactly why Razorpay ships nothing
here. Contact frequency caps, quiet hours, tone constraints, and a hard stop into statutory process.

**Low confidence:** where payment probability is uncertain it de-prioritises rather than escalates —
the failure mode to avoid is harassing a good payer.

**Human intervention:** merchant approves the chase list and message templates; any escalation beyond
a reminder requires explicit approval.

**Success:** ₹ collected against ₹ overdue on a batch; DSO movement against the 73-day benchmark;
promise-kept rate; contacts per rupee collected; **and complaints or opt-outs, reported honestly.**

---

## 3. Is Level 5 (multi-agent) ever justified here?

**Usually no.** Splitting one workflow across several agents to look sophisticated is AI washing with
extra steps, and a panel will ask why.

**One case genuinely qualifies:** a **Recovery agent** and a **Risk-headroom agent** with *opposed
objectives* — one maximises rupees recovered, the other enforces the chargeback-ratio budget and can
veto. They have different data scopes, different success metrics, and a real negotiation at the
boundary. That is a multi-agent system for a reason, not for a diagram.

Everything else in this phase is one agent with several tools. **A2 as a two-agent system is
defensible; A1, A3 and A4 as multi-agent systems would not be.**

---

## 4. Ranked agentic opportunities

| Rank | Opportunity | Level | Track | Why it wins on agentic merit |
|---|---|---|---|---|
| **1** | **A1 Reconciliation Exception Resolver** | 4 | 4 | Exception handling *is* the job; abstention is a designed output; multi-source by nature |
| **2** | **A2 Headroom-Aware Recovery Sequencer** | 4–5 | 3 | The stopping rule comes from a documented cross-domain threshold — genuine multi-step reasoning about consequences of its own actions |
| **3** | **A3 Merchant Freeze Navigator** | 4 | Open | Long-horizon case state, document assembly, drafting, escalation — and a constraint-respecting design |
| **4** | **A4 Promise-to-Pay Collections** | 4 | 3 | Long-horizon commitments and compliant escalation; nearly uncontested |
| 5 | A5 Intent verification for agentic purchases | 3 | 1 | Real, but a checkpoint rather than a loop |

---

```
PHASE 7 VALIDATION

Genuinely agentic problems (Level 4+):
  A1 Reconciliation exception resolution   - multi-source, iterative, exception-dominated
  A2 Headroom-aware recovery sequencing    - reasons about consequences of its own actions
  A3 Merchant freeze case navigation       - long-horizon state, assembly, drafting, escalation
  A4 Promise-to-pay collections            - commitments over time, compliant escalation

AI-washing candidates removed or downgraded:
  Self-cure attribution              -> Level 1. Experiment design and statistics, not an agent.
  False-positive cost in frozen days -> Level 1. Cost modelling.
  Joint RTO/conversion threshold     -> Level 1. Constrained optimisation.
  Retry-timing prediction alone      -> Level 2. Only becomes agentic when it executes and adapts.
  Stopping rules from headroom       -> Level 3. A constraint layer ON an agent, not an agent.
  Cross-period deduction linking     -> Level 3. Retrieval and matching; agentic only in the tail.
  Intent verification                -> Level 3. A gate, not an autonomous loop.

  Three of the ten open subproblems are not agentic at all. They are retained as the EVIDENCE
  LAYER that makes an agent's claims honest - which is what every track bar actually demands.

Why agents are necessary (where they are):
  In all four Level-4 cases the output is not a prediction but a SEQUENCE OF BOUNDED ACTIONS
  taken over time against changing state, where the correct behaviour in the hard cases is to
  ABSTAIN and escalate. A classifier cannot abstain into a document pack. A rules engine cannot
  reason about why three settlement lines disagree. The abstention path is the clearest single
  test: if "I don't know, here is what I checked and what a human should look at" is a
  first-class output, it is an agent problem.

Strongest agentic opportunity:
  A1 Reconciliation Exception Resolver. Exception handling is the entire job rather than an
  edge case; the honest exception list is literally Track 4's stated bar; it runs on the least
  crowded track; and its central design constraint - propose with confidence, never assert
  finality - is derived from the specific liability that explains why Razorpay shipped a viewer
  in June 2022 and has not shipped a resolver since.

Runner-up:
  A2, whose stopping rule is the most defensible design decision available in this entire
  research corpus: halt recovery before the merchant's chargeback ratio crosses Razorpay's own
  published 1% freeze trigger. It answers "what are your stopping rules?" with a documented
  external threshold rather than an arbitrary retry cap.

Confidence: 8/10

READY FOR PHASE 8: YES
```

**Why 8/10.** Level assignments were made against a stated three-question test and applied against
my own preferred candidates — three of the top ten were downgraded to Level 1, which is the evidence
the test was real. It is not 9/10 because the Level 3-versus-4 boundary is genuinely fuzzy for
cross-period linking and intent verification, and because the agent specifications are designs, not
implementations — the honest test of whether abstention works as a first-class output only comes
from building it.
