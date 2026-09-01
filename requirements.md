# requirements.md — Razorpay AI Buildathon 2026: What It Expects, and the Bar to Win

Compiled 2026-08-24. **Validated 2026-08-24** by an adversarial deep-research pass (106 agents,
3-vote refutation per claim) plus direct primary-source checks. Corrections from that pass are
marked **[v2]**. Every claim is graded:
**[A]** official Razorpay source · **[B]** primary external source · **[C]** high-quality secondary ·
**[D]** weak/indirect · **[E]** inference by this document.
Anything marked **CONSTRUCTED** is this document's own bar, not Razorpay's published rule.
Raw evidence lives in `research/phase0/`.

---

## 0. The single most important thing to understand

**This is not a hackathon. It is a hiring funnel with a build-based first round.** [A]

The prize is not money. It is a 6- or 12-month AI Builder Internship, ₹75,000/month, in-person in
Bangalore from September. [A] The form is titled *"Razorpay AI Builder Internship 2026"* and is
created inside Razorpay. [A]

That changes the optimisation target completely:

| A prize hackathon rewards | This program rewards |
|---|---|
| The best 3 projects | Every candidate who clears an absolute bar |
| Wow-factor demo | Evidence you can be trusted with production money flows |
| Team output | **Individual** output — the form has no team fields [A/E] |
| Judged once, forgotten | Judged, then **defended live in front of a panel** [A] |

The official process is four steps: *"pick a track, build something real, show your work (a public
repo, a 5 minute pitch video, the architecture), and if it has signal we call you in."* [A]
Shortlisted builders *"go straight to a panel. No aptitude test. No group discussion."* [A]

**Consequence:** the repo and video are not the deliverable — they are the *evidence* for a hiring
decision that gets stress-tested by a Razorpay engineer who owns this domain. Build accordingly.
Anything you cannot defend line-by-line is a liability, not an asset. [E]

---

## 1. Hard constraints (fail these and nothing else matters)

| Constraint | Value | Grade |
|---|---|---|
| Eligibility | Students only; graduation year must be **2027, 2028 or 2029** (form dropdown) | [A] |
| Location | In-person Bangalore, from September. Form asks availability Yes/No | [A] |
| Duration | Choose 6-month or 12-month internship | [A] |
| Track | Exactly **one** of 5, selected in a dropdown | [A] |
| Repo | Public GitHub URL | [A] |
| Video | "5-min Pitch Video Link" — **treat 5:00 as a hard ceiling** | [A] |
| Written | Project Name, "Project Objectives — What does it solve?", "Build Challenges & Technical Obstacles — What issues did you face while building, and how did you solve them?" | [A] |
| Finality | Checkbox: *"I confirm that this is my official final project submission. I understand that no further changes or edits can be made after submitting."* | [A] |
| Deadline | **5 September 2026** — reported consistently by ~6 outlets but **NOT published on razorpay.com/buildathon/, NOT in the form, NOT in the page's schema.org Event block.** Treat as a working assumption, verify independently. | [C/D] |

**[v2] Deadline, re-verified 3-0 by independent adversarial check.** A keyword audit of the full
55,250-byte page found *no* date string, no countdown and no "applications close" — the only two
temporal references are to the internship *start* ("from September"). The form has no deadline
either. **However**, §4.5 supplies strong circumstantial support: 293 competitor repos were created
in the five days to 24 Aug, a curve consistent with an imminent early-September cut-off. Plan for
5 September; do not cite it as Razorpay's published rule.

**Unpublished, do not assume:** team-size rules, judging weights, shortlist dates, which
test-mode APIs are provided, whether pre-existing code is allowed. [A — absence]

**The one-shot rule is the sharpest constraint.** No edits after submit means: freeze the repo, tag
a release, and make sure the README and video match the tagged commit exactly. A repo that has
moved on from the video is a credibility hit you cannot repair. [E, CONSTRUCTED]

---

## 2. What Razorpay actually published per track

Razorpay published **5 track mandates + 5 build specs + 5 "The bar" statements + 22 non-binding
"example directions"**. It did **not** publish discrete numbered problem statements — several blogs
misreport the example directions as such. [A]

| # | Track (exact form label) | Build spec (verbatim) | THE BAR (verbatim) |
|---|---|---|---|
| 1 | Track 1: AI Growth & Agentic Commerce | "Build an agent that grows revenue for a merchant on Razorpay test-mode APIs, or that makes a merchant transactable by an AI buyer end to end." | "Every money action explainable, bounded and gated. Show the audit trail and one failure handled gracefully." |
| 2 | Track 2: AI Risk Manager | "Build a working detector, verifier or auto-responder for one class of loss, with measured precision and recall on a held-out test set." | "Honest metrics including false-positive cost. **Strictly defense-only: anything offense-capable is disqualified.**" |
| 3 | Track 3: AI Revenue Recovery | "Build an agent that detects revenue at risk, determines the right intervention, and executes a bounded recovery workflow: from payment failures and checkout abandonment to overdue receivables." | "Don't just identify the problem. Show measured money recovered across a batch, with compliant escalation, stopping rules, and an audit trail." |
| 4 | Track 4: AI Finance Controller | "Build an agent that closes one finance-ops loop across a **50+ record batch of synthetic data**, reporting its match rate and the exceptions it could not resolve." | "Throughput plus measured accuracy plus an honest exception list. One cherry-picked match proves nothing." |
| 5 | Open Track | "Pick a real problem, use AI meaningfully, and show us something that works. Any domain, workflow, or user is fair game." | "Open doesn't mean easier. Show a real problem, a working product, meaningful use of AI, and evidence that it creates value. The same bar for execution, reliability, and depth applies here." |

