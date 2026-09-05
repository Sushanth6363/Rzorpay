# Unified Recovery Engine

**Razorpay AI Buildathon 2026 · Track 3 — AI Revenue Recovery**

One agent that detects revenue at risk across four streams (failed payments, checkout
abandonment, failed subscription renewals, overdue B2B receivables), diagnoses why it is at
risk, decides what to do about it, and then **runs the recovery to completion on its own**:
one-rung-at-a-time escalation, derived reminder timing, atomic contact budgets, stopping
rules, and a full audit trail. It reports **measured money recovered across a batch** with
confidence intervals, and it **executes for real** against Razorpay Test Mode.

---

## Read this first: two modes, and what each one proves

Conflating these would be the dishonest direction, so they are separated everywhere.

**1. The evaluation is simulated.** Every number in `results/RESULTS.md` comes from a
deterministic local simulator. Interventions, customer responses and recovery outcomes are
authored, not observed. Confidence intervals quantify sampling error *inside the simulation
only*; they say nothing about distance from a real-world value. **No claim of real-world
Razorpay recovery uplift is made or supported.**

**2. The live path really sends.** With dispatch explicitly enabled, the engine creates real
Razorpay Payment Links, sends a real email over SMTP, receives real HMAC-verified webhooks
from Razorpay, and closes the case when the money actually arrives. This has been run
end-to-end with a real Rs 25,000 test-mode payment. What it proves is that the loop closes,
not that recovery rates improve.

Dispatch is **off by default**. Two independent gates must both open (`--send` *and*
`RECOVERY_DISPATCH_ENABLED=true`) before anything leaves the process, and the test suite
forces both closed for the whole session so a test run can never contact anyone.

### The honest read on the model

- **The ML arm does not beat the transparent heuristic in any meaningful way.** A5 (CatBoost
  S-learner) vs A3 (readable rules) is **+0.0005, 95% CI [-0.0213, 0.0223], p=0.9642 —
  INCONCLUSIVE**. A5 recovers marginally more money (Rs 13.65M vs Rs 13.57M) at marginally
  lower cost (3.54 vs 3.63 paise per recovery), and none of that is distinguishable from
  noise.
- We pre-registered a data-generating-process experiment predicting the model would pull
  ahead once outcomes depended on context. **That prediction was falsified.** The finding we
  report instead: compliant escalation bounds the action space so tightly that scorer quality
  is nearly irrelevant — the two scorers disagree on 4 of 1,000 decisions, and only 4 of 7
  actions are ever chosen.
- **The primary comparison (A2 - A1) is -1.48%, INCONCLUSIVE.** That is an honest statistical
  outcome at this sample size. We never report "trending toward significance".
- The one **statistically significant** result is the engine against doing nothing:
  **A5 vs CONTROL = +0.5423, 95% CI [0.5268, 0.5577]**.

The engine's value is in safety, cross-stream arbitration and contact efficiency, not in a
model being cleverer than a rule. That is the claim, and the numbers above are why.

---

## How recovery actually runs

A case enters from a webhook (a failed payment, an abandoned checkout) or from a merchant CSV
of overdue invoices. The merchant supplies what is owed and by whom, never *why* it is
unpaid: the engine diagnoses that itself.

**Deciding.** For each case the engine estimates the incremental effect of every eligible
action against doing nothing, `d(x,a) = p(x,a) - p(x, NO_ACTION)`, converts it to expected
value against the amount at risk minus that action's cost, and takes the argmax. `NO_ACTION`
scores exactly zero by construction, so the engine abstains whenever no contact is worth
making. **That abstention is the product**: it is what stops a recovery system becoming a
harassment system.

**Executing.** It creates a live payment link, sends the message it chose, schedules its own
next review, and goes quiet. When that review falls due a background worker re-opens the
case, re-reads its state, and decides again: escalate, repeat, or stop. Nothing external
triggers the next step.

**Escalating, one rung at a time** (`app/pipeline/escalation.py`, ADR-0015):

```
rung 0  EMAIL_LINK      lowest intensity, asynchronous, ignorable
rung 1  SMS_LINK
rung 2  WHATSAPP_LINK   interactive, expects a reply
rung 3  IVR_CALL        interrupts the customer
rung 4  AGENT_DIAL      a person calls a person
```

