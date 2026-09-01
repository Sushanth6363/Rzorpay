# TOOLCHAIN — ₹0 IMPLEMENTATION STACK

**Reviewed against**: `strategy/STRATEGY.md` · `docs/EXPERIMENT_METHODOLOGY.md` · frozen architecture (`p0.1`, `p0.2`, `p0.2-patch`, `p0.2-closure`).
**Constraint**: student / solo builder, ₹0 infrastructure budget, one laptop, 10 days.
**Free-tier facts verified**: 2026-08-31 (§13, §24).

---

# 1. EXECUTIVE VERDICT

**The entire prototype runs on a laptop with zero infrastructure spend, zero cloud accounts, and zero paid services.** Nothing in the frozen architecture requires otherwise.

Four decisions do most of the cost and complexity reduction, and three of them contradict the default stack in the brief:

| Decision | Instead of | Why |
|---|---|---|
| **SQLite** (WAL + `BEGIN IMMEDIATE`) | PostgreSQL | The frozen atomic-reservation design was written for `BEGIN IMMEDIATE`. At 600 opportunities × 40 seeds on one machine, Postgres buys nothing and costs a daemon, a container, and connection config. |
| **No Docker** | Docker + Compose | Follows from SQLite. With no server process, there is nothing to containerise. |
| **Streamlit** | React / Next / Vite / Tailwind | One trace screen and a results table. A Node toolchain for that is the single biggest unnecessary dependency in the project. |
| **stdlib `sqlite3`** | SQLAlchemy | The ledger's correctness lives in exact SQL — `UPDATE … WHERE reserved + consumed < cap`, CAS on status, `BEGIN IMMEDIATE`. An ORM abstracts precisely the layer that must not be abstracted. |

**Consequence: no Node.js, no Docker, no database server, no message queue, no LLM API key, no ML platform, no cloud account.** One Python virtualenv and a `.db` file.

**Total cost: ₹0.** Not "₹0 on a free tier that might change" — ₹0 because nothing leaves the laptop.

---

# 2. MINIMUM ₹0 STACK

```
Language      Python 3.11+
Database      SQLite (stdlib sqlite3, WAL mode)
Models        frozen dataclasses + enums (stdlib)
ML            scikit-learn · CatBoost · NumPy · pandas · SciPy
Plots         Matplotlib
Tests         pytest · Hypothesis
UI            Streamlit
API           FastAPI + uvicorn        [OPTIONAL — one webhook endpoint for the demo]
VCS / CI      Git · GitHub · GitHub Actions (free, unlimited on public repos)
Editor        VS Code (free)
```

That is the whole stack. Eleven packages, one of them optional.

---

# 3. COMPLETE TOOL INVENTORY

| Tool | Purpose | Free/Local Option | Free Tier | Mandatory? | Install? |
|---|---|---|---|---|---|
| Python 3.11+ | everything | local | n/a — open source | **YES** | **YES** |
| `sqlite3` (stdlib) | database, ledger, audit, events | local | ships with Python | **YES** | no (built in) |
| `dataclasses`, `enum` (stdlib) | domain model | local | built in | **YES** | no |
| NumPy | RNG substreams, numerics | local | BSD | **YES** | YES |
| pandas | experiment analysis, tables | local | BSD | **YES** | YES |
| SciPy | t-intervals, Wilcoxon, McNemar, bootstrap | local | BSD | **YES** | YES |
| scikit-learn | calibration, Brier, metrics, splits | local | BSD | **YES** | YES |
| CatBoost | the model scorer (A5) | local | Apache 2.0 | **YES** | YES |
| Matplotlib | reliability curves, result plots | local | PSF-like | **YES** | YES |
| pytest | all tests | local | MIT | **YES** | YES |
| Hypothesis | property tests (budget invariant, exploration safety) | local | MPL 2.0 | **YES** | YES |
| Streamlit | the "why did the engine do this?" screen | local | Apache 2.0 | **YES** | YES |
| pytest-cov | coverage on the safety modules | local | MIT | no | optional |
| FastAPI + uvicorn | `POST /downtime/events` for the demo beat | local | MIT | no | **recommended** |
| Faker | realistic names/emails in generated data | local | MIT | no | optional |
| ruff | lint + format (replaces black + flake8) | local | MIT | no | optional |
| Git | version control; the freeze-order evidence | local | GPL | **YES** | **YES** |
| GitHub | remote, submission | cloud | free | **YES** | account |
| GitHub Actions | CI: tests, leakage gate | cloud | **free, unlimited on public repos** | no | recommended |
| VS Code | editor | local | free | **YES** | YES |

## MUST HAVE

Python · sqlite3 · NumPy · pandas · SciPy · scikit-learn · CatBoost · Matplotlib · pytest · Hypothesis · Streamlit · Git · GitHub · VS Code

## NICE TO HAVE (only after the MVP works)

FastAPI + uvicorn (one endpoint) · GitHub Actions · pytest-cov · ruff · Faker

## DO NOT USE