### The five bars decoded into one sentence

Every bar is the same demand wearing different clothes: **run your system over a batch, publish the
number, publish what it got wrong, and prove every action it took was bounded and traceable.**
Four of five bars explicitly name a quantitative artefact (precision/recall + FP cost; money
recovered across a batch; match rate + exception list; audit trail). [A → E]

**The load-bearing words, in order of how often candidates ignore them:**

1. **"across a batch"** / "50+ records" / "held-out test set" — a single happy-path demo scores zero.
2. **"honest"** / "exceptions it could not resolve" / "false-positive cost" — you must publish your
   own failures. A submission with no failure analysis reads as one that was never evaluated.
3. **"bounded and gated"** / "stopping rules" / "compliant escalation" — autonomy with brakes.
4. **"audit trail"** — every money action must be reconstructible after the fact.
5. **"one failure handled gracefully"** — deliberately demo a failure.

---

## 3. The novelty floor: what Razorpay already ships

This is the section most applicants will skip, and it is where most submissions die. **Razorpay
already sells or pilots most of the "example directions."** Building one naively means demoing a
worse version of their own product to the team that built it. [A → E]

### Razorpay Agent Studio — 7 prebuilt agents, already in beta/early access [A]

Built on **Anthropic's Claude Agent SDK**. [A] **[v2]** Launched **12 March 2026 at FTX'26,
Bengaluru**, as "the world's first AI-native Agent Studio for payments." Primary sources:
`razorpay.com/blog/agent-studio-ai-agents-by-razorpay/` and the FTX'26 newsroom release.

**[v2] Three corrections:**
1. The launch blog shows **8 tiles but 7 distinct agents** — *Abandoned Cart Conversion* appears
   twice, once "Powered by SuperU" and once "Powered by Nugget by Zomato". Razorpay is shipping
   **partner-powered agents**, which means a strong external agent is a business-development target
   for them, not just a competitor. That is a live route into the company.
2. The FTX'26 press release names only **four** of the seven; the 7-agent roster comes from the blog
   and product page.
3. The press release calls the agents **"production-ready"** while the product page still says
   **"Get early access"** and badges the custom builder **Beta** (checked 2026-08-24). Marketing is
   ahead of availability — so the gap you can fill is real, but assume the roadmap is not.

| Existing Agent Studio agent (verbatim) | Collides with buildathon example direction |
|---|---|
| **Dispute Responder** — "Auto-responds to chargebacks with optimized evidence to maximize dispute win rates" | T2 "Chargeback evidence responder" |
| **Subscription Recovery** — "Analyzes failed subscription payments, apply smarter retry logic, and trigger targeted customer nudges" | T3 "Failed-subscription recovery", "Mandate retry sequencer" |
| **Abandoned Cart Conversion** — "Identifies abandoned carts and re-engage customers via WhatsApp or email" | T3 "Checkout drop-off recovery" |
| **RTO Shield** — "Detects high-risk COD orders before dispatch using LLM address validation and bad pincode intelligence" | T2 "Return-risk scorer" |
| **RTO Insights** — "Analyzes RTO patterns across pincodes, products, and customers" | T2 "Return-risk scorer" |
| **Settlement Insights** — "Sends a daily settlement summary via WhatsApp" | T4 "Settlement Q&A agent" |
| **Cashflow Forecaster** — "Predicts cash position 3–7 days ahead with alerts for payroll risk" | T4 "Forward cash forecaster" |

### Razorpay Agentic Payments — already live with named partners [A]

- **Agentic UPI payments on Claude** with Zepto, Swiggy, Zomato (with NPCI, Feb 2026) [A/C]
- **In-app agentic checkout** piloted with Vodafone [A]
- **Voice-AI payments** piloted with Gnani.ai and SuperU [A]
- **International payments with Replit** — "idea → app → revenue from day one" [A]

**[v2] Correction and a gift.** The Claude pilot was announced at the **India AI Impact Summit,
New Delhi, 20 February 2026**, and it does **not** run on the unlaunched UAP. It runs on NPCI's
already-live **UPI Reserve Pay**: a **one-time, consent-based authorisation with a per-merchant
spending limit**, no repeated PIN prompts, full visibility, and **instant revocation** — reportedly
under a **₹10,000 block cap**. It is a **closed pilot**, not GA.

> **This is the single most copyable artefact in the whole program.** Razorpay has published its own
> answer to "how should an agent be allowed to touch money": *one-time scoped consent · per-merchant
> cap · no per-transaction re-auth · full visibility · instant revoke.* Build your bounded-autonomy
> layer to that exact shape and name the parallel in your README. You are then not inventing a
> safety model — you are implementing theirs. [A → E, CONSTRUCTED]

**[v2] Sourcing caveat.** The Vodafone / Gnani.ai / SuperU / Replit pilots come from Razorpay's own
summit page (`razorpay.com/m/india-ai-impact-summit-2026-razorpay-launches/`, captured verbatim in
`research/phase0/`), so they are [A]. The independent pass could not re-source them and a *different*
partner list (adding PVR Inox, Bluestone, Honasa) failed verification 0-3. Two separate product
lines are being conflated in public reporting: **agentic UPI on Claude** ≠ **in-app agentic
commerce**. Cite only the summit page, and do not merge the merchant lists.

