# 8. What to Ask the Alumni

A senior SDE who builds agentic systems can de-risk something no amount of research can: **whether
the design survives contact with reality.** Every agent architecture in this research is a design.
None has been built.

Use their time on **technical judgement**, not on strategy. Don't ask them to pick your project.

---

## Open with context, in 60 seconds

> *"I'm applying to Razorpay's AI Builder buildathon. Students build a project, submit a repo and a
> 5-minute video, and if it shows signal you go straight to a panel. I've narrowed to two options and
> I've designed the architecture, but I've never shipped an agent. I'd value 20 minutes on whether
> the design is sound and what I'm underestimating."*

That framing gets better answers than "any advice?" — it tells them exactly what expertise you want.

---

## Tier 1 — Only they can answer these

### Q1. Does the architecture read as sound or over-engineered?

> *"My plan is: do the deterministic work in plain code first, send only the residual hard cases to
> the LLM, force structured output, and give it an explicit 'abstain' path that produces an exception
> record instead of a guess. Does that read as sound, or as over-engineering?"*

**Why:** this is the single most load-bearing architectural claim in my research. If a practitioner
says "no, just let the model do the whole thing," that changes the build.

### Q2. How do you actually evaluate an agent that's allowed to abstain?

> *"If the agent can say 'I don't know', precision on the cases it did answer looks great — but it
> can game that by abstaining more. How do you handle the coverage/precision trade-off in practice?
> Is there a convention?"*

**Why:** ⭐ **This is a genuine hole in my advice.** I recommend reporting both and publishing the
curve, but I don't know what practitioners actually consider rigorous. Their answer directly shapes
your headline metric — and the headline metric is what the bars grade.

### Q3. What breaks in production that never breaks in a demo?

> *"What failure modes have bitten you in real agentic systems that wouldn't show up in a 500-record
> demo?"*

**Why:** pure experience transfer. Unresearchable. Likely answers — non-determinism across runs,
prompt drift, silent tool failures, retries causing duplicate side effects, cost blowups, context
overflow on long traces. Any one of those is a slide in your video: *"here's what broke and how I
handled it."*

### Q4. Time calibration

> *"Solo dev, has written Python but never an agent loop. Data generator, deterministic matcher, LLM
> adjudicator with structured output and abstention, eval harness, traces. I've estimated 4–5 days.
> What would you estimate?"*

**Why:** effort estimation is **the riskiest assumption in the entire plan.** I added a two-day
buffer for someone who's never built an agent loop, but that's a guess. If they say eight days, you
cut scope on day one rather than day nine.

---

## Tier 2 — The hiring lens

### Q5. ⭐ What separates "has done this before" from "read a tutorial"?

> *"When you review someone's agent code, what makes you think this person has actually built one
> versus followed a tutorial?"*

**Why:** this is the highest-value question in the list. You're being judged by exactly this
instinct, and the answer is a direct checklist for your repo. Expect things like: idempotency keys,
retry handling, structured logging, a real evaluation, sensible failure paths, no giant prompt doing
everything.

### Q6. What has become a red flag?

> *"Is there a version of 'I built an agent' that's now a red flag for you?"*

**Why:** the anti-pattern list from someone who reviews these. Probably: multi-agent systems with no
reason to be multi-agent, a chatbot wearing an agent costume, "autonomous" things that only ever run
the happy path.

### Q7. What does a real audit trail look like?

> *"For an agent taking actions with money — what does a genuinely useful audit trail look like?
> Mine logs inputs, tool calls, the decision, confidence, and outcome per action."*

**Why:** every track bar demands an audit trail. My format is reasoned, not battle-tested.

---

## Tier 3 — If time allows

### Q8. LLM in the hot path?
> *"Would you keep the LLM out of the latency-sensitive path entirely, or is sub-2-second acceptable
> in your experience?"*

### Q9. Which is more defensible in a panel?
> *"Two options. One: safer build, better data, but helps ~1% of merchants — automating a finance
> workflow. Two: reaches ~99% of merchants and creates revenue instead of saving cost, but its market
> is genuinely early. Which reads better to a hiring panel in your experience?"*

