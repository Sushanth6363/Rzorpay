# CURRENT STATUS — Unified Recovery Engine

**Last Updated**: 2026-09-05
**Verified at**: commit `e803e36`, clean tree
**Current Milestone**: post-M9 hardening complete; documentation reconciled

---

## Verified state, by execution

| Check | Command | Result |
|---|---|---|
| Test suite | `.venv/Scripts/python.exe -m pytest -q` | **255 passed, 0 failed, 9.0s** |
| Quality gate | `.venv/Scripts/python.exe scripts/verify_environment.py` | **PASSED** — 6/6, zero hardcoded secrets |
| Evaluation | `scripts/run_evaluation.py --events 200 --seeds 21-40` | reproduced batch hash `0837b24cbe3992a6…`, primary A2−A1 = −0.0148 (p=0.1846) |
| Code | `find app -name "*.py"` | 62 modules, 10,530 lines |
| Tests | `find tests -name "*.py"` | 46 files, 5,287 lines |

---

## Completed Milestones

- [x] **M1.1** Repository & reproducibility foundation
- [x] **M1.2** Environment alignment & quality gates *(the `RAZORPAY_TEST_MODE.md` capability matrix was never written as a standalone doc — its content lives in ADR-0012 and ADR-0018)*
- [x] **M2** Domain model + database schema + SQLite WAL persistence
- [x] **M3** Atomic contact ledger & reconciliation engine
- [x] **M4** Recovery pipeline & candidate generators
- [x] **M5** AI recovery decision engine (CatBoost S-learner, EV ranking)
- [x] **M6** Sandbox execution, outcome & attribution loop
- [x] **M7** Experimentation, incremental recovery measurement & feedback loop
- [x] **M8** Judge-ready end-to-end demonstration, reproducibility & validation
- [x] **M9** Final validation, judge UX, deployment & submission readiness

At M9 the suite stood at **161 tests**. Everything below landed after M9 and adds the remaining **94**.

## Post-M9 work (2026-09-03 → 2026-09-04)

Sixteen commits landed after M9 was declared complete. They were not recorded as milestones at the time; this table is that record. Test counts sum to the 94 that took the suite from 161 to 255.

| Commit | Work | Tests added | ADR |
|---|---|---:|---|
| `03d9f5c` | Differentiate experiment arms, `make eval`, fix simulator RNG | — | — |
| `600f6ad` | Rebuild judge dashboard — readable trace, live safety checks, real theme | — | ADR-0010 |
| `22b37e6` | Contact efficiency metric — the axis the engine is actually for | — | — |
| `995ba53` | Close the four Track 3 spec gaps: money metrics, stream coverage, escalation, TDS | 29 | ADR-0015, ADR-0016 |
| `280f96c` | Close the `.venv` trap; lead the README with the honest framing | — | — |
| `3a1738a` / `b881f7b` | Real-time Razorpay API & webhook integration; Streamlit Cloud entrypoint | — | — |
| `90b4edd` | Train the S-learner on the engine's own outcomes, not a mismatched table | — | ADR-0017 |
| `8a280f9` / `acbe951` | Durable, idempotent, fail-closed webhook ingestion; consume downtime & resolution webhooks | 25 | ADR-0018 |
| `8a81586` | Context-dependent outcome model — **pre-registered prediction P1 FALSIFIED** | — | ADR-0020 |
| `7d59873` | Production reliability: retry, dead-letter, reconciliation sweep, replay guard | 12 | ADR-0019 |
| `6f785ff` | Record ADR-0017 through ADR-0020 | — | — |
| `0afa01a` | Judge CSV harness that really sends email/SMS/WhatsApp/IVR | — | — |
| `03e99e9` | Act on silence; delay derived from failure reason and action | 17 | — |
| `e803e36` | Excel handoff report for every case the engine could not recover | 11 | — |

## What is NOT built

Recorded in `01_PROJECT_STATE.md` §Not built rather than left for a reviewer to discover:

- **Red-team mode** — planned as `app/ui/red_team.py` with nine attack cards. Does not exist. The Safety tab does execute live invariant checks.
- **Competing-agent arbitrator** — planned as `app/arbitration/` with 12 simulated agents. Does not exist. Arbitration is the shared atomic contact budget; the cross-stream effect is real and measured via the A1 vs A2ns arm contrast.

## Honest headline

Under the simulator the model does **not** beat the transparent heuristic (A5−A3 = +0.0005, inconclusive), and the primary comparison is **INCONCLUSIVE** (A2−A1 = −0.0148). Both are reported rather than tuned away. The engine's demonstrated value is contact efficiency and compliant escalation: comparable recovery for materially fewer customer contacts. ADR-0020 records why — policy bounds the action space so tightly that the scorer is nearly irrelevant, measured at 99.6% of decisions.
