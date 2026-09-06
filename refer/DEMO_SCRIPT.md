# 5-minute demo script

**Unified Recovery Engine · Razorpay AI Buildathon 2026 · Track 3**

---

## Before you start (2 minutes, off camera)

```bash
# 1. one command starts dashboard + webhooks + follow-up worker
PORT=8555 .venv/Scripts/python.exe -m app.server

# 2. the tunnel, so Razorpay can reach you
./scripts/start_tunnel.ps1
```

Then check, in this order:

- [ ] `curl -s localhost:8555/health` shows `followup_hour_seconds: 0.05` and `worker_interval_seconds: 2`
      — if it says `3600`/`60` the server started before the demo settings and **your escalation will take 8 days on stage**
- [ ] Dashboard open at `localhost:8555`, **Live test (CSV)** tab
- [ ] Board reset: expand *Reset the board* → tick confirm → **Clear N unpaid**. Keeps the paid cases as evidence.
- [ ] Your **email inbox open on a second screen**, and your **phone visible**
- [ ] `demo_customers.csv` ready to drag in

> **Dispatch is live.** Every upload sends a real email. Only ever use a CSV with your own address.

---

## 0:00 – 0:35 · The problem, and the one idea

> "Revenue doesn't vanish in one step. A payment fails, a checkout is abandoned, an invoice goes overdue. Most recovery today is a fixed rule — retry twice, email, then call — that fires whether or not it helps, and nobody can attribute a rupee to it.
>
> This engine treats **every contact as a decision with a number attached.** For each case it estimates the incremental effect of each action *against doing nothing*, converts it to expected value against the amount at risk, and picks the best one.
>
> `NO_ACTION` scores exactly zero by construction. So when nothing clears the bar, **it contacts nobody.** That abstention is the product — it's what stops a recovery engine becoming a harassment engine."

---

## 0:35 – 1:30 · Upload a CSV, watch a real email arrive

**Do:** drag `demo_customers.csv` onto the uploader.

> "This is a merchant's receivables export. Six columns. Notice there is **no 'reason' column** — a merchant knows *what* is owed, not *why* it's unpaid. If they typed the reason in, the diagnosis would be a formality reading back its own input.
>
> One row is deliberately malformed. It's rejected with a reason rather than silently skipped, because a dropped row is revenue the merchant believes is being chased and nothing is chasing."

**Do:** point at the board as rows appear. Then switch to your inbox.

> "That email is real. It went out over SMTP seconds ago. The amount, the name and the due date are read back from the row you just uploaded — nothing downstream re-types a number."

---

## 1:30 – 2:30 · Why it chose that — the differentiator

**Do:** click **Decision trace**.

> "This is the part most recovery demos can't show: *why*.
>
> Eight stages. Stage 1 diagnoses the cause. Candidate generation offers only actions this stream can legally take — a merchant-uploaded debt has no stored instrument, so a **retry is never even a candidate**.
>
> Then the safety filter." *(point at the amber steps marked SUPPRESSED)* "Three actions removed before any scoring happened — agent dial, WhatsApp, IVR — all rejected with `ESCALATION_CEILING`. The engine is not allowed to open a relationship with a phone call.
>
> And the answer: expected value **₹5,250**, from `EV = round(Δ̂ × amount) − cost`. Every number on this screen is read from the executed decision. Nothing is scripted."

---

## 2:30 – 3:30 · It escalates on its own

**Do:** return to the board. Wait ~10s, refresh. Then again.

> "Nothing external triggers the next step. The engine scheduled its own review, and a background worker wakes it.
>
> The timing is **derived, not configured**: `base(diagnosis) × multiplier(channel) × backoff(attempt)`. A gateway blip is retried in about 4 hours. An overdue invoice waits about 8 days — because chasing a finance team daily gets your domain filtered.
>
> I've compressed the clock for this demo — one policy hour is 0.05 seconds. **Only the unit changes; every ratio is exact.** An invoice still waits fifty times longer than a gateway failure."

**Do:** point at the ladder chips lighting up as rungs are earned.

> "One rung at a time. The ceiling is always the highest **confirmed** contact plus one — never plus two, whatever the score says. And a message that failed to send earns nothing: a lit rung is a claim that something actually arrived."

*(If the IVR rung fires, your phone rings — let it. That's the strongest 10 seconds available.)*

---

## 3:30 – 4:10 · Payment always wins

**Do:** point at the green `PAID` row already on the board.

> "That one is a real ₹25,000 test payment I made yesterday. Razorpay's webhook hit this machine, HMAC-verified, and the case closed itself: status PAID, open links cancelled, scheduled follow-ups stopped.
>
> Case state is re-read at the *moment of dispatch*, not when the action was queued — so money arriving cancels everything already in flight. A customer who has paid cannot be chased by something mid-air."

**Do:** click **Open** on that row to show the timeline.

> "`CASE_CREATED → AGENT_DECIDED → PAYMENT_LINK_CREATED → MESSAGE_SENT → FOLLOWUP_SCHEDULED → PAYMENT_RECEIVED → CASE_CLOSED`."

---

## 4:10 – 5:00 · The honest part

**Do:** click **Safety**.

> "These three checks **executed when this page loaded** — that's what the count says. Below them are six more enforced structurally and covered by the test suite, listed deliberately **without ticks**, because this page didn't run them. A green tick not backed by a live check is the thing this screen exists to avoid."

**Do:** click **Experiment**, then **Run benchmark**.

> "And the result I'd rather you heard from me. We pre-registered an experiment predicting the ML model would beat the transparent heuristic. **That prediction was falsified.** A5 versus A3 is inconclusive — p = 0.96.
>
> The finding is more interesting than a win: compliant escalation bounds the action space so tightly that scorer quality is nearly irrelevant. The two scorers disagree on 4 decisions in 1,000.
>
> The one significant result is the engine against doing nothing. **That** is where the value is — in safety, arbitration and contact efficiency, not in a model being cleverer than a rule.
>
> 521 tests. 24 architecture decision records. The evaluation reproduces bit-for-bit on a fresh clone."

---

## If something breaks

| Symptom | Say this, then move on |
|---|---|
| Email doesn't arrive | "SMTP is a live dependency — the dispatch log shows `SENT` with the provider id." Show the timeline. |
| No escalation appears | Check `/health` for `followup_hour_seconds`. If it's 3600, say "real-time timing" and show the *scheduled* next review instead. |
| WhatsApp shows FAILED | **Use it.** "That's Twilio's actual refusal — `ContentSid Required`, a paid feature. The engine records FAILED and does **not** advance the ladder, because a rung only lights on confirmed delivery." |
| SMS arrives with odd wording | "Trial accounts can only send predefined templates, so the payment link isn't included — and the record says exactly that rather than claiming success." |
| Payment doesn't close a case | Show `scripts/send_test_webhook.py` output instead: the receiving path is independently provable. |

---

## Three lines worth landing

1. **"NO_ACTION scores exactly zero, so the engine abstains when nothing is worth sending."**
2. **"A lit rung is a claim that a message arrived — so a failed send earns no escalation."**
3. **"We pre-registered a prediction, it was falsified, and we report that."**

## Do not say

- Any recovery-uplift percentage attributable to the AI — your own experiment falsified it
- That the ₹13.6M figure is real money — it is a simulation, and the README says so
- That WhatsApp works — it is implemented and provider-gated
