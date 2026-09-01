# final.md — The Project, Evaluated From Every Angle

**Razorpay AI Buildathon 2026 · Track 3 · AI Revenue Recovery**

Compiled 2026-08-25, revised 2026-08-26 after a scope decision.
Behind it: 14 research phases, 3 deep-research workflows (~320 agents), seven ideas killed against
Razorpay's live product surface, and one deliberate reversal recorded in §2B.

> **v2 scope change.** v1 was a B2B-receivables-only agent that avoided every Razorpay product.
> v2 is **one recovery engine across four leak types**, deliberately overlapping two shipped Agent
> Studio agents. Rationale in §2B. v1 preserved at `research/final_v1_b2b_only.md`.

---

# 1. The problem

> **Everyone builds an agent that recovers revenue. Nobody checks whether the revenue was lost.**

Money leaks out of a merchant's business through four holes, and the merchant sees a number against
each of them:

| Leak | What the merchant sees |
|---|---|
| Failed payment | *"₹5,000 failed"* |
| Abandoned checkout | *"₹18,000 left in a cart"* |
| Subscription renewal failed | *"₹999 didn't collect"* |
| B2B invoice overdue | *"₹5,00,000, 16 days past due"* |

Add them up and you get a **revenue-at-risk figure**. Every Track 3 submission will open with one.

**A meaningful share of that figure is fiction.**

| Leak | Why it may never have been at risk |
|---|---|
| Failed payment | The customer retried themselves and it went through |
| Abandoned checkout | They completed it on their phone an hour later; or they are a habitual browser who has never bought |
| Subscription | They **meant** to cancel. Chasing them is harassment, not recovery |
| B2B invoice | **The buyer withheld TDS.** The invoice is settled in full |

The B2B case is the sharpest, because it is arithmetic rather than judgement. A ₹2,00,000 invoice
paid as ₹1,96,000 can mean five different things:

| Cause | Chase? |
|---|---|
| TDS withheld at source | ❌ Paid in full |
| Partial payment | ✅ ₹4,000 owed |
| Agreed discount | ❌ |
| Silent dispute | ⚠️ Escalate, don't chase |
| Paid against another invoice | ⚠️ Re-match |

**Same number. Five meanings.** A tool that chases the invoice balance chases withholding tax.

**Magnitude.** Indian SMEs invoice on 0–30 day terms and are paid in **73 days**. **₹20,979 crore**
of delayed payments sit unresolved on the government's MSME Samadhaan portal, 16% of cases open
beyond a year.

### And the second problem, which only appears once you have all four

Razorpay ships **twelve separate prebuilt agents across two platforms** — seven in Agent Studio
(including Abandoned Cart Conversion and Subscription Recovery) and five in RazorpayX Agentic
Banking (including a Collections agent that places **voice calls** about unpaid invoices). The brief's own example directions are singular in the same
way — *"abandoned cart recovery"*, *"failed subscription recovery"*, *"mandate retry sequencer"*.
One agent, one leak type.

**So what happens to the customer who appears in three of them?**

They get three messages, from three systems, none of which can see the other two. Nothing in the
brief asks this question, and twelve independent agents structurally cannot answer it.

---

# 2. The solution

**One engine. Four leak types. One decision loop, one contact ledger, one policy layer.**

```
   Failed      Abandoned    Subscription    B2B invoice
   payment      checkout       failed         overdue
      │            │              │              │
      └────────────┴──────┬───────┴──────────────┘
                          ↓
        ╔═══════════════════════════════════════════╗
        ║ ◆ STAGE 0 — VALIDATE                      ║
        ║   Is this money actually at risk?         ║
        ║   already retried? · completed elsewhere? ║
        ║   deliberate cancel? · TDS deducted?      ║
        ╚═══════════════════════════════════════════╝
                          ↓
              ┌───────────┴───────────┐
        Never at risk            Genuinely at risk
              ↓                        ↓
        ✅ CLOSE                ◆ STAGE 1 — DIAGNOSE
        ⛔ DO NOT CONTACT          why did it fail / why unpaid?
        log as phantom             open hypothesis search
                                   adaptive tool calls, confidence scored
                                          ↓
                                   ◆ CORRELATE ACROSS CASES
                                   40 failures, 1 issuer outage = ONE event
                                          ↓
                                   ◆ STAGE 2 — DECIDE
                                   recoverable value × probability
                                   × relationship value − cost of contact
                                   ranked under a SHARED contact budget
                                          ↓
                                   ◆ STAGE 3 — ACT (bounded)
                                   retry · remind · payment link · update method
                                   record promise · detect breach · escalate ONE rung
                                          ↓
                                   ◆ TRACK → outcome → STOP

   ⛔ Cannot explain it → ABSTAIN. Exception record. Never contact blind.
   ⛔ Dispute signal → HALT. Hand to human.
   ⛔ Contact budget spent → STOP, regardless of how much is owed.

╔══════════════════════════════════════════════════════════════════════╗
║ POLICY LAYER — active at every step, across every stream             ║
║ Derives per case what it is PERMITTED to do, before acting:          ║
║   MSME-registered? → does MSMED apply                                ║
║   which TDS section? → what deduction is lawful                      ║
║   retry attempt n of 3? → is another retry allowed                   ║
║   contacts used this month? → shared across ALL FOUR streams         ║
║   quiet hours? · opted out? · dispute open? → blocked                ║
║ Logs why each action was permitted or blocked.                       ║
╚══════════════════════════════════════════════════════════════════════╝
```

