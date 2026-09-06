# 5-minute demo script

**Unified Recovery Engine · Razorpay AI Buildathon 2026 · Track 3**

```
0:00 – 0:50   GitHub: the README and the architecture
0:50 – 1:10   Decision trace, in two sentences
1:10 – 1:45   Experiment: the result, including the one against us
1:45 – 2:10   Safety and tests
2:10 – 5:00   The live run
```

Each section carries a **⚠ What broke here** box: a real defect found in this project and
how it was fixed. They are **optional narration** - the timings above assume you skip them.
Use one or two where you have slack, or keep them in reserve for questions. A bug you found
in your own system and can explain is worth more than a feature you can only describe.

**If you only tell one**, tell the payment one under *Payment always wins*: a verified real
payment that failed to close its case, surviving 395 passing tests.

---

## Before you start (2 minutes, off camera)

```bash
PORT=8555 .venv/Scripts/python.exe -m app.server    # dashboard + webhooks + worker
./scripts/start_tunnel.ps1                          # so Razorpay can reach you
```

- [ ] `curl -s localhost:8555/health` → `followup_hour_seconds: 0.05`, `worker_interval_seconds: 2`
      — if it reads `3600`/`60` the server predates the demo settings and **escalation takes 8 days on stage**
- [ ] **Run the Experiment benchmark once now** so results are on screen when you arrive
- [ ] Board reset → tick confirm → **Clear N unpaid**. Keeps paid cases as evidence.
- [ ] Tabs open: GitHub README, dashboard, inbox. Phone visible.
- [ ] `demo_customers.csv` ready to drag

> **Dispatch is live.** Every upload sends a real email. Only ever use a CSV with your own address.

---

## 0:00 – 0:50 · GitHub: README and architecture

**Do:** open the repo README. Scroll to the **mermaid flow diagram**.

> "One engine that finds revenue at risk across four streams — failed payments, abandoned checkouts, failed renewals, overdue receivables — decides what to do about each, and runs the recovery to completion on its own.
>
> The architecture is one loop." *(trace the diagram with the cursor)*
>
> "An event arrives, from a webhook or a merchant CSV. **Stage 0** checks there's genuine recoverable exposure. **Stage 1** diagnoses why it's unpaid. **Candidate generation** lists what's even legal for this stream. **The safety filter** removes what isn't permitted — outage suppression, contact budget, the escalation ceiling. Whatever survives is **ranked by expected value**, and the best one is executed.
>
> Then it schedules its own next review and goes quiet. A background worker wakes it, it re-reads the case, and decides again — until the money arrives or a stopping rule ends it."

**Do:** scroll to the escalation ladder diagram.

> "Contact climbs one rung at a time: email, SMS, WhatsApp, an IVR call, a human agent. And the ceiling is always the highest **confirmed** contact plus one — never plus two, whatever the score says.
>
> Everything below the fold is honesty: what's simulated, what's real, and the result that went against us."

**Do:** name the external surface — it's short, and saying it out loud shows the integration is real.

> "Four external services actually get called.
>
> **Razorpay** — the Payment Links API to create and cancel links, and signed webhooks coming back, HMAC-SHA256 verified, fail-closed.
> **Gmail SMTP** — the email that actually reaches the customer.
> **Twilio** — SMS, WhatsApp and voice, with the IVR fetching TwiML from our own signed endpoint.
> **Meta's WhatsApp Cloud API** — implemented as a second provider, because Twilio's WhatsApp can't be exercised on a free account.
>
> Everything else is deliberately boring: **SQLite** in WAL mode, **Starlette** for the webhook server, **Streamlit** for this dashboard, **CatBoost** for the scorer, and **ngrok** for a reserved public URL so Razorpay can reach a laptop. No queue, no Redis, no Docker, and **no LLM anywhere on the decision path** — a decision to chase someone for money has to be reproducible from a number."

---

## 0:50 – 1:10 · Decision trace, in two sentences

**Do:** dashboard → **Decision trace**.

> "This screen answers one question — *why did the engine do that?* — for a single case, from raw event to final action, with every value read from the executed decision record.
>
> Eight stages, and you can see exactly where the decision was made and where things were removed." *(point at the amber SUPPRESSED steps)* "Three actions rejected before any scoring happened, all `ESCALATION_CEILING`: the engine is not allowed to open a relationship with a phone call."