| Tool | Why not |
|---|---|
| **PostgreSQL** | SQLite `BEGIN IMMEDIATE` is the frozen design's prototype path and is correct at this scale |
| **Redis** | **Redis is NOT required for the MVP** — see §6 |
| **Docker / Docker Compose** | Nothing to containerise once the DB is a file |
| **React / Next.js / Vite / Tailwind / Node.js** | A whole language runtime and build chain for one screen |
| **Kafka / RabbitMQ / Redis Streams / SQS / Pub/Sub** | An events table with a unique constraint is the event log |
| **LangChain / LangGraph / AutoGen / CrewAI / OpenAI Agents SDK** | The agents are proposal-generating service classes; arbitration must be deterministic |
| **Any LLM API** | No LLM sits on the decision path. Message drafting is templated |
| **MLflow / W&B / Vertex AI / SageMaker / Azure ML** | `models/v1.cbm` + JSON metadata + a git tag is the registry |
| **Prometheus / Grafana / OpenTelemetry / Datadog / New Relic** | JSON logs + SQLite tables + one Streamlit page |
| **Locust** | Concurrency is tested with `ThreadPoolExecutor` + Hypothesis, not load-generated |
| **Vault / AWS Secrets Manager / GCP Secret Manager** | There are no production secrets |
| **Railway** | **Not free** — verified §13 |
| **Alembic** | The schema is created once by a script; migrations are ceremony here |

---

# 4. FREE DATASET INVENTORY

| Dataset | Free? | Public? | Download method | What we use it for | Classification |
|---|---|---|---|---|---|
| **NPCI UPI bank-wise TD/BD & uptime** | Yes | Yes | manual page visit; **licence check pending** (403 to automated fetch) | issuer failure probability, failure-type mix, issuer share, outage severity | **CALIBRATION DATA** |
| **MSME Samadhaan / MSEFC reports** | Yes | Yes | manual page visit; public report pages | B2B ageing and pendency distribution | **CALIBRATION DATA** |
| **Criteo Uplift** | Yes | Yes | form download, CC BY-NC-SA 4.0 | validating the estimator/CI machinery on real randomised data | **REAL DATA — estimator validation only** |
| **Synthetic generator output** | n/a | n/a | `make generate` | opportunities, actions, outcomes | **SYNTHETIC DATA** |
| **Model training set** | n/a | n/a | derived from `EXPERIMENT_SET` outcomes | training v1 / v2 | **TRAINING DATA (synthetic)** |
| UCI Bank Marketing | Yes | Yes | direct download, CC BY 4.0 | *optional* contact-fatigue prior | CALIBRATION DATA (optional) |
| Hillstrom, KKBox, LendingClub, fraud sets | Yes | Yes | — | **not used** | rejected (`docs/DATASET_RESEARCH.md`) |

**The distinction that must never blur**: NPCI and Samadhaan are **calibration** — they set how often and why payments fail. They contain **no interventions and no recovery outcomes**, so they are never training data and never evidence. No public dataset with payment-failure → intervention → outcome exists; this was searched for directly.

**No paid dataset is recommended, and none is needed.**

Cost: ₹0. Both primary sources are government/industry publications.

---

# 5. REAL vs MOCKED vs SIMULATED

| Component | Status | Note |
|---|---|---|
| Razorpay payment | **SIMULATED** | no production credentials, no test keys required |
| Gateway downtime webhook | **SIMULATED LOCAL WEBHOOK** | real HTTP `POST` to a local FastAPI endpoint, payload shaped to Razorpay's published schema |
| Customer response | **SIMULATED** | response function, `docs/EXPERIMENT_METHODOLOGY.md` §6 |
| Payment execution | **SIMULATED** | provider stub: success · failure · timeout · ambiguous · outage |
| Recovery outcome | **SYNTHETIC** | labelled `dataset_type = SYNTHETIC` in every run |
| Message delivery | **SIMULATED** | no SMS/WhatsApp/email provider, no cost |
| Environmental distributions | **CALIBRATED from public real data** | NPCI, Samadhaan |
| **Contact ledger** | **REAL IMPLEMENTATION** | atomic reservation, CAS state machine, DB `CHECK` |
| **Policy engine** | **REAL IMPLEMENTATION** | 11 hard constraints, versioned |
| **Arbitration** | **REAL IMPLEMENTATION** | deterministic, single-writer |
| **AI model** | **REAL IMPLEMENTATION** | CatBoost, trained, calibrated, versioned |
| **Attribution** | **REAL IMPLEMENTATION** | timeline rules, self-cure exclusion |
| **Experiment + statistics** | **REAL IMPLEMENTATION** | 5 arms, 40 seeds, real CIs |
| **Audit trail** | **REAL IMPLEMENTATION** | `decision_record`, `decision_trace` |

**The rule**: everything *outside* the engine's boundary is simulated; everything the project claims as a contribution is really built. That split is exactly what makes the demo honest, and it costs nothing.

---

# 6. DATABASE STACK

**SQLite. Nothing else.**

```python
conn = sqlite3.connect("recovery.db", isolation_level=None)   # explicit transactions
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA foreign_keys=ON")
conn.execute("PRAGMA busy_timeout=5000")
# every reservation: conn.execute("BEGIN IMMEDIATE")
```

Does SQLite cover the safety requirements?