## The three things this does that the brief's own framing does not

**⭐ D1 · One customer, one voice.** ✅ **Verified 2026-08-26 across four Razorpay sources** — no
orchestration layer, no shared state, and **no contact-frequency caps described at all**. There are
**12 agents across two platforms** (7 Agent Studio + 5 RazorpayX Agentic Banking), and no published
evidence any of them can see each other. A customer can receive an Agent Studio cart nudge *and* a
RazorpayX collections **phone call** on the same afternoon.

The contact budget is held **per customer, not per stream**.
A customer with an abandoned cart, a failed subscription charge and an overdue invoice gets **one**
message, chosen as the highest-value action across all three — not three messages from three agents.
This is bounded autonomy you can *demonstrate*, not claim.

**⭐ D2 · Act on the outage signal at the recovery layer.** ⚠️ **Revised 2026-08-26 after
verification** — see `research/gap_verification.md`. Razorpay already *detects* outages: it publishes
a **Payment Downtime API and downtime webhooks**, and Optimizer identifies bank-side outages
*"often within seconds of a success rate dip beginning."* **Detection is not the gap.**

The gap is downstream. Optimizer works at the **routing layer** — steering an in-flight transaction
to a healthy gateway before it fails. Our decision is at the **recovery layer**: forty payments that
have *already* failed and are sitting in a queue. Should we retry them now? Should we message these
forty customers? **Nothing published connects the downtime signal to that decision.** The
Subscription Recovery agent applies *"smarter retry logic"*; no description says it consults the
Downtime API.

So the engine **subscribes to Razorpay's own downtime webhook**, suppresses retries and contact into
a known outage, and reschedules on the resolution event. **We reason over their published taxonomy,
not one we invented** (`requirements.md` §5.11) — and we concede up front that they do the hard
part, which removes the easy panel kill *"you know we ship a downtime API, right?"*

**⭐ D3 · Validate before chasing.** Stage 0 does not exist in the brief's loop, in any of its seven
example directions, or in any shipped agent's public description. Their *"diagnose"* asks **why the
payment failed**. Stage 0 asks **whether anything failed**.

⚠️ **Precise claim.** TDS reconciliation itself is not new — Tally does it. What is new is putting it
**inside the agent's decision loop as a gate on action**, rather than producing it as an accounting
report a human reads later.

### Scope discipline — what is deliberately excluded

**GST input credit on gateway fees is excluded.** It is money between the merchant and the tax
department, not revenue recovery, and it belongs to Track 4's *"tax-line matcher."* Costs ~₹4,500/yr
of headline. Worth it for a clean track fit.

**No trial balance, no ledger posting, no month-end close.** Diagnose only far enough to decide
whether to act, then stop.

**Two statutory anchors, both India-only.** TDS tells you when *not* to chase. **MSMED Act
Section 16** tells you what the buyer owes when you should — compound interest, monthly rests, three
times the RBI bank rate, and *"notwithstanding anything contained in any agreement,"* meaning the
buyer cannot contract out of it.

---

# 2A. Track fit — is this Track 3?

**Yes, and now more obviously than v1.**

## Against Track 3's build spec, clause by clause

| Their clause | Where it lives |
|---|---|
| *"detects revenue at risk"* | Four event ingesters → Stage 0/1 |
| *"determines the right intervention"* | Stage 2, ranked under a shared budget |
| *"executes a bounded recovery workflow"* | Stage 3 + the action board (§2D) |
| *"stopping rules"* | Contact caps, retry caps, promise suppression, opt-out |
| *"compliant escalation"* | Policy layer derives the permitted rung per case |
| *"measured money recovered across a batch"* | §4, incremental against a holdout |
| *"audit trail"* | Decision-level traces, `traces/` shipped |

## Against their "why now"

> *"AI can now close the loop from detecting the problem **to diagnosing it**, choosing the right
> intervention, and recovering the money."*

**Stages 0 and 1 are that step.** Most submissions build detect → recover and skip it.

## Named example directions covered

**Four of seven**: B2B receivables chaser · promise-to-pay tracker · payment degradation root cause ·
mandate retry sequencer. Plus abandoned cart and subscription recovery as thin adapters (§2C).

## ⚠️ The Track 4 overlap, handled

Stage 0 resembles *"multi-source reconciliation"* — a Track 4 example direction.

