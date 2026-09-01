# ADR-0010 — Streamlit over a Node frontend

**Date**: 2026-08-31
**Status**: ACCEPTED
**Author/Agent**: Claude Opus 5, ratified by project owner

## Decision
The dashboard is a Streamlit app reading the same SQLite file the engine writes. No React, Next.js, Vite, Tailwind or Node.js.

## Context
The UI requirement is one trace screen answering 'why did the engine do this?', plus a results table.

## Problem
A Node toolchain would add a second language runtime, a bundler, a dev server, a CORS story and an API layer that otherwise need not exist — days of work producing no evidence.

## Options considered
1. Streamlit (CHOSEN)
2. React + Vite + a FastAPI backend
3. Jinja2 templates rendered to static HTML by the eval run

## Decision rationale
Streamlit renders the trace screen in roughly 150 lines of the language the engine is already written in, with no build step. Option 3 is the fallback if Streamlit disappoints — still no Node.

## Trade-offs
Less layout control. Irrelevant, because the dashboard is an observability layer and explicitly not a product.

## Impact
Removes Node, npm, a bundler and a build step from the install path. A reviewer runs one `streamlit run` command.

## What this prevents
The single biggest unnecessary dependency available to this project.

## Affected components
`app/dashboard.py`, `08_TOOLCHAIN.md` deny-list

## Tests required
Every widget has a source query; no literal values; dashboard refuses to render without a completed run.

## Evidence
`strategy/TOOLCHAIN.md` §12.

## Reversal conditions
If the deliverable ever becomes a customer-facing product rather than an evidence viewer.

## Related ADRs
ADR-0002, ADR-0007
