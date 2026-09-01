# top5.md — Phase 14: The Five Worth Building

Compiled 2026-08-25 from [final_ranking.md](final_ranking.md).

## How these five were chosen

**Not** by taking the top 5 scores. Three of the top-ranked entries — cross-period deduction linking
(#5), self-cure attribution (#6), late-authorisation resolution (#12) — are **components, not
projects**. They are absorbed into the projects they belong to. The five below are the ones that
stand alone as a submission.

**Track coverage is deliberate:** T4, T3, T3, Open, T1. You submit under one track; having a
defensible option in four of five means the choice can be made on fit rather than forced.

| # | Project | Track | Score | Character |
|---|---|---|---|---|
| **1** | Reconciliation Exception Resolver | **T4** | 7.35 | Lowest variance, best data |
| **2** | Recovery Sequencer with headroom veto | **T3** | 7.30 | Highest impact, worst competition |
| **3** | Promise-to-Pay with MSME statutory escalation | **T3** | 7.10 | Emptiest space found |
| **4** | Merchant Freeze Exposure Monitor | **Open** | 7.05 | Highest novelty, fragile |
| **5** | Agentic Purchase Intent Verifier | **T1** | 6.95 | Best demo, most crowded |

---

# 1. Reconciliation Exception Resolver ⭐ *the recommendation*

**Problem.** An Indian merchant running more than one payment provider closes their books by hand.
Settlement lines carry MDR, GST-on-MDR, refund offsets, chargeback deductions, net settled and a bank
UTR — and a share of them will not match. The bulk match is trivial; the residual tail eats the month.

**Why Razorpay cares.** Razorpay states the number itself: merchants spend **20–40 work-hours/month**
reconciling, and describes finance teams as needing to *"download and manually reconcile payments and
settlements"* by hand. It names the failure modes — net-only reporting, missing UTRs — and ships
**Single View Recon (June 2022)**, which *views*. Track 4's build spec is almost a description of this
problem: *"closes one finance-ops loop across a 50+ record batch of synthetic data, reporting its
match rate and the exceptions it could not resolve."*

**Existing solutions.** ⚠️ **CORRECTED 2026-08-25 after a full product audit** — Razorpay has
**three** reconciliation surfaces, not one: **Single View Recon** (displays settlement status, UTRs,
Settlement IDs), **Smart Collect 2.0** (*"Automated Reconciliation of Collections via Bank
Transfer"* — assigns each payer a unique virtual identifier so incoming UPI/IMPS/NEFT/RTGS is
unambiguous), and **Source to Pay** (RazorpayX AP automation: OCR, 3-way PO/invoice/GRN matching,
auto-TDS on line items, GST ITC checks, GL sync). Market: **Ledge**, Beam AI, HighRadius, Bluecopa.

**Why #1 still survives all three:** Smart Collect prevents ambiguity on *money in* by identifier
assignment; Source to Pay matches *money out* against supplier invoices; Single View Recon *views*
settlements. **None resolves an unmatched settlement line** whose amount differs because of MDR, GST
on that MDR, a refund offset and a chargeback deduction from three cycles earlier. See
[razorpay-product-audit.md](razorpay-product-audit.md).

**Gap.** Four years after the viewer shipped, **nothing resolves**. And the reason is specific and
defensible: an asserted match writes into the merchant's **statutory books**, so Razorpay would own
being wrong. Globally, Ledge reconciles amounts across US/EU rails — **nothing reasons about
GST-on-MDR, TDS, or Indian cross-period settlement cycles.**

**Connected problems.** P8 chargebacks and P9 refunds are *named fields inside the settlement line*.
P19 late authorisation leaves lines provisional. P7 cash position depends on the close. Absorbs #5
(cross-period linking), #12 (late-auth), #8 (multi-PSP normalising) as features.

**AI role.** The residual tail is where fields disagree — a deduction that landed three cycles later,
at a different amount, because a partial refund intervened. There is no rule for that; there is
evidence to weigh.

**Agent role.** The output is not a class, it is a **linked explanation assembled from several
retrievals with an abstain option**. A classifier cannot abstain into an exception report naming the
candidates it considered and the discriminating evidence it lacked. That abstention path *is* the
product.

**Data.** Seeded synthetic generator against Razorpay's **published** settlement schema, injecting
the defects Razorpay itself names. Live test-mode reads via MCP (`fetch_all_settlements`,
`fetch_settlement_recon_details`, `fetch_all_payments`, `fetch_all_refunds`) to prove integration.
**Ground truth is exact by construction.**

**MVP (4–5 days).** Generator: 500 rows, 6 defect types, ground truth. Deterministic matcher →
residual queue → LLM adjudicator with confidence and abstention. `proposals` table, `exceptions.csv`,
traces, eval harness.

**Killer demo.** Terminal, live, 500 records. The counter runs: matched / proposed / abstained.
Then open `exceptions.csv` and walk **one exception you could not resolve** — showing the two
candidates the agent weighed and the missing UTR that made it abstain. Then show the sensitivity
curve across a 2–10% tail. **Never claim a match was written to the books.**

**KPI.** **Proposal precision at the shipped confidence threshold**, on a held-out batch — with match
rate and exception count beside it. Precision, not match rate, because *a wrong proposal accepted is
the real failure*.

**Risk.** Precision is hard where match rate is easy — you can demo 95% matching and 70% proposal
precision and have built something no finance team would trust. Mitigation: pick the threshold on the
precision/coverage curve and publish the curve.

**Why we should NOT build it.** Cost saving, not revenue. Ledge does this better with 150+
integrations. Track 4's bar is the easiest to satisfy, so competent competitors will clear it too.
**Why it survives:** every one of those objections is about the *global* problem. Nobody is solving
the *Indian* settlement line, the data is the best available anywhere in this research, and the
design constraint — propose, never assert — is derived from the exact liability that stopped Razorpay.

---

# 2. Recovery Sequencer with Headroom Veto

**Problem.** Recurring debits fail at execution, not registration. The money isn't there at the
trigger moment — and the standard answer, retry on a fixed schedule, doesn't address timing.

**Why Razorpay cares.** For **SBI, the largest remitter bank, only ~30% of UPI AutoPay auto-debits
are approved — ~70% fail**, predominantly on insufficient funds. E-mandate volume at the top ten
remitter banks hit **~1.6bn transactions in May 2026**, roughly 3× year on year. Razorpay ships
Subscription Recovery and Vulcan's launch copy names *"a subscription that silently lapses"*.
Track 3 names **both** "Failed-subscription recovery" and "Mandate retry sequencer".

**Existing solutions.** Razorpay: Subscription Recovery (retry logic + nudges, early access).
Market: **Butter Payments** (agentic AI recovery), **Revaly/FlexPay** — which already *"analyses
decline codes and issuer behaviour to time retries intelligently"* — Slicker, Churn Buster, FlyCode.

**Gap.** ⚠️ **Be honest: retry timing is not novel.** What is unoccupied: the **UPI AutoPay / e-NACH
lifecycle** (registration, AFA, variable-amount caps — nothing like card-on-file), the **RBI 2026
24-hour pre-debit notification window**, and ⭐ **the headroom veto** — nobody stops recovery because
it is pushing the merchant toward a freeze.

**Connected problems.** P1 → P8 → P4: failed debits generate disputes (**Visa 13.2 "cancelled
recurring" = 8.5% of all chargebacks**); disputes past **1%** trigger Razorpay's freeze. Absorbs #6
self-cure attribution as its evaluation harness.

**AI role.** Choosing among rails, times and channels under conflicting signals, with an explanation
afterwards.

**Agent role.** ⭐ **It reasons about the second-order consequences of its own actions.** A model
predicts recovery probability. It does not halt because succeeding too hard will freeze the merchant.

**Data.** Synthetic ledger with temporal balance dynamics, a modelled self-cure process, and dispute
generation. Failure semantics come from Razorpay's **published** taxonomy — real codes, real `source`
enum. Live test-mode failure via `failure@razorpay`.

**MVP (5–6 days).** Ledger + deterministic classifier over the published taxonomy + learned-timing vs
fixed-interval comparison + **holdout** + headroom stopping rule + traces. *Do not attempt the
two-agent negotiation.*

**Killer demo.** Two runs side by side: fixed-interval retry vs timing-aware, on the same seed. Then
the moment that matters — **the agent halts mid-campaign** because projected chargeback ratio hit
0.9% against the 1% trigger, and the trace shows the veto. Close on incremental vs gross recovery:
*"gross says we recovered ₹X; the holdout says ₹Y of that would have arrived anyway."*

**KPI.** **Incremental ₹ recovered against a holdout** — never gross. Constraint metric alongside:
chargeback ratio never crossed the trigger.

**Risk.** The temporal simulation is a sub-project; it is where 11-day schedules break. And you are
measuring against your own generator's self-cure assumptions.

**Why we should NOT build it.** Worst competitive quadrant: 88 buildathon repos *and* a mature
commercial category. Your differentiator was already shipped by Revaly. Feasibility 4/10.
**Why it survives:** it is the highest-priority problem in the corpus, and the headroom veto is the
single most defensible design decision available — it answers *"what are your stopping rules?"* with
Razorpay's own published threshold instead of an arbitrary retry cap.

---

# 3. Promise-to-Pay with MSME Statutory Escalation

**Problem.** Indian SMEs invoice on 0–30 day terms and get paid in 73 days. The gap is follow-up
discipline, and nobody has the time.

**Why Razorpay cares.** Track 3 names **both** "B2B receivables chaser" and "Promise-to-pay tracker".
Agent Studio's own "what others are automating" list includes *"following up on unpaid invoices until
they're paid"* — an aspiration with no product behind it. **MSME Samadhaan: ₹55,244 crore claimed,
₹20,979 crore still pending, 16% unresolved beyond a year.** Parliament legislated time-bound
mediation in **August 2026**.

**Existing solutions.** Razorpay: **none**. Market: **HighRadius** (15 collections agents, and it
auto-creates promise-to-pay entries), Growfin, Kolleno.

**Gap.** ⚠️ Promise-to-pay tracking is a shipped HighRadius feature. ⭐ **What no global AR tool does
is escalate into Indian statutory machinery** — the 45-day rule, MSEFC, Samadhaan filing, and the
August 2026 mediation/arbitration timelines. And Razorpay ships nothing at all here.

**Connected problems.** Same engine as #2 over a different ledger (Phase 4, Chain A). Feeds P7 cash
forecasting.

**AI role.** Prioritisation under a limited contact budget; **extracting a commitment from a free-text
reply** is the genuinely LLM-shaped sub-task.

**Agent role.** Long-horizon state — *"they promised the 5th; it is the 6th"* — is an event no model
emits. The state machine (outstanding → contacted → promised → broken → escalated → collected/stopped)
runs over weeks.

**Data.** Synthetic invoice ledger anchored on real distribution parameters: **73-day mean DSO, 82.6%
of invoices on 0–30 day terms**, the >360-day tail. Payer-response model. Payment links via MCP.

**MVP (4–5 days).** Ledger + payment-probability model + prioritised chase list + commitment tracking
+ compliant drafting + DSO curve.

**Killer demo.** The DSO curve moving, then the *broken promise* case: agent recorded a commitment for
the 5th, detects the miss on the 6th, escalates one rung — and **stops**, handing to statutory
process rather than chasing further. Show the compliance constraints: quiet hours, contact caps,
merchant's name on every message.

**KPI.** **DSO days compressed** on a batch, with promise-kept rate and opt-outs reported alongside.

**Risk.** Debt collection is regulated conduct. If the demo looks like harassment automation, it
fails on judgement rather than engineering. Mitigation: caps, quiet hours, merchant's name only, and
a visible hard stop.

**Why we should NOT build it.** HighRadius does the core. Razorpay ships nothing here, which may mean
they don't want to. Priority 6 — the weakest Razorpay-interest signal in the five.
**Why it survives:** the emptiest space found anywhere (~3–4 competitor repos), a
government-sourced magnitude, fresh legislation proving it's live, and a statutory wedge no
incumbent touches.

---

# 4. Merchant Freeze Exposure Monitor

**Problem.** A merchant's funds get frozen with no warning. Razorpay's own resolution bands are
**2–5 days / 1–3 weeks / 30+ days**, and a 120-day hold is documented.

**Why Razorpay cares.** Razorpay publishes the four triggers (chargeback >1%, ~10× volume spikes,
stale KYC/GST/PAN, PA compliance flags), the bands, and a wholly manual remedy ending at the RBI
Ombudsman. It **recommends merchants self-monitor at 0.5%** — and ships no alerting.

**Existing solutions.** Razorpay: none. Its advice is to *negotiate hold triggers into your contract*.

**Gap.** ⭐ **The asymmetry is the whole design.** Razorpay is constrained from warning merchants —
AML tipping-off means a regulated entity often *may not* say why, and warning a fraudulent merchant
lets them cash out. **The merchant is not constrained from monitoring themselves.** And Razorpay's
1% trigger is **stricter than Visa VAMP's 1.5%** — merchants are flagged before the networks would
flag them.

**Connected problems.** P4 is the terminal severity node: P8 chargebacks, P15 fraud flags, P17 KYC,
P13 compliance all converge there. This is the only project that addresses the graph's worst outcome.

**AI role.** Modest — the ratio is arithmetic. AI earns its place in interpreting *which* trigger is
approaching and what to do about it.

**Agent role.** Weakest of the five (agentic 6). Honest about that: it is a monitor with an advisory
loop, not an autonomous actor. **Do not oversell it as multi-agent.**

**Data.** ⭐ **Computable from the merchant's own transactions** — chargeback ratio, volume baseline
and deviation, KYC document expiry all derive from data the merchant already has. This is what
separates it from the freeze *navigator*, which needs hold events that cannot be created in test mode.

**MVP (4 days).** Exposure dashboard computing live headroom to each of the four triggers, deviation
detection on volume, KYC expiry tracking, and a cash-flow scenario for a 30-day hold.

**Killer demo.** A merchant's chargeback ratio climbing across a simulated quarter. The monitor flags
at 0.5%, projects the crossing date, and models what a 30-day freeze does to payroll. Then the
counterfactual: with intervention, the ratio turns before the trigger.

**KPI.** **Lead time in days between warning and the projected trigger crossing** — plus false-alarm
rate, reported honestly.

**Risk.** 🔴 **UPGRADED 2026-08-25 after a compliance review** — this is no longer just a perception
problem, it is a **contractual-framing** one. Razorpay's merchant terms **clause 2.23** assert that
Razorpay "may... blacklist Your end users to manage fraud and risk... to protect the integrity of the
payment ecosystem", and **clause 2.31** obliges Razorpay to monitor merchant transactions under the
Master Direction. Nothing prohibits a merchant from computing their own chargeback ratio — Razorpay
*recommends* self-monitoring at 0.5% — but the framing must be *"reduce genuine risk"*, never
*"stay under the threshold"*. See [compliance_review.md](compliance_review.md) §3.
**This is now the highest-compliance-risk project of the five and should sit below #3 in your
consideration order.**

**Why we should NOT build it.** Fragile — falls from #4 to #8 if Agent Studio's roster has grown.
Weakest agentic score. No feedback loop to prove it worked. Reputational read-across risk.
**Why it survives:** highest novelty in the corpus, near-zero competition, and the AML asymmetry is
a genuinely sophisticated insight that demonstrates you understood *why* the gap exists.

---

# 5. Agentic Purchase Intent Verifier

**Problem.** An AI agent buys on your behalf. Consent covers *a merchant and an amount* — not
*what you meant*. Right price, wrong product passes every check.

**Why Razorpay cares.** Track 1's build spec: *"makes a merchant transactable by an AI buyer end to
end."* Razorpay is live on agentic UPI with NPCI via **UPI Reserve Pay** (Zomato, Swiggy, Zepto).
And **Shashank Kumar, on the record**: *"The system has to allow for a certain level of mistakes so
that you can learn from them and correct them."*

**Existing solutions.** Razorpay: rail-level consent and caps via Reserve Pay. Market: standards are
forming — **Mastercard Verifiable Intent, Visa Trusted Agent Protocol, Know Your Agent, Google
UCP/AP2** — but merchant-side enforcement barely exists. **OpenAI's Instant Checkout publicly
stumbled** on product-data accuracy with Etsy, Walmart and Shopify.

**Gap.** Consent is **amount-scoped, not intent-scoped**. And there is **no dispute or liability path
for AI-led transactions** — NPCI will authenticate agents but explicitly will not track purchase
specifics, leaving intent-level trust to intermediaries.

**Connected problems.** P5 ↔ P8: the chain terminates in an unresolved dispute that feeds back into
the trust problem it started with.

**AI role.** Heaviest of the five. Comparing a natural-language instruction against an assembled cart
and characterising divergence is irreducibly language work.

**Agent role.** Honest classification: **Level 3** — a verification gate, not an autonomous loop.
Say so. Claiming Level 5 here would be exactly the AI-washing the bars punish.

**Data.** Synthetic catalog, instruction set, and deliberately divergent carts (substitution, quantity
drift, recurring-vs-one-off, right-price-wrong-product). Live test-mode orders and capture via MCP.
**Track 1 is the only track native to test mode.**

**MVP (4 days).** Catalog + instruction parser + cart comparator + cap enforcement **before** capture
+ audit trail + adversarial test set.

**Killer demo.** The agent shops correctly, and you approve. Then the adversarial run: it returns a
subtly wrong item at the right price. **The gate blocks capture, shows the instruction/cart diff, and
asks.** Close on the audit chain: instruction → consent → cart → decision → payment.

**KPI.** **Divergence-detection precision and recall** on a labelled adversarial set — with the
false-block rate, because blocking good purchases is the failure mode that kills adoption.

**Risk.** ~100 competitor repos in this track. Latency matters (target <2–3s) and LLM calls in the
hot path will hurt. And Reserve Pay is a closed pilot — you reimplement the consent model, you cannot
call it.

**Why we should NOT build it.** The most crowded track in the buildathon. Razorpay has already
piloted conversational and voice checkout. Level 3, not 4.
**Why it survives:** the best demo in the set, the only Track 1 option, and it answers a question
Razorpay's own MD posed publicly.

---

```
FINAL VALIDATION

Candidate 1 - Reconciliation Exception Resolver
Why we should NOT build it: cost saving not revenue; Ledge does it better globally with 150+
  integrations; Track 4's bar is the easiest to clear so good competitors will clear it too.
Why it survives: every objection is about the GLOBAL problem. The Indian settlement line -
  MDR, GST-on-MDR, TDS, UTR, cross-period cycles - is untouched by any incumbent. Best data
  score in the entire research (9), least crowded track, MVP in under half the window, and a
  design constraint derived from the specific liability that explains Razorpay's own inaction.

Candidate 2 - Recovery Sequencer with Headroom Veto
Why we should NOT build it: worst competitive quadrant (88 repos + Butter/Revaly/Slicker);
  the retry-timing differentiator is already shipped by Revaly; feasibility 4/10 because the
  temporal simulation is a sub-project.
Why it survives: highest-priority problem in the corpus, and the headroom veto answers "what
  are your stopping rules?" with Razorpay's own published 1% freeze trigger rather than an
  arbitrary cap. That single design decision is the most defensible thing in this research.

Candidate 3 - Promise-to-Pay with MSME Statutory Escalation
Why we should NOT build it: HighRadius ships the core including promise-to-pay; Razorpay's
  demonstrated interest is the weakest of the five; collections is regulated conduct and a
  clumsy demo reads as harassment automation.
Why it survives: emptiest competitive space found (~3-4 repos), a government-sourced magnitude
  (Rs 20,979 cr pending), August 2026 legislation proving it is live, and a statutory
  escalation wedge no global AR tool models.

Candidate 4 - Merchant Freeze Exposure Monitor
Why we should NOT build it: fragile under the roster assumption (4 -> 8); weakest agentic
  score (6); no feedback loop; and a real risk that judges read it as coaching merchants
  around Razorpay's risk controls.
Why it survives: highest novelty in the corpus, near-zero competition, and the AML
  tipping-off asymmetry - Razorpay cannot warn, the merchant can monitor - is the most
  sophisticated single insight in this research. It also targets P4, the graph's terminal
  severity node, which nothing else does.

Candidate 5 - Agentic Purchase Intent Verifier
Why we should NOT build it: ~100 competing repos; Razorpay has already piloted conversational
  and voice checkout; it is honestly Level 3, not Level 4; and Reserve Pay is a closed pilot
  you cannot call.
Why it survives: best demo of the five, the only Track 1 option, standards are still forming
  so merchant-side enforcement is genuinely early, and it answers a question Razorpay's own
  MD asked in public.

Strongest opportunity:
  Reconciliation Exception Resolver. It is first on score, first on data, lowest variance,
  holds rank 1 under every sensitivity scenario tested, and is the only top-5 entry whose
  novelty claim does not depend on the Agent Studio roster I could not verify.

Biggest risk:
  For the portfolio: the Agent Studio roster is five months old and Razorpay has said the
  studio will open to third-party agents. If it has grown, candidates 3 and 4 lose their
  novelty claim outright.
  For candidate 1 specifically: achieving PROPOSAL PRECISION, not match rate. It is entirely
  possible to build something that matches 95% and proposes wrongly 30% of the time - and
  that is a system no finance team would use.

Most important unanswered question:
  What is Razorpay's CURRENT Agent Studio roster? The product page is client-side rendered
  and defeated every fetch attempt across three research passes. Everything claimed as "no
  Razorpay product exists" rests on a launch blog dated 12 March 2026. A rendered-browser
  check is the single cheapest remaining action in this entire project and it would firm up
  or demolish two of these five.

Overall research confidence: 8/10
```

---

## Recommendation

**Build #1.** It wins on score, on data, on competition, on schedule, and on robustness — and its
novelty claim is the only one in the five that survives the roster uncertainty.

**If you want the higher ceiling, build #2** and accept the variance: keep the MVP scope, skip the
two-agent negotiation, and make the headroom veto the centrepiece of the video.

**One combination is stronger than either alone:** #1 extended with cross-period deduction linking
(#5) and evaluated with a proper holdout harness (#6). All three are Track 4-aligned, all score ≥7.00,
and they form one coherent project rather than three — a reconciler that resolves, links across
cycles, and proves its own precision.
