# 01 — PROJECT STATE

**Last full verification**: 2026-09-05, by direct repository inspection and execution.
**Verification method**: `git log` → 33 commits, HEAD `e803e36`, clean tree · `find app -name "*.py"` → 62 modules, 10,530 lines · `.venv/Scripts/python.exe -m pytest -q` → **255 passed in 9s** · `scripts/verify_environment.py` → **QUALITY GATE PASSED** (6/6) · `scripts/run_evaluation.py --events 200 --seeds 21-40` → reproduced batch hash `0837b24cbe3992a6…` and primary A2−A1 = −0.0148 (p=0.1846) identical to the committed report.

> **This file was wrong for four days.** Until 2026-09-05 it stated that no component had been
> implemented and that the repository had zero commits, while 33 commits and 255 passing tests
> sat beside it. Treat any status document here as evidence, never as truth: `git log` plus an
> executed suite is the only authority. See `progress/BUILD_LOG.md` for the correction entry.

## Status vocabulary

`PLANNED` · `IN_PROGRESS` · `IMPLEMENTED` · `TESTED` · `VERIFIED` · `BLOCKED` · `DEPRECATED` · `REJECTED` · `UNKNOWN`

Vague phrases — "mostly done", "basically working", "should work", "probably implemented" — are forbidden in this file. If a status cannot be established, write `UNKNOWN — REQUIRES VERIFICATION`.

`VERIFIED` here means: the code exists, its tests exist, and the suite was executed on the date
recorded at the top of this file.

---

## Summary

| Status | Count |
|---|---|
| `VERIFIED` | **26** |
| `IMPLEMENTED` (no dedicated test) | 2 |
| `NOT_BUILT` (planned, never built — see §Not built) | 2 |
| `BLOCKED` | 2 |
| `REJECTED` | 4 |

**Every component on the critical path is implemented, tested and executed.** Two planned
features were never built and are recorded as such rather than quietly dropped.

---

## Components

### Foundation

**Repository skeleton** · `VERIFIED`
- Location: `requirements.txt`, `pytest.ini`, `Makefile`, `scripts/bootstrap.py`, `.env.example`
- Tests: `tests/test_smoke.py` (1), `tests/test_environment.py` (3)
- Notes: `.venv` on Python 3.12.9; `make setup` bootstraps a supported interpreter. Python 3.14 is unsupported — the pinned scientific stack has no wheels for it.

**Database schema (SQLite)** · `VERIFIED`
- Location: `app/db/schema.sql`, `app/db/init.py`
- Tests: `tests/db/test_init.py` (4)
- Notes: WAL mode, foreign keys on, `CHECK (reserved_count + consumed_count <= cap)` enforced at the schema level and proven by raw-SQL attack test. Single-process by design (ADR-0002).

**Domain model** · `VERIFIED`
- Location: `app/domain/models.py` (816), `enums.py` (232), `money.py` (129), `app/clock.py`
- Tests: `tests/domain/test_money.py` (8), `tests/domain/test_clock.py` (2)
- Notes: integer paise only, UTC, injectable clock, `merchant_id` on every tenant-scoped entity.

### Safety core

**Contact ledger / atomic reservation** · `VERIFIED` — *the highest-value component in the project*
- Location: `app/ledger/engine.py`, `app/db/dal.py` (626)
- Tests: `tests/ledger/` (25 across 8 files) incl. `test_ledger_concurrency.py` (10 workers, cap 5 → exactly 5 granted) and `test_ledger_hypothesis.py` (arbitrary interleavings preserve the cap)
- Notes: `BEGIN IMMEDIATE` + CAS; six states, eight legal transitions, all others rejected. Correctness scoped to single-process SQLite; **not distributed**. ADR-0003.

**Reservation state machine** · `VERIFIED`
- Tests: `tests/ledger/test_execution_transitions.py` (7), `test_reconciliation.py` (3)
- Notes: `EXECUTION_UNKNOWN` holds the slot until the reconciliation ladder resolves it; `RECONCILED_UNRESOLVED` consumes the slot conservatively (commit `829a8ac` documents why).

**Policy engine (hard filter)** · `VERIFIED`
- Location: `app/pipeline/safety_filter.py`
- Tests: `tests/pipeline/test_candidate_generation.py` (7), `tests/scoring/test_exploration.py` (4)
- Notes: eligibility decided **once**, before scoring; a `SAFETY_REJECTED` candidate can never become eligible and is unreachable by exploration (INV-3, ADR-0004).