The ceiling is always `highest_confirmed_rung + 1`, never +2, whatever the score says. Only a
contact **confirmed delivered** advances the ladder, so a message that failed to send does
not buy the right to phone someone. Escalation never creates capacity: a louder channel still
reserves a slot against the same per-customer budget.

**Reminder timing is derived, not fixed** (`app/realtime/followup.py`):

```
delay = base(diagnosis) x multiplier(action) x backoff(attempt)
```

| Diagnosis | Base | Why |
|---|---:|---|
| Customer abandonment | 6h | intent is still warm |
| Gateway failure | 8h | the fault was ours; re-check soon |
| Card declined | 24h | needs a different instrument |
| Subscription renewal failure | 48h | |
| Insufficient funds | 72h | wait for a likely payday |
| Customer unresponsive | 120h | |
| Invoice overdue | 168h | chasing a finance team daily gets you blocked |

Channel multipliers reflect read latency, not urgency: email 1.2 (unanswered does not mean
ignored), SMS 0.8, WhatsApp 0.9, IVR 1.5, agent dial 2.0 (a person called; do not crowd
them), a machine retry 0.5. Each successive silence widens the gap: 1x, 1.5x, 2.5x, 4x.

So a gateway blip is retried in about 4 hours and an overdue invoice is followed up in about
8 days, from the same engine, with no per-case rules written.

**Stopping is a first-class outcome.** Four follow-ups maximum, a 30-day recovery window, a
per-customer contact budget, a quiet period between touches, suppression while the gateway is
in a known outage, and abstention whenever nothing has positive expected value.

**Payment always wins.** Case state is re-read at the moment of dispatch, not when the action
was queued, so money arriving cancels every pending message and every open payment link
immediately. A customer who has paid cannot be chased by something already in flight.

**What it cannot recover, it hands over honestly.** Everyone still unpaid once the ladder is
exhausted is exported with what was already tried, so a human collections agent does not
re-send the email the engine already sent three times.

---

## Quickstart

> **Requirements:** Python **3.11, 3.12 or 3.13** (3.12 recommended). **Not 3.14** — the
> pinned scientific stack (CatBoost, NumPy, SciPy, scikit-learn) has no wheels for it yet.
> The setup below creates an isolated virtual environment so it never matters what `python`
> points to globally.

`make setup` builds a `.venv` with a supported interpreter and installs everything into it.
Every other `make` target runs through that venv, never a bare `python` or `pytest`.

```bash
make setup      # creates .venv (needs 3.11-3.13 available) and installs deps
make test       # 413 tests, all in .venv
make eval       # writes results/report.json + results/RESULTS.md
make demo       # judge dashboard on http://localhost:8555
```

### No GNU make (common on Windows)

```bash
python scripts/bootstrap.py
```

**Windows (PowerShell):**

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe scripts\run_evaluation.py --events 200 --seeds 21-40
.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.port 8555
```

**macOS / Linux:**

```bash
.venv/bin/python -m pytest
.venv/bin/python scripts/run_evaluation.py --events 200 --seeds 21-40
.venv/bin/python -m streamlit run streamlit_app.py --server.port 8555
```

If `python` on your PATH is unsupported, `bootstrap.py` finds an installed 3.11-3.13 or tells
you exactly how to install one. It never leaves a half-built environment behind.

---

## Running the live loop (real Razorpay, real email)

This actually contacts people. Read the gates above first, and use a CSV containing only
addresses you own.

```bash
cp .env.example .env          # then fill in Razorpay TEST keys and SMTP credentials
```

Three terminals:

```bash
# 1. the webhook server: receives Razorpay's signed events
.venv/Scripts/python.exe -m app.api.webhook_listener

# 2. the public tunnel: reads NGROK_DOMAIN from .env, nothing to substitute
./scripts/start_tunnel.ps1

# 3. the demo: CSV to decision to link to email, then wait for payment
.venv/Scripts/python.exe scripts/run_demo_a.py --csv demo_customers.csv --send
```

Register `https://<your-domain>/webhooks/razorpay` in Razorpay Test Mode once. Paying the
link fires the webhook and the case closes itself: status `PAID`, open links cancelled,
scheduled follow-ups stopped.

