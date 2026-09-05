# TEST MATRIX

**Never write `PASS` unless the test was actually run.** Record the date and commit when you do.

Legend: `NOT_RUN` · `PASS` · `FAIL` · `SKIP` · `UNKNOWN`

**Suite total: 255 tests, all passing.** Verified 2026-09-05 at commit `e803e36` on a clean tree
(`.venv/Scripts/python.exe -m pytest` → 255 passed in 9.0s).

This document has two parts, and they are maintained differently:

1. **§Milestones M1–M8** — the original hand-written matrix, 161 rows, verified 2026-09-01. It is
   a *historical* record: the dates and commits are the ones the rows were verified at and are
   deliberately not restamped.
2. **§Post-M8** — the 94 tests added after the M1–M8 matrix was frozen, enumerated per file from
   `pytest --collect-only`, not by hand. 161 + 94 = 255, which is why the two parts reconcile.

If these numbers and a status document ever disagree, run the suite; the suite is the authority.

---

## Milestones M1–M8 — 161 tests (historical, verified 2026-09-01)

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
| UI Integration | M8-01 All 12 Golden Scenarios execute | Every scenario in GOLDEN_DEMO_SCENARIOS runs to completion | PASSED (0.35s) | PASS | 2026-09-01 (M8) |
| UI Integration | M8-02 Scenario 1 Retry Recovery | Scenario 1 produces intervention recovery with attributed recovery > 0 | PASSED (0.05s) | PASS | 2026-09-01 (M8) |
| UI Integration | M8-03 Scenario 3 Self-Cure Attribution (INV-8) | Scenario 3 yields SELF_CURED outcome with strictly ₹0 AI Attribution | PASSED (0.04s) | PASS | 2026-09-01 (M8) |
| UI Integration | M8-04 Scenario 5 Gateway Outage Safety (INV-4) | Scenario 5 suppresses retry recommendations via hard safety filter | PASSED (0.04s) | PASS | 2026-09-01 (M8) |
| UI Integration | M8-05 Scenario 6 Contact Cap Exhaustion (INV-2) | Scenario 6 blocks active intervention reservation | PASSED (0.05s) | PASS | 2026-09-01 (M8) |
| UI Integration | M8-06 Scenario 11 Cross-Tenant Isolation (INV-1) | Scenario 11 preserves complete tenant isolation | PASSED (0.06s) | PASS | 2026-09-01 (M8) |
| Reproducibility | M8-07 Deterministic Scenario Reproducibility | Identical scenario execution with same seed produces 100% identical outputs | PASSED (0.05s) | PASS | 2026-09-01 (M8) |
| Reproducibility | M8-08 Reproducible Experiment Runner | ExperimentRunner with identical seeds produces identical summary metric hashes | PASSED (0.08s) | PASS | 2026-09-01 (M8) |
| Reconciliation | M8-09 Scenario 8 Execution Unknown Reconciled | EXECUTION_UNKNOWN simulation correctly transitions to reconciliation status | PASSED (0.05s) | PASS | 2026-09-01 (M8) |
| Abstention | M8-10 Scenario 12 Negative EV Abstention | Scenario 12 forces NO_ACTION | PASSED (0.04s) | PASS | 2026-09-01 (M8) |

**Subtotal: 161 tests specified · 161 run · 161 passing (100% pass rate), 2026-09-01.**

---

## Post-M8 — 94 tests (verified 2026-09-05 at `e803e36`)

Five files, added by four feature commits after the matrix above was frozen. Counts are collected
from the suite, not asserted: `995ba53` +29, `acbe951` +25, `7d59873` +12, `03e99e9` +17,
`e803e36` +11 → 94.

### `tests/pipeline/test_escalation.py` — 15 tests, added in `995ba53` (ADR-0015)