→ "Conversational in-app checkout" and "Hinglish voice recovery" are **not blue ocean**. They are
demos of things Razorpay has already piloted with real partners. You must beat the pilot on a
specific axis, not restage it. [E]

### Razorpay Vulcan — their own payments foundation model [A]

"India's first AI Payments Foundation Model", trained on proprietary data from *"almost 4 billion
customer-to-merchant payments every year"*, targeting **routing, fraud detection, and checkout
conversion**. [A]

**[v2] Corrections, and the timing point that matters most in this document.** Vulcan was announced
**18 August 2026 — six days before this was compiled, and days before applications close.** It was
built **with NVIDIA and AWS**. The "4 billion payments" figure is Razorpay's *annual C2M volume*,
feeding a corpus of **~3 trillion data points at ~3,000 signals per transaction**; reported results
are an **8–10% payment success-rate lift across 1.5M+ transactions and 50,000+ merchants**. It has
its own product page at `razorpay.com/foundation-model/`.

→ Do not propose to out-model Vulcan on raw fraud detection or routing from public data. You will
lose on data by ~4 billion transactions per year. Compete on **workflow, reasoning, verification
and action** — the parts a foundation model does not do. [E]

→ **[v2] And read the calendar.** Vulcan (18 Aug), Agent Studio (12 Mar), agentic UPI on Claude
(20 Feb) — Razorpay shipped its entire AI stack in the six months before this buildathon, and is
hiring builders *immediately after*. The tracks are not hypothetical exercises; they are the
roadmap. A project that reads as the next thing on that roadmap is the one that gets called. [E]

### Other named Razorpay AI systems [A]

"Slash, Call-E, AI-led marketing campaigns, Agentic Platform, Agentic Payments, and Agent Studio."

### The tool you should be using

**Razorpay ships an official MCP server** (`razorpay/razorpay-mcp-server`) with **~45 tools**, a
hosted remote option, and test-mode key support (`rzp_test_...`). [A] Tools cover payments, payment
links, orders, refunds, QR codes, settlements including `fetch_settlement_recon_details`, instant
settlements, payouts, tokens, and registration links. [A]

**[v2]** Razorpay's docs headline **"35+ tools"**; the repo README table contains **exactly 45**
uniquely named tools (`main`, 2026-08-24). Say "45 in the repo" or "35+ per the docs" — never
attribute 45 to Razorpay. The server **auto-detects test vs live from the key prefix**
(`rzp_test_` / `rzp_live_`), configured via `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` or
`--key-*` flags. A few tools (e.g. `create_refund`) are **not available on the hosted remote
server** — run it locally if your loop needs those.

→ Using their own MCP server against test-mode APIs is the cheapest possible proof that you can
work *inside* Razorpay's stack rather than beside it. Track 1's spec names "Razorpay test-mode APIs"
explicitly. [A → E, CONSTRUCTED recommendation]

> **[v2] A refutation I checked and rejected.** The deep-research pass claimed 0-3 that the official
> page does *not* scope Track 1 to "Razorpay test-mode APIs". That is wrong. The raw HTML I captured
> contains verbatim: *"Build an agent that grows revenue for a merchant on Razorpay test-mode APIs,
> or that makes a merchant transactable by an AI buyer end to end."* The verifiers most likely
> fetched a JS-rendered view that dropped the copy. **The phrase is on the page and the constraint
> is real for Track 1.** Its one useful corollary still stands, though: nothing on the page forbids
> synthetic or public data, and for Tracks 2–4 you will *need* it — see §3.6.

### Rule derived from this section (CONSTRUCTED)

> **The Delta Rule.** Your README must contain a section titled "What Razorpay already has, and what
> this adds." Name the closest existing Razorpay product, state its published capability, and state
> your measurable delta. If you cannot name a delta, change your project.

**Example directions with the least collision with shipped Razorpay products** [E]:
agent-readable catalog (T1), campaign orchestrator (T1), abuse-ring sentinel (T2), fraud-spike
detector as a *merchant-facing* tool (T2), B2B receivables chaser (T3), promise-to-pay tracker (T3),
payment degradation → root cause → recovery (T3), multi-source reconciliation (T4), tax-line matcher
(T4). Collision is lowest where the work is **cross-source, multi-step and exception-heavy** —
exactly where agents beat both rules engines and single models.

---

## 3.6 [v2] Build substrate: what you can actually simulate, and the taxonomy to reason over

This section did not exist in v1 and is the most execution-critical addition. **Check it before you
choose a track** — it decides what is buildable in the time left.

### What Razorpay test mode can and cannot do [A]

| Capability | Status | Detail |
|---|---|---|
| Card payment success/failure | ✅ | Mock bank page with Success/Failure buttons |
| Trigger success vs failure via OTP | ✅ | Random OTP of **4–10 digits succeeds**; **under 4 digits fails** |
| UPI success/failure | ✅ | Test VPAs **`success@razorpay`** and **`failure@razorpay`** |
| Webhooks | ✅ | Test events fire on test-mode transactions; payloads verifiable |
| Refunds, orders, payment links, QR | ✅ | Full CRUD via API / MCP |
| Settlements & recon report | ⚠️ | Endpoints exist (`fetch_settlement_recon_details`) but test-mode data is thin |
| **Disputes / chargebacks** | ❌ | **Cannot be created via the test API** — disputes are raised by banks and card networks, not merchants |
| UPI payment cancellation | ⚠️ | **In test mode, cancellation returns SUCCESS.** A real trap: a naive cancellation-handling path will silently pass in test and break in live. Say this in your README — it is exactly the kind of detail that reads as someone who actually built it |
| Card tokens for subscriptions | ⚠️ | Valid **3 days only**, so subsequent-debit testing must happen inside that window |

