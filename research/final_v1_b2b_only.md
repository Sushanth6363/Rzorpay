# final.md — The Project, Evaluated From Every Angle

**Razorpay AI Buildathon 2026 · Track 3 · AI Revenue Recovery**
Compiled 2026-08-25, after 14 research phases, 3 deep-research workflows (~320 agents), and seven
ideas killed against Razorpay's live product surface.

---

# 1. The problem

> **Indian suppliers can't tell the difference between a customer who hasn't paid and a customer
> whose payment was legally reduced — so they chase people who already paid in full.**

Indian SMEs invoice on 0–30 day terms and are paid in **73 days**. **₹20,979 crore** of delayed
payments sit unresolved on the government's MSME Samadhaan portal, 16% of cases open beyond a year.

But before you can chase, you must know what is genuinely outstanding — and **in India payments
routinely arrive short by a lawful amount**, because buyers withhold TDS at source.

A ₹2,00,000 invoice paid as ₹1,96,000 can mean five different things:

| Cause | Chase? |
|---|---|
| TDS withheld | ❌ Paid in full |
| Partial payment | ✅ ₹4,000 owed |
| Agreed discount | ❌ |
| Silent dispute | ⚠️ Escalate, don't chase |
| Paid against another invoice | ⚠️ Re-match |

**Same number. Five meanings.** A tool that chases the invoice balance chases withholding tax.

---

# 2. The solution

**An agent that diagnoses before it collects, and regulates its own conduct.**

```
Payment received against invoice
        ↓
◆ STAGE 1 — DIAGNOSE: why is it short?
   open hypothesis search · adaptive tool calls · confidence scored
   TDS? · partial? · discount? · dispute? · misallocation?
        ↓
   ┌────────────┴────────────┐
Lawful deduction         Genuine shortfall
   ↓                            ↓
✅ SETTLED               ◆ STAGE 2 — DECIDE
   log TDS credit           true outstanding · payment probability
   ⛔ DO NOT CHASE          × relationship value · §16 interest accruing
                            escalation economics
                                   ↓
                         ◆ STAGE 3 — ACT (bounded)
                            draft in merchant's name · attach payment link
                            extract promises · detect breach next day
                            escalate ONE rung · never two
                                   ↓
                            ⛔ STOP → Samadhaan application DRAFTED, never filed

   ⛔ Can't explain the gap → ABSTAIN. Escalate to merchant. Never chase blind.
   ⛔ Silent dispute detected → HALT. Hand to human.

╔══════════════════════════════════════════════════════════════════╗
║ POLICY LAYER — active at every step                              ║
║ Derives per case what it is PERMITTED to do, before acting:      ║
║   MSME-registered? → does MSMED apply                            ║
║   which TDS section? → what deduction is lawful                  ║
║   days past due? → which escalation rung is available            ║
║   contacts this month? → cap reached                             ║
║   dispute open? → chasing blocked                                ║
║ Logs why each action was permitted or blocked.                   ║
╚══════════════════════════════════════════════════════════════════╝
```

**⭐ The policy layer is the differentiator.** Every shipped agent has rules a human configures once
— RazorpayX's own page says *"set rules for frequency and channels."* This one **derives its
permissions per case from which rules actually apply**, which is what Track 3's bar means by
*"compliant escalation."*

### Scope discipline — what is deliberately excluded

Uncollected **entitlements** were considered and trimmed to those a *buyer* owes: §16 statutory
interest, and TDS withheld but not deposited. **GST input credit on gateway fees is excluded** —
it is money between the merchant and the tax department, not revenue recovery, and it belongs to
Track 4's *"tax-line matcher."* Costs ~₹4,500/yr of headline. Worth it for a clean track fit.

**Two statutory anchors, both India-only:** TDS tells you when *not* to chase. **MSMED Act
Section 16** tells you what the buyer owes when you should — compound interest, monthly rests, three
times the RBI bank rate, and *"notwithstanding anything contained in any agreement,"* meaning the
buyer cannot contract out of it.

---

# 2A. Track fit — is this Track 3?

**Yes. Here is the test and the evidence.**

## The deciding test

**What does the money do at the end?** Collected from a buyer → recovery → **Track 3**. Books closed
and reported → finance control → Track 4.