| Requirement | SQLite mechanism |
|---|---|
| Atomic contact reservation | `BEGIN IMMEDIATE` + `UPDATE … WHERE reserved_count + consumed_count < cap` |
| Contact budget invariant | `CHECK (reserved_count + consumed_count <= cap)` — enforced by the engine, not by code |
| Transactions | full ACID, WAL |
| Tenant isolation | composite PKs on `(merchant_id, …)` + a data-access layer that rejects unscoped SQL |
| Ledger / audit | append-only tables, `UNIQUE (merchant_id, idempotency_key)` |
| Idempotent transitions | CAS via `UPDATE … WHERE status = 'reserved'`, rowcount decides |
| Event log | `events` table, `UNIQUE(source_event_id)` |

> **Redis is NOT required for the MVP.** SQLite alone implements atomic contact reservations, the contact budget, transactions, tenant isolation, and the ledger. Adding Redis would introduce a second source of truth for the exact state the project's central safety claim depends on — strictly worse, not better.

> **PostgreSQL is not required either.** It is the correct V2 choice (row-level security, partitioned arbitration) and the schema is written to port cleanly, but installing a server for a single-writer prototype is cost without benefit. Say this out loud in the README rather than apologising for SQLite.

**Concurrency caveat, stated honestly**: the 100-worker test demonstrates correctness under contention in one process against one file. It is not evidence about distributed deployment, and the submission must not imply it is.

---

# 7. BACKEND STACK

```
Python 3.11+
stdlib: sqlite3 · dataclasses · enum · hashlib · json · uuid · threading · pathlib
```

**No web framework is required for the engine.** The experiment runner calls the engine in-process; there is no external caller. FastAPI earns its place for exactly one reason:

```python
# app/api.py — the entire optional API surface
@app.post("/downtime/events")
def downtime_event(ev: DowntimeEvent):
    return ingest_downtime(ev)      # idempotent on downtime_id
```

Being able to `curl` a real webhook on camera and watch 40 retry recommendations get suppressed is worth 30 lines and one install. It is optional; a Python function call proves the same thing less vividly.

**Pydantic**: optional. Frozen dataclasses cover the domain model, and the money type must be `int` paise regardless. Use Pydantic only if you add the FastAPI endpoint, where it comes along anyway.

**SQLAlchemy: do not use.** The ledger's correctness is in exact SQL and exact transaction boundaries. An ORM hides the layer that must stay visible, and every reviewer question about the T0 race is answered by pointing at one `UPDATE` statement.

---

# 8. AI / ML STACK

`pandas` · `NumPy` · `scikit-learn` · `CatBoost` · `SciPy` · `Matplotlib` — **sufficient for all of it**, with no paid platform:

| Need | Tool |
|---|---|
| Feature engineering | pandas + stdlib (point-in-time assertions are hand-written; that is the point) |
| Heuristic baseline | plain Python — it must be readable, that is its job |
| Linear/additive baseline | `sklearn.linear_model.LogisticRegression` |
| Model scorer | `catboost.CatBoostClassifier` (S-learner: action as a feature) |
| Calibration | `sklearn.calibration.calibration_curve`, `CalibratedClassifierCV` |
| Brier score | `sklearn.metrics.brier_score_loss` |
| Confidence intervals | `scipy.stats.t.interval` (paired), `scipy.stats.bootstrap` (BCa) |
| Statistical tests | `scipy.stats.wilcoxon`, `ttest_rel`, `mannwhitneyu`; McNemar via `statsmodels` *or* a 12-line exact binomial |
| Splits | `sklearn.model_selection.GroupKFold` for customer-grouped, time-ordered splits |
| Plots | Matplotlib — reliability curve, per-seed paired differences |

**No LLM.** Nothing in the frozen architecture puts one on the decision path; message drafting is templated. This removes an API key, a cost, a rate limit, and a failure mode.

**statsmodels**: one extra package for McNemar. Either install it or write the exact binomial test yourself — the latter is ~12 lines and one less dependency. Either is fine.

---

# 9. AGENT / ORCHESTRATION STACK

**Plain Python classes and a state machine. No framework.**

```python
class RecoveryAgent(Protocol):
    stream: str
    def propose(self, ctx: OpportunityContext) -> list[Proposal]: ...

class SubscriptionAgent:   ...
class PaymentFailureAgent: ...
class ReminderAgent:       ...
class AbandonedCartAgent:  ...
```

Each agent emits **scored proposals with no side effects**. Arbitration is a deterministic function over proposals. That is the entire orchestration layer.

> **LangChain, LangGraph, AutoGen, CrewAI, and the OpenAI Agents SDK: do not use them.**

Three reasons, in order of weight:

1. **The frozen architecture forbids what they are for.** Arbitration must be deterministic and auditable (`p0.1` Part 15: *"Arbitration — NO, must not be an agent"*). A framework whose value is LLM-driven control flow is being used against its purpose.
2. **They would obscure the contribution.** The recovery intelligence is action-conditional prediction + `NO_ACTION` + estimated incremental effect + expected value + feedback. None of that is an LLM orchestration problem.
3. **"Where is the AI?" gets a worse answer.** *"Stage 2 action selection, a calibrated CatBoost model comparing five actions against NO_ACTION"* beats *"we used an agent framework"* in every room, and especially in a room containing engineers.

**Do not use an LLM to make the project look like AI.** The architecture must remain explainable, and an evaluator asking *"why did the engine do this?"* must get an answer read from a database row, not generated.

---

# 10. EXPERIMENT STACK

```
Python · NumPy · pandas · SciPy · pytest   — sufficient. joblib optional.
```

