# ADR-0009 — External public data is used for calibration only

**Date**: 2026-08-31
**Status**: ACCEPTED
**Author/Agent**: Claude Opus 5, ratified by project owner

## Decision
Public real-world aggregate data (NPCI issuer decline rates, MSME Samadhaan ageing) calibrates the synthetic generator's parameters. It never provides recovery labels. Criteo, if used, is a separate estimator-validation experiment.

## Context
Dataset research across Kaggle, Hugging Face, UCI, GitHub and the dunning literature searched specifically for a payment-failure + intervention + outcome dataset.

## Problem
No such public dataset exists. Every 'failed payment recovery' search returns vendor marketing quoting internal rates with no data behind it.

## Options considered
1. Calibration only, Level 1 (CHOSEN)
2. Use LendingClub or KKBox as training data, Level 2
3. Synthetic only, Level 0

## Decision rationale
Option 2 would train on a target that is not incremental recovery, then imply it is — trading experimental validity for the appearance of real data. Option 3 leaves the failure distribution invented when a real one is available at near-zero cost and risk. Option 1 converts 'I invented the failure distribution' into 'the failure distribution comes from NPCI's published rates'.

## Trade-offs
Both primary sources are BLOCKED on a manual licence check. Fallback: use published ranges from secondary reporting as priors, cite inline, redistribute nothing.

## Impact
The `CalibrationSource` protocol has no `opportunities()` and no `outcomes()` method, so real data structurally cannot contribute a recovery label.

## What this prevents
Presenting aggregate public statistics as customer-level recovery outcomes.

## Affected components
`app/data/external/`, `06_DATA_AND_DATASETS.md`, all claim language

## Tests required
No result renders without a provenance block; calibration sources cannot emit outcomes; no real dataset credited with recovery evidence.

## Evidence
`docs/DATASET_RESEARCH.md`, research performed 2026-08-31 with sources listed.

## Reversal conditions
If a licensed dataset containing state, action and outcome for payment recovery becomes available.

## Related ADRs
ADR-0011
