# CONTINUATION — handoff to the next engineer

**Written:** 2026-09-05 · **HEAD:** `5e41f95` · **Branch:** `main`
**Verified state:** 355 tests passing · 73 modules under `app/` · quality gate 6/6

Read sections 0–3 before writing any code. They will save you more time than they cost.

---

## 0. THE RULES. Do not break these.

These are not style preferences. Each one was learned by finding the bug that came from
violating it.

**0.1 — Do NOT rewrite the Recovery Engine.**
Nothing under `app/pipeline/`, `app/scoring/`, `app/ledger/`, `app/orchestration/` should
change. It is tested, evaluated, and its numbers are published in `results/report.json`.
Extend it by giving it better inputs, never by overriding its outputs.

**0.2 — If the engine gives a "wrong" answer, the input is wrong.**
This happened. The agent kept choosing `RECOMMEND_RETRY` and sending nothing. The instinct
is to force `EMAIL_LINK` in the loop. That would have been wrong: `build_event` was
declaring `event_type=FAILED_PAYMENT` for a CSV row that was a *receivable* — no charge was
ever attempted, so there was no instrument to retry. The engine was right about a lie it had
been told. Fix inputs, never outcomes.

**0.3 — Never report a send that did not happen.**
Every adapter returns `NOT_CONFIGURED` naming the exact missing env var, or `FAILED` with
the provider error. A demo that prints "Sent!" while sending nothing is worse than one that
sends nothing, because the viewer now believes something false — and this project's entire
argument is that its numbers can be trusted.

**0.4 — Dry run is the default.** `RECOVERY_DISPATCH_ENABLED` defaults to false. Tests must
never be able to send. Do not invert this "temporarily".

**0.5 — Payment always wins.** A `PAID` case can never produce an outbound contact. The
enforcement point is `ChannelDispatcher.dispatch()`, which **re-reads the case from the
database** and ignores any `Case` object it is handed. A passed-in case is stale by
construction. Do not "optimise" that re-read away.

**0.6 — Do not weaken a test to make it pass.** If a test is flaky, find the
nondeterminism. One test here was intermittent because ε-exploration is real; the fix was
to seed the *test*, not to remove exploration.

---

## 1. ENVIRONMENT — the trap that will cost you 20 minutes

**The system Python is 3.14 and CANNOT run this suite.** CatBoost/NumPy/SciPy have no 3.14
wheels. Bare `pytest` will show ~16 collection errors that have nothing to do with the code.

Always use the venv interpreter explicitly:

```bash
cd "C:/Users/Dell/Documents/New folder/Razorpay"
.venv/Scripts/python.exe -m pytest -q
```

`make setup` builds a correct venv via `scripts/bootstrap.py` (finds a 3.11–3.13, refuses
3.14 with an actionable message). `make test`, `make eval`, `make demo` all route through
the venv — never call bare `python` or `pytest`.

**Credentials are real and verified working** (`.env`, gitignored):
- Razorpay **test** key — confirmed creating real `plink_` links, `is_simulated: False`
- Gmail SMTP — confirmed `AUTH OK`
- `app/config_env.py` loads `.env` on import. An already-exported variable always wins.

⚠️ The Razorpay test secret was pasted into a chat log. **Regenerate it after the demo.**

---

## 2. WHAT IS DONE (verified, not claimed)

### The original engine — untouched
Stage 0 (+ TDS derivation), Stage 1 diagnosis, candidate generation, hard safety filter,
escalation ceiling, EV ranking, atomic contact reservation, attribution, follow-up
scheduling, retry/DLQ, reconciliation, replay guard, 5-arm evaluation.

### Built this session

| Package | What it does |
|---|---|
| `app/cases/` | `Customer`, `Case`, `PaymentLink`, `CaseEvent` + repository + CSV ingestion |
| `app/payments/` | `PaymentLinkService` — idempotent creation, **payment→case resolution** |
| `app/dispatch/` | `ChannelDispatcher`, channel adapters, rung-aware copy, HTML email |
| `app/agent/` | `RecoveryAgent` — the thin observe→delegate→act→record loop |
| `app/realtime/` | webhook ingestion, live downtime, follow-up scheduler, reliability |
| `app/reporting/` | unrecovered handoff Excel report |

### The blocker that was fixed
A customer paying through a recovery link produced `plink_...`, while every follow-up was
keyed on the original failure's `pay_...`. They never met, so a paying customer kept being
contacted. `CaseRepository.find_case_for_provider_entity()` now resolves **all four** id
shapes: `plink_`, `pay_`, our `reference_id`, and the engine's `opportunity_id`.

---

## 3. BUGS ALREADY FOUND — do not reintroduce these

Each was found by *running* the system, not reading it. If you touch the relevant area,
re-read this list.

1. **`payment.captured` → `FAILED_PAYMENT`.** A family-prefix fallback in `resolve_stream()`
   mapped *successes* to failures — the engine would have chased customers who had just
   paid. Event mapping is now **explicit-only**. Never add a prefix fallback.