**Is parallel execution necessary? No.** Rough budget: 5 arms × 40 seeds × 600 opportunities = 120,000 decisions. A CatBoost prediction on a small feature vector is microseconds; the dominant cost is SQLite writes. Expect **single-digit minutes serial** on a laptop.

Parallelism is a convenience, not a requirement — and it carries a real risk: parallel seeds sharing one SQLite file will contend on the write lock and, if implemented carelessly, break the reproducibility hash. If you do parallelise:

```python
from joblib import Parallel, delayed
Parallel(n_jobs=4)(delayed(run_seed)(s, db_path=f"runs/seed_{s}.db") for s in seeds)
# one DB file per seed; merge for analysis. Never share a writer.
```

Run serial first. Parallelise only if a full run exceeds ~10 minutes and it is costing you iterations.

**Everything else is pandas + SciPy**: paired differences per seed, t-interval, Wilcoxon, bootstrap for relative lift, Holm correction over the secondary family, McNemar for paired proportions. All free, all local, all in one script that regenerates every number in the submission.

---

# 11. TESTING STACK

```
pytest        — everything
Hypothesis    — property tests where a random seed must never break an invariant
pytest-cov    — optional; point it at ledger/, policy/, arbitration/ only
```

| Test | Tool | Mechanism |
|---|---|---|
| Atomic contact reservation | pytest + `ThreadPoolExecutor` | 2/10/100 workers, same and distinct keys |
| Budget invariant under arbitrary interleavings | Hypothesis | fuzz op sequences; assert `reserved + consumed ≤ cap` |
| Tenant isolation | pytest | same email at two merchants; assert independence |
| Feature leakage | pytest, marked `leakage` | `build_features` raises; CI gate |
| Retry ownership | pytest | static call-graph assertion, `EXECUTE_RETRY` absent |
| Outage suppression | pytest | 40 failures one issuer → suppressed → batched |
| `NO_ACTION` | pytest | scored on every decision; 7 triggers |
| Self-cure attribution | pytest | payment before delivery → `SELF_CURED` |
| Execution unknown | pytest | three ladder outcomes; send count stays 1 |
| Exploration safety | **Hypothesis** | 2,000 seeds × 6 constraints; no seed produces an ineligible action |
| Falsification (4 nulls) | pytest, slow marker | equal effects · shuffled features · NO_ACTION dominates · permuted labels |

> **Locust is not needed.** It generates HTTP load. The concurrency risk here is *database write contention inside one process* — `ThreadPoolExecutor` hitting `reserve_contact_budget()` directly tests the actual hazard. HTTP load testing would test uvicorn, which is not the thing that can be wrong.

```
pytest -m "not slow"     # fast loop during the build
pytest -m leakage        # CI gate, blocks merge
pytest                   # everything, before the freeze
```

---

# 12. FRONTEND STACK

**Streamlit. Not React, not Next, not Vite, not Tailwind, not Node.**

```bash
streamlit run app/dashboard.py
```

Why: the UI must demonstrate one flow —

```
payment failure → validation → diagnosis → AI recommendation → policy
    → arbitration → contact ledger → execution → recovery → attribution
```

— which is one page reading `decision_trace`. In Streamlit that is roughly 150 lines of Python, no build step, no `package.json`, no second language, and it queries the same SQLite file the engine writes.

**A React/Vite/Tailwind stack for one screen is the single biggest unnecessary dependency available to this project.** It would add Node, npm, a bundler, a dev server, a CORS story, and an API layer that otherwise need not exist — days of work that produce no evidence.

Screen order, built in this sequence:

1. **"Why did the engine do this?"** — one opportunity, the full trace (candidates, `p̂`, `Δ̂`, EV, policy result, arbitration, reservation, outcome, attribution, provenance). *Build this first; ship nothing else until it works.*
2. Results table — 5 arms, primary metric with CI, guardrails.
3. Contact savings, phantom-risk filtering, agent collisions, downtime suppressions, model versions.

If Streamlit somehow fails you, the fallback is a Jinja2 template rendered to static HTML by the eval run — still no Node.

**Do not build a production dashboard.**

---

# 13. DEPLOYMENT OPTIONS

**Recommendation: deploy nothing. Run locally, record the demo.** Cloud deployment adds accounts, limits, cold starts, and a failure mode on demo day, in exchange for nothing an evaluator needs.

Verified free-tier facts, current as of **2026-08-31**:

### GitHub Actions — **RECOMMENDED**
```
Current as of        2026-08-31
Free tier exists     YES — unlimited minutes on PUBLIC repositories
Private repos        2,000 Linux minutes/month + 500 MB artifacts on the Free plan
Credit card          NO
Hard limits          none for public repos
Risk of cost         none if the repo is public
Recommended          YES — run tests + the leakage gate on every push
```

### GitHub (repo hosting) — **REQUIRED**
```
Free tier exists     YES     Credit card  NO     Risk  none     Recommended  YES
```

### Streamlit Community Cloud — **OPTIONAL**
```
Current as of        2026-08-31
Free tier exists     YES — unlimited public apps, 1 private app
Resources            ~1 GB memory; throttles or fails past the limit
Sleep behavior       apps sleep after 12 hours without traffic
Credit card          NO
Risk of cost         none
Recommended          OPTIONAL — a shareable link for judges, if the run DB is small
                     enough to commit. Local + recorded video is safer.
```