**Consequences for track choice:**

- **Track 2 chargeback work cannot be demonstrated end-to-end on Razorpay test data.** Six of the
  competitor repos in §4.5 are chargeback projects; most will hit this wall. If you take it, commit
  to a synthetic dispute corpus *and say why* — that is a strength, not an excuse.
- **Track 3 and Track 4 need synthetic ledgers regardless.** Design the generator as a first-class,
  seeded, committed artefact. It is also your only route to a batch big enough for §5.2.
- **Track 1 is the one track that runs natively on test-mode APIs** end to end.

### The error-code taxonomy — the best ready-made substrate Razorpay publishes [A]

The strongest single finding of the validation pass. Razorpay publishes a **structured,
method-specific, machine-readable failure taxonomy**:

- `razorpay.com/docs/errors/payments/list/` — hub, "top error codes… along with their reasons,
  descriptions and steps for resolution"
- `razorpay.com/docs/errors/payments/upi/` — **10 enumerated UPI codes**: `bank_technical_error`,
  `credit_failed`, `gateway_technical_error`, `insufficient_funds`, `invalid_vpa`,
  `payment_cancelled`, `payment_collect_request_expired`, `payment_declined`, `payment_timed_out`,
  `vpa_resolution_failed` — each with Description and Next Steps
- `razorpay.com/docs/errors/payments/cards/` — card-specific codes
- `razorpay.com/docs/errors/payments/payment-methods-error-parameters/` — the error **object schema**
  (`code`, `description`, `field`, `source`, `step`, `reason`, `metadata`) with **enumerated
  per-method `source` values**, plus a **downloadable spreadsheet of every reason value with a
  next-best-action**

> **Why this decides Track 3.** The buildathon's hint "payment degradation → root cause → recovery
> action" needs a root-cause ontology. Razorpay has already published one — including the
> `source` field that attributes failure to bank / gateway / customer / issuer, which is precisely
> the discrimination a root-cause agent must make, and a next-best-action column that gives you a
> **labelled ground truth to evaluate against**. Build your agent's reasoning over *their* taxonomy
> and your metrics become directly legible to a Razorpay engineer. Most competitors will invent
> their own failure categories and lose that legibility. [A → E]

### Regulatory bounds worth designing to [C]

NPCI's **Unified Agent Protocol (UAP)** — the agent registration/verification layer for agentic UPI
— **has not launched and awaits RBI approval**, and surfaced publicly only in July 2026, five months
*after* the Claude pilot. That is why the pilot runs on **UPI Reserve Pay** instead. Build to the
Reserve Pay consent model that exists (§3, one-time scoped consent + per-merchant cap + instant
revoke); reference UAP as the direction of travel, never as something you integrated.

---

## 4. Neighbouring programs: what actually wins, and what transfers