**Tenant isolation** · `VERIFIED`
- Location: `app/db/dal.py` (`TenantScopedDB`)
- Tests: `tests/db/test_tenant_isolation.py` (3), `tests/scoring/test_multi_tenant.py` (2)
- Notes: unscoped or cross-tenant access raises `TenantScopeViolation`; `merchant_id` excluded from the feature vector (INV-1).

**Cross-stream arbitration** · `VERIFIED` — **but read the note**
- Location: `app/orchestration/recovery_orchestrator.py:185-195`; `app/experiment/policies.py`
- Tests: demonstrated experimentally by the A1 vs A2ns arm contrast, not by a unit test
- **The arbitration mechanism is the shared contact budget itself, not a separate arbitrator.** There is no `app/arbitration/` module, no agent-proposal objects, and no "12 competing agents". Streams contend for one atomic per-customer slot and the cap decides; that *is* the arbitration. The measured effect is in `results/RESULTS.md` — A1 (no shared ledger) spends 1,500 contacts at 22.73 per customer, A2ns (shared ledger) spends 1,347 at 20.41, for statistically indistinguishable recovery. Earlier drafts of `00_START_HERE.md` and `09_IMPLEMENTATION_ROADMAP.md` M9 described a competing-agent arbitrator; that was never built and the claim has been removed.

### Recovery pipeline

**Stage 0 — Validate** · `VERIFIED`
- Location: `app/pipeline/stage0.py`
- Tests: `tests/pipeline/test_stage0_validation.py` (8), `test_opportunity_construction.py` (3)
- Notes: a gate, not a report — a phantom opportunity is closed without contact. Deterministic and probabilistic verdicts reported separately.

**Stage 1 — Diagnose** · `VERIFIED`
- Location: `app/pipeline/stage1.py` · Tests: `tests/pipeline/test_stage1_diagnosis.py` (3)

**Candidate generation** · `VERIFIED`
- Location: `app/pipeline/candidate_generator.py` · `NO_ACTION` is candidate #1 in every set, always.

**Compliant escalation ladder** · `VERIFIED`
- Location: `app/pipeline/escalation.py` (317) · Tests: `tests/pipeline/test_escalation.py` (15)
- Notes: `EMAIL_LINK → SMS_LINK → WHATSAPP_LINK → IVR_CALL → AGENT_DIAL`. One rung at a time, only on a CONFIRMED prior contact, only after the quiet period, never past the ceiling. A value control layered **under** safety — it can only remove a candidate, never revive a rejected one. ADR-0015.

**TDS derivation** · `VERIFIED`
- Location: `app/pipeline/tds.py` (297) · Tests: `tests/pipeline/test_tds_derivation.py` (14)
- Notes: withholding derived from the invoice's own facts (section, payee constitution, PAN, amount remitted), never read off a flag. The engine declines to chase a shortfall the payer already remitted to the exchequer. ADR-0016.

**Downtime consumer** · `VERIFIED`
- Location: `app/pipeline/downtime.py`, `app/realtime/downtime_live.py`
- Notes: separate module, not inside diagnosis. Live path consumes `payment.downtime.*` (provenance `REAL_DATA`); the lookup fails **safe** (reports healthy) rather than raising inside the decision path. INV-4.

**Action executor** · `VERIFIED`
- Location: `app/dispatch/channels.py` (228), `app/dispatch/copy.py`, `app/integrations/razorpay_client.py`
- Notes: sole holder of send credentials; **no retry capability by design** — the engine recommends retries and never executes payments (ADR-0006, INV-5). Dispatch is OFF unless `RECOVERY_DISPATCH_ENABLED`, and refuses `rzp_live_` credentials unless `RECOVERY_ALLOW_LIVE_CREDENTIALS` is separately set.

**Attribution** · `VERIFIED`
- Location: `app/attribution/attribution_engine.py` (208) · Tests: `tests/attribution/test_attribution.py` (2)
- Notes: self-cure receives strictly ₹0 attributed recovery (INV-8), separated from intervention-driven recovery everywhere it is reported.

### AI / ML

