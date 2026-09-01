# gap_verification.md — Are We Actually Covering a Razorpay Gap?

Verified 2026-08-26 against primary Razorpay sources. Ten checks.
Grading: **[A]** official Razorpay · **[B]** primary external · **[C]** secondary.

**Verdict: two deltas survive, one must be rewritten, and one prior claim was wrong.**

---

## Summary table

| # | Claim under test | Verdict |
|---|---|---|
| 1 | Agent Studio ships 7 prebuilt agents | ✅ **CONFIRMED** [A] |
| 2 | The roster has not grown since March | ✅ **CONFIRMED** — closes the biggest open question |
| 3 | No orchestration / agent coordination exists | ✅ **CONFIRMED on 3 sources** → **D1 SURVIVES** |
| 4 | "Agentic Experience Platform" is not an orchestration layer | ✅ **CONFIRMED** [B] |
| 5 | No contact-frequency caps are described anywhere | ✅ **CONFIRMED** → D1 stronger than assumed |
| 6 | Nothing validates whether revenue is genuinely at risk | ✅ **CONFIRMED** → **D3 SURVIVES** |
| 7 | Razorpay publishes a **Payment Downtime API + webhooks** | 🔴 **NEW — I did not know this** |
| 8 | **Optimizer already detects downtime, reroutes and retries** | 🔴 **NEW — D2 MUST BE REWRITTEN** |
| 9 | RazorpayX ships **5 more agents**, incl. a Receivables agent that calls | ⚠️ **12 agents total, not 7** |
| 10 | Audit trail, approval gates, opt-out are already shipped | ⚠️ **Our F36–F39 are table stakes, not deltas** |

---

# 🔴 The two findings that change the project

## 7 + 8 · D2 was overclaimed. Rewrite it.

**What I claimed:** *"Forty failed payments sharing one issuer outage is one event. Per-case agents
retry forty times into a bank that is down. The engine correlates first."*

**What is actually true:**

Razorpay publishes a **Payment Downtime API and downtime webhooks** [A]. Downtimes are detected per
payment method — cards by network and issuer, netbanking by bank, UPI — and classified High /
Medium / Low severity. Creation *and resolution* are posted to a webhook any merchant can subscribe
to from the dashboard.

**Razorpay Optimizer goes further** [A]: *"proactive downtime management ... AI-driven detection to
identify bank-side outages in real time — often within seconds of a success rate dip beginning."*
It creates temporary 20-minute downtimes when success rate drops below threshold, reroutes traffic
to a healthy gateway, and its automated retries *"recover 15-20% of failed transactions."*

⚠️ **So detection is not the gap. Detection is a shipped Razorpay product.**

### The rewritten D2 — narrower, and better

Optimizer operates at the **routing layer**: an in-flight transaction is steered to a healthy
gateway *before* it fails. Our decision is at the **recovery layer**: forty payments that have
*already* failed and are sitting in a queue — should we retry them now, and should we message these
customers?

**Nothing published connects the downtime signal to the recovery decision.** The Subscription
Recovery agent applies *"smarter retry logic"*; no description says it consults the Downtime API.

> **D2 (revised): consume Razorpay's own published downtime signal as an input to the recovery
> decision — suppress retries and customer contact into a known outage, and reschedule for
> resolution.** We are not detecting the outage. We are the first thing to *act on it downstream*.

**Why this is better than the original claim:**

- `requirements.md` §5.11 explicitly asks you to **reason over Razorpay's published taxonomy, not
  one you invented.** Consuming the Downtime API *is* that rule satisfied
- It scores on Engineering / stack fit — real API, real webhook, test mode
- It is unfalsifiable by a panel, because it concedes their product does the hard part
- ⚠️ **It also removes an easy panel kill:** *"You know we ship a downtime API, right?"*

**Two caveats worth keeping:**

- **Optimizer is a multi-gateway enterprise product.** A small merchant on plain Razorpay PG has the
  Downtime API but not Optimizer's rerouting
- Optimizer reroutes payments. It never decides **whether to contact a human being**

---

## 9 · There are 12 agents, not 7. My earlier count was wrong.

**RazorpayX Agentic Banking ships five more** [A/C]: Payouts, **Collections**, Reporting,
Bookkeeping, Insights.

The Collections agent: *"tracks unpaid invoices and automatically follows up **on call**"* — it
places **voice calls**, which I had not established.