| Program | Scale / reach | How winners were chosen | What transfers to Razorpay |
|---|---|---|---|
| **Razorpay FTX Hackathon** (2020/21, same company) [B] | ₹2L / ₹1L / ₹50k, teams of 2–5, judges incl. Kailash Nadh (CTO, Zerodha) | *"The number of projects to be awarded and amount to be given will be decided by the judges based on the **depth and quality** of the projects."* All code written during the event. | Razorpay's own historic language is **depth and quality**, and they reserve the right to award *nobody*. There is no participation floor. |
| **HackRx / Bajaj Finserv** (Indian fintech, students) [C] | National, engineering students | **Live leaderboard from daily code submissions** against a defined task, then a finale judged on *"innovation, technical execution, scalability, user experience, and overall presentation"* | The Indian fintech norm is now **objective scoring on a held-out task first, subjective judging second**. Razorpay's bars ("held-out test set", "match rate") are the self-service version of the same thing. Build your own leaderboard, because they didn't give you one. |
| **UC Berkeley AI Hackathon 2026** (world's largest AI hackathon) [C] | **1,099 participants**, $96,700+ in prizes | Four equally-weighted axes: **Application** (real-world feasibility), **Functionality/Quality** (bug-free, appealing), **Creativity**, **Technical Complexity**. *"Previous projects are not allowed."* | "Bug-free execution" is a scored axis at the top of the field. A crashing demo is not a minor deduction anywhere in this ecosystem. |
| **Solo.io MCP & AI Agents Hackathon 2026** [C] | Multi-track, agent-native | Judges valued **practical utility and real-world applicability**; winners shipped working systems serving enterprise needs (autonomously detect/analyse/resolve infrastructure waste; an agent-governance scoring model; 9 substantial upstream PRs) | In agent hackathons, winners ship **closed loops** (detect → analyse → resolve) and **governance/observability**, not chat UIs. Razorpay's "bounded, gated, audit trail" is the same instinct. |
| **GitLab AI Hackathon 2026** [C] | Company-run | Scored on technical work, design, potential impact, idea quality; bonus for **novel use cases** | Novelty is scored explicitly even at company hackathons — reinforces the Delta Rule. |
| **Sarvam Epoch Buildathon** (GrowthX, hosted at Razorpay's Koramangala office, Razorpay-supported) [C] | ~200 curated builders, 8 hours, ₹10L pool | Top 10 present at the Epoch frontier-AI conference | The Bangalore AI-builder pool Razorpay recruits from is small, curated and already shipping agents. Assume your competition is that calibre, not a college-project pool. |
| **2026 agent-hackathon playbook consensus** [C] | — | *"a shared eval harness teams build against from day one, with a public rubric"*; scoring **trace logs** with the criteria enterprise AI teams use in production | The strongest transferable signal: **ship the eval harness and the traces with the project.** |

**[v2] Reach is no longer unknown — see §4.5, which measures it directly (300 public repos, 293
created in five days).** Razorpay still publishes no applicant count [A — absence], but the field is
now observable. What is knowable: ₹75k/month + no-resume-screen + a public
landing page is a high-virality combination; the tracks are narrow; and the four non-open tracks
each demand a quantitative artefact most applicants will not produce. **The realistic competitive
strategy is not to out-idea the field — it is to be in the small minority that actually publishes
measured results on a batch.** [E]

---

## 4.5 [v2] The actual competitive field — measured, not guessed

v1 said reach was unknown. It no longer is. A GitHub sweep on 2026-08-24 found **300 unique public
repos** self-identifying with this buildathon. [B]

**Creation curve — this is a stampede, and it is peaking now:**

| Date | New repos |
|---|---|
| ≤ 2026-08-19 | 7 (total, all time) |
| 2026-08-20 | 30 |
| 2026-08-21 | 63 |
| 2026-08-22 | **93** |
| 2026-08-23 | 79 |
| 2026-08-24 | 28 (partial day) |

**293 of 300 repos were created in five days.** Independent support for an early-September deadline,
and proof you are not early.

**Track crowding — from keywords across all 300 descriptions:**

| Signal | Repos | Read |
|---|---|---|
| recovery | **88** | Track 3 is by far the most crowded — nearly 1 in 3 |
| commerce / agentic | 57 / 43 | Track 1 heavily contested |
| risk / fraud | 46 / 18 | Track 2 crowded |
| reconciliation / settlement | **24 / 9** | **Track 4 is the emptiest by a factor of ~3–4** |
| chargeback / dispute | 6 / 2 | Thin — and §3.6 explains why (can't be simulated) |
| invoice / receivables / RTO | 4 / 3 / 1 | Nearly untouched |

**The bar vocabulary is already commoditised.** "bounded" appears in **36** descriptions, "audit"
**35**, "explainable" **18**, "gated" **12**. Everyone has read the same "The bar" sentences and is
repeating them back. **Claiming boundedness is now worth zero. Only demonstrating it scores.**

**Quality sample — the decisive number.** Of 8 repos whose descriptions claim the strongest bar
vocabulary, README evidence for real evaluation:

| Evidence present | Repos |
|---|---|
| Full stack: metrics + held-out + baseline + eval dir + exception/failure analysis | **1 of 8** (`Shikari-ai/recoup` — precision, recall, F1, AUC, held-out, baseline, `eval/`) |
| Partial (some metrics or a baseline, no held-out eval) | 3 of 8 |
| Thin or empty (≤ 9 KB README, no metrics at all) | 4 of 8 |

**Strategic conclusions [E]:**

1. **The §6b thesis survives contact with the field, and is sharpened.** ~7 in 8 of even the
   *self-selected serious* repos have no held-out evaluation. Measurement remains the differentiator.
2. **But a real top decile exists.** Beating "most submissions" is not enough; you are competing
   with a handful of genuinely rigorous builds. The §5.2 floors are the right target, not a stretch.
3. **Track 4 is the value play** — a third to a quarter of the density of Track 3, on a track whose
   bar (match rate + throughput + honest exception list) is the *easiest to satisfy objectively* and
   the one where synthetic data is explicitly sanctioned by Razorpay's own "50+ record batch"
   wording. Highest score-per-unit-effort of the five.
4. **Track 3 needs a sharp angle to survive.** 88 repos, and Agent Studio already ships Subscription
   Recovery and Abandoned Cart Conversion. If you stay in Track 3, go where the crowd isn't:
   B2B receivables, promise-to-pay, mandate retry sequencing — 3–6 repos each, not 88.
5. **Name your differentiator in the repo description.** Judges will skim hundreds of these. A
   description reading "bounded, auditable AI agent" is now indistinguishable from 35 others. A
   description with **a number in it** is not.

---

## 5. The bar to win — 12 non-negotiables

CONSTRUCTED from §2 (Razorpay's own bars, [A]) + §4 (what wins in neighbouring programs, [C]).
A submission that misses any of the first five is not competitive regardless of idea quality.
**[v2]** Items 10 and 11 were added after measuring the competitive field (§4.5): with 36 repos already
claiming "bounded" and 35 claiming "audit", generic safety language no longer differentiates —
matching Razorpay's *own* published consent model and *own* published taxonomy does.

1. **One track, one loop, closed end to end.** Detect → decide → act → verify → report. Not a
   dashboard, not a chatbot over docs. Winners at agent hackathons ship closed loops. [C→E]

2. **A batch run, not a demo.** Minimum floors (CONSTRUCTED, above Razorpay's stated minimum):
   - **Track 2:** held-out test set, **≥500 labelled records**; report precision, recall, **and the
     rupee cost of a false positive** — Razorpay names FP cost explicitly. [A]
   - **Track 3:** **≥200 at-risk cases**; report ₹ recovered vs ₹ at risk, recovery rate, and cost
     per recovery. "Measured money recovered across a batch" is the literal wording. [A]
   - **Track 4:** Razorpay's floor is 50+ records — **treat 50 as the disqualification line and ship
     500+**; report match rate, throughput (records/min), and the full exception list.
   - **Track 1:** ≥50 simulated buyer sessions or catalog items; report conversion or
     transactability rate end-to-end.
   - **Open:** pick the metric a Razorpay PM would care about, and hold yourself to the same floors.

3. **A published, reproducible eval harness.** One command (`make eval`) regenerates every number in
   your README and video from a committed dataset with a fixed seed. Numbers a judge cannot
   reproduce in one command are treated as claims, not evidence. [C→E]

4. **An honest failure section.** Exceptions you could not resolve, failure modes, FP cost, and the
   cases where a human must take over. Razorpay asks for this in three of five bars. [A]
   Publishing your own weaknesses is the highest-leverage credibility move in this program.

5. **Bounded autonomy with a visible audit trail.** Every money-touching action must be explainable
   (why), bounded (limits/caps), gated (approval or policy check), reversible or idempotent, and
   logged as a structured, replayable trace. Ship `traces/` in the repo. [A]

6. **Real agentic necessity, not AI-washing.** State plainly why a rules engine or a single
   classifier is *insufficient*: multi-step decisions, tool use, cross-source reasoning, dynamic
   exception handling. If a `CASE WHEN` would do it, you have an ML/rules project wearing an agent
   costume — and the panel will find that in 90 seconds. [E, CONSTRUCTED]

7. **Built inside Razorpay's stack.** Razorpay test-mode APIs and/or the official MCP server
   (~45 tools), with realistic synthetic data shaped like real Razorpay objects (payment ids, order
   ids, settlement recon reports, UPI/mandate failure codes). Fake-looking data undermines every
   number you report. [A→E]

8. **The Delta Rule satisfied.** Name the nearest existing Razorpay product (Agent Studio agent,
   Agentic Payments pilot, Vulcan) and your measurable delta. [E, CONSTRUCTED]

9. **Deliberate failure handling on camera.** Track 1's bar literally asks for *"one failure handled
   gracefully."* Show the agent hitting a wall — API error, ambiguous match, policy block,
   low-confidence case — and degrading correctly. Do this in **every** track. [A→E]

10. **[v2] Bounded to Razorpay's own consent model.** Don't invent a safety scheme. Implement the
    shape Razorpay and NPCI already shipped on UPI Reserve Pay — one-time scoped consent, a
    per-merchant cap, no per-transaction re-auth, full visibility, instant revoke — and name that
    parallel explicitly. A panel recognises its own design immediately. [A→E, CONSTRUCTED]

11. **[v2] Legible against Razorpay's published taxonomy.** Where Razorpay has published an
    ontology — the UPI/card error codes, the `source` attribution field, the reason→next-best-action
    spreadsheet (§3.6) — reason over *theirs*, not one you invented. It converts your output into
    something a Razorpay engineer can grade at a glance, and it hands you labelled ground truth.

12. **Defensible under adversarial questioning.** Assume the panel asks: *"What's your false-positive
    rate at the threshold you shipped?"* · *"Show me the trace for case #47."* · *"Why not just use
    Agent Studio's Dispute Responder?"* · *"What breaks at 10x volume?"* · *"Which number in your
    README are you least confident about?"* Prepare all five. The last one rewards honesty and
    punishes rehearsed answers. [E, CONSTRUCTED]

---

## 6. The judging criteria — as published, and as it will actually be scored

### 6a. What Razorpay actually published [A]

There is **no public rubric and no weights.** The complete official evaluation surface is:
(i) the five "The bar" statements; (ii) *"if it has signal we call you in"*; (iii) shortlist → panel.
Historic Razorpay hackathon wording: judged on *"the depth and quality of the projects."* [B]

### 6b. Strict scoring rubric — CONSTRUCTED

Reverse-engineered from Razorpay's bars [A], their historic criteria [B], the hiring context [A],
and the criteria used by comparable 2026 agent hackathons [C]. **This is our bar, not Razorpay's.**
Score yourself honestly; anything under 75 is not worth submitting under a one-shot rule.

**Stage 0 — Kill switches (any one = zero, no partial credit)**

- [ ] Not a student graduating 2027/2028/2029, or unavailable in-person in Bangalore from September
- [ ] Repo not public, or video over 5:00, or links broken at submission time
- [ ] **Track 2 only:** anything offense-capable — *"Strictly defense-only: anything offense-capable is disqualified"* [A]
- [ ] Demo crashes, or the flow shown in the video cannot be reproduced from the repo
- [ ] Numbers in the video/README not reproducible from committed code + data
- [ ] Handles real credentials, real PII, or live-mode money movement
- [ ] A rebuild of an existing Agent Studio agent with no stated delta
- [ ] A single cherry-picked success case as the only evidence — *"One cherry-picked match proves nothing"* [A]

**Stage 1 — Scored (100 points)**

| # | Criterion | Wt | 0–40% | 60% | 85% | 100% |
|---|---|---|---|---|---|---|
| 1 | **Measured outcome on a batch** | 25 | Demo only | Small batch, one metric | Meets §5.2 floors, metric + baseline | Floors exceeded; baseline + ablation, cost-per-action, seed-stable reruns |
| 2 | **Bounded autonomy & audit trail** | 20 | Free-running LLM calls | Some logging | Structured replayable traces, caps, approval gate | Full policy layer: caps, stopping rules, idempotency, human-in-loop escalation, `traces/` shipped |
| 3 | **Honest evaluation & failure analysis** | 15 | None | Mentions limitations | Exception list + FP cost + failure taxonomy | Above, plus threshold / precision-recall tradeoff analysis and "what I'd need to trust this in prod" |
| 4 | **Novelty vs Razorpay's existing stack (Delta Rule)** | 15 | Rebuild of a shipped agent | Adjacent to a shipped agent | Clear delta, named and measured | Solves something Razorpay's stack visibly cannot yet do, and shows why |
| 5 | **Agentic necessity (anti-AI-washing)** | 10 | LLM wrapper | LLM + tools, linear | Multi-step planning, tool use, exception handling justified | Genuinely needs reasoning / multi-agent, justified against a rules-engine baseline you actually ran |
| 6 | **Engineering quality & Razorpay-stack fit** | 10 | Notebook | Runs locally with effort | One-command setup, tests, test-mode APIs / MCP | Above, plus realistic Razorpay-shaped data, error handling, latency reported |
| 7 | **Communication: 5-min video + architecture** | 5 | Slides only, over time | Demo but rambling | Tight demo, architecture explained, numbers on screen | Under 5:00, live batch run, failure shown on camera, architecture defensible |
| 8 | **Problem truth (does a real merchant lose money here?)** | 10 | Invented problem | Plausible | Grounded in a documented Razorpay/merchant pain | Grounded, plus impact math at Razorpay's scale |

**Interpretation:** ≥85 competitive · 75–84 needs one more evidence pass · <75 do not submit yet.

**Weighting logic:** criteria 1 + 2 + 3 = **60 of 100 points** on measurement, control and honesty.
That is deliberate. Razorpay's own five bars spend almost all their words there, and it is the axis
where most submissions in every comparable program fail. [A→E]

---

## 7. Deliverable specification

### 7a. Repo (public, tagged, frozen at submit)

```
README.md                 <- the whole argument, see 7b
ARCHITECTURE.md           <- diagram + components + failure-mode table + why-an-agent justification
DELTA.md                  <- "What Razorpay already has, and what this adds"
data/                     <- committed synthetic dataset + generator + fixed seed
eval/                     <- harness; one command reproduces every number
  results/                <- metrics.json, confusion matrix, exceptions.csv
traces/                   <- structured replayable traces of real runs, including failures
src/
tests/
Makefile                  <- make setup / make demo / make eval
```

### 7b. README contract (in this order)

1. One-sentence problem, in money terms, for a named merchant persona
2. The headline number, with batch size and date (e.g. "₹X of ₹Y at risk recovered across 200 cases")
3. 60-second quickstart a judge can actually run
4. Architecture diagram
5. **Evaluation** — method, dataset, held-out split, metrics table, baseline comparison
6. **Where it fails** — exception list, FP cost, failure taxonomy, human-escalation rules
7. **Safety & bounds** — caps, gates, stopping rules, idempotency, audit-trail format
8. **Delta** — nearest Razorpay product, its capability, your measured delta
9. What you'd build next with four more weeks

### 7c. The 5-minute video (hard ceiling; budget it)

| Time | Beat |
|---|---|
| 0:00–0:20 | The money problem, in one sentence, with a number |
| 0:20–0:50 | What the agent does — one clean end-to-end loop |
| 0:50–2:30 | **Live batch run.** Real terminal, real records, metrics appearing on screen |
| 2:30–3:15 | **A failure, on camera**, and the graceful degradation |
| 3:15–4:00 | Audit-trail / trace walkthrough of one money action |
| 4:00–4:35 | Architecture, and why this needs an agent rather than a rules engine |
| 4:35–5:00 | Honest limitations, the delta vs Razorpay's stack, what's next |

**Never:** open with a slide deck, spend a minute on the problem, show a mocked UI, or run out of
time before the metrics. Half the field will do all four.

### 7d. Form answers (they are read)

- *Project Objectives — What does it solve?* → problem + persona + the headline measured number.
- *Build Challenges & Technical Obstacles* → **this is the anti-vibe-coding question.** Name two
  specific technical problems, the diagnosis, and the fix. Non-obvious, honest and specific beats
  polished. This field is where a panel decides whether you built it or prompted it. [E]

---

## 8. Automatic credibility killers

1. A chatbot over documentation.
2. A dashboard where no agent takes an action.
3. Generic fraud detection on a Kaggle credit-card dataset.
4. Numbers with no dataset behind them.
5. "Improves user experience" as the stated outcome.
6. An architecture diagram with a box labelled "AI".
7. Any agent that can move money without a cap and a gate.
8. Rebuilding Dispute Responder, Subscription Recovery, Abandoned Cart Conversion, RTO Shield,
   Settlement Insights or Cashflow Forecaster without a stated delta.
9. Track 2 work that could be repurposed offensively. [A]
10. A repo whose last commit is after the video was recorded.

---

## 9. Pre-submit checklist

- [ ] Clean clone → `make setup && make eval` reproduces every README number
- [ ] Batch size meets the §5.2 floor for my track; the held-out split is real
- [ ] `exceptions.csv` exists, is non-empty, and I can explain every row
- [ ] Every money action has a cap, a gate, and a trace entry
- [ ] Track 2: nothing offense-capable, stated explicitly in the README
- [ ] `DELTA.md` names the closest Razorpay product and a measured delta
- [ ] Video ≤ 5:00, shows a live batch run and a failure
- [ ] Repo tagged; video and README describe that exact tag
- [ ] I can answer: FP rate at shipped threshold · trace for a specific case · why not Agent Studio ·
      what breaks at 10x · which number I trust least
- [ ] Deadline verified independently (5 Sep 2026 is unconfirmed by Razorpay)
- [ ] **[v2]** My repo *description* contains a number, not just "bounded, auditable AI agent"
      (36 other repos already say that)
- [ ] **[v2]** My bounded-autonomy layer mirrors UPI Reserve Pay's consent model, and says so
- [ ] **[v2]** Where Razorpay publishes a taxonomy (UPI/card error codes, `source`, reason →
      next-best-action), I reason over theirs rather than one I invented
- [ ] **[v2]** I know which of my flows *cannot* be simulated in test mode, and my README says so

---

## 10. Validation of this document

**Fact/inference split:** §1, §2, §3 are [A] with verbatim quotes. §4 is [B/C], attributed per row.
§5, §6b, §7, §8, §9 are **CONSTRUCTED** — reasoned bars, explicitly not Razorpay's published rules.

**Evidence quality:** A: 21 claims · B: 2 · C: 7 · D: 1 (the deadline) · E: 12 (all labelled).

**Known gaps:** applicant volume, judging weights, team rules, pre-existing-code policy, which
test-mode APIs are provisioned, and whether the panel sees the repo before or after shortlisting.

**Contradictions resolved:** "Razorpay AI for Good Hackathon 2026" (hackortech.in, ₹1.2Cr, deadline
2026-08-20) contradicts the official program on every attribute, has no organizer URL, and
self-labels as auto-aggregated — excluded as not a Razorpay event. Secondary-source track names
("Risk & Collections", "Finance Operations") are wrong; the form dropdown labels are authoritative.

**Strongest claim in this document:** the winning bar is measurement + bounded autonomy + honesty,
not idea novelty. Four of five official bars name a quantitative artefact; Razorpay's historic
hackathon language is "depth and quality"; and the 2026 agent-hackathon consensus is
eval-harness-first.

**Weakest claim:** the §5.2 batch-size floors are constructed, not published. Razorpay states only
"50+ records" (Track 4) and "held-out test set" (Track 2). Treat the higher floors as competitive
positioning, not as rules.

**Confidence: 9/10** on what the program expects (two agreeing official artefacts).
**[v2] 8/10** on the winning threshold — raised from 7 because the competitive field in §4.5 is now
measured rather than guessed, and it independently corroborates the §6b thesis (7 of 8 serious repos
have no held-out evaluation). Still not 9: no rubric and no past cohort exist to calibrate against.

### [v2] What the adversarial validation pass changed

**Confirmed unchanged (3-0 votes):** no published rubric or weights; Agent Studio built on Claude
Agent SDK and still gated behind early access; Vulcan as the named foundation model; MCP test-mode
key handling; the deadline's absence from every official surface; the individual-vs-team question
being genuinely unstated by Razorpay.

**Corrected:** Agent Studio = 8 tiles / 7 distinct agents, two of them partner-powered (SuperU,
Nugget by Zomato), launched 12 Mar 2026 at FTX'26, with a "production-ready" press release
contradicting the "early access" product page · agentic UPI runs on **UPI Reserve Pay**, not UAP,
as a closed pilot with a ₹10,000 block cap · Vulcan was built with NVIDIA and AWS, launched
18 Aug 2026, ~3tn data points / ~3,000 signals per transaction, 8–10% success lift over 1.5M+
transactions and 50,000+ merchants · MCP is "35+" per docs but exactly 45 in the repo, with some
tools unavailable on the hosted server.

**Added:** §3.6 (test-mode limits + the error-code taxonomy) and §4.5 (the measured field) —
neither existed in v1, and both change track selection.

**One finding rejected.** The pass voted 0-3 that the official page does not scope Track 1 to
"Razorpay test-mode APIs". I checked the raw HTML I captured myself; the phrase is present verbatim.
The verifiers were wrong, most likely from a JS-rendered fetch that dropped the copy. Recorded here
because a validation pass that is never itself validated is just a louder claim.

**Still unfilled, and honestly so:** public dataset options with licences (Gap C), 2026 statements
by Razorpay leaders on what constitutes "signal" (Gap E), Razorpay/NPCI/RBI metrics on success
rates, RTO and DSO (Gap F), 2026 agent-evaluation and audit-trail practice under Indian regulation
(Gap G), and any account of past winners or AI Builder interns (Gap H). Nothing survived
verification on these. They are gaps, not silence to be filled with plausible text.

### Sources

razorpay.com/buildathon · the official application form (forms.gle/d9r2gvxp8cmoZhon9) ·
razorpay.com/ai-builders · razorpay.com/agent-studio ·
razorpay.com/m/india-ai-impact-summit-2026-razorpay-launches ·
razorpay.com/blog/one-foundation-model-built-for-indias-payments-ecosystem ·
github.com/razorpay/razorpay-mcp-server · github.com/razorpay/ftx-hackathon/wiki ·
ftx-hackathon.devfolio.co · ai-hackathon-2026.devpost.com · solo.io MCP & AI Agents Hackathon 2026 ·
about.gitlab.com AI Hackathon 2026 · unstop.com HackRx 6.0 ·
angelhack.com AI agent hackathon playbook · growthx.club Sarvam Epoch Buildathon ·
business-standard.com / outlookbusiness.com (NPCI UAP)