2. **Ledger stamped from wall clock.** `resolved_at` came from `SystemClock` while decisions
   ran on the batch's time axis, so every prior contact looked like a different epoch, the
   quiet period was permanently active, and the escalation ladder **never advanced in any
   run**. The control was live in code and dead in execution. Fixed by stamping the ledger
   from the supplied `decision_timestamp`.

3. **`INSERT OR IGNORE` on a unique delivery id** silently dropped the completion row, so
   every event showed as `ACCEPTED` forever. Now an upsert that advances one row in place.

4. **Replay protection was documented but never enforced.** `WEBHOOK_MAX_AGE_SECONDS` was in
   config and on `/health` while nothing checked it. A documented-but-absent control is
   worse than a missing one.

5. **SQLite connections are thread-bound.** Starlette acknowledges on the event loop and
   processes on a worker thread. A shared connection raises on the first background write —
   *behind an already-sent 202*, so it fails invisibly. Everything is thread-local now.

6. **The live path ran an UNFITTED model.** Agent and listener built a bare
   `RecoveryOrchestrator`, whose CatBoost is not fitted; it silently falls back to cold-start
   baselines and abstains with `INSUFFICIENT_TRAINING_DATA`. The scorer being demonstrated
   was not the scorer being reported. Both now use
   `build_orchestrator_for_arm(ExperimentArm.A5, db_conn=...)`.

---

## 4. WHAT TO DO NEXT — in order

### PHASE 5 (finish it) — Demo A end to end · **THE ONLY MILESTONE THAT DECIDES SUCCESS**

The code path exists and works in dry run. What remains is the live proof.

**4.1 — External setup (the human must do this).**
```bash
# terminal 1
cd "C:/Users/Dell/Documents/New folder/Razorpay" && .venv/Scripts/python.exe -m app.api.webhook_listener
# terminal 2
winget install --id Cloudflare.cloudflared      # then reopen the shell
cloudflared tunnel --url http://localhost:8000
```
Register in Razorpay **Test Mode** → Account & Settings → Webhooks:
- URL `https://<tunnel>/webhooks/razorpay`
- Secret = the exact `RAZORPAY_WEBHOOK_SECRET` from `.env`
- Events: `payment_link.paid`, `payment.captured`, `order.paid`, `payment.failed`,
  `payment_link.expired`, `payment_link.cancelled`, `invoice.partially_paid`,
  `invoice.expired`, `payment.downtime.started`, `payment.downtime.resolved`

**Verify before involving Razorpay** — this exercises tunnel + HMAC + replay + mapping
without needing a payment, so a failure localises instantly:
```bash
.venv/Scripts/python.exe scripts/send_test_webhook.py --url https://<tunnel>
```
Expect `HTTP 202`. A `401` means the secret in `.env` differs from the server's (restart the
server after editing `.env`).

**4.2 — What you still need to write.** A `run_demo` entrypoint or Streamlit action that:
1. `parse_csv()` → `create_cases()`
2. `RecoveryAgent(conn).run_cycle(case_id)` per case
3. Show decision + reasoning + link + dispatch status

Set `RECOVERY_DISPATCH_ENABLED=true` only when demonstrating.

**Acceptance:** a real email lands in Gmail, `PAY NOW` opens the correct Razorpay test
checkout, a test-success payment fires `payment_link.paid`, and the case becomes `PAID` with
follow-ups cancelled. **Stop and verify this before building anything else.**

### PHASE 10 — Dashboard case timeline · **DO THIS SECOND**
The loop works but is **invisible**. A judge cannot watch a SQLite table. `app/ui/dashboard.py`
has a `Live test (CSV)` tab already; add a case list + per-case timeline reading
`CaseRepository.timeline(case_id)`. Target:
```
09:01  Agent selected EMAIL_LINK
09:01  Email sent
11:35  PAYMENT RECEIVED  →  CASE CLOSED
```
This turns architecture into something a person can see. Higher value than any new channel.

### PHASE 13 — Clean-environment run
Fresh clone → `make setup` → `make test` → full demo. Catches what only breaks on someone
else's machine, and a judge *is* someone else's machine.

### THEN, if time allows (in this order)
- **Twilio WhatsApp** — user has a 30-day trial. The **Sandbox needs no Meta template
  approval**, which removes the biggest schedule risk. Recipient must text `join <code>`
  first, and the sandbox session expires after ~24h of inactivity — re-join on demo day.
- **Twilio Voice/IVR** — real calls to *verified* numbers. Adapter already written.
- **Promise-to-pay** — see §6.
- **SMS** — see §6, it is not what it looks like.

---

## 5. DELIBERATELY NOT DONE — say these out loud, do not hide them

- **No contact-budget time window.** The cap is lifetime-per-customer with no monthly reset.
  A production system needs a rolling window.
