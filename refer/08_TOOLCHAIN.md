# 08 — TOOLCHAIN

Approved stack. Consolidated from `strategy/TOOLCHAIN.md` (free-tier facts verified 2026-08-31).

**Total cost: ₹0** — not "free tier" but "nothing leaves the laptop".

---

## Approved stack

| Tool | Purpose | Mandatory |
|---|---|---|
| Python 3.11+ | everything | **YES** |
| `sqlite3` (stdlib) | database, ledger, audit, events | **YES** |
| `dataclasses`, `enum` (stdlib) | domain model | **YES** |
| NumPy | RNG substreams, numerics | **YES** |
| pandas | experiment analysis | **YES** |
| SciPy | t-intervals, Wilcoxon, bootstrap, McNemar | **YES** |
| scikit-learn | calibration, Brier, splits | **YES** |
| CatBoost | the model scorer (A5) | **YES** |
| Matplotlib | reliability curves, plots | **YES** |
| pytest | all tests | **YES** |
| Hypothesis | property tests (budget invariant, exploration safety) | **YES** |
| Streamlit | the trace screen | **YES** |
| Git · GitHub · VS Code | version control, submission, editing | **YES** |
| FastAPI + uvicorn | one endpoint: `POST /downtime/events` | optional, recommended |
| pytest-cov · ruff · Faker · statsmodels | coverage, lint, data realism, McNemar | optional |
| GitHub Actions | CI (free, unlimited on public repos) | optional, recommended |

**No Node. No Docker. No database server. No message queue. No LLM API key. No ML platform. No cloud account.**

---

## DO NOT ADD WITHOUT AN ADR

These are not forbidden forever. They require an explicit architectural decision with a recorded rationale, because each was already considered and rejected for stated reasons.

| Tool | Rejected in | Reason |
|---|---|---|
| **PostgreSQL** | ADR-0002 | SQLite `BEGIN IMMEDIATE` is the frozen prototype path; a server buys nothing at this scale |
| **Redis** | ADR-0002 | SQLite does atomic reservation; Redis would create a second source of truth for the exact state the safety claim depends on |
| **Docker / Compose** | ADR-0002 | nothing to containerise once the DB is a file |
| **Kubernetes** | — | not remotely applicable to a single-laptop prototype |
| **Kafka / RabbitMQ / Redis Streams / SQS / Pub-Sub** | ADR-0002 | an events table with a unique constraint is the event log |
| **LangChain / LangGraph / AutoGen / CrewAI / Agents SDK** | ADR-0007 | arbitration must be deterministic; a framework for LLM control flow works against its purpose |
| **Any LLM API** | ADR-0007 | no LLM sits on the decision path; message drafting is templated |
| **MLflow / W&B / Vertex / SageMaker / Azure ML** | ADR-0008 | `models/vN.cbm` + JSON + git tag is the registry |
| **React / Next / Vite / Tailwind / Node** | ADR-0010 | a second language runtime and build chain for one screen |
| **Prometheus / Grafana / OTel / Datadog / New Relic** | ADR-0002 | JSON logs + SQLite tables + one Streamlit page |
| **Locust** | ADR-0002 | wrong hazard — contention is in-process, tested with threads |
| **SQLAlchemy / Alembic** | ADR-0002 | the ledger's correctness is in exact SQL; an ORM hides the layer that must stay visible |
| **Vault / cloud secret managers** | — | there are no production credentials in this project |
| **Production payment integrations** | ADR-0006 | no production credentials; the provider is simulated |

**If a future agent believes one of these is now necessary**: stop, write the ADR, get explicit approval, then implement. Do not add infrastructure because it "would be better".

---

## Deployment

**Recommendation: deploy nothing.** Run locally, record the demo.

Verified 2026-08-31:

| Service | Free tier | Card | Verdict |
|---|---|---|---|
| **GitHub Actions** | unlimited minutes on **public** repos; 2,000 min/mo private | NO | **recommended** |
| **GitHub** | yes | NO | **required** (submission) |
| **Streamlit Community Cloud** | unlimited public apps, ~1 GB, sleeps after 12h idle | NO | optional |
| **Render** | 750 instance-hrs; **free Postgres expires after 30 days**; 15-min spin-down, 30–60s cold start | NO | **not recommended** — cold start during a 5-min demo is an unforced error |
| **Railway** | **NO free tier** — removed July 2023; $5 one-time trial, **card required** since Aug 2023 | YES | **do not use** |
| Vercel / Cloudflare / Supabase / Neon | not evaluated | — | not needed — no frontend to host, no DB to host |

**If any uncertainty exists about a service's free tier, run locally instead.**

## Environment

```
Python 3.11+ · Windows 11 (dev machine) · SQLite WAL · no containers
pip install numpy pandas scipy scikit-learn catboost matplotlib pytest hypothesis streamlit
pip install fastapi uvicorn pytest-cov ruff faker      # optional
```

Pin everything with `pip freeze > requirements.txt` and commit it. A reviewer's failed install is a failed submission — they will not debug it.
