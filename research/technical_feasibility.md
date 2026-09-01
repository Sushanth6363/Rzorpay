# technical_feasibility.md — Phase 10: Can a Student Actually Build This?

Compiled 2026-08-25 for the opportunities that survived
[data_availability.md](data_availability.md).

**Time budget: ~11 days** (25 Aug → an assumed 5 Sep deadline, which Razorpay has never published).
Every difficulty score is *relative to that window*, for **one person** — the official form has no
team fields.

**Difficulty: 1 = trivial · 10 = not realistic in the window.**
**Classification:** EASY (build quickly) · MODERATE (significant engineering) · HARD (possible but
risky) · EXTREME (not realistic).

---

## 0. The shared foundation — build this once, whatever you pick

Roughly **40% of the work is identical across all four candidates**, and it is the part the track
bars actually grade.

| Component | What it is | Effort |
|---|---|---|
| **Seeded synthetic generator** | Deterministic, `--seed`, emits ground truth alongside the data. **The single most valuable artefact you will write** — the bars demand batch evidence, and the generator is what makes it exact | 1–1.5 days |
| **Eval harness** | One command regenerates every number in the README and video. Metrics to `eval/results/metrics.json`, exceptions to `exceptions.csv` | 0.5–1 day |
| **Trace format** | Structured, replayable JSONL per action: inputs, tool calls, decision, confidence, outcome. Ships in `traces/` | 0.5 day |
| **Policy/bounds layer** | Caps, gates, quiet hours, stopping rules, idempotency keys, kill switch | 0.5 day |
| **`make setup / demo / eval`** | A judge must reproduce your numbers in one command | 0.25 day |

**Stack that fits the window:** Python · SQLite (no server, commits with the repo, trivially
reproducible) · the official Razorpay MCP server with `rzp_test_` keys · Claude with structured
outputs · APScheduler if you need time · pytest.

> **Architectural rule that matters more than any other here:** *deterministic first, LLM on the
> residual.* Match, filter and classify with code; send the LLM only the cases code could not
> resolve. It is cheaper, faster, more reproducible — and it makes your exception list a designed
> output rather than an accident.

---

## 1. 🥇 A1 — Reconciliation Exception Resolver · **Difficulty 5/10 · MODERATE**

| Dimension | Requirement |
|---|---|
| **ML** | **Minimal.** Fuzzy matching on amount/date/counterparty (edit distance + tolerance windows). No model training needed. Optionally a small classifier for exception type — but rules cover most of it |
| **LLM** | Adjudication of the ambiguous tail: which candidate explains this unmatched line, what evidence supports it, what is missing. **Structured output mandatory** (proposal + confidence + evidence chain + abstain flag) |
| **Agent architecture** | Single tool-using agent. Deterministic matcher → residual queue → LLM adjudicator → proposal store. **Never writes to a ledger, only to a `proposals` table** |
| **APIs / tools** | MCP read tools: `fetch_all_settlements`, `fetch_settlement_with_id`, `fetch_settlement_recon_details`, `fetch_all_payments`, `fetch_all_refunds`, `fetch_order_payments`. Local: CSV/bank-statement parser, matcher, proposal writer |
| **Databases** | SQLite: `transactions`, `settlement_lines`, `bank_lines`, `proposals`, `exceptions`, `traces` |
| **Event processing** | **Batch.** No streaming needed. Optional webhook listener for late-authorisation updates — a nice-to-have, not MVP |
| **Evaluation** | Match rate, **proposal precision** (a wrong proposal accepted is the true failure), recall on resolvable exceptions, exception composition, and a **sensitivity curve across a 2–10% tail share** |
| **Simulation** | The centrepiece. Inject the defects Razorpay itself names: missing UTR, net-only reporting, cross-period deductions, late authorisation, partial refunds, fee/GST rounding, duplicates |
| **Security** | Test keys only via env vars; read-only against Razorpay; no PII; secrets never committed |
| **Latency** | Batch. Target **500 records in under 5 minutes**, with per-exception LLM calls in seconds. Comfortably demoable live |

**Minimum viable (4–5 days):** generator producing 500 rows with 6 defect types and ground truth ·
deterministic matcher · LLM adjudicator on the residual with confidence scores · `exceptions.csv` ·
eval harness · traces.

**Ambitious (+3–4 days):** multi-PSP schema inference (map an arbitrary competitor export onto a
canonical model) · cross-period deduction linking · materiality ranking for close-readiness ·
tax-line reasoning with abstention · full sensitivity curve · live MCP run against test mode
alongside the synthetic batch.

**Why 5 and not lower:** the matching logic is easy; getting *precision* on proposals and a
genuinely useful exception taxonomy is where the days go.

---

## 2. 🥈 A2 — Headroom-Aware Recovery Sequencer · **Difficulty 7/10 · MODERATE→HARD**