**Why:** this is the one strategic question worth their time — because it's about **how engineers
judge candidates**, which is their expertise, not about Razorpay's business, which isn't.

### Q10. Only if they work in fintech
> *"What does a payments engineer immediately distrust when an outsider models their domain?"*

---

## Don't ask

- ❌ *"Which idea should I build?"* — they lack the research context, and it's your call
- ❌ *"How do I prepare for the interview?"* — generic, wastes the specialist
- ❌ *"What is Razorpay looking for?"* — unless they work there, they're guessing
- ❌ Anything already answered in `research/` — it signals you didn't do the work

---

## How to run it

**Send the architecture diagram and the README skeleton beforehand.** Senior engineers give far
better answers to concrete artefacts than to verbal descriptions. It also demonstrates you've
already done the thinking.

**Take the criticism literally, not personally.** If they say the abstention design is
over-engineered, that's the most valuable 30 seconds of the call.

**Ask at the end:** *"Would you be willing to look at the repo before I submit?"* A second review
from someone who's shipped agents is worth more than another day of building.

---

## The decisions that actually decide this

Separate from the conversation. Ranked by impact.

### 1. ⭐ Build the evaluation harness *before* the agent

The strongest single finding in this research: of eight competitor repos using the language of
measurement — "bounded", "auditable", "explainable" — **only one had any measurement behind it.**

Every track bar demands measured outcomes on a batch. If you build the agent first you will run out
of time and ship no numbers. If you build the harness first, it forces you to define what "correct"
means, which shapes the agent — and you always have a number to report.

**This is the decision most likely to determine whether you clear the bar.**

### 2. Lock the track in the first 48 hours

One shot, no edits after submission, ~11 days. Switching tracks on day six is fatal. Decide, commit,
don't revisit.

### 3. Choose your headline metric before writing code

The metric determines the architecture. *Proposal precision* builds a different system from *match
rate*. *Incremental recovery* requires a holdout designed in from the start — you cannot bolt it on
afterwards.

### 4. Reserve two of eleven days for the README and video

Not padding. Under a one-shot rule, this is the difference between good work and a good *submission*.

### 5. Deliberately engineer one failure to demo

Track 1 asks for *"one failure handled gracefully."* Track 4 asks for *"the exceptions it could not
resolve."* Most submissions will demo only success — and will be answering a question nobody asked.

---

# Part 2 — Razorpay-specific research questions

**He works at Razorpay on agentic AI.** That makes him the only person who can close gaps this
research could not — but it also means he has real confidentiality limits.

**The rule:** ask him to *confirm or correct your reading of public information*. Never ask him to
disclose internal information. Phrase everything as *"my understanding is X — is that right?"* That
lets him correct you without disclosing anything, and a correction is just as useful to you as a
disclosure.

Save these for a **second conversation**, after the technical one has gone well.

---

## The five that would change a decision

### ⭐ R1. Is the Agent Studio roster still the seven from the March launch?

> *"The March 2026 launch post lists seven prebuilt agents — Dispute Responder, Subscription
> Recovery, Abandoned Cart, RTO Shield, RTO Insights, Settlement Insights, Cashflow Forecaster. The
> live page is client-side rendered so I couldn't read it. Is that list still current, or has it
> grown?"*

**Why it matters most:** this is the largest unresolved gap in the entire research. Two of the five
project options rest on *"no Razorpay product exists for this."* If the roster has grown, both lose
their central claim.
**Fair to ask:** yes — it's public product information he can point you to.

### ⭐ R2. Is the 1% chargeback threshold applied as a flat ratio?

> *"The published guidance says merchant funds can be held above a 1% chargeback ratio. Modelling it,
> a merchant doing ~200 transactions a month at the global average dispute rate has roughly a 19%
> chance a year of crossing that by pure statistical noise. Is the published 1% a simplification of
> something more volume-aware internally?"*

