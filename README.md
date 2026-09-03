# Unified Recovery Engine

**Razorpay AI Buildathon 2026 · Track 3 — AI Revenue Recovery**

One engine that detects revenue at risk across four streams — failed payments, checkout
abandonment, failed subscription renewals, and overdue B2B receivables — determines the
right intervention, and executes a **bounded, compliant** recovery workflow: atomic contact
budgets, one-rung-at-a-time escalation, stopping rules, and a full audit trail. It reports
**measured money recovered across a batch**, with confidence intervals and honest verdicts.

---

## What this is, and what it is not — read this first

This is the honest framing. If a reviewer is going to find it, they should find it here,
from us, not catch it later.

- **Every outcome is simulated.** There is no live payment system, no real customers, no
  external gateway calls. Interventions, customer responses and recovery outcomes come from
  a deterministic local simulator. Confidence intervals quantify sampling error **inside the
  simulation only** — they say nothing about distance from a real-world value. The dashboard
  states this on every screen.

- **Under the simulator, the ML model does not beat the transparent heuristic.** The
  CatBoost arm (A5) is *significantly worse* than the readable rule-based arm (A3), and we
  report that verdict rather than tuning it away. That is deliberate: the engine's value is
  in its **safety, cross-stream arbitration, and contact efficiency** — comparable recovery
  for materially fewer customer contacts — not in a model being cleverer than a rule. The
  headline of every generated report says this out loud, computed from the run.

- **The primary comparison is often INCONCLUSIVE.** That is an honest statistical outcome at
  this sample size, not a hidden failure. We never report "trending toward significance".

What *is* real and defensible: the concurrency-safe contact ledger, the compliant escalation
ladder, the derived (not declared) TDS withholding logic, the point-in-time leakage guard,
the audit trail, and full reproducibility from a seed.

---

## Quickstart

> **Requirements:** Python **3.11, 3.12 or 3.13** (3.12 recommended). **Not 3.14** — the
> pinned scientific stack (CatBoost, NumPy, SciPy, scikit-learn) has no wheels for it yet,
> and a suite run there will fail to build. The setup below creates an isolated virtual
> environment so it never matters what `python` points to globally.

### The one path that always works

`make setup` builds a `.venv` with a supported interpreter and installs everything into it.
Every other `make` target runs through that venv — never a bare `python` or `pytest`.

```bash
make setup      # creates .venv (needs 3.11-3.13 available) and installs deps
make test       # 190 tests, all in .venv
make eval       # writes results/report.json + results/RESULTS.md
make demo       # judge dashboard on http://localhost:8555
```

### No GNU make (common on Windows)

Run the same bootstrap directly, then use the `.venv` it created:

```bash
python scripts/bootstrap.py
```

**Windows (PowerShell):**

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe scripts\run_evaluation.py --events 200 --seeds 21-40
.venv\Scripts\python.exe -m streamlit run app/ui/dashboard.py --server.port 8555
```

**macOS / Linux:**

```bash
.venv/bin/python -m pytest
.venv/bin/python scripts/run_evaluation.py --events 200 --seeds 21-40
.venv/bin/python -m streamlit run app/ui/dashboard.py --server.port 8555
```

If `python` on your PATH is 3.14 (or otherwise unsupported), `bootstrap.py` will find an
installed 3.11–3.13 for you, or tell you exactly how to install one. It never leaves a
half-built environment behind.

---

## What a reviewer should look at

| To see… | Look at |
|---|---|
| Measured money, streams, escalation, verdicts | `make eval`, then `results/RESULTS.md` |
| The decision trace, live safety checks, the five-arm comparison | `make demo` (dashboard) |
| That the tests actually pass | `make test` (190 tests) |
| Why each design call was made | `refer/decisions/` (ADRs) |
| How Track 3's spec maps to the build | the requirements table at the end of `results/RESULTS.md` |

---

## How it answers Track 3

| Spec / bar clause | Where |
|---|---|
| detects revenue at risk | Stage 0 validation + Stage 1 diagnosis (`app/pipeline/`) |
| determines the right intervention | candidate generation → EV ranking → arbitration (`app/scoring/`) |
| bounded recovery workflow | contact budget, atomic reservation, reconciliation ladder (`app/ledger/`) |
| payment failures / checkout / receivables | mixed-stream batch (`app/experiment/batch.py`) |
| measured money across a batch | `results/RESULTS.md` — ≥200 cases required, this run covers 4,000 |
| **compliant escalation** | `app/pipeline/escalation.py` (ADR-0015) |
| stopping rules | contact cap, quiet period, escalation ceiling, outage suppression, abstention |
| audit trail | per-decision correlation trace + suppression reasons |
| ₹ recovered vs ₹ at risk, recovery rate, cost per recovery | the Money table in `results/RESULTS.md` |

A distinguishing piece: **overdue B2B receivables have their TDS withholding *derived* from
the invoice's own facts** (section, payee constitution, PAN, amount remitted) rather than
read off a flag — so the engine declines to chase a shortfall that is simply statutory
withholding the payer already remitted to the government. See `app/pipeline/tds.py` and
ADR-0016.

---

## Layout

```
app/
  pipeline/      Stage 0/1, candidate generation, safety filter, escalation, TDS
  scoring/       heuristic + CatBoost S-learner, EV calculator, cost schedule
  ledger/        concurrency-safe contact ledger (atomic reservation)
  orchestration/ end-to-end closed-loop orchestrator
  experiment/    arm policies, batch generator, statistical runner
  ui/            Streamlit judge dashboard
scripts/
  bootstrap.py       one-command venv setup
  run_evaluation.py  produces results/report.json + RESULTS.md
  verify_environment.py
refer/decisions/     Architecture Decision Records
tests/               190 tests
```

---

*All figures produced by this project describe an authored simulation. No claim of
real-world Razorpay recovery uplift is made or supported.*