1. **Never call it reconciliation.** It is *validation* / *payment attribution* / *shortfall diagnosis*
2. **Headline metric is ₹ recovered**, never match rate — the metric decides the track
3. **GST-on-fees excluded** (above)
4. **One line in the README**, pre-emptively:

> *"This project validates and diagnoses revenue-at-risk events before deciding whether to act on
> them. That validation resembles reconciliation, which appears in Track 4 — but here it is
> instrumental rather than the objective: nothing is reported as a match rate, and the measured
> outcome is money recovered and customers not wrongly contacted."*

---

# 2B. ⭐ The Delta Rule — this leads, or the submission dies

`requirements.md` §6b **Stage 0 kill switch**: *"A rebuild of an existing Agent Studio agent with no
stated delta."* Zero. No partial credit.

**We now deliberately overlap two shipped agents.** So this section is not a footnote — it is the
first thing in the README and the first forty seconds of the video.

## The decision, recorded honestly

v1 avoided every Razorpay product and scored **95/100**. v2 overlaps two of them and, after the
2026-08-26 verification pass, also scores **95/100**. The reversal was made on a judgement call worth stating plainly:

> **Razorpay is hiring builders, not inventors.** A solution that works, measures itself and knows
> its own limits is worth more than a novel one that doesn't. Novelty is **15 of 100** on the rubric.
> Measurement, bounds and honesty together are **60**.

⚠️ **The cost, stated against my own prior research.** `requirements.md` §4.5 conclusion 4 says:
*"if you stay in Track 3, go where the crowd isn't: B2B receivables, promise-to-pay — 3–6 repos each,
not 88."* Broadening moves **toward** the crowd. D1/D2/D3 are what buys that back. If they are not
communicated well, this decision is a net loss.

## The delta, in the form it must be stated

| Nearest existing thing | What it does | **Our measured delta** |
|---|---|---|
| **Agent Studio · Abandoned Cart Conversion** | Recovers abandoned checkouts | Cannot see the same customer's failed subscription or overdue invoice. **Shared contact ledger.** Also contacts carts that completed elsewhere — **Stage 0 removes them** |
| **Agent Studio · Subscription Recovery** | Recovers failed renewals | Retries per subscription. **Cannot correlate 40 failures to one issuer outage.** Also retries customers who intended to cancel |
| **RazorpayX Agentic Banking · collections** | *"Tracks unpaid invoices and automatically follows up"* — announced 12 Mar 2026, still early access | Published description mentions **no TDS validation, no statutory interest, no statutory escalation** |
| **Agent Studio + RazorpayX** | **12 agents, two platforms** | **Twelve agents cannot share a contact budget, and no frequency caps are published at all.** One engine can |
| **Payment Downtime API + Optimizer** | Detects outages in real time, reroutes in-flight traffic | ✅ They own detection. **Nothing published consumes that signal at the recovery layer** — we subscribe to their webhook and suppress retries into a known outage |

⚠️ **Discipline: say "their published description does not mention X" — never "their product does
not do X."** The first is verifiable. The second is a claim you cannot defend in a room containing
the person who built it.

## The sentence

> *"Razorpay ships twelve agents across two platforms. I built one engine that does what four of
> them do — and then the thing twelve separate agents structurally cannot: hold one contact budget
> per customer. It consumes Razorpay's own downtime webhook so it never chases into an outage. And
> it does the step none of them take — checking the money was ever lost."*

---

# 2C. Required functionality

Every function traces to a clause in the build spec or the bar. Nothing decorative.

**Depth strategy — this is the scope guard.** Two streams deep, two thin. The thin adapters exist to
prove the engine generalises and to make the coverage argument; they are not where the evidence
comes from.

```
ENGINE — built once, shared by all four
   ├── B2B invoice        ← DEEP    full validation, §16 interest, promise tracking
   ├── Failed payment     ← DEEP    root-cause correlation, retry sequencing
   ├── Abandoned checkout ← THIN    adapter only (~0.5 day)
   └── Subscription       ← THIN    adapter only (~0.5 day)
```

## Stage 0 · VALIDATE — ⭐ the differentiator
*Serves: nothing in the brief. This is the addition.*

| # | Function | MVP |
|---|---|---|
| F1 | Ingest all four event types (Razorpay MCP test mode + synthetic ledger) | ✅ |
| F2 | **Payment→invoice matching** — exact on reference, fuzzy on amount/date/buyer | ✅ |
| F3 | **Classify B2B shortfall** — TDS · partial · discount · dispute · misallocation · unexplained | ✅ |
| F4 | **Verify TDS against a configurable statutory rate table** (by section) | ✅ |
| F5 | **Multi-invoice allocation** — one payment covering several invoices | ✅ |
| F6 | **Failed-payment self-recovery check** — did the customer already retry successfully? | ✅ |
| F7 | **Cart completion check** — completed in another session/device? habitual non-buyer? | ✅ |
| F8 | **Deliberate-cancellation detection** — chasing an intended cancel is harassment | ✅ |
| F9 | ⛔ **Abstain when unexplained** — emit hypotheses tested and evidence missing | ✅ |
| F10 | ⭐ **Phantom risk report** — *"13% of your at-risk list was never at risk"* | ✅ |