**Heuristic scorer** · `VERIFIED` — `app/scoring/heuristic.py`; a flat readable table, deliberately. Left unchanged by ADR-0020.
**CatBoost S-learner** · `VERIFIED` — `app/scoring/s_learner.py`; action as a feature (ADR-0005). Tests: `tests/scoring/test_s_learner.py` (4).
**Feature builder (point-in-time)** · `VERIFIED` — `app/scoring/feature_builder.py`; `observed_at <= decision_timestamp` enforced, raises `PointInTimeLeakageError`. Tests: `tests/scoring/test_leakage_safety.py` (3), `pytest -m leakage`.
**EV calculator** · `VERIFIED` — `app/scoring/ev_calculator.py`, `costs.py`; integer paise. Tests: `tests/scoring/test_ev_calculator.py` (4).
**Model registry** · `VERIFIED` — `app/scoring/registry.py`; `models/*.cbm` + `*.meta.json`, no MLflow (ADR-0008).
**Training source** · `VERIFIED` — `app/scoring/logged_dataset.py`; the S-learner trains on the engine's **own** logged outcomes, not a mismatched synthetic table (ADR-0017, commit `90b4edd`).
**Exploration** · `VERIFIED` — `app/scoring/exploration.py`; ε=0.05 over eligible candidates only. No seed on the live path (ADR-0018 §7).
**Feedback loop** · `VERIFIED` — `app/experiment/feedback_loop.py`. Tests: `tests/experiment/test_feedback_loop.py` (2).

### Simulation / experiment

**Sandbox simulator** · `VERIFIED` — `app/sandbox/simulator.py`, `outcome_model.py`. Tests: `tests/sandbox/test_simulator.py` (3).
**Outcome model (DGP)** · `VERIFIED` — `app/sandbox/outcome_model.py`; diagnosis × channel interaction plus an amount effect, base channel rates identical to the context-free model so the old world is a strict special case. ADR-0020.
**Batch generator** · `VERIFIED` — `app/experiment/batch.py`; seeded, content-hashed, four streams mixed.
**Golden scenarios** · `VERIFIED` — `app/sandbox/scenarios.py` (12 demo scenarios) + `app/pipeline/scenarios.py` (S001–S010). Tests: 12 + 12 + 10 + 1 across `tests/orchestration/`, `tests/experiment/`, `tests/scoring/`, `tests/pipeline/`.
**Experiment runner** · `VERIFIED` — `app/experiment/runner.py` (375); 6 arms, identical batch per arm asserted by content hash, Newcombe CIs, Holm-Bonferroni. Tests: `tests/experiment/test_runner.py` (3), `test_assignment.py` (4).
**Arm policies** · `VERIFIED` — `app/experiment/policies.py`; CONTROL, A1, A2ns, A2, A3, A5 (ADR-0011).

### Real-time path

**Webhook ingestion** · `VERIFIED` — `app/api/webhook_listener.py` (492), `app/realtime/ingest.py` (307), `event_mapper.py`, `config.py`. Tests: `tests/realtime/test_webhook_ingestion.py` (25).
- Notes: HMAC SHA256 verification **fails closed** — absent configuration is a 401, not a skip. Idempotent on Razorpay's event id. Explicit event mapping, never a family prefix (`payment.captured` is a success, not a failure). Fast acknowledge, then process. One durable WAL database shared with the UI, thread-local connections. ADR-0018.
- **Known limitation, disclosed**: `subscription.*` events are unavailable on the demo Razorpay account, so live traffic reaches **3 of the 4 streams**. The fourth is exercised only in batch evaluation.

**Production reliability** · `VERIFIED` — `app/realtime/reliability.py` (279). Tests: `tests/realtime/test_reliability.py` (12).
- Notes: bounded retry, dead-letter queue, reconciliation sweep, replay guard. Retries re-enter the same idempotent path keyed on the same intervention key, so a retry cannot double-contact. ADR-0019.

**Follow-up on silence** · `VERIFIED` — `app/realtime/followup.py` (262). Tests: `tests/realtime/test_followup.py` (17).
- Notes: delay derived from failure reason and action taken; a follow-up enters as a **new** opportunity so the escalation ladder governs it, rather than colliding with the original's idempotency key and silently sending nothing.

### Interface & reporting

**Streamlit judge dashboard** · `VERIFIED` — `app/ui/dashboard.py` (789); five tabs (Trace, Experiment, Live Test, Safety, About). Tests: `tests/ui/` (10). Safety checks are **executed** and report real PASS/FAIL — a green tick not backed by a live check is forbidden. ADR-0010.
**Unrecovered handoff report** · `VERIFIED` — `app/reporting/unrecovered.py` (300); Excel report for every case the engine could not recover. Tests: `tests/reporting/test_unrecovered.py` (11).
**Judge CSV dispatch harness** · `VERIFIED` — `app/dispatch/csv_runner.py` (341); really sends email/SMS/WhatsApp/IVR when explicitly enabled.
**Evaluation reporting** · `VERIFIED` — `scripts/run_evaluation.py` → `results/report.json` + `results/RESULTS.md`, stamped with commit and dirty-tree state.

