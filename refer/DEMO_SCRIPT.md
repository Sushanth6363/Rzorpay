# 5-minute demo script

**Unified Recovery Engine · Razorpay AI Buildathon 2026 · Track 3**

```
0:00 – 0:50   GitHub: the README and the architecture
0:50 – 1:10   Decision trace, in two sentences
1:10 – 1:45   Experiment: the result, including the one against us
1:45 – 2:10   Safety and tests
2:10 – 5:00   The live run
```

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

---

## 1:45 – 2:10 · Safety and tests

**Do:** **Safety**.

> "These checks **executed when the page loaded** — that's what the count says, and a tick means it ran just now.
>
> Below them, six more enforced structurally and covered by the test suite, deliberately listed **without ticks**, because this page didn't run them. A green tick not backed by a live check is the thing this screen exists to avoid.
>
> **521 tests. 24 architecture decision records. The evaluation reproduces bit-for-bit on a fresh clone** — I cloned it cold this morning and got the identical batch hash."

---

## 2:10 – 3:00 · Live: upload a CSV, a real email goes out

**Do:** **Live test (CSV)**. Drag `demo_customers.csv` in.

> "A merchant's receivables export. Six columns — and notice there's **no 'reason' column**. A merchant knows *what* is owed, not *why* it's unpaid. If they typed the reason in, the diagnosis would be a formality reading back its own input.
>
> One row is deliberately malformed. Rejected with a reason, not silently skipped — a dropped row is revenue the merchant thinks is being chased and nothing is chasing."

**Do:** switch to your inbox.

> "That email is real, sent over SMTP seconds ago. The amount, the name and the due date are read back from the row you just uploaded. Nothing downstream re-types a number."

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

*(If the IVR rung fires, your phone rings. Let it.)*

---

## 4:00 – 4:40 · Payment always wins

**Do:** point at the green `PAID` row, then click **Open**.

> "A real ₹25,000 test payment. Razorpay's webhook hit this machine, HMAC-verified, and the case closed itself — PAID, open links cancelled, follow-ups stopped.
>
> Case state is re-read at the *moment of dispatch*, not when the action was queued. Money arriving cancels everything already in flight."

> "`CASE_CREATED → AGENT_DECIDED → PAYMENT_LINK_CREATED → MESSAGE_SENT → FOLLOWUP_SCHEDULED → PAYMENT_RECEIVED → CASE_CLOSED`"

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