This agent gets a supplier paid. Nothing is reported as a match rate; nothing is posted to a ledger.

## Against Track 3's build spec, clause by clause

| Their words | This project |
|---|---|
| *"detects revenue at risk"* | Overdue invoices ranked by probability × relationship value |
| *"determines the right intervention"* | ⭐ **Stage 1 — sometimes the right intervention is none** |
| *"executes a bounded recovery workflow"* | Caps, quiet hours, merchant's name, opt-in interest, one-rung escalation |
| *"…to overdue receivables"* | **Named explicitly in the spec** |

**4 of 4.**

## Against the bar

| Bar demand | This project |
|---|---|
| *"Don't just identify the problem"* | It acts — and decides when not to |
| *"measured money recovered across a batch"* | 500-invoice batch, DSO compressed vs holdout |
| ⭐ *"**compliant escalation**"* | **The policy layer. Statutory ladder + conduct rules, derived per case** |
| *"stopping rules"* | Dispute abstention · one-rung cap · opt-in interest · draft-never-file |
| *"audit trail"* | Decision-level traces including blocked actions |

**5 of 5.**

## And their own "why now" names the diagnosis step

> *"AI can now close the loop from detecting the problem **to diagnosing it**, choosing the right
> intervention, and recovering the money."*

**Stage 1 is the diagnose step.** Most submissions will build detect → recover and skip it entirely.

## Two named example directions, not one

**B2B receivables chaser** *and* **promise-to-pay tracker**.

## ⚠️ The overlap risk, handled

Stage 1 resembles *"multi-source reconciliation"* — a **Track 4** example direction. Mitigations,
applied:

1. **Never call it reconciliation.** It is *payment attribution* / *shortfall diagnosis*
2. **Headline metric is false-chase rate**, never match rate — the metric decides the track
3. **GST-on-fees credit excluded** (see §2 scope discipline)
4. **No trial balance, no ledger posting, no month-end close** — diagnose only enough to decide whether to chase, then stop
5. **Address it in one line in the README**, pre-emptively

> *"This project diagnoses short payments before deciding whether to collect. That diagnosis
> resembles reconciliation, which appears in Track 4 — but here it is instrumental rather than the
> objective: nothing is reported as a match rate, and the measured outcome is money recovered and
> customers not wrongly chased."*

---

# 2B. Required functionality

Every function traces to a clause in the build spec or the bar. Nothing here is decorative.

## Stage 1 · DIAGNOSE
*Serves: "determines the right intervention" · "diagnosing it" (why now)*

| # | Function | MVP |
|---|---|---|
| F1 | Ingest invoices + received payments (Razorpay MCP test mode + synthetic ledger) | ✅ |
| F2 | Match payment → invoice: exact on reference, fuzzy on amount/date/buyer | ✅ |
| F3 | **Classify the shortfall** — TDS · partial · discount · dispute · misallocation · unexplained | ✅ |
| F4 | **Verify TDS against a configurable statutory rate table** (by section) | ✅ |
| F5 | **Multi-invoice allocation** — one payment covering several invoices | ✅ |
| F6 | ⛔ **Abstain when unexplained** — emit hypotheses tested and evidence missing | ✅ |
| F7 | **Phantom receivables report** — *"₹1.6L of ₹18.4L was never outstanding"* | ✅ |

## Stage 2 · DECIDE
*Serves: "detects revenue at risk" · "determines the right intervention"*

| # | Function | MVP |
|---|---|---|
| F8 | Compute genuine outstanding + days overdue | ✅ |
| F9 | Payment-probability model by ageing bucket and buyer history | ✅ |
| F10 | **Relationship-value score** — lifetime orders vs amount owed | ✅ |
| F11 | **Prioritise the chase list** under a limited contact budget | ✅ |
| F12 | **Accruing §16 statutory interest** — compound, monthly rests, 3× bank rate | ✅ |
| F13 | Select intervention: none · reminder · statement · escalate · stop | ✅ |
| F14 | **Escalation economics** — expected recovery vs relationship cost | ⭐ |
| F15 | **TDS credit gap check** — withheld but not in 26AS *(hard timing buffer)* | ⭐ |

## Stage 3 · ACT
*Serves: "executes a bounded recovery workflow" · "don't just identify the problem"*

