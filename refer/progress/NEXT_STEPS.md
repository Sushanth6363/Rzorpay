# NEXT STEPS — Unified Recovery Engine

**Current State**: build complete and verified at `e803e36` (2026-09-05). 255 tests pass, quality gate passes, evaluation reproduces. Remaining work is submission packaging, not engineering.

---

## For a judge or reviewer — the one path

```bash
python scripts/bootstrap.py        # creates .venv with a supported Python (3.11-3.13)
python run_demo.py                 # quality gate, then the dashboard on :8555
```

`run_demo.py` runs `scripts/verify_environment.py` first and refuses to launch if the gate fails, so a green dashboard is always backed by a green suite.

**Every entrypoint serves the same dashboard on the same port (8555):**

| Path | Command | When |
|---|---|---|
| Launcher (recommended) | `python run_demo.py` | gate + dashboard in one step |
| `make` | `make demo` | if GNU make is available |
| Direct | `.venv/Scripts/python.exe -m streamlit run app/ui/dashboard.py --server.port 8555` | Windows, no make |
| Direct | `.venv/bin/python -m streamlit run app/ui/dashboard.py --server.port 8555` | macOS / Linux |
| Streamlit Community Cloud | `streamlit_app.py` (root entrypoint; port assigned by the platform) | hosted demo only |

`ui_app.py` is a thin shim kept for the Cloud/`streamlit run` path; it renders the same dashboard.

## To see the numbers rather than the UI

```bash
make eval
```

Writes `results/report.json` and `results/RESULTS.md`. Both are stamped with the commit and whether the tree was dirty. `results/` is gitignored — the report is meant to be regenerated, never trusted from a checkout.

---

## Remaining work

| # | Task | Blocked on |
|---|---|---|
| 1 | Confirm the submission deadline and submit | Razorpay never published it; third-party sources said **2026-09-05, which is today** — treat the build as submittable now |
| 2 | Record the walk-through video against the code as it stands at `e803e36` | nothing |
| 3 | Decide whether to deploy the public Streamlit demo | nothing; `streamlit_app.py` is ready |
| 4 | Re-run `make eval` immediately before submitting so `RESULTS.md` carries a clean-tree stamp at the final commit | nothing |

## Explicitly out of scope

These were planned and deliberately not built. Do not add them under deadline pressure — see `01_PROJECT_STATE.md` §Not built.

- **Red-team mode** (`app/ui/red_team.py`, nine attack cards). The Safety tab's executed invariant checks cover the intent.
- **Competing-agent arbitrator** (`app/arbitration/`, 12 simulated agents). Arbitration is the shared atomic contact budget; the effect is measured via the A1 vs A2ns arm contrast.

## Rule for whoever picks this up

Establish state by running the suite, not by reading a status file. This project's own status documents were wrong for four days — see the note at the top of `01_PROJECT_STATE.md`.