---

## 1:10 – 1:45 · The result, including the one against us

**Do:** **Experiment**. Results already on screen.

> "Five arms over an identical seeded batch, each isolating one capability.
>
> We pre-registered a hypothesis: that the machine-learning model would beat the transparent heuristic. **It was falsified.** A5 versus A3 — inconclusive, p = 0.96." *(point)*
>
> "The finding is better than a win. Compliant escalation bounds the action space so tightly that scorer quality is nearly irrelevant — the two scorers disagree on **4 decisions in 1,000**. The one significant result is the engine against doing nothing.
>
> Every comparison is on screen, including the four inconclusive ones. Showing only the flattering one is how an honest experiment becomes a marketing chart."

**⚠ What broke here** *(say it if you have 15 seconds — it is the strongest thing on this screen)*

> "The model looked like it was losing, and the first instinct was to tune it. Instead we looked for a reason and found a **train/serve mismatch**: the contact ledger was being stamped from wall-clock time instead of decision time, which killed the escalation ladder in every evaluation run. **The model was being graded in a world that didn't exist.**
>
> We fixed the clock, re-ran it, and the prediction was *still* falsified. That's the result we're reporting."

---

## 1:45 – 2:10 · Safety and tests

**Do:** **Safety**.

> "These checks **executed when the page loaded** — that's what the count says, and a tick means it ran just now.
>
> Below them, six more enforced structurally and covered by the test suite, deliberately listed **without ticks**, because this page didn't run them. A green tick not backed by a live check is the thing this screen exists to avoid.
>
> **523 tests. 24 architecture decision records. The evaluation reproduces bit-for-bit on a fresh clone** — I cloned it cold this morning and got the identical batch hash."

**⚠ What broke here**

> "Two things this suite didn't catch until we went looking.
>
> The **contact ledger was recording the simulator's outcome, not the dispatcher's** — a row stamped EXECUTED with a payment outcome nine milliseconds after creation, six seconds before the email actually left. Dry runs were recorded as real contacts. That matters because the ledger drives the escalation ceiling and the handoff report, so a fabricated contact would escalate toward a phone call for a message nobody received.
>
> And the **test suite was reading the developer's `.env`** — enabling dispatch for a live demo meant tests ran with real sending enabled and live credentials loaded. One test caught itself; nothing protected the rest. Now a session fixture forces every outbound gate closed."

---

## 2:10 – 3:00 · Live: upload a CSV, a real email goes out

**Do:** **Live test (CSV)**. Drag `demo_customers.csv` in.

> "A merchant's receivables export. Six columns — and notice there's **no 'reason' column**. A merchant knows *what* is owed, not *why* it's unpaid. If they typed the reason in, the diagnosis would be a formality reading back its own input.
>
> One row is deliberately malformed. Rejected with a reason, not silently skipped — a dropped row is revenue the merchant thinks is being chased and nothing is chasing."

**Do:** switch to your inbox.

> "That email is real, sent over SMTP seconds ago. The amount, the name and the due date are read back from the row you just uploaded. Nothing downstream re-types a number."

**⚠ What broke here**

> "A customer with a **valid phone and no email was never contacted at all** — zero times, indefinitely, while the debt sat recoverable. Receivables enter the ladder at email, nothing checked whether an address existed on that channel, the send was skipped, so the contact was never confirmed, so the ceiling never rose. The engine offered the same impossible action forever.
>
> Now an unreachable channel is rejected outright, and the ladder skips to the lowest rung that can actually reach them."

---

## 3:00 – 4:00 · It escalates on its own

**Do:** back to the board. Wait ~10s, refresh. Again.

> "Nothing external triggers the next step. The engine scheduled its own review; a background worker wakes it.
>
> Timing is **derived, not configured**: `base(diagnosis) × multiplier(channel) × backoff(attempt)`. A gateway blip is retried in about 4 hours; an overdue invoice waits about 8 days, because chasing a finance team daily gets your domain filtered.
>
> I've compressed the clock for this demo — one policy hour is 0.05 seconds. **Only the unit changes; every ratio is exact.**"