## Stage 1 · DIAGNOSE
*Serves: "diagnosing it" (why now) · "determines the right intervention"*

| # | Function | MVP |
|---|---|---|
| F11 | **Failure-reason classification over Razorpay's published error-code taxonomy** | ✅ |
| F11b | ⭐ **Subscribe to Razorpay's Payment Downtime webhook** — suppress retries and contact into a known outage, reschedule on the resolution event | ✅ |
| F12 | ⭐ **Cross-case correlation** — cluster failures by issuer/bank/method/window | ✅ |
| F13 | **Degradation detection** — success-rate drop vs baseline → suppress individual retries | ✅ |
| F14 | Buyer/customer history assembly — prior failures, prior promises, prior recoveries | ✅ |

## Stage 2 · DECIDE
*Serves: "detects revenue at risk" · "determines the right intervention"*

| # | Function | MVP |
|---|---|---|
| F15 | Compute genuine recoverable amount + ageing | ✅ |
| F16 | Recovery-probability model by stream, ageing bucket and history | ✅ |
| F17 | **Relationship-value score** — lifetime value vs amount at risk | ✅ |
| F18 | ⭐ **Cross-stream ranking under a SHARED per-customer contact budget** | ✅ |
| F19 | **Accruing §16 statutory interest** — compound, monthly rests, 3× bank rate | ✅ |
| F20 | **Retry-timing selection** — when, not just whether | ✅ |
| F21 | Select intervention: none · retry · remind · link · update method · escalate · stop | ✅ |
| F22 | **Escalation economics** — expected recovery vs relationship cost | ⭐ |
| F23 | **TDS credit gap check** — withheld but not in 26AS *(hard timing buffer)* | ⭐ |

## Stage 3 · ACT
*Serves: "executes a bounded recovery workflow" · "don't just identify the problem"*

| # | Function | MVP |
|---|---|---|
| F24 | **Draft compliant message in the merchant's name** — never Razorpay's | ✅ |
| F25 | Attach payment link (`create_payment_link` / `send_payment_link`) | ✅ |
| F26 | **Execute payment retry** at the chosen time, idempotency key enforced | ✅ |
| F27 | Request payment-method update when the instrument is the cause | ✅ |
| F28 | **Extract promises from free-text replies** — *"we'll release on the 5th"* | ✅ |
| F29 | **Detect the breach the day after**, follow up on *that* commitment | ✅ |
| F30 | Escalate **one rung** on breach — never two | ✅ |
| F31 | ⛔ **Silent-dispute detection → halt, escalate to merchant** | ✅ |
| F32 | ⛔ **Samadhaan application as a populated PDF — with reason and full attempt log. DRAFTED, NEVER FILED** | ⭐ |
| F33 | **Negotiation** — evaluate part-payment offers against cost of capital, hard caps | ⭐ |

## Cross-cutting · POLICY LAYER
*Serves: ⭐ "compliant escalation" · "stopping rules" · "audit trail"*

| # | Function | MVP |
|---|---|---|
| F34 | ⭐ **Per-case permission derivation** — MSME-registered? · TDS section? · retry n of 3? · cap reached? · dispute open? → permitted vs blocked | ✅ |
| F35 | ⭐ **Shared contact ledger** — caps enforced per customer across all four streams | ✅ |
| F36 | Quiet hours · opt-out honoured permanently | ✅ |
| F37 | **Approval gates** — interest **opt-in**, escalation **confirmed**, filing **never automatic** | ✅ |
| F38 | ⭐ **Mirror Razorpay's own consent model** — one-time scoped consent, per-merchant cap, no per-action re-auth, full visibility, instant revoke *(the UPI Reserve Pay shape; name the parallel)* | ✅ |
| F39 | **Decision-level audit trail** — alternatives considered, chosen, blocked, and why | ✅ |
| F40 | Idempotency keys on every money-touching action; safe replay | ✅ |

## Evaluation harness — ⭐ BUILD FIRST
*Serves: "measured money recovered across a batch" — **40 of 100 rubric points***

| # | Function | MVP |
|---|---|---|
| F41 | **Seeded generator with ground truth** — statutory TDS rates, 73-day DSO, Razorpay error-code distribution | ✅ |
| F42 | **Holdout group** — recovery measured incrementally, never gross | ✅ |
| F43 | **Rules-engine baseline** in the same repo, same batch | ✅ |
| F44 | ⭐ **Per-stream-agent baseline** — four independent agents with no shared budget, to measure D1 | ✅ |
| F45 | Metrics + intervention breakdown (§4) | ✅ |
| F46 | Sensitivity curve over payer-model parameters | ⭐ |
| F47 | `make setup / demo / eval` — one command regenerates every number | ✅ |