`scripts/send_test_webhook.py` exercises the whole receiving path (tunnel, HMAC, replay
window, idempotency, event mapping, case resolution) without needing a payment. If that works
and a real payment does not, the problem is the dashboard registration, not the code.

---

## Deployment

`render.yaml` deploys the dashboard to Render. The webhook listener deliberately is **not**
deployed there: Render's free instances have an ephemeral filesystem and spin down after 15
minutes without traffic, and the recovery loop closes when a customer pays *on Razorpay's
site*, which sends no traffic to the service. The instance would sleep during exactly the gap
that matters, the SQLite file would be wiped, and the payment webhook would arrive to find no
case to close. Hosting the full loop needs a paid instance with a disk at `/var/data`.

---

## What a reviewer should look at

| To see... | Look at |
|---|---|
| Measured money, streams, escalation, verdicts | `make eval`, then `results/RESULTS.md` |
| The decision trace, executed safety checks, five-arm comparison | `make demo` (dashboard) |
| The recovery workflow end to end, on real money | `scripts/run_demo_a.py` |
| Per-customer state: what was decided, sent, and paid | the Case board in the dashboard |
| That the tests actually pass | `make test` (413 tests) |
| Why each design call was made | `refer/decisions/` (ADRs) |
| How Track 3's spec maps to the build | the requirements table at the end of `results/RESULTS.md` |

---

## How it answers Track 3

| Spec / bar clause | Where |
|---|---|
| build an **agent** | `app/agent/loop.py` — decides, executes, schedules its own next review |
| detects revenue at risk | Stage 0 validation + Stage 1 diagnosis (`app/pipeline/`) |
| determines the right intervention | candidate generation, EV ranking, arbitration (`app/scoring/`) |
| **executes** a bounded recovery workflow | `app/dispatch/` — real links, real email, real webhooks |
| payment failures / checkout / receivables | mixed-stream batch (`app/experiment/batch.py`) |
| measured money across a batch | `results/RESULTS.md` — 200 cases required, this run covers 4,000 |
| **compliant escalation** | `app/pipeline/escalation.py` (ADR-0015) |
| stopping rules | contact cap, quiet period, escalation ceiling, outage suppression, abstention |
| audit trail | case timeline, contact ledger, dispatch log, per-decision correlation trace |
| Rs recovered vs Rs at risk, recovery rate, cost per recovery | the Money table in `results/RESULTS.md` |

Measured, from the 4,000-case run: **Rs 25,128,982 at risk, Rs 13,646,953 attributed
recovered (54.31% by value), at 3.54 paise per recovery.**

A distinguishing piece: **overdue B2B receivables have their TDS withholding *derived* from
the invoice's own facts** (section, payee constitution, PAN, amount remitted) rather than read
off a flag — so the engine declines to chase a shortfall that is simply statutory withholding
the payer already remitted to the government. See `app/pipeline/tds.py` and ADR-0016.

---

## Layout

```
app/
  pipeline/      Stage 0/1, candidate generation, safety filter, escalation, TDS
  scoring/       heuristic + CatBoost S-learner, EV calculator, cost schedule
  ledger/        concurrency-safe contact ledger (atomic reservation)
  orchestration/ end-to-end closed-loop orchestrator
  experiment/    arm policies, batch generator, statistical runner
  agent/         the autonomous cycle: decide, execute, schedule the next review
  cases/         durable case, CSV ingest, repository, case board
  dispatch/      channel adapters, copy, HTML email, the dispatcher gate
  payments/      Razorpay payment link lifecycle
  realtime/      webhook ingestion, live downtime, follow-up queue, reliability
  reporting/     unrecovered handoff export
  api/           signed webhook listener
  ui/            Streamlit judge dashboard
scripts/
  bootstrap.py         one-command venv setup
  run_evaluation.py    produces results/report.json + RESULTS.md
  run_demo_a.py        the live CSV-to-payment demo
  send_test_webhook.py signed webhook probe
  start_tunnel.ps1     public tunnel for Razorpay callbacks
refer/decisions/       Architecture Decision Records
tests/                 413 tests
```

---

*Every figure in `results/` describes an authored simulation. The live path really sends, but
proves only that the loop closes. No claim of real-world Razorpay recovery uplift is made or
supported.*