### Render — **NOT RECOMMENDED here**
```
Current as of        2026-08-31
Free tier exists     YES — 750 instance hours/month; static sites unlimited
Sleep behavior       web services spin down after 15 min idle; 30-60s cold start
Database             free Postgres is 256 MB and EXPIRES AFTER 30 DAYS
Credit card          NO for web services
Risk of cost         low, but the expiring database is a silent demo-killer
Recommended          NO — we use SQLite, and a 60s cold start during a 5-minute demo
                     is an unforced error
```

### Railway — **DO NOT USE**
```
Current as of        2026-08-31
Free tier exists     NO — the free tier was removed in July 2023
What exists          one-time $5 trial credit, expiring at $5 spent or 30 days;
                     a $1/month "Free" plan; $5/month Hobby
Credit card          YES — required at signup since August 2023
Risk of cost         REAL
Recommended          NO
```

### Vercel / Cloudflare / Supabase / Neon — **NOT EVALUATED, NOT NEEDED**
There is no frontend to host (Streamlit runs locally) and no database to host (SQLite is a file). Not verified, because not recommended. **If any uncertainty exists about a service's free tier, run locally instead** — which is the recommendation regardless.

---

# 14. TOOLS WE EXPLICITLY DO NOT NEED

| Category | Rejected | One-line reason |
|---|---|---|
| Database server | PostgreSQL, MySQL | SQLite `BEGIN IMMEDIATE` is the frozen prototype path |
| Cache / KV | **Redis** | **Not required for the MVP** — SQLite does atomic reservation |
| Containers | Docker, Compose | Nothing to containerise |
| Queue | Kafka, RabbitMQ, Redis Streams, SQS, Pub/Sub | **OVERKILL** — an events table is the log |
| Frontend runtime | Node, React, Next, Vite, Tailwind | **OVERKILL** for one screen |
| Agent frameworks | LangChain, LangGraph, AutoGen, CrewAI, Agents SDK | Arbitration must be deterministic |
| LLM APIs | any | No LLM on the decision path |
| ML platforms | MLflow, W&B, Vertex, SageMaker, Azure ML | **No paid ML platform is required** — see §16 |
| Observability | Prometheus, Grafana, OTel, Datadog, New Relic | JSON logs + SQLite tables suffice |
| Load testing | Locust | Wrong hazard; use threads |
| Secrets | Vault, AWS/GCP Secret Manager | `.env` + `.env.example`, and there are no real secrets |
| ORM / migrations | SQLAlchemy, Alembic | The SQL must stay visible |
| Paid CI | CircleCI, Travis paid tiers | GitHub Actions is free on public repos |

**Classification for §7 of the brief:**

```
FastAPI + one webhook endpoint    OPTIONAL   (recommended for demo vividness)
Database-backed event log         REQUIRED
Python async tasks                OPTIONAL   (synchronous is fine at this scale)
Kafka / RabbitMQ / Redis Streams  OVERKILL
SQS / Pub/Sub                     OVERKILL
```

### Model storage

```
models/
  v1.cbm
  v1.meta.json      { model_version, artifact_hash, features_version,
                      trained_on_seeds, metrics{auc,brier,slope}, promoted_at }
  v2.cbm
  v2.meta.json
```
plus a `model_registry` table and a git tag per promotion.

> **No paid ML platform is required.** MLflow would add a server and a UI to track four artefacts. The JSON + git-tag approach is auditable, diffable, reviewable in a pull request, and costs nothing.

### Secret management

`.env` (git-ignored) + `.env.example` (committed) is sufficient. There are **no production credentials in this project at all** — the payment provider, message delivery and downtime feed are simulated. Vault-class tooling would be protecting nothing.

---

# 15. EXACT INSTALLATION CHECKLIST

Windows 11. Roughly 20 minutes end to end.

```
Step 1  — Install Git and VS Code
          winget install --id Git.Git -e
          winget install --id Microsoft.VisualStudioCode -e

Step 2  — Install Python 3.11+
          winget install --id Python.Python.3.12 -e
          python --version        # verify 3.11 or newer

Step 3  — Create the repo and virtual environment
          mkdir unified-recovery-engine && cd unified-recovery-engine
          git init
          python -m venv .venv
          .venv\Scripts\activate          # PowerShell
          # source .venv/Scripts/activate # Git Bash

Step 4  — Install Python packages
          pip install --upgrade pip
          pip install numpy pandas scipy scikit-learn catboost matplotlib \
                      pytest hypothesis streamlit
          pip install fastapi uvicorn pytest-cov ruff faker   # optional
          pip freeze > requirements.txt

Step 5  — Node.js                    SKIPPED — not required
Step 6  — Docker                     SKIPPED — not required
Step 7  — PostgreSQL                 SKIPPED — not required

Step 8  — Initialise the database
          python -m app.db.init        # creates recovery.db, WAL, schema, CHECKs

Step 9  — Generate synthetic data
          python -m app.simulation.generate --seed 1 --reference-timestamp 2026-01-01T00:00:00Z

Step 10 — Train the heuristic baseline (tune on seeds 1-10)
          python -m app.scoring.tune_heuristic --seeds 1-10

Step 11 — Train CatBoost v1
          python -m app.models.train --version v1 --seeds 1-10

Step 12 — Run the API                 [optional]
          uvicorn app.api:app --reload --port 8000

Step 13 — Run the dashboard
          streamlit run app/dashboard.py

Step 14 — Run tests
          pytest -m "not slow"
          pytest -m leakage
          pytest

Step 15 — Run experiments
          python -m app.evaluation.run --arms A1,A2ns,A2,A3,A5 --seeds 21-60
          python -m app.evaluation.analyse --out results/
```