**41 MVP functions · 6 stretch.** ⭐ **Every stretch item is one that can harm the merchant.** Losing
them to time costs nothing you can't survive.

---

# 2D. The action board

What the agent may and may not do. This is a slide, not prose.

```
✅ ALLOWED                              ⛔ FORBIDDEN
─────────────────────────────────      ─────────────────────────────────
Retry a failed payment (≤3)            Retry beyond the cap
Send reminder in merchant's name       Send in Razorpay's name
Generate + send a payment link         Move money directly
Request payment-method update          Store or handle card data
Record a promise-to-pay                Contact during a live promise
Compute statutory interest             Include interest without opt-in
Escalate ONE rung                      Escalate two rungs
Draft the Samadhaan application        File it
Propose a part-payment within caps     Discount beyond the merchant cap
Halt and hand to a human               Contact outside quiet hours
Abstain and log an exception           Contact after opt-out
                                       Exceed 4 contacts/customer/month
                                       Contact about a disputed case
```

**Every ⛔ is enforced in the policy layer and logged when it fires** — a blocked action is a trace
entry, not a silence.

⚠️ **Do NOT present this board as novel.** Verification on 2026-08-26 found Razorpay already ships,
in their own words: *"No agent takes an irreversible action without explicit merchant approval"*,
*"review-first mode"*, *"customers who opt out are permanently suppressed — no exceptions"*, and
*"every single action is logged with a full audit trail … what the agent did, when, and why."*

✅ **Present it as compliance with their published standard, and cite their wording.**
`requirements.md` §5.10 asks for exactly that. **The differentiation is only in F35 (shared ledger),
F34 (per-case permission derivation) and F9 (abstention)** — none of which appear anywhere in their
material.

---

# 3. Evaluated from every angle

## 3.1 Merchant

**Who it serves.** Any merchant with recurring revenue, online checkout, or B2B credit terms —
which is most of the 12M. Strongest for the merchant with no accountant and no collections person.

| Benefit | Concrete |
|---|---|
| **Stops false contacts** | Never demands money from a customer who paid, cancelled, or already retried |
| **Phantom risk removed** | *"13% of your at-risk list was never at risk"* |
| **One voice per customer** | Not three messages from three systems |
| **Outage-aware** | Doesn't burn 40 retries into a bank that's down |
| Lost TDS credits found | Deductions never deposited = money lost twice |
| DSO compression | Systematic follow-up they cannot sustain manually |
| Relationship protection | Aggression modulated by customer value |

**Where it can hurt them** — the honest part:

| Risk | Mitigation built in |
|---|---|
| 🔴 Statutory interest can cost the customer | Computed by default, **sent only on instruction** |
| 🔴 **§43B(h)**: invoking MSMED reveals they're MSME-registered — some buyers avoid such suppliers | Gated behind relationship check; never in a first reminder |
| 🔴 Samadhaan filing ends the relationship | **Drafted, never filed** |
| 🟠 26AS gaps may be quarterly timing, not default | Hard timing buffer; merchant-facing only |
| 🟠 Negotiation erodes margin | Hard caps; cumulative concession reported |
| 🟠 Shared contact cap may under-serve a high-value stream | Cap is per customer but ranking is value-weighted; report suppressed value |

## 3.2 Razorpay

**Strategic fit.** Their goal is *"a financial operating system, not a payments provider"*, and
revenue per merchant (~₹3,150/yr) must rise before an IPO. Recovery is a surface they have entered
seven times and not unified once.

**Do they want it?** Evidence yes — they built **twelve** agents in this space. **The orchestration layer
above those agents is the natural next product, and it is the thing this demonstrates.**

**Commercial value:** payment links and retries on recovered revenue are billable TPV; an
orchestration layer raises products-per-merchant, which is exactly the monetisation pivot visible in
FY25 (+65% revenue on +20% volume).

## 3.3 Competitive

| Competitor | What it does | Gap |
|---|---|---|
| **Agent Studio (7 agents)** | Per-leak-type recovery, in beta/early access | ✅ Verified: **no shared contact budget, no frequency caps at all, no orchestration, no validation step** |
| **RazorpayX Agentic Banking (5 agents)** | Collections agent *"tracks unpaid invoices and automatically follows up **on call**"* | Published description mentions no TDS, no statutory interest. ⚠️ **They use voice; do not compete on channel** |
| **Payment Downtime API / Optimizer** | Real-time outage detection + rerouting + retries recovering *"15-20% of failed transactions"* | ⚠️ **They own detection.** Gap is that nothing consumes the signal at the recovery layer |
| **88 Track 3 repos** | 36 claim "bounded", 35 claim "audit" | **1 of 8 sampled had held-out evaluation.** Measurement is still the differentiator |
| HighRadius / Growfin / Kolleno | Collections agents, promise-to-pay | Built for US/EU rails. No TDS, no MSMED |

