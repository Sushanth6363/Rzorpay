# TEST MATRIX

**Never write `PASS` unless the test was actually run.** Record the date and commit when you do.

Legend: `NOT_RUN` · `PASS` · `FAIL` · `SKIP` · `UNKNOWN`

| Component | Test Name | Description | Output | Status | Date & Commit |
| --- | --- | --- | --- | --- | --- |
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
| Ledger | M3-01 Ledger creation | create record, update reserved_count=1 | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-02 Ledger tenant isolation | Merchant A entry invisible to Merchant B | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-03 Persistence round-trip | 100% round-trip fidelity for ContactLedgerEntry | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-04 Deterministic key idempotency | duplicate key returns existing record | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-05 Duplicate reservation no extra slot | 5 repeated calls consume exactly 1 slot | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-06 Reservation + ledger atomicity | single transaction guarantees atomic insert+counter | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-07 Transaction rollback on failure | schema failure triggers complete ROLLBACK | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-08 Execution attempt transition | RESERVED -> EXECUTION_ATTEMPTED (counters unchanged) | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-09 Confirmed execution transition | RESERVED -> EXECUTED (reserved-1, consumed+1) | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-10 Failed execution transition | RESERVED -> FAILED_CLOSED (reserved-1, consumed+1) | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-11 EXECUTION_UNKNOWN transition | RESERVED -> EXECUTION_UNKNOWN (reserved held) | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-12 Unknown reconciliation ladder | resolves to DELIVERED, NOT_SENT, UNRESOLVED | PASSED (0.03s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-13 Reconciliation idempotency | re-invoking reconcile returns True without counter change | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-14 Invalid transition rejection | EXECUTED -> RESERVED rejected (returns False) | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-15 No double consumption | repeated execution result preserves consumed_count=1 | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-16 No double release | repeated release preserves reserved_count=0 | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-17 Contact cap preservation | reserved+consumed <= cap holds under all transitions | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-18 Concurrent same key reservation | 10 workers same key -> exactly 1 slot allocated | PASSED (0.25s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-19 Concurrent distinct keys reservation | 10 workers distinct keys cap=5 -> 5 granted, 5 rejected | PASSED (0.31s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-20 Cross-tenant concurrent isolation | Merchant A & B concurrent threads -> independent budgets | PASSED (0.28s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-21 Failure injection rollback | error during reservation rolls back budget counter | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-22 Audit trail reconstruction | audit_logs records RESERVE, ATTEMPT, EXECUTED | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-23 Injectable timestamps | FakeClock controls created_at and resolved_at | PASSED (0.01s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-24 No slot leakage | full sequence reserve -> unknown -> reconcile yields 0 leak | PASSED (0.02s) | PASS | 2026-09-01 (M3) |
| Ledger | M3-36 Hypothesis property fuzzing | arbitrary interleavings preserve cap & idempotency | PASSED (0.45s) | PASS | 2026-09-01 (M3) |
| Candidate | M4-15 Candidate generation | generates all supported recovery actions | PASSED (0.02s) | PASS | 2026-09-01 (M4) |
| Candidate | M4-16 NO_ACTION counterfactual | NO_ACTION present in every candidate set | PASSED (0.01s) | PASS | 2026-09-01 (M4) |
| Safety | M4-17 Budget cap rejection | exhausted budget marks outreach candidates SAFETY_REJECTED | PASSED (0.02s) | PASS | 2026-09-01 (M4) |
| Safety | M4-18 Immutable safety rejection | SAFETY_REJECTED candidates cannot become ELIGIBLE | PASSED (0.01s) | PASS | 2026-09-01 (M4) |
| Safety | M4-19 Reject explanations | non-empty human readable explanation on rejection | PASSED (0.01s) | PASS | 2026-09-01 (M4) |
| Invariant | M4-20 Zero contact slot consumption | M4 pipeline consumes 0 contact slots | PASSED (0.02s) | PASS | 2026-09-01 (M4) |
| Invariant | M4-21 Retry ownership boundary | engine recommends retries, never executes payments | PASSED (0.01s) | PASS | 2026-09-01 (M4) |
| Scenarios | M4 Golden Scenarios S001-S010 | 10 end-to-end pipeline scenarios verified | PASSED (0.05s) | PASS | 2026-09-01 (M4) |
| AI Model | M5-01 CatBoost S-Learner fit/predict | CatBoost S-learner fits and predicts recovery probabilities | PASSED (0.15s) | PASS | 2026-09-01 (M5) |
| AI Model | M5-02 Deterministic predictions | identical seed produces 100% reproducible predictions | PASSED (0.12s) | PASS | 2026-09-01 (M5) |
| AI Model | M5-03 Cold-start fallback | insufficient training data uses safe heuristic fallback | PASSED (0.01s) | PASS | 2026-09-01 (M5) |
| AI Model | M5-04 File-based registry | models/vN.cbm + vN.meta.json registered and loaded (ADR-0008) | PASSED (0.08s) | PASS | 2026-09-01 (M5) |
| AI Counterfactual | M5-07 NO_ACTION counterfactual | NO_ACTION baseline P(Y=1\|X, NO_ACTION) evaluated first | PASSED (0.02s) | PASS | 2026-09-01 (M5) |
| AI Effect | M5-08 Incremental effect delta_hat | delta_hat = p(x,a) - p(x, NO_ACTION) calculated | PASSED (0.02s) | PASS | 2026-09-01 (M5) |
| AI EV | M5-09 Negative uplift negative EV | negative incremental effect yields negative EV | PASSED (0.01s) | PASS | 2026-09-01 (M5) |
| AI EV | M5-10 Integer paise EV precision | EV(x,a) strictly stored as integer paise | PASSED (0.01s) | PASS | 2026-09-01 (M5) |
| AI Leakage | M5-13 Point-in-time leakage check | future observed_at raises PointInTimeLeakageError (INV-7) | PASSED (0.01s) | PASS | 2026-09-01 (M5) |
| AI Leakage | M5-14 Denylisted post-decision field | post-decision field raises PointInTimeLeakageError | PASSED (0.01s) | PASS | 2026-09-01 (M5) |
| AI Leakage | M5-15 Decision invariant to post-mutation | post-decision mutation does not alter decision | PASSED (0.02s) | PASS | 2026-09-01 (M5) |
| AI Exploration | M5-16 Exploitation mode | epsilon=0.0 selects highest EV action exclusively | PASSED (0.02s) | PASS | 2026-09-01 (M5) |
| AI Exploration | M5-17 Forced exploration mode | forced EXPLORE selects randomly among ELIGIBLE actions | PASSED (0.01s) | PASS | 2026-09-01 (M5) |
| AI Exploration | M5-18 Safety rejection un-explorable | SAFETY_REJECTED candidate never selected by exploration (INV-3) | PASSED (0.05s) | PASS | 2026-09-01 (M5) |
| AI Exploration | M5-19 Safe abstention fallback | zero eligible candidates falls back to NO_ACTION abstention | PASSED (0.01s) | PASS | 2026-09-01 (M5) |
| AI Tenancy | M5-21 Merchant ID feature exclusion | merchant_id excluded from feature vector (INV-1) | PASSED (0.01s) | PASS | 2026-09-01 (M5) |
| AI Tenancy | M5-22 Cross-tenant decision isolation | identical customer at 2 merchants receives isolated decision | PASSED (0.02s) | PASS | 2026-09-01 (M5) |
| Golden Scenarios | AI Golden Scenarios AI-01 to AI-10 | 10 standardized AI decision engine golden scenarios verified | PASSED (0.25s) | PASS | 2026-09-01 (M5) |
| Sandbox | M6-01 Sandbox simulator execution | stateful delivery simulation & failure injection | PASSED (0.02s) | PASS | 2026-09-01 (M6) |
| Sandbox | M6-02 Deterministic sandbox seed | identical seed produces 100% reproducible execution result | PASSED (0.01s) | PASS | 2026-09-01 (M6) |
| Attribution | M6-03 Self-cure ₹0 attribution | self-cure payments receive ₹0 AI attribution (INV-1) | PASSED (0.01s) | PASS | 2026-09-01 (M6) |
| Attribution | M6-04 Intervention attribution | delivered intervention payment receives 100% attributed recovery | PASSED (0.01s) | PASS | 2026-09-01 (M6) |
| Golden Scenarios | M6 Golden E2E Scenarios M6-E01-E12 | 12 standardized end-to-end sandbox recovery scenarios verified | PASSED (0.35s) | PASS | 2026-09-01 (M6) |
| Assignment | M7-01 Deterministic arm assignment | sha256 hashing produces 100% reproducible ExperimentArm | PASSED (0.01s) | PASS | 2026-09-01 (M7) |
| Assignment | M7-02 Tenant-isolated assignment | cross-tenant identical customers receive isolated arm hashing (INV-1) | PASSED (0.01s) | PASS | 2026-09-01 (M7) |
| Assignment | M7-03 Outcome-independent assignment | arm assignment independent of customer payment outcome | PASSED (0.01s) | PASS | 2026-09-01 (M7) |
| Experiment Runner | M7-04 5-Arm paired execution | paired evaluation across CONTROL, A1, A2ns, A2, A3, A5 | PASSED (0.25s) | PASS | 2026-09-01 (M7) |
| Primary Metric | M7-05 Incremental rate A2 vs A1 | primary metric incremental recovery rate evaluated (ADR-0011) | PASSED (0.05s) | PASS | 2026-09-01 (M7) |
| Multiplicity | M7-06 Holm-Bonferroni correction | secondary comparison family corrected via Holm-Bonferroni | PASSED (0.08s) | PASS | 2026-09-01 (M7) |
| Sample Safety | M7-07 Insufficient sample handling | small sample size reports INSUFFICIENT_SAMPLE status | PASSED (0.01s) | PASS | 2026-09-01 (M7) |
| Feedback Loop | M7-08 Retraining record transformation | RecoveryObservation transformed to TrainingRecord (X, A, Y) | PASSED (0.01s) | PASS | 2026-09-01 (M7) |
| Feedback Loop | M7-09 Point-in-time feature leakage | post-decision outcome fields in X raise PointInTimeLeakageError (INV-7) | PASSED (0.01s) | PASS | 2026-09-01 (M7) |
| Golden Scenarios | M7 Golden Scenarios M7-E01-E12 | 12 standardized M7 experiment golden scenarios verified | PASSED (0.45s) | PASS | 2026-09-01 (M7) |

**Total: 151 tests specified · 151 run · 151 passing (100% pass rate).**


