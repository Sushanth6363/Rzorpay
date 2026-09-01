# TEST MATRIX

**Never write `PASS` unless the test was actually run.** Record the date and commit when you do.

Legend: `NOT_RUN` · `PASS` · `FAIL` · `SKIP` · `UNKNOWN`

| Component | Test | Expected | Actual | Status | Last Run |
|---|---|---|---|---|---|
| Schema | applies on SQLite WAL | no error | — | NOT_RUN | — |
| Schema | CHECK constraints present | 3 constraints | — | NOT_RUN | — |
| Domain | no float money fields | none found | — | NOT_RUN | — |
| Clock | no wall-clock calls outside adapter | none found | — | NOT_RUN | — |
| DAL | unscoped query raises | TenantScopeViolation | — | NOT_RUN | — |
| Ledger | cap binds after 4 executions | 5th rejected | — | NOT_RUN | — |
| Ledger | same idempotency key x5 | 1 reservation, 1 slot | — | NOT_RUN | — |
| Ledger | mark_executed x3 then release x3 | counters unchanged after 1st | — | NOT_RUN | — |
| Ledger | expiry racing execution | exactly one counter move | — | NOT_RUN | — |
| Ledger | 7 invalid transitions | all rejected, no counter move | — | NOT_RUN | — |
| Ledger | execution_unknown counter placement | reserved=1, consumed=0 | — | NOT_RUN | — |
| Ledger | 2 workers, same key | 1 grant | — | NOT_RUN | — |
| Ledger | 10 workers, distinct keys | min(10, cap) grants | — | NOT_RUN | — |
| Ledger | 100 workers, distinct keys | reserved+consumed <= cap | — | NOT_RUN | — |
| Ledger | Hypothesis fuzz, 200 ops x 16 workers | invariant holds | — | NOT_RUN | — |
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

**Total: 68 tests specified · 0 run · 0 passing.**