## 3.4 Judge / panel — scored on `requirements.md` §6b

| # | Criterion | Wt | Score | Why |
|---|---|--|--|---|
| 1 | Measured outcome on a batch | 25 | **21** | Exceeds the ≥200 floor at 600 events; baseline + holdout + ablation. Deducted: four authored payer models |
| 2 | Bounded autonomy & audit trail | 20 | **19** | Shared ledger, policy layer, idempotency, `traces/`, blocked actions logged, Razorpay's own consent shape |
| 3 | Honest evaluation & failure analysis | 15 | **14** | False-contact rate, holdout, harm metrics, abstention rate, sensitivity curve |
| 4 | **Novelty (Delta Rule)** | 15 | **10** ⚠️ | D1/D2/D3 are structural and defensible — but we visibly rebuild two shipped agents. **Highest-variance criterion** |
| 5 | Agentic necessity | 10 | **10** | Abduction, cross-case correlation, sequential decisions, meaningful abstention, baseline actually run |
| 6 | Engineering & stack fit | 10 | **8** | Consuming the real Downtime API + webhook is genuine stack fit. Deducted: four streams solo in ~10 days |
| 7 | Communication | 5 | **4** | Four streams in five minutes gets rambly. Budget it hard |
| 8 | Problem truth | 10 | **9** | Government-sourced magnitude; universal leak types |
| | | | **95/100** | ≥85 = competitive |

**Kill-switch check:** *"a rebuild of an existing Agent Studio agent with no stated delta"* — cleared
**only because §2B leads.** If the delta becomes a footnote, this scores **zero**, not 94.

## 3.5 Engineering — why an agent, not a rules engine

- **Stage 0/1 is abduction** — inferring cause from an open explanation space, where which evidence
  you gather depends on the hypothesis you currently hold. A rules engine resolves the cases you
  enumerated; the agent resolves the one you didn't.
- **Cross-case correlation is not a lookup.** Whether 40 failures are one outage or 40 unrelated
  events depends on issuer, method, time window, base rate and merchant mix simultaneously.
- **Stage 2 is sequential decision-making under a shared budget** — every reply changes the state,
  streams compete for the same contact slot, objectives conflict, the horizon is weeks.
- **Abstention is the highest-value output.** A rules engine has no notion of confidence; a
  classifier must emit a class. Only an agent can say *"I can't explain this, so I won't act"* — and
  here that restraint prevents real commercial damage.

**Proof, not assertion:** two baselines ship in the same repo — a rules engine (F43) **and four
independent per-stream agents with no shared budget (F44)**. The second is what measures D1.

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
| Agent Studio ships 7 agents incl. Abandoned Cart + Subscription Recovery | ✅ **VERIFIED 2026-08-26 on the live page. Roster has NOT grown** |
| No orchestration layer / shared contact budget across agents | ✅ **VERIFIED on 4 sources** — launch blog, guardrails blog, live page, Agentic Experience Platform |
| No validation-before-acting in any published description | ✅ **VERIFIED** — consent validation exists; risk validation does not |
| RazorpayX ships 5 further agents incl. Collections (voice calls) | ✅ **VERIFIED** — 12 agents total across two platforms |
| Razorpay publishes a Payment Downtime API + webhooks | ✅ **VERIFIED** — D2 rewritten because of this |
| Optimizer detects outages and reroutes in real time | ✅ **VERIFIED** — detection is theirs, not ours |
| Downtime API available in **test mode** | ❌ **Unverified — check before relying on it in the demo** |
| RazorpayX collections agent exists, early access | ✅ Verified on the live page |
| **TDS rates by section** | ⚠️ **Mechanic verified; specific rates NOT — verify before building** |
| Test-mode partial payments against invoices | ❌ Unverified |
| Payer-response models (all four streams) | ❌ **Authored by you. Publish parameters** |

---

# 4. Metrics

**Lead with the metric the bar names. Differentiate with yours.**

| Rank | Metric | Why |
|---|---|---|
| **1 · HEADLINE** | **₹ recovered across the batch — incremental against a holdout** | ⭐ Exactly what the bar demands. Never gross |
| **2 · SET-UP** | **₹ removed at Stage 0 — money that was never at risk** | The reframe. Delivered before the headline |
| **3 · DISTINCTIVE** | **False-contact rate** — customers contacted about money not at risk | The harm metric. Almost nobody reports one |
| **4 · PROVES D1** | **Contacts saved vs four independent agents** | Measures the orchestration delta directly |
| 5 | Recovery rate · cost per recovery | Named in the Track 3 floor |
| 6 | Stage-0 accuracy vs **statutory** ground truth (B2B) | The half that isn't authored |
| 7 | DSO days compressed | The merchant's language |
| 8 | Abstention rate · promise-kept rate · opt-outs · margin conceded | Honest reporting of cost and harm |