| # | Function | MVP |
|---|---|---|
| F16 | **Draft compliant message in the merchant's name** — never Razorpay's | ✅ |
| F17 | Attach payment link (`create_payment_link` / `send_payment_link`) | ✅ |
| F18 | **Extract promises from free-text replies** — *"we'll release on the 5th"* | ✅ |
| F19 | **Detect the breach the day after**, follow up on *that* commitment | ✅ |
| F20 | Escalate **one rung** on breach — never two | ✅ |
| F21 | ⛔ **Silent-dispute detection → halt, escalate to merchant** | ✅ |
| F22 | ⛔ **Generate the Samadhaan application as a PDF — populated, with the reason for escalation and the full attempt log. DRAFTED, NEVER FILED** | ⭐ |
| F23 | **Negotiation** — evaluate part-payment offers against cost of capital, hard caps | ⭐ |

## Cross-cutting · POLICY LAYER
*Serves: ⭐ **"compliant escalation"** · "stopping rules" · "audit trail"*

| # | Function | MVP |
|---|---|---|
| F24 | ⭐ **Per-case permission derivation** — MSME-registered? · which TDS section? · days overdue? · cap reached? · dispute open? → permitted vs blocked | ✅ |
| F25 | Contact-frequency caps + quiet hours | ✅ |
| F26 | Opt-out honoured permanently | ✅ |
| F27 | Approval gates — interest **opt-in**, escalation **confirmed**, filing **never automatic** | ✅ |
| F28 | **Decision-level audit trail** — considered, chose, blocked, and why | ✅ |

## Evaluation harness — build first
*Serves: "measured money recovered across a batch"*

| # | Function | MVP |
|---|---|---|
| F29 | **Seeded generator** with ground truth — statutory TDS rates, 73-day DSO, 82.6% on 0–30 day terms | ✅ |
| F30 | **Holdout group** — recovery measured incrementally, never gross | ✅ |
| F31 | **Rules-engine baseline** in the same repo, same batch | ✅ |
| F32 | Metrics (see §4) | ✅ |
| F33 | Sensitivity curve over payer-model parameters | ⭐ |

**26 MVP functions · 7 stretch.** Stretch items are the ones that can harm the merchant — losing
them to time costs nothing you can't survive.

---

# 3. Evaluated from every angle

## 3.1 Merchant

**Who it serves.** Any supplier selling B2B on credit terms — strongest for the merchant with no
accountant, because a maintained ledger already handles TDS.

**What they get:**

| Benefit | Concrete |
|---|---|
| Stops false chases | Never demands money from a customer for obeying tax law |
| **Phantom receivables** | *"₹1.6L of your ₹18.4L outstanding was TDS, already settled"* |
| **Lost TDS credits found** | Deductions never deposited = money lost twice |
| DSO compression | Systematic follow-up they can't sustain manually |
| Relationship protection | Aggression modulated by customer value |

**Where it can hurt them** — the honest part:

| Risk | Mitigation built in |
|---|---|
| 🔴 Statutory interest can cost the customer | Computed by default, **sent only on instruction** |
| 🔴 **§43B(h)**: invoking MSMED reveals they're MSME-registered — some buyers avoid such suppliers | Gated behind relationship check; never in a first reminder |
| 🔴 Samadhaan filing ends the relationship | **Drafted, never filed** |
| 🟠 26AS gaps may be quarterly timing, not default | Hard timing buffer; merchant-facing only |
| 🟠 Negotiation erodes margin | Hard caps; cumulative concession reported |

## 3.2 Razorpay

**Strategic fit.** Their goal is *"a financial operating system, not a payments provider"* and
revenue per merchant (~₹3,150/yr) must rise. Receivables is a finance-ops surface they've entered
but not finished.

**Do they want it?** Evidence yes — RazorpayX Agentic Banking ships a collections agent, and Agent
Studio lists *"following up on unpaid invoices"* as a use case. **The space is endorsed.**

**Commercial value to them:** payment links on collected invoices are billable TPV; a stickier
finance product raises products-per-merchant.

## 3.3 Competitive