**Why:** ⭐ **The entire volume-blind thesis rests on this single assumption**, and I flagged it as
the one most likely to be wrong. If they already volume-adjust, that project collapses.
**Fair to ask:** ⚠️ carefully. It edges toward risk internals. He may decline — **and a decline is
still informative.** Frame it as your modelling, not as a demand.

### R3. Does anything resolve settlement exceptions, or only display them?

> *"I can see Single View Recon consolidates settlement status, Smart Collect matches incoming
> transfers via virtual identifiers, and Source to Pay does 3-way matching on supplier invoices. Is
> there anything that actually *resolves* an unmatched settlement line — the MDR, GST-on-MDR, refund
> offset, cross-cycle chargeback case?"*

**Why:** the core claim of the top-ranked project. Also quietly demonstrates you surveyed the whole
product stack rather than one blog post.
**Fair to ask:** yes.

### ⭐ R4. The reaction test — merchant-side risk monitoring

> *"If a merchant-facing tool helped a merchant watch their own chargeback exposure and warned them
> before they approached the hold threshold — would that read as helpful, or as working around
> Razorpay's risk controls?"*

**Why:** ⭐ **His instinctive reaction *is* the answer.** This is the exact compliance ambiguity from
the review — Razorpay's terms assert risk management as their prerogative, but they also recommend
merchants self-monitor at 0.5%. If an engineer there flinches, don't build it. If he says "that's
just good hygiene," the objection dissolves.
**Fair to ask:** yes — it's a judgement question, not a disclosure.

### R5. Is agentic commerce demand real yet?

> *"Agentic payments are live with Zomato, Swiggy and Zepto. Is there meaningful buyer volume coming
> through that channel yet, or is it still pilot-scale? I'm weighing a project that assumes AI buyers
> become a discovery channel for small merchants."*

**Why:** the single biggest unknown behind the agent-readable catalog idea. No public data exists on
Indian AI-agent shopping volume.
**Fair to ask:** ⚠️ carefully — volumes may be confidential. He can answer directionally without
numbers.

---

## Worth asking if there's time

**R6 — Is Single View Recon gated behind Optimizer?**
If yes, merchants running two gateways *without* Optimizer get no consolidated view at all — and they
have the worst reconciliation pain. Would sharpen the problem statement considerably.

**R7 — Does Razorpay Capital reach a merchant doing ~₹12 lakh a year?**
Determines whether the working-capital idea is an open gap or already served.

**R8 — What can't be simulated in test mode?**
*"I've confirmed disputes can't be created via the test API. Is settlement data deep enough in test
mode to demo a batch reconciliation, or should I plan on synthetic data throughout?"*
Practical, entirely fair, and saves you a day of discovering it yourself.

**R9 — Is the MCP server the intended integration path for this kind of build?**
Confirms your architecture uses the route Razorpay actually wants people using.

**R10 — Administrative, if he happens to know:** is the deadline actually 5 September? Individual or
team? Is pre-existing code allowed? None of these is published anywhere.

---

## ❌ Do not ask

- **Anything about judging** — criteria, who judges, what wins. Puts him in an impossible position
  and taints the process for both of you.
- **Roadmap** — *"what are you building next?"* is a confidentiality problem, not a question.
- **Internal metrics** — real chargeback rates, freeze frequency, merchant distribution, revenue
  splits.
- **"Can you refer me?"** — the buildathon has **no resume screening**. A referral buys nothing your
  submission doesn't, and it converts a mentor into a gatekeeper.
- **Anything he'd have to check before answering.** If it needs internal lookup, it's the wrong
  question.

---

## How to use his answers

**A correction is worth more than a confirmation.** If he says *"actually, that roster has grown"* or
*"we don't apply that flat"*, you've saved yourself from building on a false premise — which is
exactly what this research has been trying to prevent at every stage.

**Update the files afterwards.** `razorpay-product-audit.md` for R1/R3/R6, `micro_merchant_thesis.md`
§8 for R2, `compliance_review.md` §3 for R4, `growth_thesis.md` §6 for R5.

**And if he flinches at R4, drop that project.** An engineer's instinctive reaction to
*"is this adversarial?"* is better evidence than any amount of my reasoning about their terms of
service.
