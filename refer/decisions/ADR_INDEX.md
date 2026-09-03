# ADR INDEX

Every significant decision is recorded as an ADR. **An ADR is mandatory before** changing: the database · the model · exploration behaviour · experiment design · a safety invariant · attribution logic · a dataset · the architecture · an API contract · or adding an external service.

`ADR-0001-template.md` is the template. Real decisions are numbered from **0002**.

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
| [0012](ADR-0012-adapter-boundary-and-canonical-event.md) | Provider-neutral adapter boundary & `CanonicalEvent` contract (Razorpay Test Mode + Simulator) | PROPOSED | 2026-09-01 | ingestion, adapters, domain |
| [0013](ADR-0013-webhook-verification-and-idempotency.md) | Webhook HMAC SHA256 verification, idempotency, and tenant mapping | PROPOSED | 2026-09-01 | webhooks, security, ledger |
| [0014](ADR-0014-streamlit-judge-sandbox-architecture.md) | Streamlit Public Live Demo & Judge Interactive Sandbox (Live, Sandbox, Red-Team modes) | PROPOSED | 2026-09-01 | UI, judge sandbox, deployment |
| [0015](ADR-0015-compliant-escalation-ladder.md) | Compliant escalation: one rung, on evidence, after a quiet period | ACCEPTED | 2026-09-03 | policy, actions, pipeline, audit |
| [0016](ADR-0016-tds-derivation-over-declared-flag.md) | TDS position derived from the invoice, never read off a flag | ACCEPTED | 2026-09-03 | Stage 0, attribution, money reporting |

## Open decisions


| # | Question | Blocking | Owner |
|---|---|---|---|
| OD-1 | Actual submission deadline (third-party sources say 2026-09-05; unpublished by Razorpay) | which roadmap applies | human |
| OD-2 | NPCI / MSME Samadhaan licence terms | calibration source; fallback defined | human |
| OD-3 | Razorpay Payment Downtime API access (support-request gated) | D2 realism; simulate if denied | human |

## Superseded

None yet.