---

## Not built (planned, then not delivered — recorded, not dropped)

**Red-team mode** · `NOT_BUILT`
- Planned in `09_IMPLEMENTATION_ROADMAP.md` M13 as `app/ui/red_team.py` with nine attack cards returning verified PASS/FAIL.
- Reality: no `red_team` module exists; `grep -ri red.team app/` returns nothing. The Safety tab does execute live invariant checks, which covers part of the intent. The "Red-Team mode" phrasing has been removed from `00_START_HERE.md`.

**Competing-agent arbitrator** · `NOT_BUILT`
- Planned in M9 as `app/arbitration/arbitrate.py` plus `app/agents/*.py` with 12 simulated agent recommendations contending for one slot.
- Reality: arbitration is the shared contact budget (see Safety core above). The cross-stream effect is real and measured; the agent-proposal layer was never written.

**`refer/integrations/RAZORPAY_TEST_MODE.md`** · `NOT_BUILT` — the M1.2 capability matrix was never written as a standalone document. What it was to contain is now split across ADR-0012 (the `CanonicalEvent` contract) and ADR-0018 (verified webhook behaviour, including which events the demo account does not deliver).

## Blocked

**NPCI issuer failure rates** · `BLOCKED` — licence terms unverified (page returned HTTP 403 to automated fetch). Fallback active: published ranges from secondary sources, cited inline, nothing redistributed.
**MSME Samadhaan ageing** · `BLOCKED` — same reason, same fallback.

Neither blocks the build. Both are calibration-only inputs (ADR-0009).

## Rejected (do not reintroduce without an ADR)

**PostgreSQL / Redis / Docker** · ADR-0002 · **Agent frameworks (LangChain, LangGraph, AutoGen, CrewAI)** · ADR-0007 · **LLM on the decision path** · ADR-0007 · **React / Next / Vite / Node** · ADR-0010

---

## Tests

**255 passed, 0 failed, 9.0s** — executed 2026-09-05 at `e803e36`. Per-file counts are in `testing/TEST_MATRIX.md`. Breakdown: 161 tests carried from M1–M8 plus 94 added after (escalation 15, TDS 14, webhook ingestion 25, reliability 12, follow-up 17, unrecovered reporting 11).

Quality gate: `scripts/verify_environment.py` → 6/6 checks pass, including zero hardcoded secrets.

## Experiments

**One evaluation is current and reproducible.** `results/report.json` + `results/RESULTS.md`, regenerated 2026-09-05 at `e803e36` on a clean tree: 200 events × 20 seeds (21–40) = 4,000 opportunities per arm, batch content hash `0837b24cbe3992a6…`.

- Primary (pre-registered) A2−A1 = **−0.0148**, 95% CI [−0.0365, 0.0070], p=0.1846 → **INCONCLUSIVE**.
- A5−A3 = **+0.0005** → **INCONCLUSIVE**. ADR-0020's pre-registered prediction P1 (the model beats the heuristic) is **FALSIFIED** and reported as such.
- The finding that survived: the two scorers differ on 4 of 1,000 decisions; `WHATSAPP_LINK`, `IVR_CALL` and `AGENT_DIAL` are never chosen at all, because compliant escalation caps intensity. **Policy has already made the decision 99.6% of the time.**
- Contact efficiency is where the engine earns its keep: comparable recovery for materially fewer contacts (A1 22.73 contacts/customer → A2 20.24).

Every figure is a property of an authored simulation. No claim of real-world Razorpay recovery uplift is made or supported.

## Known open items requiring verification

| Item | Status |
|---|---|
| Submission deadline | Third-party sources said 2026-09-05, which is **today**. Razorpay never published it. Treat the build as submittable now. |
| NPCI / Samadhaan licence terms | Open; fallback active, does not block |
| Razorpay Payment Downtime API access | Support-request gated. Live downtime consumption is implemented and works when the account delivers the events; simulator fallback otherwise. Declare on camera which path is running. |
| Razorpay retry-state interface | Assumed, never verified. Engine therefore only *recommends* retries (ADR-0006). |