| Dimension | Requirement |
|---|---|
| **ML** | Two small models: **(a)** per-customer success-timing (empirical histograms over hour/day-of-month are often enough; a gradient-boosted model if time allows), **(b)** a self-cure baseline so incremental lift is computable |
| **LLM** | Failure classification is mostly **deterministic** — the error codes are given. LLM earns its place in intervention selection under conflicting signals, and in drafting customer messages |
| **Agent architecture** | Recovery agent + **risk-headroom policy layer with veto**. Two agents are defensible *only* because their objectives genuinely oppose (Phase 7 §3) |
| **APIs / tools** | `fetch_all_payments`, `fetch_payment`, `create_payment_link`, `create_payment_link_upi`, `send_payment_link`, `create_registration_link`, `fetch_tokens` |
| **Databases** | SQLite: `payments`, `attempts`, `customers`, `mandates`, `chargeback_ledger`, `policy_state`, `traces` |
| **Event processing** | **Scheduler required** (APScheduler) plus a retry queue with **idempotency keys** — the double-debit risk is real and a judge may probe it |
| **Evaluation** | ⭐ **Holdout: treated vs control.** Report **incremental** recovery, never gross · recovery rate by failure class · cost per attempt · **chargeback-ratio trajectory against the 1% trigger** |
| **Simulation** | ⚠️ **The hard part.** You must simulate customer balance dynamics over time, a self-cure process, and dispute generation — a small agent-based simulation, and the main reason this scores 7 |
| **Security** | Attempt caps, quiet hours, no real contact, idempotency, kill switch, full audit trail per money action |
| **Latency** | Asynchronous and scheduled. Compress simulated time for the demo — **say so on camera** |

**Minimum viable (5–6 days):** synthetic ledger with temporal balance dynamics · deterministic
classifier over the published taxonomy · learned-timing vs fixed-interval comparison · holdout ·
headroom stopping rule · traces.

**Ambitious (+3–4 days):** true two-agent negotiation with logged vetoes · live payment links against
test mode · multi-rail policy with mandate-validity checks · Hinglish nudges.

**Watch:** test-mode card tokens expire in **3 days**, and **UPI cancellation returns success in test
mode**. Both will corrupt a naive subscription demo. Name them in the README.

---

## 3. 🥉 A4 — Promise-to-Pay Collections Agent · **Difficulty 6/10 · MODERATE**

| Dimension | Requirement |
|---|---|
| **ML** | Payment-probability model by ageing bucket and payer history (logistic regression or GBM — a small, honest model beats a large opaque one here) |
| **LLM** | Message drafting under compliance constraints; **promise extraction from free-text replies** (the genuinely LLM-shaped sub-task); escalation drafting |
| **Agent architecture** | Single agent over a long-horizon state machine: `outstanding → contacted → promised → broken → escalated → collected/stopped` |
| **APIs / tools** | `create_payment_link`, `send_payment_link`, `fetch_payment_link`, `fetch_all_payment_links` |
| **Databases** | SQLite: `invoices`, `buyers`, `commitments`, `contacts`, `traces` |
| **Event processing** | Scheduler plus **commitment-expiry triggers** — "they promised the 5th, it is the 6th" is the core event |
| **Evaluation** | DSO days compressed · ₹ collected ÷ ₹ overdue · **promise-kept rate** · contacts per rupee · **opt-outs and complaints reported honestly** |
| **Simulation** | Payer-response model: probability of reply, promise, honour, default — anchored on 73-day mean DSO and 82.6% of invoices at 0–30 day terms |
| **Security** | ⭐ Operates **in the merchant's name, never Razorpay's** · contact-frequency caps · quiet hours · tone constraints · hard stop into statutory MSME process |
| **Latency** | Daily batch |

**Minimum viable (4–5 days):** invoice generator with ageing · probability model · prioritised chase
list · commitment tracking · compliant drafting · DSO curve.
**Ambitious (+3 days):** reply parsing with promise extraction · negotiation of part-payment plans ·
statutory escalation pack · multi-channel cadence.

---

## 4. A5 — Agentic Purchase Intent Verification · **Difficulty 6/10 · MODERATE**

| Dimension | Requirement |
|---|---|
| **ML** | Minimal — semantic similarity at most |
| **LLM** | **Heaviest LLM dependence of the four.** Parse the instruction, compare the resulting cart against it, detect and characterise divergence |
| **Agent architecture** | Shopping agent + **verifier gate before capture**. The gate is the product |
| **APIs / tools** | `create_order`, `fetch_order`, `capture_payment`, `initiate_payment`; MCP as the agent's tool surface |
| **Databases** | SQLite: `catalog`, `instructions`, `carts`, `consent_tokens`, `audit_log` |
| **Event processing** | Synchronous request/response |
| **Evaluation** | Divergence-detection precision and recall on labelled instruction/cart pairs, including adversarial ones |
| **Simulation** | Catalog + instruction set + deliberately divergent carts (right price/wrong product, quantity drift, substitution) |
| **Security** | Caps enforced **before** capture · consent-token validation · test mode only |
| **Latency** | ⚠️ **Interactive — must feel instant.** Target under 2–3s, which constrains how much LLM you can put in the hot path |

