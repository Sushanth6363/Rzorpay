# JUDGE GUIDE — Unified Recovery Engine

**Verified at**: commit `e803e36`, clean tree, 2026-09-05 · **481 tests passing**
**Project**: Razorpay AI Buildathon 2026 · Track 3 — AI Revenue Recovery

> Restamped 2026-09-05. The version dated 2026-09-01 described the pre-`600f6ad` dashboard —
> four tabs that no longer exist — and port 8501. Both are corrected below.

---

## 1. Executive Summary & Prototype Boundary

The **Unified Recovery Engine** is a multi-tenant AI decision and closed-loop recovery
orchestration system: one engine over four revenue-leak streams, deciding the right
intervention and executing a bounded, compliant recovery workflow.

### ⚠️ Critical Prototype Boundary Notice

- **Every recovery outcome is simulated.** There is no live payment system and no real
  customers. Interventions, customer responses and recovery outcomes come from a deterministic
  local simulator (`SandboxSimulator`). Confidence intervals quantify sampling error *inside the
  simulation only*.
- **Nothing leaves the machine by default.** Outbound dispatch is off unless
  `RECOVERY_DISPATCH_ENABLED` is set, and a live `rzp_live_` key is refused unless
  `RECOVERY_ALLOW_LIVE_CREDENTIALS` is *separately* set. With no credentials configured the
  engine runs fully and dry-runs every send.
- **A real integration path exists and is off, not absent.** `app/api/webhook_listener.py`
  accepts HMAC-verified Razorpay webhooks (fail-closed: no secret configured → 401) and
  `app/dispatch/` can really send email/SMS/WhatsApp/IVR. That is the "Live test" tab. It is
  gated, not simulated — do not read this guide as saying the code cannot send.
- **Deterministic local execution.** Python 3.12 + SQLite WAL + CatBoost S-learner. No
  PostgreSQL, Redis, Kafka, or LLM on the decision path (ADR-0002, ADR-0007).
- **Under the simulator, the model does not beat the transparent heuristic.** A5 vs A3 is
  inconclusive (+0.0005) and the primary A2−A1 comparison is **INCONCLUSIVE** (−0.0148,
  p=0.1846). Both are reported rather than tuned away; ADR-0020 explains why.

---

## 2. Quick Start

### Option A: One-command launcher (recommended)
```bash
python run_demo.py
```
Runs the quality gate **first** — 481 tests plus a secret scan — and refuses to launch if it
fails, then serves the dashboard on `http://localhost:8555`.

### Option B: `make`
```bash
make demo
```

### Option C: Direct
```bash
.venv/Scripts/python.exe -m streamlit run app/ui/dashboard.py --server.port 8555
```
On macOS / Linux use `.venv/bin/python`. First time on any platform, run
`python scripts/bootstrap.py` — it builds a `.venv` on a supported interpreter (**3.11–3.13; not
3.14**, which has no wheels for the pinned scientific stack).

### Option D: Full regression suite (481 tests)
```bash
.venv/Scripts/python.exe -m pytest
```

### Option E: The numbers rather than the UI
```bash
make eval
```
Writes `results/report.json` and `results/RESULTS.md`, each stamped with the commit and whether
the tree was dirty. `results/` is gitignored — regenerate it, never trust a checked-in copy.

---

## 3. Recommended Judge Exploration Flow

The dashboard has **five tabs**: `Decision trace` · `Experiment` · `Live test (CSV)` · `Safety` ·
`About`.

### Tab 1 — Decision trace: "Why did the engine do this?"
1. Pick any of the **12 golden scenarios** from the dropdown.
2. Follow one opportunity from raw event through Stage 0 validation, Stage 1 diagnosis,
   candidate generation, safety filter, EV ranking, ledger reservation, execution and
   attribution. **Every value is read from the executed decision record — nothing is scripted.**
3. Use the sidebar to change the world the engine sees — force an **HDFC outage**, **exhaust a
   contact budget**, or change the **seed** — then re-read the trace.
