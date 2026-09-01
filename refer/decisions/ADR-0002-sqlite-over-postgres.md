# ADR-0002 — SQLite over PostgreSQL; no Redis, no Docker

**Date**: 2026-08-31
**Status**: ACCEPTED
**Author/Agent**: Claude Opus 5, ratified by project owner

## Decision
The prototype uses SQLite in WAL mode with `BEGIN IMMEDIATE` transactions. PostgreSQL, Redis, Docker, message queues, ORMs and observability platforms are excluded.

## Context
Solo student builder, no infrastructure budget, 10-day build (possibly shorter). The frozen atomic-reservation design in `p0.2` was written against `BEGIN IMMEDIATE`. Scale is ~600 opportunities x 40 seeds on one laptop.

## Problem
The default instinct is Postgres + Redis + Docker. Each adds a daemon, configuration, and a failure mode, and each must be installed by any reviewer who tries to run the project.

## Options considered
1. SQLite, stdlib driver (CHOSEN)
2. PostgreSQL in Docker
3. PostgreSQL native install
4. SQLite + Redis for the budget counter

## Decision rationale
SQLite supports every safety requirement: ACID transactions, `BEGIN IMMEDIATE` write locks, `CHECK` constraints, composite primary keys, partial indexes. At single-writer prototype scale, serialized writes are not a throughput problem. Option 4 is actively worse: it creates a second source of truth for the exact state the project's central safety claim depends on.

## Trade-offs
Single-writer only. Parallel experiment runs need one DB file per seed. The concurrency claim is scoped to one process and must be stated that way, never implied to be distributed.

## Impact
No Docker, no server process, no connection config. A reviewer runs `pip install` and `pytest`. Removes the largest install-failure surface.

## What this prevents
A reviewer's failed environment setup — which is a failed submission, because they will not debug it for you.

## Affected components
`app/db/`, `app/ledger/`, deployment, `08_TOOLCHAIN.md` deny-list

## Tests required
Schema applies on SQLite WAL; every statement runs on the prototype stack; 2/10/100-worker reservation test green.

## Evidence
`p0.2` Part 32 (prototype vs production); `strategy/TOOLCHAIN.md` §6.

## Reversal conditions
If the project ever needs multi-process arbitration or row-level security. The schema is written to port to Postgres cleanly; V2 partitions by `customer_id`.

## Related ADRs
ADR-0003, ADR-0010