| Component | Test Name | Description | Output | Status | Date & Commit |
| --- | --- | --- | --- | --- | --- |
| Escalation | first touch never reaches an IVR or agent call | a cold opportunity cannot open on a phone rung | PASSED | PASS | 2026-09-05 (e803e36) |
| Escalation | entry rung is stream aware but hard capped | stream picks the entry rung; the cap still binds | PASSED | PASS | 2026-09-05 (e803e36) |
| Escalation | escalation advances exactly one rung, never two | single-rung advance per confirmed contact | PASSED | PASS | 2026-09-05 (e803e36) |
| Escalation | ladder never advances past the top | AGENT_DIAL is terminal | PASSED | PASS | 2026-09-05 (e803e36) |
| Escalation | an unknown send does not earn an escalation | EXECUTION_UNKNOWN is not evidence of contact | PASSED | PASS | 2026-09-05 (e803e36) |
| Escalation | a reconciled delivery does earn an escalation | reconciled DELIVERED is confirmed evidence | PASSED | PASS | 2026-09-05 (e803e36) |
| Escalation | a NOT_SENT reconciliation does not earn an escalation | a send that never left does not advance the ladder | PASSED | PASS | 2026-09-05 (e803e36) |
| Escalation | no escalation inside the quiet period | quiet period holds the ladder | PASSED | PASS | 2026-09-05 (e803e36) |
| Escalation | escalation resumes once the quiet period has elapsed | the hold is temporal, not permanent | PASSED | PASS | 2026-09-05 (e803e36) |
| Escalation | unreadable timestamps hold the ladder still | unparseable time fails closed, does not advance | PASSED | PASS | 2026-09-05 (e803e36) |
| Escalation | escalation can never revive a safety-rejected candidate | INV-3: layered under safety, removal only | PASSED | PASS | 2026-09-05 (e803e36) |
| Escalation | off-ladder actions are untouched by escalation | NO_ACTION and retries are not ladder rungs | PASSED | PASS | 2026-09-05 (e803e36) |
| Escalation | suppression is recorded with its working | audit trail carries the reason, not just the verdict | PASSED | PASS | 2026-09-05 (e803e36) |
| Escalation | ladder advances one rung per contact through the full engine | end-to-end through the orchestrator | PASSED | PASS | 2026-09-05 (e803e36) |
| Escalation | the engine does not escalate inside the quiet period, end to end | quiet period holds through the full engine | PASSED | PASS | 2026-09-05 (e803e36) |

### `tests/pipeline/test_tds_derivation.py` — 14 tests, added in `995ba53` (ADR-0016)

| Component | Test Name | Description | Output | Status | Date & Commit |
| --- | --- | --- | --- | --- | --- |
| TDS | shortfall equal to statutory withholding is not customer debt | the payer already remitted it; nothing to chase | PASSED | PASS | 2026-09-05 (e803e36) |
| TDS | shortfall exceeding withholding recovers only the excess | chase the genuine gap, not the whole shortfall | PASSED | PASS | 2026-09-05 (e803e36) |
| TDS | under-withholding leaves the whole shortfall recoverable | less withheld than due → full amount chaseable | PASSED | PASS | 2026-09-05 (e803e36) |
| TDS | individual/HUF gets a different rate than a company under 194C | payee constitution changes the derived rate | PASSED | PASS | 2026-09-05 (e803e36) |
| TDS | missing PAN raises the rate to the 206AA floor | no PAN → statutory higher rate | PASSED | PASS | 2026-09-05 (e803e36) |
| TDS | rounding slack is tolerated within one rupee | paise-level rounding does not create phantom debt | PASSED | PASS | 2026-09-05 (e803e36) |
| TDS | unknown section never suppresses a recovery | fail toward chasing, not toward silent write-off | PASSED | PASS | 2026-09-05 (e803e36) |
| TDS | absent remittance figure never suppresses a recovery | missing facts cannot justify suppression | PASSED | PASS | 2026-09-05 (e803e36) |
| TDS | integer paise only, no float leaks into money | INV: money is integer paise throughout | PASSED | PASS | 2026-09-05 (e803e36) |
| TDS | Stage 0 declines to chase an invoice settled net of TDS | the derivation actually gates Stage 0 | PASSED | PASS | 2026-09-05 (e803e36) |
| TDS | Stage 0 restates the chaseable amount on a partial payment | amount at risk is recomputed, not inherited | PASSED | PASS | 2026-09-05 (e803e36) |
| TDS | derivation beats a contradicting declared flag | facts outrank a self-reported flag | PASSED | PASS | 2026-09-05 (e803e36) |
| TDS | declared flag still suppresses when no facts are available | graceful degradation to the flag | PASSED | PASS | 2026-09-05 (e803e36) |
| TDS | withholding is not derived for non-receivable streams | TDS logic is scoped to B2B invoices | PASSED | PASS | 2026-09-05 (e803e36) |