- **No rate limiting** on the webhook endpoint.
- **No circuit breaker** on the outbound Razorpay API.
- **Unbounded backpressure** — a burst spawns unbounded background tasks.
- **`subscription.*` events unavailable** on this Razorpay account → live traffic reaches
  **3 of 4 streams**. The fourth exists only in batch evaluation.
- **ADR-0021…0026 are cited in code but do not exist.** `followup.py`, `copy.py`,
  `unrecovered.py`, `dispatcher.py`, `csv_ingest.py`, `loop.py` all reference them. Write
  them, or a reviewer following a citation hits nothing. **~30 min, high credibility value.**
- **Follow-up delays are in hours**, so they will not fire during a live demo. If you want to
  show the sequence on stage, add a compression multiplier — clearly labelled so nobody
  mistakes it for the production schedule.

---

## 6. TRAPS SPECIFIC TO THE REMAINING WORK

**SMS in India is not a Twilio problem.** TRAI mandates **DLT registration** — sender header
and every template registered with an Indian operator. A Twilio trial does not bypass it;
carriers scrub unregistered traffic. **Razorpay's own `notify: {sms: true}` is the viable
path**, since Razorpay holds its own registration. *Unverified:* whether Razorpay Test Mode
actually dispatches those notifications — sandboxes commonly suppress them. Test it; do not
claim live SMS delivery until you have seen one arrive.

**Promise-to-pay without WhatsApp.** If Meta/Twilio slips, a **response form** gives it on
email alone with no approvals: `[I'll pay by ___] [Request extension] [This isn't me]`.
Signed links to our own backend emitting domain events directly — confidence 1.0, because
the customer *chose* the intent rather than an LLM inferring it. `WRONG_PERSON` is also a
real safety signal we currently cannot receive. ~2 hours, fully in your control.

**The agent is deliberately non-deterministic.** ε-exploration (ADR-0004) means it will
occasionally abstain. That is a feature, not a bug — but a judge could see `NO_ACTION`.
Either seed the demo path or say it out loud: *"it explores, and here is the abstention."*

**Do not build a second decision engine.** `app/agent/loop.py` is thin on purpose. The
temptation is "just a little" logic — a special case for invoices, a shortcut for small
amounts. That is how the audited engine stops being the one that decides. If a question is
about WHETHER or WHICH, it belongs upstream.

---

## 7. HONESTY CONSTRAINTS — non-negotiable

This project's strongest asset is that its numbers can be trusted. Do not spend that.

- **Everything is synthetic** unless a real webhook produced it. Say so on every screen.
- **Do not claim AI uplift.** Measured: `A2−A1 = −0.0148` (inconclusive), `A5−A3 = +0.0005`
  (inconclusive). CatBoost does **not** beat the heuristic. Policy determines 99.6% of
  decisions. That finding — *the controls matter more than the model* — is stronger than a
  fake win, and it is defensible because it was pre-registered and falsified honestly
  (ADR-0020).
- **Do not tune a result.** If a number is unflattering, report it.
- Position as **Autonomous Revenue Recovery**, not "AI Payment Reminder". The claim is:
  *recover revenue with the minimum necessary intervention, and stop the instant payment is
  verified.*

---

## 8. QUICK REFERENCE

```bash
cd "C:/Users/Dell/Documents/New folder/Razorpay"

.venv/Scripts/python.exe -m pytest -q                    # 355 expected
.venv/Scripts/python.exe -m app.api.webhook_listener     # webhook server :8000
.venv/Scripts/python.exe scripts/send_test_webhook.py    # signed self-test
.venv/Scripts/python.exe -m streamlit run app/ui/dashboard.py --server.port 8555
make eval                                                # regenerates results/
```

**Key files**
| Purpose | File |
|---|---|
| Payment→case resolution (the blocker fix) | `app/cases/repository.py::find_case_for_provider_entity` |
| Payment-always-wins enforcement | `app/dispatch/dispatcher.py::precheck` |
| The agent loop | `app/agent/loop.py::run_cycle` |
| CSV validation | `app/cases/csv_ingest.py::parse_csv` |
| Email content | `app/dispatch/copy.py` + `email_template.py` |
| Webhook entry | `app/api/webhook_listener.py::handle_razorpay_webhook` |
| Live config / safety gates | `app/realtime/config.py` |

**Decision principle the engine uses** (quote this to a judge):
```
Δ̂(x,a) = p̂(x,a) − p̂(x, NO_ACTION)
EV(x,a) = round(Δ̂ × amount_paise) − cost(a)
choose argmax EV over ELIGIBLE candidates
```
`NO_ACTION` has EV = 0 by construction, so any action must beat *doing nothing* in expected
rupees or the engine abstains. A 90%-likely channel is worth ₹0 if the customer would have
paid anyway — which is what stops the engine claiming self-cures.

---

## 9. IF YOU ONLY HAVE ONE HOUR

1. Register the webhook (§4.1) — 10 min, and nothing else can be proven without it
2. Run Demo A live and fix whatever breaks — 30 min
3. Write ADR-0021…0026 — 20 min

That is a working, honest, defensible submission. Everything else is breadth.