## The batch — illustrative shape, not measured

⚠️ **These numbers do not exist yet.** They show the format the eval harness must produce.

```
BATCH: 600 revenue-at-risk events, ₹79,20,000 claimed at risk

STAGE 0 — VALIDATE
  B2B invoices        60 events    ₹6,10,000 was TDS / already settled
  Failed payments    240 events    ₹1,90,000 customer already retried
  Abandoned carts    180 events    ₹2,20,000 completed elsewhere
  Subscriptions      120 events      ₹14,000 deliberate cancellation
  ─────────────────────────────────────────────────────────────────
  REMOVED                         ₹10,34,000  = 13.1% never at risk
  TRUE EXPOSURE                   ₹68,86,000

INTERVENTION BREAKDOWN
  Intervention            Cases   Contacts   Recovered
  ──────────────────────────────────────────────────────
  Batch retry (post-outage)  40          0   ₹ 2,10,000
  Individual retry           88          0   ₹ 3,40,000
  Payment-link reminder     112        112   ₹ 6,80,000
  Method-update request      46         46   ₹ 1,90,000
  B2B reminder + promise     38         61   ₹ 7,20,000
  Escalated to human         14          0   ₹      —
  No action (low value)      97          0   ₹      —
  ABSTAINED                  23          0   ₹      —
  ──────────────────────────────────────────────────────
  TOTAL                                219   ₹21,40,000

BASELINES
  Rules engine                         287   ₹16,90,000
  4 independent agents (no shared cap) 394   ₹19,60,000

DELTA
  vs rules engine        +₹4,50,000    −68 contacts
  vs per-stream agents   +₹1,80,000   −175 contacts  ← this is D1
  False contacts:  agent 0  ·  rules 41  ·  per-stream agents 47
```

**The order matters.** A judge scanning for the number the bar names finds it immediately. The
13.1% and the −175 contacts are what they remember afterwards.

---

# 5. Build plan — evidence first, safeguards before sharp instruments

| Days | Work | Harm |
|---|---|---|
| **1–2** | ⭐ **Eval harness first** — generator, ground truth, holdout, trace format, `make eval`, both baselines | 🟢 None |
| **3–4** | Engine core + Stage 0 validation, all four streams · phantom risk report | 🟢 None |
| **5** | Shared contact ledger · policy layer · action board enforcement | 🟢 Protective |
| **6** | Cross-case correlation · degradation detection · retry sequencing | 🟢 None |
| **7** | Dispute abstention · relationship weighting · escalation economics | 🟢 Protective |
| **8** | Statutory interest *(opt-in)* · 26AS check *(timing buffer)* · thin adapters x2 | 🔴 Gated |
| **9–10** | README · video · freeze · tag · submit | — |
| *slack* | Samadhaan draft *(never files)* · negotiation *(hard caps)* | 🔴 Gated |

**Two rules that decide this build:**

⭐ **1. The eval harness is days 1–2, not days 9–10.** It is 40 of 100 points, and 7 of 8 serious
competitor repos do not have one — because they built features first and ran out of time. Building
it first also forces you to define what "correct" means, which shapes the engine.

⭐ **2. If you run out of time, cut the thin adapters, not the evidence.** Two deep streams with a
holdout beats four shallow ones with a demo. And you ship a cautious agent rather than an aggressive
one — the correct failure mode for software touching customer relationships.

---

# 6. The demo — five minutes, budgeted hard

| Time | Beat |
|---|---|
| **0:00–0:35** | ⭐ **The delta, first.** *"Razorpay ships twelve agents across two platforms. Here is what one engine does that twelve cannot."* Name them |
| 0:35–1:00 | The problem: 73 days, ₹20,979 cr — and the claim that a share of every at-risk figure is fiction |
| **1:00–1:45** | ⭐ **Stage 0 live.** Short payment arrives → agent identifies TDS → **marks settled instead of chasing.** Then the batch: **₹10.34L removed, 13.1% never at risk** |
| 1:45–2:45 | **Live batch, 600 events.** Intervention breakdown filling in. False-contact counter at zero |
| **2:45–3:15** | ⭐ **D2 on camera.** 40 failures, one issuer. Agent correlates, **suppresses 40 retries**, schedules one batch retry |
| 3:15–3:45 | ⭐ **D1 on camera.** One customer in three streams → **one message**, and the trace showing which two were suppressed and why |
| 3:45–4:15 | **The stop.** Third broken promise → halt → Samadhaan application **drafted, not filed**. Plus one abstention: *"cannot explain, will not contact"* |
| 4:15–4:40 | Both baselines side by side. **−175 contacts, +₹1.8L** |
| **4:40–5:00** | ⭐ **How it could hurt the merchant, and what I did** (§43B(h), opt-in interest) + the number I trust least |

