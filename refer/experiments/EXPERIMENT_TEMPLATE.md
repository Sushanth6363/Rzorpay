# EXPERIMENT E-XXX

**Experiment ID**:
**Date**:
**Status**: PLANNED / RUNNING / COMPLETE / FAILED / ABANDONED

## Hypothesis
State it before running. One sentence, falsifiable.

## Pre-registration
Pre-registered? YES / NO. If NO, this experiment is **exploratory** and must be labelled so in any report.
Pre-registration commit/tag:

## Configuration
```
Code commit:
Dataset version:
Dataset hash:
Model version:
Model artifact hash:
Seeds:
Arms:
Contact cap:
Cooldown:
Epsilon (exploration):
Observation window:
Attribution window:
```

## Control
Arm, and what it does.

## Treatment
Arm, and what differs — exactly one flag unless the difference is declared joint.

## Metrics
Primary:
Secondary:
Guardrails:

## Observed results
**Leave blank until the experiment has actually run.** Never fill this with expected values.

```
Primary metric:
  point estimate:
  95% CI:
  n (randomisation unit):
  interval method:
  MDE at this n:

Secondary:

Guardrails:
```

## Statistical results
Test used, statistic, p-value (raw and Holm-adjusted where part of the secondary family).

## Interpretation
What this shows. If the CI includes zero, write: *inconclusive at this sample size — not evidence of no effect.*

## Limitations
At minimum: synthetic data-generating process; authored response function; sampling error quantified only within the simulation.

## Decision
What changes because of this result. If nothing changes, say so.

## Reproduction
```
make eval SEEDS=... ARMS=...
```
