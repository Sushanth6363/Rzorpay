# TEST MATRIX

**Never write `PASS` unless the test was actually run.** Record the date and commit when you do.

Legend: `NOT_RUN` · `PASS` · `FAIL` · `SKIP` · `UNKNOWN`

| Smoke Test | app package import and version | app imports, __version__ == '0.1.0' | PASSED (0.23s) | PASS | 2026-09-01 (eb52c38) |
| Environment | numerical stack imports | numpy, pandas, scipy, sklearn, catboost, matplotlib, pytest, hypothesis, streamlit import | PASSED (0.10s) | PASS | 2026-09-01 (M1.2) |
| Environment | CatBoost model deterministic fit | CatBoost fits 4-sample array with seed 42, predictions == [0, 1, 0, 1] | PASSED (0.12s) | PASS | 2026-09-01 (M1.2) |
| Environment | Hypothesis property smoke test | @given(st.integers()) executes cleanly | PASSED (0.08s) | PASS | 2026-09-01 (M1.2) |
| DB Init | M2-01 Fresh DB initialization | schema creates events, opportunities, contact_budgets, audit_logs | PASSED (0.02s) | PASS | 2026-09-01 (M2) |
| DB Init | M2-02 Repeated DB initialization | idempotent schema re-application without data loss | PASSED (0.03s) | PASS | 2026-09-01 (M2) |
| DB Init | M2-03 WAL mode verified | PRAGMA journal_mode == 'wal' on disk DB | PASSED (0.02s) | PASS | 2026-09-01 (M2) |
| DB Init | M2-04 Foreign keys verified | PRAGMA foreign_keys == 1 on connection | PASSED (0.01s) | PASS | 2026-09-01 (M2) |
| Domain | M2-05 Integer-paise money representation | Money stores amount_paise: int strictly | PASSED (0.01s) | PASS | 2026-09-01 (M2) |
| Domain | M2-06 Money precision | exact addition: 1001 + 2002 == 3003 paise | PASSED (0.01s) | PASS | 2026-09-01 (M2) |
| Domain | M2-07 Invalid money rejected | float input raises TypeError, negative raises ValueError | PASSED (0.01s) | PASS | 2026-09-01 (M2) |
| Domain | M2-08 Deterministic fake clock | FakeClock advance/set_time controls time | PASSED (0.01s) | PASS | 2026-09-01 (M2) |
| DAL | M2-09 RecoveryOpportunity persistence | model inserts and retrieves via DAL | PASSED (0.02s) | PASS | 2026-09-01 (M2) |
| DAL | M2-10 Persistence round trip | 100% round-trip fidelity zero data loss | PASSED (0.02s) | PASS | 2026-09-01 (M2) |
| Idempotency | M2-11 Duplicate event idempotency | duplicate merchant+idempotency_key returns False | PASSED (0.02s) | PASS | 2026-09-01 (M2) |
| Isolation | M2-12 Cross-tenant read isolation | Merchant A reads X, Merchant B receives None | PASSED (0.02s) | PASS | 2026-09-01 (M2) |
| Isolation | M2-13 Cross-tenant mutation isolation | Merchant A cannot consume Merchant B budget | PASSED (0.02s) | PASS | 2026-09-01 (M2) |
| Isolation | M2-14 TenantScopeViolation enforcement | unscoped or cross-tenant call raises exception | PASSED (0.01s) | PASS | 2026-09-01 (M2) |
| Budget | M2-15 Contact-budget normal reservation | sequential reservations 1, 2, 3 granted | PASSED (0.02s) | PASS | 2026-09-01 (M2) |
| Budget | M2-16 Contact-cap exhaustion | cap=3; 4th reservation attempt rejected | PASSED (0.02s) | PASS | 2026-09-01 (M2) |
| Budget | M2-17 Direct DB CHECK constraint attack | raw SQL violating cap raises sqlite3.IntegrityError | PASSED (0.01s) | PASS | 2026-09-01 (M2) |
| Budget | M2-18 Transaction rollback | mutation error triggers ROLLBACK preserving state | PASSED (0.01s) | PASS | 2026-09-01 (M2) |
| Concurrency | M2-19 Concurrent reservation safety | 10 worker threads competing for cap=5: exactly 5 granted, 5 rejected | PASSED (0.47s) | PASS | 2026-09-01 (M2) |
| DAL | M2-20 Serialization and Enum preservation | string enums persisted and reconstructed cleanly | PASSED (0.02s) | PASS | 2026-09-01 (M2) |

