# ADR INDEX

Every significant decision is recorded as an ADR. **An ADR is mandatory before** changing: the database · the model · exploration behaviour · experiment design · a safety invariant · attribution logic · a dataset · the architecture · an API contract · or adding an external service.

`ADR-0001-template.md` is the template. Real decisions are numbered from **0002**.

> **On the documents these ADRs cite.** Several record where a decision came from, naming
> working files like `p0.1-technical-correction.md`, `p0.2-closure.md`, `final.md` or a
> path under `research/`. Those were correction passes and pre-build research, not part of
> the product, and they were removed from the tree to keep a clone readable. They remain in
> git history: `git log --all --diff-filter=D --name-only` finds them, and any commit before
> the removal has them in full. The citations are left as written because they are accurate
> about where each decision was made.

| ADR | Title | Status | Date | Affects |
|---|---|---|---|---|
| [0001](ADR-0001-template.md) | *(template — not a decision)* | — | — | — |
| [0002](ADR-0002-sqlite-over-postgres.md) | SQLite over PostgreSQL; no Redis, no Docker | ACCEPTED | 2026-08-31 | database, ledger, deployment |
| [0003](ADR-0003-atomic-reservation-semantics.md) | Atomic reservation and `reserved + consumed` cap semantics | ACCEPTED | 2026-08-30 | ledger, INV-2 |
| [0004](ADR-0004-safety-constrained-exploration.md) | Safety-constrained exploration; SAFETY vs VALUE triggers | ACCEPTED | 2026-08-31 | policy, scoring, INV-3 |
| [0005](ADR-0005-s-learner-incremental-effect.md) | S-learner for incremental effect; model estimate ≠ causal claim | ACCEPTED | 2026-08-31 | AI/ML, experiment |
| [0006](ADR-0006-retry-ownership.md) | Retry ownership stays outside the engine | ACCEPTED | 2026-08-30 | actions, policy, INV-5 |
| [0007](ADR-0007-no-agent-framework.md) | No agent framework; no LLM on the decision path | ACCEPTED | 2026-08-31 | architecture, toolchain |
| [0008](ADR-0008-file-based-model-registry.md) | File-based model registry instead of an ML platform | ACCEPTED | 2026-08-31 | AI/ML, toolchain |
| [0009](ADR-0009-external-data-calibration-only.md) | External data for calibration only | ACCEPTED | 2026-08-31 | data, claims |
| [0010](ADR-0010-streamlit-over-react.md) | Streamlit over a Node frontend | ACCEPTED | 2026-08-31 | frontend, toolchain |
| [0011](ADR-0011-five-arms-and-primary-metric.md) | Five experiment arms; primary metric = incremental recovery rate | ACCEPTED | 2026-08-31 | experiment, claims |
| [0012](ADR-0012-adapter-boundary-and-canonical-event.md) | Provider-neutral adapter boundary & `CanonicalEvent` contract (Razorpay Test Mode + Simulator) | ACCEPTED | 2026-09-01 | ingestion, adapters, domain |
| 0013 | *(withdrawn — never written; superseded before it existed)* | WITHDRAWN | 2026-09-05 | — |
| 0014 | *(withdrawn — never written; partly superseded, partly never built)* | WITHDRAWN | 2026-09-05 | — |
| [0015](ADR-0015-compliant-escalation-ladder.md) | Compliant escalation: one rung, on evidence, after a quiet period | ACCEPTED | 2026-09-03 | policy, actions, pipeline, audit |
| [0016](ADR-0016-tds-derivation-over-declared-flag.md) | TDS position derived from the invoice, never read off a flag | ACCEPTED | 2026-09-03 | Stage 0, attribution, money reporting |
| [0017](ADR-0017-train-on-logged-outcomes.md) | S-learner trains on the engine's own logged outcomes | ACCEPTED | 2026-09-03 | AI/ML, experiment |
| [0018](ADR-0018-realtime-webhook-ingestion.md) | Real-time webhook ingestion: durable, idempotent, fail-closed | ACCEPTED | 2026-09-04 | ingestion, security, downtime |
| [0019](ADR-0019-production-reliability.md) | Retry, dead-letter, reconciliation sweep, replay guard | ACCEPTED | 2026-09-04 | reliability, observability, PII |
| [0020](ADR-0020-context-dependent-dgp.md) | Context-dependent sandbox outcome model (prediction falsified) | ACCEPTED | 2026-09-04 | experiment, claims |
| [0021](ADR-0021-dynamic-followup-timing.md) | Follow-up timing derived from diagnosis, channel and attempt | ACCEPTED | 2026-09-05 | recovery workflow, contact policy |
| [0022](ADR-0022-unrecovered-handoff-report.md) | The unrecovered handoff report is a first-class output | ACCEPTED | 2026-09-05 | reporting, claims, operations |
| [0023](ADR-0023-durable-case-and-payment-resolution.md) | A durable case, and payment always wins | ACCEPTED | 2026-09-05 | domain, persistence, dispatch, payments |
| [0024](ADR-0024-html-email-rendering.md) | HTML email built for mail clients, not for browsers | ACCEPTED | 2026-09-05 | dispatch, deliverability |
| [0025](ADR-0025-merchant-csv-without-a-reason-column.md) | Merchant CSV carries no reason column; nothing is silently dropped | ACCEPTED | 2026-09-05 | ingestion, domain, claims |
| [0026](ADR-0026-thin-agent-loop.md) | The agent loop is thin, and runs the evaluated engine | ACCEPTED | 2026-09-05 | architecture, claims, experiment integrity |
| [0027](ADR-0027-case-board-reports-delivery-not-readership.md) | The case board reports delivery and payment, never readership | ACCEPTED | 2026-09-05 | UI, claims, operations |

## Open decisions


| # | Question | Blocking | Owner |
|---|---|---|---|
| OD-1 | *Closed 2026-09-05.* Deadline believed to be 2026-09-05 — that is today. Third-party sources only; Razorpay never published it. Treat the build as submittable now rather than waiting for confirmation. | nothing | human |
| OD-2 | NPCI / MSME Samadhaan licence terms | calibration source; fallback defined and active | human |
| OD-3 | Razorpay Payment Downtime API access (support-request gated) | D2 realism; live path built, simulator fallback active | human |

## Withdrawn

Three ADR numbers were listed as `PROPOSED` in this index on 2026-09-01 with links to files
that were never written. Rather than back-fill documents for decisions that were not made as
described, the numbers are retired here. **0012 was the exception** — its decision was real,
implemented, and cited by a code docstring, so the document was written on 2026-09-05.

| # | Was to cover | Disposition |
|---|---|---|
| 0013 | Webhook HMAC verification, idempotency, tenant mapping | **Superseded before it was written.** The subject was decided and recorded in full in [ADR-0018](ADR-0018-realtime-webhook-ingestion.md) (fail-closed HMAC SHA256, idempotency on the Razorpay event id, explicit event mapping) and [ADR-0019](ADR-0019-production-reliability.md) (replay guard, pseudonymous customer keys). Nothing is undocumented; only the number is dead. |
| 0014 | Streamlit public demo & judge sandbox with Live, Sandbox and **Red-Team** modes | **Partly superseded, partly never built.** The Streamlit-over-Node decision is [ADR-0010](ADR-0010-streamlit-over-react.md); the dashboard rebuild is recorded there. Red-team mode **was never built** — see `01_PROJECT_STATE.md` §Not built. Writing this ADR would have documented a feature that does not exist. |

## Superseded

None yet.

