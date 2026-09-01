# EXPERIMENT INDEX

**NO EXPERIMENT HAS BEEN RUN.** This index is empty by design, not by omission.

| ID | Hypothesis | Date | Commit | Status | Result |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Rules

1. **Never overwrite an experiment.** If E001 produces a bad result, E001 stays `FAILED`. A new attempt is E002.
2. Every experiment records: commit, dataset version + hash, model version, seeds, configuration, control, treatment, metrics, observed results, statistical results, interpretation, limitations, decision.
3. An experiment without a recorded commit is not reproducible and does not count.
4. Results are `EXPECTED`, `OBSERVED`, or `NOT YET RUN`. **Never convert EXPECTED to OBSERVED without a real run.**
5. Pre-registration (`experiments/preregistration.json` in the repo root) must be git-tagged **before** the first evaluation run. An experiment run before its pre-registration is exploratory and must be labelled so.

## Planned experiments

| Planned ID | Hypothesis | Arms | Seeds | Status |
|---|---|---|---|---|
| E001 | The unified engine recovers more per opportunity than independent agents | A2 vs A1 | 21–60 | PRE_REGISTERED (EXECUTABLE) |
| E002 | The ledger + arbitration alone contribute measurably | A2ns vs A1 | 21–60 | PRE_REGISTERED (EXECUTABLE) |
| E003 | Stage 0 validation contributes measurably | A2 vs A2ns | 21–60 | PRE_REGISTERED (EXECUTABLE) |
| E004 | Downtime-signal consumption contributes measurably | A3 vs A2 | 21–60 | PRE_REGISTERED (EXECUTABLE) |
| E005 | The model scorer outperforms the heuristic | A5 vs A3 | 21–60 | PRE_REGISTERED (EXECUTABLE) |

| E006 | Contact-cap sensitivity sweep | A3 at caps 2/4/6/8 | 21–60 | NOT YET RUN |
| E007 | Customer-overlap sweep (adversarial: low overlap) | A2 vs A1 at 0.1/0.3/0.5 | 21–60 | NOT YET RUN |
| F001 | Null: equal action effects → no advantage | A5 vs A3 | 20 | NOT YET RUN |
| F002 | Null: shuffled features → no uplift | A5 vs A3 | 20 | NOT YET RUN |
| F003 | Null: NO_ACTION dominates → high abstention | A5 vs A3 | 20 | NOT YET RUN |
| F004 | Null: permuted labels → AUC ~ 0.5 | offline | — | NOT YET RUN |
| V001 | Estimator validation on Criteo (optional) | — | — | NOT YET RUN |