**Minimum viable (4 days):** catalog · instruction parser · cart comparator · cap enforcement ·
audit trail · adversarial test set.
**Ambitious (+3 days):** agent-readable catalog schema (the one unoccupied Track 1 direction) ·
consent model mirroring UPI Reserve Pay · dispute record for divergent purchases.

**The constraint here is not difficulty — it is ~100 competitor repos.**

---

## 5. Eliminated

| Opportunity | Difficulty | Why |
|---|---|---|
| **A3 Freeze Navigator** | 6/10 to build, but **EXTREME to evidence** | Already eliminated in Phase 9. The engineering is fine; you must invent the event, the trigger and the outcome |
| Chargeback evidence responder | — | Disputes cannot be created in test mode |
| Anything needing cross-merchant data | EXTREME | Legally unobtainable |

---

## 6. Summary

| Opportunity | Difficulty | Class | MVP | Ambitious | Main risk |
|---|---|---|---|---|---|
| **A1 Reconciliation** | **5** | MODERATE | 4–5 days | +3–4 | Proposal precision, not matching |
| **A4 Collections** | **6** | MODERATE | 4–5 days | +3 | Payer-response model realism |
| **A5 Intent Verification** | **6** | MODERATE | 4 days | +3 | Competition, and latency in the hot path |
| **A2 Recovery** | **7** | MODERATE→HARD | 5–6 days | +3–4 | **Temporal simulation** is the schedule risk |

**With ~11 days, one person:** A1 or A4 comfortably reach the ambitious version. A5 reaches ambitious
if you skip the catalog schema. **A2's MVP fits, but its ambitious version does not** — the temporal
simulation plus two-agent negotiation is where schedules break.

---

```
PHASE 10 VALIDATION

Easy:
  (none - anything genuinely easy here would fail the bars, which demand batch evidence,
   audit trails and honest exception reporting)

Moderate:
  A1 Reconciliation Exception Resolver (5)  - deterministic matcher + LLM on the residual
  A4 Promise-to-Pay Collections (6)         - state machine + small probability model
  A5 Intent Verification (6)                - LLM-heavy but architecturally simple

Hard:
  A2 Headroom-Aware Recovery Sequencer (7)  - the temporal simulation of balance dynamics,
                                              self-cure and dispute generation is a genuine
                                              sub-project inside the project

Extreme:
  A3 Freeze Navigator - not to BUILD (6) but to EVIDENCE. Eliminated in Phase 9.
  Cross-merchant fraud rings, payment routing - data is legally or structurally unobtainable.

Ideas eliminated:
  A3 stays eliminated. Its engineering was never the problem.
  A2's AMBITIOUS version is eliminated on schedule, not on capability - the MVP survives and is
  strong. Attempting two-agent negotiation AND a full temporal simulation in 11 days is the
  most likely way to arrive on 5 September with a half-working demo.

Most realistic high-impact opportunity:
  A1 Reconciliation Exception Resolver. Lowest difficulty of the survivors (5), highest data
  score (9), least crowded track (24 repos vs 88), maps DIRECT to a BUILD SPEC rather than an
  optional example direction, and its central design constraint - propose with confidence,
  never assert finality - is derived from the specific audit liability that explains why
  Razorpay shipped a viewer in June 2022 and no resolver since. The MVP fits in under half the
  window, leaving real time for the eval harness, the failure demo and the video - which is
  where most submissions run out of road.

  Runner-up: A4 Collections. Slightly harder, government-sourced problem magnitude, almost no
  competition, and no Razorpay agent covering it.

Confidence: 8/10

READY FOR PHASE 11: YES
```

**Why 8/10.** Difficulty scores are anchored on concrete component lists and a named stack rather
than on impression, and one ambitious version was cut on schedule grounds rather than being waved
through. It is not 9/10 because effort estimates for a single unknown builder carry real variance —
if you have not written an agent loop with structured outputs before, add roughly two days to every
MVP figure — and because the 11-day window rests on a deadline Razorpay has never officially
published.

---

## 7. Suggested 11-day shape (for A1)

| Days | Work |
|---|---|
| 1–2 | Generator with ground truth + 6 defect types; SQLite schema; `make setup` |
| 3–4 | Deterministic matcher; residual queue; first eval numbers |
| 5–6 | LLM adjudicator with structured output, confidence, abstention; traces |
| 7 | Exception taxonomy and `exceptions.csv`; materiality ranking |
| 8 | Sensitivity curve; live MCP test-mode run alongside the synthetic batch |
| 9 | README with the full evidence chain; `DELTA.md`; architecture diagram |
| 10 | Video: live batch run, a failure on camera, trace walkthrough |
| 11 | Buffer, freeze, tag the release, submit |

**Two days of that plan are documentation and video.** That is not padding — under a one-shot
submission rule with no edits after submitting, it is the difference between good work and a good
*submission*.