**Do:** point at the ladder chips lighting.

> "A lit rung means a message was **confirmed sent**. A message that failed earns nothing — so a broken channel can never walk the ladder up to a phone call."

**⚠ What broke here**

> "Razorpay's payment links carry a `notify` flag, and we had it on. So **Razorpay was sending its own SMS and email** on top of ours — three messages for a one-rung decision, none of them through our dispatcher, none in the ledger. The escalation ladder, the contact budget and the quiet period were all being bypassed by sends the engine couldn't see. Ownership of contact is now an explicit setting.
>
> And Twilio: a trial account rejects inline TwiML for voice. So the engine **serves its own TwiML from a signed endpoint** — HMAC'd, because Twilio fetches it with no credentials and a bare case id would read a customer's name and debt aloud to anyone who guessed one."

*(If the IVR rung fires, your phone rings. Let it.)*

---

## 4:00 – 4:40 · Payment always wins

**Do:** point at the green `PAID` row, then click **Open**.

> "A real ₹25,000 test payment. Razorpay's webhook hit this machine, HMAC-verified, and the case closed itself — PAID, open links cancelled, follow-ups stopped.
>
> Case state is re-read at the *moment of dispatch*, not when the action was queued. Money arriving cancels everything already in flight."

> "`CASE_CREATED → AGENT_DECIDED → PAYMENT_LINK_CREATED → MESSAGE_SENT → FOLLOWUP_SCHEDULED → PAYMENT_RECEIVED → CASE_CLOSED`"

**⚠ What broke here** *(the best story in the project — use it if you have 20 seconds)*

> "The first time I actually paid this link, **the case didn't close.** The webhook arrived, passed HMAC verification, was recorded — and the case stayed open with a follow-up still scheduled. The engine was about to chase me for money I'd just paid. That survived 395 passing tests.
>
> Razorpay sent `payment.captured` and `order.paid`, not `payment_link.paid`. A payment-link entity carries our reference at the top level; a **payment** entity hides it inside `notes`. We were only reading the top level.
>
> And a second bug underneath it: cancelling the follow-up matched on the wrong column, so it updated zero rows and returned zero, and nothing checked. Both fixed — and the regression test uses the **actual payload Razorpay sent**, because a hand-written mock would have encoded the same wrong assumption that caused the bug."

---

## 4:40 – 5:00 · Close

> "`NO_ACTION` scores exactly zero by construction, so when nothing clears the bar the engine contacts nobody. **That abstention is the product** — it's what stops a recovery engine becoming a harassment engine.
>
> Every figure in the experiment is simulated and labelled as such. What's real is the loop: a real link, a real email, a real webhook, a real case closing."

---

## If something breaks

| Symptom | Say this, then move on |
|---|---|
| Email doesn't arrive | "SMTP is a live dependency — the dispatch log shows `SENT` with a provider id." Show the timeline. |
| No escalation appears | Check `/health`. If `followup_hour_seconds` is 3600, say "real-time timing" and show the *scheduled* next review. |
| WhatsApp shows FAILED | **Use it.** "Twilio's actual refusal — `ContentSid Required`, a paid feature. The engine records FAILED and does **not** advance the ladder, because a rung only lights on confirmed delivery." |
| SMS wording looks odd | "Trial accounts can only send predefined templates, so the link isn't included — and the record says exactly that rather than claiming success." |
| Payment doesn't close a case | Run `scripts/send_test_webhook.py`; the receiving path is independently provable. |
| Asked "is that your model deciding?" on the trace tab | "No — that screen says so. It's scored by base rates; the live CSV path uses the fitted CatBoost model. We measured it: across all seven scenarios the fitted model picks the identical action, because the safety filter already bounded the choice." |

---

## Three lines worth landing

1. **"`NO_ACTION` scores exactly zero, so the engine abstains when nothing is worth sending."**
2. **"A lit rung is a claim that a message arrived — so a failed send earns no escalation."**
3. **"We pre-registered a prediction, it was falsified, and we report that."**

## Do not say

- Any recovery-uplift percentage attributable to the AI — your own experiment falsified it
- That the ₹13.6M figure is real money — it is a simulation, and the README says so
- That WhatsApp works — it is implemented and provider-gated
