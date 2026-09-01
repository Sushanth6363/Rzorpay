# ADR-0008 — File-based model registry instead of an ML platform

**Date**: 2026-08-31
**Status**: ACCEPTED
**Author/Agent**: Claude Opus 5, ratified by project owner

## Decision
Models are stored as `models/vN.cbm` with a sibling `vN.meta.json`, a `model_registry` table row, and a git tag per promotion. No MLflow, Weights & Biases, Vertex AI, SageMaker or Azure ML.

## Context
Four to six model artefacts across a 10-day prototype, one developer, no budget.

## Problem
Tracking model lineage without adding a server, an account, or a cost.

## Options considered
1. Files + JSON + git tag (CHOSEN)
2. MLflow locally
3. Weights & Biases free tier

## Decision rationale
The metadata that matters — version, artifact hash, features version, training seeds, offline metrics, promotion timestamp — fits in a JSON file that is diffable and reviewable in a pull request. MLflow adds a server and a UI to track four artefacts. W&B adds an account and sends data off the machine.

## Trade-offs
No experiment-tracking UI. Comparison is done in pandas from the registry table.

## Impact
Model provenance is stamped on every decision and every outcome, so results can be sliced by model version without a platform.

## What this prevents
Adding a service, an account, or a cost for something a file solves.

## Affected components
`app/models/registry.py`, `models/`, `08_TOOLCHAIN.md` deny-list

## Tests required
Every outcome carries full provenance; report regenerable from the join; model hash constant within a run.

## Evidence
`strategy/TOOLCHAIN.md` §14.

## Reversal conditions
If the project ever runs many concurrent training experiments needing comparison at scale.

## Related ADRs
ADR-0002