Everything above is free. Nothing requires an account except GitHub.

---

# 16. REPOSITORY STRUCTURE

```
unified-recovery-engine/
├── app/
│   ├── db/                  init.py, schema.sql, dal.py  ← TenantScopedDB, the ONLY query path
│   ├── domain/              models.py (dataclasses), enums.py, money.py (int paise)
│   ├── ingestion/           events.py (dedup on source_event_id)
│   ├── identity/            resolve.py (merchant-scoped, confidence-thresholded)
│   ├── validation/          objective/ (TDS, matching)  probabilistic/ (confidence-gated)
│   ├── diagnosis/           classify.py, correlate.py
│   ├── downtime/            consumer.py   ← separate module, not inside diagnosis
│   ├── candidates/          generate.py   ← NO_ACTION always included
│   ├── scoring/             base.py, heuristic.py, model.py   ← no DB write, no credentials
│   ├── policy/              hard_filter.py, triggers.py (SAFETY vs VALUE), versions/
│   ├── arbitration/         arbitrate.py  ← deterministic, single serialized section
│   ├── ledger/              reservation.py, transitions.py  ← ONLY writer of budget tables
│   ├── actions/             executor.py, provider.py  ← ONLY holder of send credentials
│   ├── agents/              subscription.py, payment_failure.py, reminder.py, cart.py
│   ├── attribution/         classify.py (timeline rules)
│   ├── models/              train.py, registry.py, features.py (as_of enforced)
│   ├── evaluation/          run.py, analyse.py, stats.py, falsification.py
│   ├── simulation/          generate.py, response.py (git-tagged), provider_sim.py
│   ├── data/                base.py, synthetic_adapter.py, external/
│   ├── audit/               trace.py
│   ├── api.py               [optional] POST /downtime/events
│   └── dashboard.py         Streamlit
├── tests/                   test_ledger.py, test_exploration_safety.py, test_leakage.py,
│                            test_tenant.py, test_attribution.py, test_falsification.py, ...
├── models/                  v1.cbm, v1.meta.json, ...
├── results/                 report.json, plots/, traces/
├── docs/                    DATASET_RESEARCH.md, EXPERIMENT_METHODOLOGY.md
├── strategy/                STRATEGY.md, full_plan.md, TOOLCHAIN.md
├── experiments/             preregistration.json  ← git-tagged before the first eval run
├── .github/workflows/ci.yml
├── .env.example
├── Makefile                 setup · generate · train · eval · demo · test
├── requirements.txt
└── README.md
```

---

# 17. ARCHITECTURE-TO-TOOL MAPPING

| Architecture component | Tool | Module |
|---|---|---|
| Contact ledger, atomic reservation | stdlib `sqlite3`, `BEGIN IMMEDIATE`, CHECK | `app/ledger/` |
| Reservation state machine | Python enum + CAS SQL | `app/ledger/transitions.py` |
| Tenant isolation | composite PKs + `TenantScopedDB` | `app/db/dal.py` |
| Stage 0 validation | plain Python + rate table | `app/validation/` |
| Stage 1 diagnosis | plain Python | `app/diagnosis/` |
| Downtime consumption | FastAPI endpoint (optional) + poll fallback | `app/downtime/` |
| Candidate generation | plain Python | `app/candidates/` |
| Heuristic scorer | plain Python | `app/scoring/heuristic.py` |
| Model scorer | CatBoost + scikit-learn calibration | `app/scoring/model.py` |
| Policy engine | plain Python, versioned config | `app/policy/` |
| Arbitration | deterministic function + one transaction | `app/arbitration/` |
| Agents | Python classes (no framework) | `app/agents/` |
| Payment provider | Python stub | `app/simulation/provider_sim.py` |
| Attribution | pandas + timeline rules | `app/attribution/` |
| Experiment runner | Python + NumPy | `app/evaluation/run.py` |
| Statistics | SciPy | `app/evaluation/stats.py` |
| Feedback loop | CatBoost + JSON registry + git tag | `app/models/` |
| Audit trail | SQLite `decision_record` + `decision_trace` view | `app/audit/` |
| Dashboard | Streamlit | `app/dashboard.py` |
| Tests | pytest + Hypothesis | `tests/` |
| CI | GitHub Actions | `.github/workflows/ci.yml` |

---

# 18. 10-DAY ₹0 IMPLEMENTATION ROADMAP

**Day 1 — Foundation**
- **Build**: repo, venv, SQLite schema with CHECK constraints, dataclasses, integer-paise money type, `FixedClock`, `TenantScopedDB`. Write and **git-tag the response function**. Do the NPCI/Samadhaan licence check.
- **Tools**: Python, sqlite3, pytest, Git
- **Tests**: schema applies on WAL; tenant cannot read across merchants; no wall-clock calls outside the clock adapter
- **Output**: `recovery.db`, `tag: response-function-frozen`