### `tests/realtime/test_followup.py` — 17 tests, added in `03e99e9`

| Component | Test Name | Description | Output | Status | Date & Commit |
| --- | --- | --- | --- | --- | --- |
| Follow-up timing | an abandoned cart is chased far sooner than an overdue invoice | delay derives from the stream | PASSED | PASS | 2026-09-05 (e803e36) |
| Follow-up timing | insufficient funds waits for a realistic funding cycle | delay derives from the failure reason | PASSED | PASS | 2026-09-05 (e803e36) |
| Follow-up timing | a gateway outage is rechecked quickly | transient cause → short delay | PASSED | PASS | 2026-09-05 (e803e36) |
| Follow-up timing | email is given longer to be read than SMS | delay derives from the channel | PASSED | PASS | 2026-09-05 (e803e36) |
| Follow-up timing | a phone call earns the longest pause | the most intrusive channel waits longest | PASSED | PASS | 2026-09-05 (e803e36) |
| Follow-up timing | each unanswered touch widens the gap | backoff across successive silences | PASSED | PASS | 2026-09-05 (e803e36) |
| Follow-up timing | a delay is never less than an hour | hard floor on re-contact | PASSED | PASS | 2026-09-05 (e803e36) |
| Follow-up state | a contact schedules the next reconsideration | silence is an event the engine acts on | PASSED | PASS | 2026-09-05 (e803e36) |
| Follow-up state | payment arriving stops every scheduled follow-up | stopping rule on resolution | PASSED | PASS | 2026-09-05 (e803e36) |
| Follow-up state | follow-ups are bounded | a finite ladder, not an unbounded loop | PASSED | PASS | 2026-09-05 (e803e36) |
| Follow-up state | nothing is due before its delay has elapsed | the scheduler respects its own clock | PASSED | PASS | 2026-09-05 (e803e36) |
| Message copy | tone escalates with the rung | later rungs read differently | PASSED | PASS | 2026-09-05 (e803e36) |
| Message copy | the ask follows the diagnosis, not the channel | content is driven by why it failed | PASSED | PASS | 2026-09-05 (e803e36) |
| Message copy | B2B invoices get accounts-payable language | audience-appropriate copy | PASSED | PASS | 2026-09-05 (e803e36) |
| Message copy | every message identifies itself and offers an opt-out | compliance floor on every send | PASSED | PASS | 2026-09-05 (e803e36) |
| Message copy | copy never invents a deadline or a threat | no fabricated urgency or coercion | PASSED | PASS | 2026-09-05 (e803e36) |
| Message copy | the spoken message never reads out a URL | IVR copy is channel-appropriate | PASSED | PASS | 2026-09-05 (e803e36) |

### `tests/realtime/test_reliability.py` — 12 tests, added in `7d59873` (ADR-0019)