4. Scenarios worth testing:
   - **Successful retry** — intervention delivered, payment recovered, attribution > ₹0.
   - **Natural self-cure** — `NO_ACTION` baseline, payment arrives anyway → **₹0 AI
     attribution** (INV-8).
   - **Self-cure before delivery** — payment precedes outreach → still **₹0** (INV-8).
   - **Gateway outage** — hard safety filter rejects retries regardless of EV (INV-4).
   - **Contact budget exhausted** — atomic reservation fails, nothing is sent (INV-2).
   - **Execution unknown** — ambiguous delivery enters the reconciliation ladder
     (`RECONCILED_DELIVERED` / `NOT_SENT` / conservative slot hold `UNRESOLVED`) (INV-6).

### Tab 2 — Experiment: the five-arm comparison
1. Set the seed range (defaults 21–25) and opportunity count, then **Run benchmark**.
2. All arms consume an **identical seeded batch** from the same generator the CLI evaluation
   uses (`app/experiment/batch.py`), so these numbers describe the same batch as
   `results/report.json`.
3. Read the **primary pre-registered metric (A2 vs A1)**: incremental recovery rate, 95%
   Newcombe CI, p-value, and verdict. Expect `INCONCLUSIVE` — that is an honest outcome at this
   sample size, not a hidden failure.
4. Read the **contact-efficiency** figures. This is the axis the engine is actually for:
   A1 spends 1,500 contacts (22.73 per customer) for recovery statistically indistinguishable
   from A2's 1,336 (20.24). Each comparison isolates one capability; secondaries are
   Holm-Bonferroni corrected.

### Tab 3 — Live test (CSV): the one screen where a decision leaves the machine
1. Download the sample CSV, or upload one with **your own** email and phone.
2. The real engine decides — Stage 0, diagnosis, EV ranking, safety filter — and then sends what
   it chose over email/SMS/WhatsApp/IVR.
3. With no channel credentials set it **dry-runs** and still shows every decision. The tab states
   per-channel readiness before you upload.

### Tab 4 — Safety: invariants that execute
1. `INV-1` … `INV-9` are **run when the page loads**. A tick means the check ran and passed just
   now — not that a document claims it.
2. There is no red-team mode; it was planned and never built (`01_PROJECT_STATE.md` §Not built).
   These executed checks are what covers that intent.

### Tab 5 — About: the honest framing, restated in the product itself

---


## 4. Key AI Concepts Explained

### 1. Incremental Recovery Uplift (Not Direct Recovery)
The AI does **not** "recover money" directly. It estimates:
$$\Delta P = P(Y=1 \mid X, \text{action}) - P(Y=1 \mid X, \text{NO\_ACTION})$$
An intervention is recommended **only if** $\Delta P > 0$ and Expected Value ($\Delta P \times \text{Amount} - \text{Cost}$) is positive.

### 2. Attribution Rule: Intervention Recovery vs Self-Cure (`INV-8`)
- **Intervention Recovered**: Delivered intervention followed by payment within attribution window $\rightarrow$ 100% of recovery value attributed to AI.
- **Self-Cure**: Payment under `NO_ACTION`, uncontacted baseline, or payment before outreach delivery $\rightarrow$ **₹0 AI Attribution**.

### 3. Contact Cap & Atomic Reservation (`INV-2`)
Contacts are capped (e.g. 5 attempts per customer/month). Budget reservation executes via atomic conditional SQL (`UPDATE contact_budgets SET reserved = reserved + 1 WHERE reserved + consumed < cap`). Failed reservations safely fall back to uncontacted evaluation without slot leakage.

---

## 5. Summary of Architecture Invariants (`INV-1` to `INV-9`)

- `INV-1` Tenant Isolation: Merchant ID salting for arm hashing and budget isolation.
- `INV-2` Atomic Contact Reservation: Database-enforced conditional reservation.
- `INV-3` Exploration Safety: Safety-rejected candidates cannot be chosen by exploration.
- `INV-4` Gateway Outage Safety: Known gateway outages reject retry actions.
- `INV-5` Retry Ownership: Single active recovery owner per opportunity.
- `INV-6` Execution Unknown: Ambiguous delivery resolves via reconciliation ladder.
- `INV-7` Point-in-Time Features: Post-decision leakage blocked from training vector.
- `INV-8` Self-Cure Attribution: Self-cures get strictly ₹0 AI attribution.
- `INV-9` NO_ACTION Counterfactual: Uncontacted baseline evaluated first.