**Day 2 — Contact safety core** *(hard gate)*
- **Build**: `reserve_contact_budget`, single `transition()`, six-state machine, `consumption_basis`, expiry
- **Tools**: sqlite3, pytest, Hypothesis, `ThreadPoolExecutor`
- **Tests**: cap binds after executions · same key → one slot · 7 invalid transitions rejected · 2/10/100 workers · Hypothesis fuzz
- **Output**: **all green, or stop and fix before anything else**

**Day 3 — Simulator + experiment skeleton**
- **Build**: seeded generator with content hash, calibration config, provider stub (5 outcomes), reconciliation ladder, experiment runner end-to-end on an empty engine
- **Tools**: NumPy, pandas, pytest
- **Tests**: same seed → same hash across processes and days · ambiguous send resolves three ways · never re-sent
- **Output**: `make eval` produces a report shape

**Day 4 — Stage 0 + Stage 1 + attribution**
- **Build**: five Stage 0 verdicts, diagnosis taxonomy, timeline attribution rules
- **Tools**: Python, pandas, pytest
- **Tests**: payment before delivery → `SELF_CURED` · TDS → `PHANTOM_RISK`, zero contacts · attribution window boundaries
- **Output**: phantom-risk report, split deterministic/probabilistic

**Day 5 — Candidates + policy + heuristic**
- **Build**: candidate generation with `NO_ACTION`, 11 hard constraints, SAFETY/VALUE trigger split, heuristic scorer tuned on seeds 1–10
- **Tools**: Python, pytest, Hypothesis
- **Tests**: policy-blocked candidate reserves nothing · exploration cannot bypass policy (2,000 seeds × 6 constraints)
- **Output**: heuristic frozen; `A1`, `A2ns`, `A2` runnable

**Day 6 — Agents, arbitration, model v1**
- **Build**: four agent classes, deterministic arbitration, CatBoost v1 (S-learner), calibration check
- **Tools**: CatBoost, scikit-learn, pytest
- **Tests**: two agents → one contact with trace · Brier improved, slope ∈ [0.85, 1.15]
- **Output**: `models/v1.cbm` + metadata; `A3`, `A5` runnable

**Day 7 — Abstention, downtime, disagreement**
- **Build**: 7 abstention triggers, downtime suppression wiring, AI-vs-heuristic comparison over the complete population
- **Tools**: pandas, pytest
- **Tests**: each trigger fires with its reason · 40 failures one issuer suppressed · disagreement table is not sampled
- **Output**: real disagreement rate + breakdown by failure reason, amount band, ageing bucket

**Day 8 — Full experiment**
- **Build**: 5 arms × 40 seeds, paired analysis, CIs, Holm, MDE from a 5-seed pilot, four falsification runs
- **Tools**: NumPy, SciPy, pandas, Matplotlib
- **Tests**: identical `input_hash` and `world_hash` across arms · null conditions show no uplift
- **Output**: `results/report.json` — every number in the submission

**Day 9 — Dashboard + feedback loop**
- **Build**: the trace screen first, then the results table; v1 → outcomes → v2 → promotion gate → rollback
- **Tools**: Streamlit, CatBoost
- **Tests**: trace answers all six questions, renders without an LLM · holdout locked until promotion decided · bad model rejected
- **Output**: `streamlit run` shows a real decision end to end

**Day 10 — Freeze**
- **Build**: README, claim-language scan, demo recording, tag
- **Tools**: Git, GitHub Actions
- **Tests**: full suite green · forbidden-phrase scan clean · `make eval` reproduces every number from seeds alone
- **Output**: submitted repo + 5-minute video

---

# 19. 5-DAY EMERGENCY ROADMAP

### If 10 days becomes 7 — cut
```
Criteo estimator validation · feedback loop (describe the design, run the v1→v2 script only)
dashboard beyond the trace screen · the 4th agent · Stage 0 probabilistic checks
```

### If 7 becomes 5
```
Day 1  schema + ledger + concurrency tests            (never cut)
Day 2  generator + provider + attribution             (never cut)
Day 3  Stage 0 deterministic + policy + candidates + heuristic
Day 4  CatBoost + arbitration + 2 agents + abstention
Day 5  experiment (A1 / A3 / A5, 20 seeds) + trace screen + demo
```
Dropped: `A2ns` and `A2` arms (keep A1, A3, A5 — the unified lift and the AI contribution), the feedback loop, downtime suppression, falsification tests 3–4.

### If only 3 days remain — the absolute minimum

The core loop must survive intact:

```
failure → validation → diagnosis → AI decision → NO_ACTION comparison
        → policy → contact budget → execution → outcome → attribution
```

```
Day 1  SQLite schema + ledger with atomic reservation + the 100-worker test
       + generator (one stream: failed payments only)
Day 2  Stage 0 (deterministic only) + diagnosis + candidates incl. NO_ACTION
       + policy hard filter + heuristic + CatBoost + arbitration + attribution
Day 3  Two arms (A1 vs A5), 20 seeds, CI on the primary metric
       + the trace screen + record the demo
```

Non-negotiable even here: the contact budget must actually bind under concurrency, `NO_ACTION` must be scored, self-cure must be excluded, and the number must carry a confidence interval. A prototype with two arms and honest statistics beats five arms with none.

---

# 20. CRITICAL PATH