| Platform | Agents |
|---|---|
| Agent Studio | Dispute Responder · Subscription Recovery · Abandoned Cart *(two vendors: SuperU, Nugget by Zomato)* · RTO Shield · RTO Insights · Settlement Insights · Cashflow Forecaster |
| RazorpayX Agentic Banking | Payouts · **Collections** · Reporting · Bookkeeping · Insights |
| **Total** | **12 across two platforms** |

**This cuts both ways:**

🟢 **D1 gets stronger.** Twelve agents across **two separate platforms**, and no published evidence
any of them share state. A customer can now be contacted by an Agent Studio abandoned-cart nudge
*and* a RazorpayX collections **phone call** in the same afternoon.

🔴 **The B2B novelty gets weaker.** Their Collections agent makes voice calls. Ours drafts emails.
Do not compete on channel — compete on **what it does before it contacts anyone.**

---

# ✅ What survives, and the evidence

## D1 · Shared contact budget — SURVIVES, three independent confirmations

| Source | Finding |
|---|---|
| Agent Studio launch blog [A] | No mention of agents coordinating, sharing state, or a shared contact budget |
| **Guardrails & merchant control blog [A]** | No contact-frequency caps, message limits or budgets described. No central policy layer across agents |
| Live `/agent-studio/` page [A] | No orchestration layer, no shared budget, no coordination |
| Agentic Experience Platform [B] | **Not** orchestration — it is Agentic Onboarding, Agentic Dashboard, Agentic Integration |

⭐ **Stronger than assumed.** I expected per-agent frequency caps to exist. **No frequency caps are
described at all.** So D1 is now two claims, not one: (a) caps, and (b) caps *shared across agents*.

## D3 · Validate before chasing — SURVIVES

No source describes checking whether money is genuinely at risk before acting: no prior-payment
check, no already-retried check, no deliberate-cancellation check, no TDS diagnosis.

⚠️ **One distinction to make carefully.** The guardrails page *does* describe consent validation —
*"telephony consent is validated against the merchant's customer records"* and *"customers who opt
out are permanently suppressed."*

**That is permission to contact, not whether there is anything to contact about.** Say it that way,
precisely, or a panel will think you missed their consent model.

---

# ⚠️ 10 · What we thought were differentiators but are table stakes

The guardrails page already ships, in Razorpay's own words [A]:

| Ours | Their published equivalent |
|---|---|
| F37 approval gates | *"No agent takes an irreversible action without explicit merchant approval"* |
| F37 review before send | *"review-first mode: the agent does all the work ... but holds it for the merchant to review"* |
| F31 escalate to human | *"agents escalate to the merchant — typically on WhatsApp — rather than acting unilaterally"* |
| F36 opt-out | *"Customers who opt out are permanently suppressed — no exceptions"* |
| **F39 audit trail** | *"**Every single action is logged with a full audit trail.** The merchant can see exactly what the agent did, when, and why"* |

🔴 **Consequence: do not present bounded autonomy or the audit trail as novel.** Razorpay shipped all
of it and wrote a blog post about it.

✅ **Present them as compliance with their own published standard**, and put the differentiation
entirely in **F35 (shared ledger)**, **F34 (per-case permission derivation)** and **F9 (abstention)**
— none of which appear anywhere in their material.

This is also an opportunity: `requirements.md` §5.10 says *do not invent a safety scheme — implement
the shape Razorpay already shipped and name the parallel.* Now you can cite their exact wording.

---

# The quote to use

An independent industry writeup of RazorpayX Agentic Banking asks the open question directly [B]:

> *"Can these agents handle messy finance reality, edge cases, policy variance, tax complexity,
> reconciliation issues, and real-world exceptions?"*

**That is our project stated as a question, by someone who does not work for us.** It belongs in the
README and in the first minute of the video.

---

# Net effect on the score

| Criterion | Before | After | Why |
|---|---|--|---|
| Novelty (Delta Rule) | 10 | **10** | D2 narrowed (−), D1 strengthened by 12-agent fragmentation (+) |
| Engineering & stack fit | 7 | **8** | Consuming the real Downtime API is genuine stack fit |
| Honest evaluation | 14 | **14** | — |
| **Total** | **94** | **95** | |

**The gap is real. It is just not the gap I described yesterday.**

---

# Still unverified

- **TDS rates by section** — still the one load-bearing unchecked fact
- Whether the Downtime API is available in **test mode**
- Whether the RazorpayX Collections agent does any TDS handling *(nothing published either way)*
- Whether Agent Studio agents will gain coordination — **this is a roadmap question, do not ask it**

---

## Sources