| Component | Test Name | Description | Output | Status | Date & Commit |
| --- | --- | --- | --- | --- | --- |
| Retry | a failed event is scheduled for retry, not dropped | no silent loss on processing failure | PASSED | PASS | 2026-09-05 (e803e36) |
| Retry | retries are bounded and end in a visible dead letter | bounded attempts, then a queue a human can see | PASSED | PASS | 2026-09-05 (e803e36) |
| Retry | backoff delays the next attempt | exponential backoff between attempts | PASSED | PASS | 2026-09-05 (e803e36) |
| Retry | a succeeded retry leaves the queue | success drains the entry | PASSED | PASS | 2026-09-05 (e803e36) |
| Reconciliation sweep | the sweep reports how many entries it closed | the sweep is observable | PASSED | PASS | 2026-09-05 (e803e36) |
| Reconciliation sweep | a reconciliation failure does not abort the sweep | one bad entry cannot stall the rest | PASSED | PASS | 2026-09-05 (e803e36) |
| Replay guard | a stale webhook is rejected | timestamp outside the window is refused | PASSED | PASS | 2026-09-05 (e803e36) |
| Replay guard | a fresh webhook is accepted | in-window traffic passes | PASSED | PASS | 2026-09-05 (e803e36) |
| Replay guard | a missing timestamp is not rejected | absent header does not break ingestion | PASSED | PASS | 2026-09-05 (e803e36) |
| Privacy | a raw email is never used as the customer key | no PII as a primary key | PASSED | PASS | 2026-09-05 (e803e36) |
| Privacy | the pseudonymous key is stable for the same person | deterministic pseudonymisation | PASSED | PASS | 2026-09-05 (e803e36) |
| Privacy | an explicit customer id is preserved | a real id is not overwritten | PASSED | PASS | 2026-09-05 (e803e36) |

### `tests/realtime/test_webhook_ingestion.py` — 25 tests, added in `8a280f9` / `acbe951` (ADR-0018)

| Component | Test Name | Description | Output | Status | Date & Commit |
| --- | --- | --- | --- | --- | --- |
| Stream coverage | all four streams are reachable from real webhooks (`payment.failed`) | → FAILED_PAYMENT | PASSED | PASS | 2026-09-05 (e803e36) |
| Stream coverage | all four streams are reachable from real webhooks (`payment_link.expired`) | → ABANDONED_CHECKOUT | PASSED | PASS | 2026-09-05 (e803e36) |
| Stream coverage | all four streams are reachable from real webhooks (`subscription.halted`) | → FAILED_SUBSCRIPTION_RENEWAL | PASSED | PASS | 2026-09-05 (e803e36) |
| Stream coverage | all four streams are reachable from real webhooks (`invoice.partially_paid`) | → OVERDUE_B2B_INVOICE | PASSED | PASS | 2026-09-05 (e803e36) |
| Mapping | a successful event is not a recovery opportunity | success never enters the pipeline | PASSED | PASS | 2026-09-05 (e803e36) |
| Mapping | an unrecognised event is dropped rather than guessed | explicit mapping, never a family prefix | PASSED | PASS | 2026-09-05 (e803e36) |
| Mapping | zero amount is not revenue at risk | ₹0 is not a leak | PASSED | PASS | 2026-09-05 (e803e36) |
| Mapping | epoch timestamps are converted, not replaced with a placeholder | real event time is preserved | PASSED | PASS | 2026-09-05 (e803e36) |
| Mapping | a B2B invoice carries the facts the TDS derivation needs | ingestion feeds ADR-0016 | PASSED | PASS | 2026-09-05 (e803e36) |
| Mapping | entity is found under each Razorpay family key | payload shape handled across families | PASSED | PASS | 2026-09-05 (e803e36) |
| Signature | a forged signature is rejected | HMAC SHA256 verification | PASSED | PASS | 2026-09-05 (e803e36) |
| Signature | a valid signature is accepted | correct signature passes | PASSED | PASS | 2026-09-05 (e803e36) |
| Signature | missing secret refuses traffic instead of opening the door | fail-closed: absent secret → 401 | PASSED | PASS | 2026-09-05 (e803e36) |
| Dispatch gate | dispatch is off by default | requires `RECOVERY_DISPATCH_ENABLED` | PASSED | PASS | 2026-09-05 (e803e36) |
| Dispatch gate | live credentials need a second explicit acknowledgement | `rzp_live_` refused without a separate opt-in | PASSED | PASS | 2026-09-05 (e803e36) |
| Idempotency | a redelivered event is recognised | idempotent on the Razorpay event id | PASSED | PASS | 2026-09-05 (e803e36) |
| Idempotency | a delivery advances in place rather than duplicating | state advances, no duplicate row | PASSED | PASS | 2026-09-05 (e803e36) |
| Downtime | a downtime notification marks the gateway down | consumes the downtime signal | PASSED | PASS | 2026-09-05 (e803e36) |
| Downtime | downtime matches on payment method too | method-scoped outage matching | PASSED | PASS | 2026-09-05 (e803e36) |
| Downtime | resolving an outage clears the signal | resolution webhook lifts suppression | PASSED | PASS | 2026-09-05 (e803e36) |
| Downtime | a downtime event is never a recovery opportunity | infrastructure signal, not a leak | PASSED | PASS | 2026-09-05 (e803e36) |
| Provenance | the live provider reports real provenance | `source: RAZORPAY_TEST` is not faked | PASSED | PASS | 2026-09-05 (e803e36) |
| Provenance | the downtime lookup fails safe, not open | lookup failure does not license a send | PASSED | PASS | 2026-09-05 (e803e36) |
| Provenance | a success event is never treated as a failure | polarity is not inverted anywhere | PASSED | PASS | 2026-09-05 (e803e36) |
| Provenance | a paid entity is remembered across webhooks | resolution persists between deliveries | PASSED | PASS | 2026-09-05 (e803e36) |