```
Day 1  →  database + domain + response function frozen
Day 2  →  contact safety core          ← HARD GATE: everything downstream is void without it
Day 3  →  simulator + experiment skeleton   ← defines "correct" before building to it
Day 4  →  Stage 0 / Stage 1 / attribution
Day 5  →  candidates + policy + heuristic
Day 6  →  agents + arbitration + AI
Day 7  →  abstention + downtime + disagreement
Day 8  →  full experiment + statistics
Day 9  →  dashboard + feedback
Day 10 →  freeze + demo
```

Two ordering rules that differ from the obvious sequence, both inherited from the frozen plan:

1. **Safety before AI.** The ledger is day 2, the model is day 6. A model producing decisions an unsafe ledger executes proves nothing.
2. **The experiment runner before the features it measures.** Day 3 runs the harness on an empty engine. Defining what "correct" looks like first is what stops the eval harness from becoming the thing that runs out of time — the failure mode in 7 of 8 sampled competitor repos.

---

# 21. DEFINITION OF DONE

Done when all three lists are green — not when features stop being addable.

**Engine (14 stop conditions, `full_plan.md` §11)**: Stage 0 removes phantoms · AI ranks actions · AI sometimes differs from the heuristic · AI can abstain · policy can override AI · agents cannot exceed budgets · duplicates prevented · downtime suppresses retries · ambiguous execution reconciles · self-cure not attributed · incremental recovery measured · outcomes feed the loop · real data calibrates · claims scoped.

**Methodology (22 acceptance criteria, `STRATEGY.md`)**: exploration cannot bypass safety/budget/tenancy/outage · model probability distinguished from causal effect · `NO_ACTION` first-class · point-in-time executable and CI-gated · disagreement measured on the full population · A5 vs A3 on frozen experiments · retry ownership outside the engine · `EXECUTION_UNKNOWN` safe · provenance preserved · datasets used only for supported claims · Criteo separated · DGP documented · falsification tests exist · dashboard from real outputs · no hardcoded numbers · claims scoped.

**Reproducibility**: `make setup && make eval` regenerates every number in the submission from the seed list alone, on a fresh clone, with no account and no key.

---

# 22. RAZORPAY FEASIBILITY VERDICT

**Is this roadmap realistically buildable by a student?**
Yes — with the four substitutions in §1. As briefed (Postgres + Docker + React + Redis) it is *not* comfortably buildable in 10 days by one person: roughly two days would go to infrastructure that produces no evidence. With SQLite + Streamlit + no containers, the 10-day plan has genuine slack, and the 5-day emergency path is real rather than aspirational.

**Does it require paid infrastructure?**
No. ₹0, and not "₹0 until a free tier changes" — ₹0 because nothing leaves the laptop. The only accounts are GitHub (free) and optionally Streamlit Community Cloud (free, verified).

**Are we overengineering anything?**
Three things, all now cut: PostgreSQL + Docker for a single-writer prototype; a Node frontend for one screen; and the queue/observability tier, where the frozen architecture's needs are met by a table and a log line.

**Which technology is the biggest unnecessary dependency?**
**The Node/React toolchain.** It brings a second language runtime, a build system, an API layer, and a CORS story to render a page that Streamlit renders in ~150 lines of the language the engine is already written in. Second place: PostgreSQL, which additionally drags in Docker.

**What can be demonstrated entirely locally?**
All of it. The engine, the 100-worker concurrency proof, the five arms with confidence intervals, the falsification suite, the feedback loop, the trace screen, and the webhook beat via a local `POST`.

**What should be shown in the final demo?**
Five beats, five minutes: (1) ₹50,000 failure → validate → diagnose → AI ranks five actions including `NO_ACTION` → policy → arbitration → reservation → sent → paid → attributed. (2) High self-cure → **AI chooses `NO_ACTION`** — the strongest single moment. (3) Two agents compete → one contact, with the suppression trace. (4) Outage → retry recommendations suppressed → batched on resolution. (5) Timeout → `EXECUTION_UNKNOWN` → reconciliation. Close with the results table, CIs, and what it does not prove.

**What evidence should exist before submission?**
A green test suite including the concurrency and leakage gates; `results/report.json` regenerable from seeds alone; the four falsification runs reported *including* where the advantage disappears; `experiments/preregistration.json` git-tagged before the first eval run; the `response-function-frozen` tag preceding both scorers; and a README whose claims are scoped to the evidence — every synthetic number carrying *"under the synthetic data-generating process."*

---

## Sources

- [Railway — Pricing Plans (docs)](https://docs.railway.com/pricing/plans) · [Railway pricing history](https://www.saaspricepulse.com/blog/railway-pricing-history)
- [Render — platforms with a real free tier (2026)](https://render.com/articles/platforms-with-a-real-free-tier-for-developers-in-2026) · [Render free-tier guide](https://dashdashhard.com/posts/ultimate-guide-to-renders-free-tier/)
- [Streamlit — Community Cloud status and limitations](https://docs.streamlit.io/deploy/streamlit-community-cloud/status) · [resource limits](https://docs.streamlit.io/knowledge-base/deploy/resource-limits)
- [GitHub Actions pricing update (changelog, Dec 2025)](https://github.blog/changelog/2025-12-16-coming-soon-simpler-pricing-and-a-better-experience-for-github-actions/) · [GitHub Actions free tier explained (2026)](https://cicdcalculator.com/github-actions-free-tier)