- [Payment Downtime API — Razorpay Docs](https://razorpay.com/docs/api/payments/downtime/) [A]
- [Downtime alert notifications — Razorpay Blog](https://razorpay.com/blog/razorpay-downtime-alert-notifications-outage/) [A]
- [Agent Studio: AI Agents by Razorpay](https://razorpay.com/blog/agent-studio-ai-agents-by-razorpay/) [A]
- [Agent Studio: Principles, Guardrails, and Merchant Control](https://razorpay.com/blog/razorpay-agent-studio-principles-guardrails-and-merchant-control/) [A]
- [Razorpay Agent Studio product page](https://razorpay.com/agent-studio/) [A]
- [Razorpay Optimizer — AI-powered payments router](https://razorpay.com/blog/razorpay-optimizer-ai-powered-payments-router/) [A]
- [Payment success rate optimization India 2026](https://razorpay.com/blog/payment-success-rate-optimization-india/) [A]
- [Razorpay launches Agent Studio and Agentic Experience Platform — The Paypers](https://thepaypers.com/payments/news/razorpay-launches-ai-agent-studio-and-agentic-experience-platform) [B]
- [Razorpay Agentic Business Banking — Future of Banking](https://futureofbanking.ai/article/razorpay-agentic-business-banking) [B]

---

# Part 2 — What the evidence implies

Written 2026-08-26. Everything above is **FACT** (verified against primary sources). Everything below
is **INFERENCE** — reasoned from that evidence, labelled with confidence and with what would falsify
it. Do not present these to a panel as facts.

---

## I1 · Agent Studio is a marketplace, not an in-house build programme
**Confidence: 8/10**

**Evidence:** Two of the seven agents are partner-built — Abandoned Cart Conversion appears twice,
once from **SuperU** and once from **Nugget by Zomato**. One trade writeup calls the launch a
*"B2B agent marketplace."* Razorpay's own history is consistent: payroll, loyalty, POS, fraud and
lending tech were **all acquired rather than built** (`growth_history.md` §3).

**Inference:** Razorpay is shipping a *platform* and letting partners fill the catalogue. They built
roughly five agents themselves and sourced the rest.

**⭐ Why this matters more than anything else in this document:**

- **Partners build agents. Partners do not build the layer above agents.** No individual vendor has
  the incentive or the access to enforce a contact budget across a competitor's agent
- So the orchestration gap is **structural to their strategy**, not a backlog item
- And it means a strong external build is plausibly a **partner or acquisition target**, which is
  exactly how Razorpay has historically acquired capability

**Falsified by:** Razorpay announcing a first-party orchestration or agent-manager product.

---

## I2 · The missing frequency caps are architectural, not an oversight
**Confidence: 8/10**

**Evidence:** No contact-frequency caps are described anywhere — not per agent, not shared. Yet the
guardrails blog is detailed on consent, opt-out, approval and audit.

**Inference:** They did not forget. A frequency cap requires a **shared customer identity and a
shared state store across independently-owned agents.** That is platform infrastructure, and under
I1 nobody owns it. A team that thought carefully enough to write *"customers who opt out are
permanently suppressed — no exceptions"* did not overlook rate limiting; they could not implement it
in the architecture they chose.

**⭐ Consequence: D1 cannot be closed by shipping a feature inside one agent.** It requires the
layer we are building. That makes it durable rather than a race.

---

## I3 · Their guardrails are permission-shaped. Ours is warrant-shaped.
**Confidence: 9/10 — this is the sharpest line available**

**Evidence:** Every published control is about *may we contact this person*: consent validated
against merchant records, opt-out permanently suppressed, approval before irreversible actions,
review-first mode, full audit trail.

**Inference:** Razorpay's entire safety vocabulary answers **"is this contact permitted?"** Nothing
published answers **"is this contact warranted?"** — is there anything to contact them about.

> **The line for the panel:** *"Your guardrails answer whether we may contact this customer. Mine
> answers whether we should — whether there is anything to contact them about at all."*

That concedes their model fully, uses their own framing, and lands D3 in one sentence. It is also
why D3 was never an oversight on their part: **it is outside the frame they chose.**

---

## I4 · The agents were built on the merchant-facing API surface, not on internal signals
**Confidence: 6/10 — weakest inference here, rests on absence in marketing copy**

**Evidence:** The Downtime API and webhooks predate the agents. Subscription Recovery is described as
applying *"smarter retry logic"* with no mention of downtime awareness — and downtime awareness would
be a selling point if it existed.

**Inference:** The agents consume roughly the same merchant-facing surface an external builder can.

**⭐ Consequence: an outside build is not structurally disadvantaged.** Same webhooks, same APIs,
same error taxonomy. This is why the project is viable at all.

**Falsified by:** any documentation showing agents consuming internal risk or downtime signals.

---

## I5 · The buildathon is recruiting for the layer partners cannot supply
**Confidence: 7/10**

**Evidence:** Agent Studio March 2026. Vulcan August 2026. Confidential DRHP June 2026, IPO targeted
year-end. Buildathon opens August 2026 hiring AI builders, in person in Bangalore. Roster flat for
five months.

**Inference:** They can source *agents* from partners indefinitely. They cannot source **platform
architecture** — orchestration, shared policy, cross-agent state — from partners, because no partner
can build it. That is in-house work, it is on the critical path to an IPO story about AI, and it
needs headcount they do not have.

**⭐ Consequence: a submission that looks like the missing platform layer is strategically more
interesting to them than a better individual agent** — because better individual agents are already
arriving for free from SuperU and Zomato.

**This is the strongest available justification for the v2 scope decision**, and it was not the
reason the decision was originally made.

---

## I6 · RazorpayX Collections targets the tier above our merchant
**Confidence: 7/10**

**Evidence:** The Collections agent *"follows up **on call**"* — voice. It lives inside RazorpayX
Business Banking+ behind a chat interface.

**Inference:** Voice calling is not economics you run across 12M merchants at ~₹3,150 revenue each.
This is aimed at businesses with real AR operations and a Business Banking+ relationship.

**⭐ Consequence: the small-supplier B2B segment is genuinely unserved.** Position the B2B arm
**below** the Business Banking+ tier and never compete on channel.

---

## I7 · Most of the 88 Track 3 repos are rebuilding shipped Razorpay products
**Confidence: 7/10**

**Evidence:** 88 repos matched "recovery"; the crowded example directions are abandoned cart,
subscription recovery and failed payments — precisely what Agent Studio ships.

**Inference:** A judge will see the same rebuild many dozens of times. **Being one of 88 is only
fatal if you are the same as the 88.** The differentiating question is not *"did you build a recovery
agent"* — everyone did — but *"did you notice the agents cannot see each other."*

---

## I8 · D1 is safe for the submission window
**Confidence: 8/10**

Roster unchanged for five months; orchestration is platform work under I1/I2. **Probability that a
first-party orchestration layer ships in the next ~10 days: low.**

---

## I9 · The likely panel objection, and why it is a good outcome
**Confidence: 6/10**

If I1 is right, the natural response to *"you need orchestration"* is **"yes, we know, it is on the
roadmap."**

⭐ **That is not a rejection. That is the best possible outcome.** It means you independently derived
their roadmap from public evidence — which is exactly the signal a hiring panel is looking for.

**Prepared answer:** *"I'd expect it to be. I couldn't find it published, so I built it and measured
what it's worth — 175 fewer contacts on a 600-event batch. If it's already planned, that's the
strongest signal I picked the right problem."*

---

## What these inferences change

| Inference | Changes the build? | Changes the pitch? |
|---|---|---|
| I1 marketplace | No | ⭐ **Yes — frames the whole submission** |
| I2 architectural gap | No | Yes — D1 is durable, not a race |
| I3 permission vs warrant | No | ⭐ **Yes — best single line available** |
| I4 same API surface | No | Yes — justifies an external build |
| I5 recruiting for platform | No | ⭐ **Yes — retroactive justification for v2** |
| I6 tier positioning | ⚠️ **Yes — target below Business Banking+** | Yes |
| I7 crowd | No | Yes |
| I8 safe window | No | No |
| I9 panel objection | No | Yes — prepare the answer |

**None of these require rebuilding anything.** Seven of nine change how it is presented, and one
(I6) changes who the B2B arm is aimed at.

---

## Confidence discipline

⚠️ **These are inferences, not facts.** In the README and on camera, state the **fact** and let the
listener draw the inference:

| ❌ Do not say | ✅ Say |
|---|---|
| *"Agent Studio is a marketplace so they'll never build orchestration"* | *"Two of the seven agents are partner-built. I couldn't find any published coordination between them"* |
| *"Razorpay forgot about frequency caps"* | *"I couldn't find contact-frequency caps described in any published material"* |
| *"They only care about consent, not whether the contact is warranted"* | *"Their published guardrails cover consent and opt-out. I couldn't find anything that checks whether the money is genuinely at risk"* |

**Same content. One is defensible in a room containing the person who built it; the other is not.**
