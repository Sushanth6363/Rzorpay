# ADR-0011 — Five experiment arms; primary metric is incremental recovery rate

**Date**: 2026-08-31
**Status**: ACCEPTED
**Author/Agent**: Claude Opus 5, ratified by project owner

## Decision
The experiment executes five distinct configurations — A1, A2ns, A2, A3, A5 — with A4 as a readability alias of A3. The single primary metric is incremental recovery rate on the A2 vs A1 comparison.

## Context
An earlier draft defined six configurations in which A3 and A4 were byte-identical, and named recovered paise per opportunity as primary.

## Problem
Two names for one configuration inflates the apparent arm count and would double-count in the multiplicity family. Rupee amounts are heavily right-skewed at this batch size, making revenue the noisier estimator.

## Options considered
1. Five configurations, rate as primary (CHOSEN)
2. Six configurations as originally drafted
3. Revenue as primary because the Track 3 brief names money

## Decision rationale
Rate is the more stable statistic and therefore the more honest primary. Revenue is still reported with equal visual prominence for the rubric, but labelled secondary and higher-variance, and the statistical verdict is taken from the rate. Naming A4 an alias also revealed that A2ns vs A1 isolates the ledger + arbitration contribution — D1 — at zero extra build cost.

## Trade-offs
Two headline numbers instead of one, requiring discipline about which carries the verdict.

## Impact
The results renderer marks exactly one metric primary:true; zero or more than one fails the build. Secondary family gets Holm correction.

## What this prevents
Multiplicity abuse, and a skewed estimator carrying the verdict.

## Affected components
`app/evaluation/`, `07_EXPERIMENT_METHODOLOGY.md`, `experiments/preregistration.json`

## Tests required
Exactly five distinct configurations; A4 declared an alias; each comparison isolates exactly its declared flag difference; exactly one primary metric.

## Evidence
`p0.2-patch.md` FIX 2; `p0.2-closure.md` §2 and §6.

## Reversal conditions
Changing arms or the primary metric after the pre-registration is git-tagged voids the results and requires a fresh pre-registration.

## Related ADRs
ADR-0005, ADR-0009
