# PHASE 0 — Buildathon Ground Truth (retrieved 2026-08-24)

Primary A-source: https://razorpay.com/buildathon/ (full page text captured verbatim in
official-buildathon-page-verbatim.txt — the page is server-rendered and ~4.3 KB of copy total,
so this is the COMPLETE official text, not a summary).
Second A-source: the official Google Form (see official-submission-form-structure.md).

## Program identity
"Razorpay AI Buildathon — Build. Show. Get hired."  == form title "Razorpay AI Builder Internship 2026".
It is a HIRING FUNNEL for a 6- or 12-month AI Builder Internship, not a prize hackathon.
Students only. In-person, Bangalore, from September. Stipend Rs 75,000/month.
"No resume screening. No long application." / "Shortlisted builders go straight to a panel.
No aptitude test. No group discussion."

## The four steps (official)
"pick a track, build something real, show your work (a public repo, a 5 minute pitch video,
the architecture), and if it has signal we call you in."

## The 5 official tracks — verbatim mandate + build spec + bar

01 — AI Growth & Agentic Commerce
  Mandate: "Grow the merchant's revenue, and make them sellable to AI buyers."
  Spec: "Build an agent that grows revenue for a merchant on Razorpay test-mode APIs, or that
        makes a merchant transactable by an AI buyer end to end."
  Why now: "NPCI's UAP and the global protocol race (ACP, AP2, x402) make agent-to-agent commerce
        the open problem of the year, and Razorpay's in-app pilots are already live."
  Example directions: Conversational in-app checkout, Agent-readable catalog, Upsell & cross-sell
        agent, Campaign orchestrator.
  THE BAR: "Every money action explainable, bounded and gated. Show the audit trail and one
        failure handled gracefully."

02 — AI Risk Manager
  Mandate: "Stop the merchant losing money to fraud, returns and chargebacks."
  Spec: "Build a working detector, verifier or auto-responder for one class of loss, with measured
        precision and recall on a held-out test set."
  Why now: "AI-enabled fraud is hitting Indian BFSI while returns and chargebacks quietly eat
        margin. This track surfaces the risk and ML minded builders the others miss."
  Example directions: Chargeback evidence responder, Return-risk scorer, Fraud-spike detector,
        Abuse-ring sentinel.
  THE BAR: "Honest metrics including false-positive cost. Strictly defense-only: anything
        offense-capable is disqualified."

03 — AI Revenue Recovery
  Mandate: "Find revenue that's slipping away and win it back."
  Spec: "Build an agent that detects revenue at risk, determines the right intervention, and
        executes a bounded recovery workflow: from payment failures and checkout abandonment to
        overdue receivables."
  Why now: "Revenue loss rarely happens in one clean step. A payment degrades, a checkout gets
        abandoned, a subscription fails, or an invoice goes overdue. AI can now close the loop from
        detecting the problem to diagnosing it, choosing the right intervention, and recovering
        the money."
  Example directions: Payment degradation -> root cause -> recovery action, Checkout drop-off
        recovery, Failed-subscription recovery, B2B receivables chaser, Mandate retry sequencer,
        Hinglish voice recovery, Promise-to-pay tracker.
  THE BAR: "Don't just identify the problem. Show measured money recovered across a batch, with
        compliant escalation, stopping rules, and an audit trail."

04 — AI Finance Controller
  Mandate: "Run the books and the cash position."
  Spec: "Build an agent that closes one finance-ops loop across a 50+ record batch of synthetic
        data, reporting its match rate and the exceptions it could not resolve."
  Why now: "The 2026 builder consensus: verification capacity, not generation speed, is the
        bottleneck. Reconciliation, settlement and forecasting are still done by hand."
  Example directions: Multi-source reconciliation, Settlement Q&A agent, Forward cash forecaster,
        Tax-line matcher.
  THE BAR: "Throughput plus measured accuracy plus an honest exception list. One cherry-picked
        match proves nothing."

05 — Open Track
  Mandate: "Build what you believe should exist."
  Spec: "Have an idea that doesn't fit the tracks above? Build it. Pick a real problem, use AI
        meaningfully, and show us something that works. Any domain, workflow, or user is fair game."
  Example directions: "Surprise us", "Solve a problem you deeply understand", "Build something we
        haven't thought of".
  THE BAR: "Open doesn't mean easier. Show a real problem, a working product, meaningful use of AI,
        and evidence that it creates value. The same bar for execution, reliability, and depth
        applies here."

## CRITICAL STRUCTURAL FACT
Razorpay publishes 5 TRACK MANDATES + 5 BUILD SPECS + 5 BARS + 22 non-binding "example directions".
It does NOT publish discrete numbered problem statements. The example directions are explicitly
"example directions", i.e. permission-granting illustrations, not a required menu. Several
third-party blogs re-present them as "problem statements" — that is the blog's framing, not
Razorpay's.

## Evaluation criteria (official, all of it)
There is no published scoring rubric or weights. The only official evaluation language is:
(a) the five per-track "The bar" statements above; (b) "if it has signal we call you in";
(c) shortlist -> panel. Cross-cutting bar themes, restated by Razorpay across tracks:
  - measured outcomes on a BATCH, not a cherry-picked demo
  - honest error/exception reporting (false-positive cost, exception list)
  - audit trail for every money action; bounded + gated actions; stopping rules
  - graceful failure handling
  - defense-only for risk work

## Known unknowns / not published officially
- No application deadline anywhere on the official page or in the form (see validation report).
- No team-size rule (form has no team fields -> individual submission).
- No judging weights, no shortlist date, no interview format detail beyond "panel".
- No list of which Razorpay test-mode APIs are in scope; only Track 1 names "Razorpay test-mode
  APIs" and Track 4 names "50+ record batch of synthetic data".

## Adjacent-but-different programs (do NOT conflate)
- https://razorpay.com/ai-builders/ — general (non-student) AI Builder hiring page. Different
  funnel, 3 steps, "call in 48 hrs". Useful A-source: names Razorpay's own AI systems —
  "Slash, Call-E, AI-led marketing campaigns, Agentic Platform, Agentic Payments, and Agent Studio".
- "Razorpay AI for Good Hackathon 2026" (hackortech.in) — aggregator-generated listing, Rs 1.2Cr
  prize, deadline 2026-08-20, no organizer URL, page self-describes as "Data sourced from free
  public APIs". No corroboration on any Razorpay property. Treated as NOT a real Razorpay event.
- "Razorpay FTX Hackathon" (devfolio) — separate/older event tied to the FTX conference.