| Competitor | What it does | Gap |
|---|---|---|
| **RazorpayX Agentic Banking** | *"Tracks unpaid invoices, and automatically follows up"* — announced FTX'26 (12 Mar), **still early access** | Published description mentions no TDS reconciliation, no statutory interest, no statutory escalation |
| HighRadius | 15 collections agents, auto promise-to-pay | Built for US/EU rails. No TDS, no MSMED |
| Growfin, Kolleno | Behavioural prediction, channel/timing | Same — no Indian statute |

⚠️ **Say "their published description doesn't mention X" — never "their product doesn't do X."** The
first is verifiable; the second is a claim you cannot support in a room containing the person who
built it.

## 3.4 Judge / panel — scored on `requirements.md` §6b

| Criterion | Wt | Score | Why |
|---|--|--|---|
| Measured outcome on a batch | 25 | **21** | Stage 1 ground truth is **structural** (statutory rates are objectively checkable); stage 2 authored |
| Bounded autonomy & audit trail | 20 | **19** | Caps, quiet hours, opt-in interest, draft-never-file, abstention |
| Honest evaluation | 15 | **14** | False-chase rate, holdout, harm metrics, sensitivity curve |
| Novelty vs Razorpay | 15 | **9** | Competing agent exists; delta is real but not virgin territory |
| Agentic necessity | 10 | **10** | Abduction + sequential decisions + meaningful abstention |
| Engineering & stack fit | 10 | **8** | MCP, test mode, one-command reproduce |
| Communication | 5 | **5** | Three strong demo moments |
| Problem truth | 10 | **9** | Government-sourced magnitude |
| | | **95/100** | ≥85 = competitive |

**Kill-switch check:** *"a rebuild of an existing agent with no stated delta"* — cleared **only if
the delta leads**. It must be your first sentence, not a README footnote.

## 3.5 Engineering

**Why an agent is necessary, not decorative:**

- **Stage 1 is abduction** — inferring cause from an open explanation space, where which evidence you
  gather depends on the hypothesis you currently hold. A rules engine resolves the cases you
  enumerated; the agent resolves the one you didn't.
- **Stage 2 is sequential decision-making** — every buyer reply changes the state, objectives
  conflict, the horizon is weeks.
- **Abstention is the highest-value output.** A rules engine has no notion of confidence; a
  classifier must emit a class. Only an agent can say *"I can't explain this, so I won't chase"* —
  and here that restraint prevents real commercial damage.

**Proof, not assertion:** ship the rules-engine baseline in the same repo, run it on the same batch,
publish both numbers and the cases only the agent resolved.

**Stack.** Python · SQLite · Razorpay MCP (test keys) · Claude with structured outputs · seeded
generator · `make setup / demo / eval`.

## 3.6 Compliance

| Area | Position |
|---|---|
| RBI | Nothing engaged — no lending, no processing, no risk decisioning |
| Collections conduct | Merchant's name only · contact caps · quiet hours · opt-out · hard stop into statutory process |
| DPDP 2023 | Synthetic data throughout; data minimisation stated |
| Razorpay ToS 2.30 | Read-only; merchant-side tool, not a payments platform |
| Tax | Computation is arithmetic; **label all tax output indicative, not advice**; rates configurable |
| Track 2 disqualifier | N/A — nothing offense-capable |

## 3.7 Evidence quality

| Claim | Status |
|---|---|
| 73-day SME DSO; 82.6% on 0–30 day terms | ⚠️ Vendor report, self-selected sample |
| ₹20,979 cr pending on Samadhaan | ✅ Government portal *(date may be a restatement)* |
| MSMED §16 interest terms | ✅ Statute |
| RazorpayX collections agent exists, early access | ✅ Verified on the live page today |
| **TDS rates by section** | ⚠️ **Mechanic verified; specific rates NOT — verify before building** |
| Payer-response model | ❌ Authored by you. Publish parameters |

---

# 4. Metrics

⚠️ **Corrected 2026-08-26.** An earlier draft led with false-chase rate. **The bar asks for
"measured money recovered."** Lead with the metric they asked for; differentiate with yours.

| Rank | Metric | Why |
|---|---|---|
| **1 · HEADLINE** | **₹ recovered across the batch — incremental against a holdout** | ⭐ Exactly what the bar demands. Never gross |
| 2 · Supporting | **DSO days compressed** | The merchant's language |
| **3 · DISTINCTIVE** | **False-chase rate** — customers contacted who owed nothing | The harm metric. Almost nobody reports one, and it proves diagnosing first was necessary |
| 4 | Stage-1 classification accuracy vs **statutory** ground truth | The half that isn't authored |
| 5 | Promise-kept rate · opt-outs · cumulative margin conceded | Honest reporting of cost and harm |

