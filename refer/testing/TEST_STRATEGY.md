# TEST STRATEGY

**Status: NO TEST HAS EVER BEEN RUN.** `tests/` does not exist. Every row in `TEST_MATRIX.md` is `NOT_RUN`.

## Principle

Tests are the only thing that converts `DOCUMENTED` into `VERIFIED`. A component is not implemented because a document says so; it is implemented when its test runs and passes.

## Layers

### Unit tests
Pure functions with no I/O: scoring, expected-value arithmetic, attribution timeline rules, money arithmetic, feature assembly.
Tool: `pytest`. Fast, run on every save.

### Integration tests
Multiple modules against a real SQLite file: event to opportunity to candidates to decision to reservation to execution to outcome.
Tool: `pytest` with a temp database per test.

### Property tests
Invariants that must hold for *any* input, not just chosen examples.
Tool: `Hypothesis`.
- budget invariant under arbitrary op interleavings
- exploration never yields an ineligible action (2,000+ seeds x 6 constraints)
- replaying any event twice yields identical state

### Concurrency tests
The T0 race and the reservation lifecycle.
Tool: `pytest` + `ThreadPoolExecutor` (NOT Locust — the hazard is in-process write contention, not HTTP load).
- 2 / 10 / 100 workers, same idempotency key and distinct keys
- expiry racing execution
- webhook racing poll during reconciliation

### Data leakage tests
Marked `@pytest.mark.leakage`. **These gate CI.** A violation fails the build; it never warns.
- `test_no_future_features`
- `test_training_cutoff`
- `test_inference_cutoff`
- `test_outcome_not_available_at_decision_time`
- permuted-label canary: AUC must land in (0.45, 0.55)

### ML tests
- calibration slope in [0.85, 1.15]; Brier improved over baseline
- identical `ScoringContext` hash across A3 and A5
- splits never share a customer
- model artifact hash constant within a run

### Experiment tests
- identical `input_hash` and `world_hash` across all arms
- tuning and evaluation seed sets disjoint
- exactly one metric flagged primary
- a null experiment reports `inconclusive`, never `significant`
- Holm correction applied to the secondary family

### End-to-end tests
One opportunity through the full loop, asserting the trace answers all six audit questions.

### Falsification tests
Marked `slow`. Four null conditions where the AI should show no advantage. Reported in the submission including where the advantage disappears.

## Markers

```
pytest -m "not slow"    fast loop during the build
pytest -m leakage       CI gate, blocks merge
pytest                  everything, before the freeze
```

## Rules

1. **Never write PASS in `TEST_MATRIX.md` unless the test was actually executed.** Record the date and the commit.
2. A test that has never run is `NOT_RUN`, not `PASS` and not `UNKNOWN`.
3. A failing invariant test stops feature work.
4. Deleting a test requires an ADR.
5. Every bug fixed gets a regression test, recorded in `FAILURE_LOG.md`.