### `tests/reporting/test_unrecovered.py` — 11 tests, added in `e803e36`

| Component | Test Name | Description | Output | Status | Date & Commit |
| --- | --- | --- | --- | --- | --- |
| Handoff report | a customer who paid is never listed | recovered money is not reported as a failure | PASSED | PASS | 2026-09-05 (e803e36) |
| Handoff report | an opportunity stopped because it resolved is not a failure | self-cure is not an unrecovered case | PASSED | PASS | 2026-09-05 (e803e36) |
| Handoff report | an exhausted unpaid opportunity is listed | genuine failures do appear | PASSED | PASS | 2026-09-05 (e803e36) |
| Handoff report | contact history comes from the ledger, not an estimate | effort is read from the audit trail | PASSED | PASS | 2026-09-05 (e803e36) |
| Handoff report | an unconfirmed contact is not counted as effort | only confirmed contact counts | PASSED | PASS | 2026-09-05 (e803e36) |
| Handoff report | biggest exposure is listed first | ordered by money at risk | PASSED | PASS | 2026-09-05 (e803e36) |
| Handoff report | the suggested step is derived from what happened | next action follows the case history | PASSED | PASS | 2026-09-05 (e803e36) |
| Handoff report | a never-contacted customer is flagged as such | zero-touch cases are visible | PASSED | PASS | 2026-09-05 (e803e36) |
| Handoff report | the summary totals only unrecovered money | totals exclude recovered amounts | PASSED | PASS | 2026-09-05 (e803e36) |
| Handoff report | a real .xlsx workbook is produced | the file opens as a genuine workbook | PASSED | PASS | 2026-09-05 (e803e36) |
| Handoff report | an empty report still produces a valid workbook | no-failures case does not crash | PASSED | PASS | 2026-09-05 (e803e36) |

**Post-M8 subtotal: 94 tests · 94 run · 94 passing.**

---

## Reconciliation

| Part | Tests |
|---|---:|
| M1–M8 (historical, 2026-09-01) | 161 |
| Post-M8 (2026-09-05) | 94 |
| **Suite total, verified by execution at `e803e36`** | **255** |

Not covered by tests, because it does not exist: red-team mode and a competing-agent arbitrator.
See `01_PROJECT_STATE.md` §Not built.