**The order matters.** A judge scanning for the number the bar names must find it in the first
frame. False-chase rate is what they remember afterwards.

---

# 5. Build plan — safeguards before sharp instruments

| Days | Work | Harm |
|---|---|---|
| **1–3** | Generator · eval harness · trace format · phantom receivables · rules baseline · multi-invoice allocation | 🟢 None |
| **4–5** | Dispute abstention · relationship weighting · escalation economics | 🟢 Protective |
| **6–7** | Statutory interest *(opt-in)* · 26AS check *(timing buffer)* | 🔴 Gated |
| **8** | Samadhaan draft *(never files)* · negotiation *(hard caps)* | 🔴 Gated |
| **9–10** | README · video · freeze · tag · submit | — |

**If you run out of time you ship a cautious agent, not an aggressive one.** That is the correct
failure mode for software touching a merchant's customer relationships.

---

# 6. The demo — five minutes

| Time | Beat |
|---|---|
| 0:00–0:20 | The problem, with the number: 73 days, ₹20,979 cr |
| 0:20–1:00 | **The near-miss** — short payment arrives, agent identifies TDS, **marks settled instead of chasing** |
| 1:00–2:30 | **Live batch, 500 invoices.** DSO curve moving. False-chase rate on screen |
| 2:30–3:15 | **The stop** — third broken promise, agent halts and drafts (does not file) the Samadhaan application |
| 3:15–4:00 | Rules baseline vs agent — the cases only the agent resolved |
| 4:00–4:35 | **How it could hurt the merchant, and what I did about it** (§43B(h), opt-in interest) |
| 4:35–5:00 | Limitations, the delta, what's next |

---

# 7. Panel questions

| Q | A |
|---|---|
| *"Doesn't Tally handle TDS?"* | Yes — for merchants who keep books properly. This is for those who don't, and for tools reading payment data rather than ledgers |
| *"Doesn't RazorpayX do this?"* | Their published description says "tracks unpaid invoices and follows up." No mention of TDS or statutory interest. Announced March, still early access |
| *"How do you know the TDS rate?"* | Configurable table by section. The agent proposes and abstains when ambiguous |
| *"Where's your ground truth?"* | Stage 1 structural — statutory rates are objectively checkable. Stage 2 is a model I wrote; parameters and sensitivity published |
| *"Couldn't rules do this?"* | Baseline is in the repo. Here are the cases only the agent got, and why |
| *"Would suppliers really claim the interest?"* | Often not — it's commercially aggressive. Computed by default, sent only on instruction. §43B(h) is why |
| **"Which number do you trust least?"** | The payer-response model. It's mine. Everything downstream of it is directional |

---

# 8. The honest case against

**Ground truth in stage 2 is authored.** You write the payer model. Structural in stage 1, not in
stage 2.

**The problem is narrower than it first sounds.** A merchant with a properly maintained ledger
already handles TDS. This serves the ones without — real and large, but say it before a judge does.

**A competing product exists.** Announced five months ago, still early access, one-sentence public
spec. Your delta is real but you are not in empty territory.

**Would a supplier chase ₹4,000?** Probably not individually. The stronger framing is ₹1.6 lakh of
phantom receivables distorting their books, not one small chase.

**Seven ideas died against Razorpay's product surface before this one.** My picture of what they've
built has been wrong six times. It may still be incomplete.

---

# 9. Next actions

1. **Verify TDS rates by section** — the one load-bearing fact I have not checked
2. **Ask Abhishek:** *"Does the RazorpayX collections agent reconcile a short payment against TDS
   before it follows up?"* — factual, not confidential, and it confirms or dissolves the delta
3. **Start the scaffolding tonight** — generator, eval harness, trace format. A third of the work,
   and it's identical regardless of what the answers change
4. **Lock the track within 48 hours.** One shot, no edits after submission

---

**The one-sentence pitch:**

> *Their agent chases ₹4,000 of withholding tax. Mine doesn't — and when money genuinely is owed, it
> tells the buyer what the delay is legally costing them.*