⚠️ **Four streams in five minutes is the single biggest communication risk.** Do not tour the
architecture. Show the deltas and the batch; the repo carries the rest.

---

# 7. Panel questions

| Q | A |
|---|---|
| ⭐ *"Why not just use Agent Studio's Abandoned Cart agent?"* | You should — for abandoned carts alone. It cannot see that the same customer also has a failed renewal and an overdue invoice. Here is the trace where three would have fired and one did |
| ⭐ *"So you rebuilt two of our agents."* | Yes, deliberately, and the components are not the contribution. The contribution is the layer above them. Here are two baselines measuring exactly that |
| *"Doesn't RazorpayX do the B2B part?"* | Their published description says *"tracks unpaid invoices and follows up."* It does not mention TDS or statutory interest. Announced March, still early access |
| *"Doesn't Tally handle TDS?"* | Yes — as a report, for merchants who keep books properly. Here it is a gate on action inside the loop, for merchants who do not |
| *"How do you know the TDS rate?"* | Configurable table by section. The agent proposes and **abstains when ambiguous** |
| *"Where is your ground truth?"* | Stage 0 B2B is **structural** — statutory rates are objectively checkable. The behavioural models are mine; parameters and sensitivity published |
| *"Couldn't rules do this?"* | The rules baseline is in the repo, same batch. Here are the cases only the agent got, and why |
| *"What is your false-positive rate at the threshold you shipped?"* | *(have the number and the curve)* |
| *"Show me the trace for case #47."* | *(have `traces/` and be able to open it live)* |
| *"What breaks at 10x volume?"* | Correlation is O(n) bucketed; LLM is on the residual only — quantify the residual share |
| **⭐ "Which number do you trust least?"** | The payer-response models. All four are mine. Everything downstream is directional — which is why the delta against baselines, not the absolute, is the claim |

---

# 8. The honest case against

**Behavioural ground truth is authored — and now four times over.** Stage 0's B2B arm is structural.
Everything downstream of "would this customer have paid anyway" is a model I wrote. Broadening
multiplied that surface. **The absolute recovery number is authored; the delta against baselines
facing identical simulated customers is what is defensible.**

**We are now in the crowd.** 88 Track 3 repos, and two of our four streams are shipped Razorpay
products. v1 deliberately avoided this. The reversal is defensible and recorded in §2B — but if D1
and D2 do not land, this is strictly worse than v1.

**Four streams, one builder, ~10 days.** The scope guard (two deep, two thin) exists because this is
the most likely failure mode. Engineering and Communication both took a point for it.

**✅ The roster question is now closed.** Verified 2026-08-26 on the live page: still 7 in Agent
Studio, plus 5 in RazorpayX. No orchestration layer on any of four sources. D1 holds.

**⚠️ But D2 was overclaimed and had to be rewritten.** Razorpay ships a Payment Downtime API, and
Optimizer detects outages *"within seconds of a success rate dip."* I claimed detection as our
delta; it is theirs. The surviving claim — that nothing consumes the signal at the recovery layer —
is narrower and rests on absence of evidence in published descriptions, not on proof.

**Half of our bounded-autonomy story is table stakes.** Approval gates, review-first, opt-out
suppression and the audit trail are all shipped and blogged about. Only the shared ledger,
per-case permission derivation and abstention are ours.

**Would a supplier chase ₹4,000?** Individually, no. The framing is ₹1.6L of phantom receivables
distorting their books, not one small chase.

**Seven ideas died against Razorpay's product surface before this one.** My picture of what they
have built has been wrong six times. It may still be incomplete.

---

# 9. Next actions

**Before writing code:**

1. ⭐ **Verify TDS rates by section.** The one load-bearing fact still unchecked
2. ✅ ~~Re-check the Agent Studio roster~~ — **DONE 2026-08-26.** Still 7 + 5. No orchestration.
   See `research/gap_verification.md`
3. **Verify test-mode partial payments against invoices** — decides how much is synthetic
4. ⭐ **Verify the Payment Downtime API works in test mode.** F11b depends on it; if not, simulate
   the webhook payload and say so on camera

**Then, in order:**

5. ⭐ **Days 1–2: the eval harness.** Not the agent. 40 of 100 points, and the thing 7 of 8
   competitors never finish
6. **Write the delta sentence (§2B) before anything else** and put it at the top of the README. It
   is a kill switch, not a talking point
7. **Repo description must contain a number.** *"Bounded, auditable AI agent"* is indistinguishable
   from 35 others
8. **Lock the track. One shot, no edits after submission**

**If Abhishek replies:** *"Does the RazorpayX collections agent validate a short payment against TDS
before following up — and can Agent Studio agents share a contact budget across use cases?"* Both
factual, neither confidential, and together they confirm or dissolve the entire delta.

---

**The one-sentence pitch:**

> *Twelve agents chase twelve leaks and cannot see each other. One engine sees all four, checks the
> money was ever lost, and speaks to each customer once.*