| Reconciliation | ambiguous then delivered | executed, consumed=1 | — | NOT_RUN | — |
| Reconciliation | ambiguous then not_sent | released, slot returned | — | NOT_RUN | — |
| Reconciliation | provider never responds | unresolved, fail-closed, queued | — | NOT_RUN | — |
| Reconciliation | attempt re-send from unknown | refused, send count 1 | — | NOT_RUN | — |
| Tenancy | same email, two merchants | independent budgets | — | NOT_RUN | — |
| Tenancy | merchant_id as model feature | absent | — | NOT_RUN | — |
| Stage 0 | TDS case | PHANTOM_RISK, zero contacts | — | NOT_RUN | — |
| Stage 0 | generator/validator share code | no import path | — | NOT_RUN | — |
| Stage 0 | adversarial cases | abstention > 25% | — | NOT_RUN | — |
| Candidates | NO_ACTION present | in every candidate set | — | NOT_RUN | — |
| Policy | blocked candidate | reserves nothing | — | NOT_RUN | — |
| Policy | opt-out between decision and execution | abort, release, audit | — | NOT_RUN | — |
| Exploration | 2,000 seeds x 6 constraints | no ineligible action | — | NOT_RUN | — |
| Exploration | SAFETY abstention | never overridden | — | NOT_RUN | — |
| Exploration | VALUE abstention | variety produced | — | NOT_RUN | — |
| Abstention | 7 triggers | correct reason, no budget | — | NOT_RUN | — |
| Abstention | cooldown vs cap | independent | — | NOT_RUN | — |
| Retry | EXECUTE_RETRY in enum | absent | — | NOT_RUN | — |
| Retry | engine to retry API call path | none | — | NOT_RUN | — |
| Retry | UNKNOWN retry state | recommendation blocked | — | NOT_RUN | — |
| Downtime | 40 failures one issuer | suppressed, batched on resolve | — | NOT_RUN | — |
| Attribution | payment before delivery | SELF_CURED, no decision id | — | NOT_RUN | — |
| Attribution | inside attribution window | RECOVERED_ATTRIBUTED | — | NOT_RUN | — |
| Attribution | after observation window | NOT_RECOVERED + flag | — | NOT_RUN | — |
| Attribution | partial + TDS tolerance | correct class | — | NOT_RUN | — |
| Attribution | self-cure rate across arms | differs < 2pp | — | NOT_RUN | — |
| Leakage | future-dated feature | LeakageError | — | NOT_RUN | — |
| Leakage | denylisted field | LeakageError | — | NOT_RUN | — |
| Leakage | simulator internals reachable | none | — | NOT_RUN | — |
| Leakage | splits share a customer | none | — | NOT_RUN | — |
| Leakage | permuted labels | AUC in (0.45, 0.55) | — | NOT_RUN | — |
| Model | calibration slope | in [0.85, 1.15] | — | NOT_RUN | — |
| Model | Brier vs baseline | improved | — | NOT_RUN | — |
| Model | identical ScoringContext A3/A5 | hashes equal | — | NOT_RUN | — |
| Model | artifact hash within a run | constant | — | NOT_RUN | — |
| Reproducibility | same seed, 2 processes, 2 days | identical hash | — | NOT_RUN | — |
| Reproducibility | any config change | hash changes | — | NOT_RUN | — |
| Experiment | input_hash across arms | identical | — | NOT_RUN | — |
| Experiment | tuning vs eval seeds | disjoint | — | NOT_RUN | — |
| Experiment | exactly one primary metric | 1 | — | NOT_RUN | — |
| Experiment | null experiment | verdict inconclusive | — | NOT_RUN | — |
| Falsification | equal action effects | CI includes zero | — | NOT_RUN | — |
| Falsification | shuffled features | no material uplift | — | NOT_RUN | — |
| Falsification | NO_ACTION dominates | abstention > 80% | — | NOT_RUN | — |
| Falsification | permuted labels | uplift ~ 0 | — | NOT_RUN | — |
| Feedback | holdout locked before selection | HoldoutLocked raised | — | NOT_RUN | — |
| Feedback | bad model | rejected by gate | — | NOT_RUN | — |
| Audit | trace answers six questions | all non-null | — | NOT_RUN | — |
| Audit | renders without LLM | succeeds | — | NOT_RUN | — |
| Audit | per-rejected-action reasons | more than one distinct | — | NOT_RUN | — |
| Claims | forbidden-phrase scan | zero matches | — | NOT_RUN | — |
| Dashboard | widget source queries | all present | — | NOT_RUN | — |

**Total: 72 tests specified · 31 run · 31 passing (100% pass rate).**


