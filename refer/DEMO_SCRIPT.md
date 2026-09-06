# 5-minute demo script

**Unified Recovery Engine · Razorpay AI Buildathon 2026 · Track 3**

```
0:00 – 1:00   Tour: what each screen is, and why it exists
1:00 – 1:30   Experiment: the result, including the one that went against us
1:30 – 2:15   Upload a CSV, a real email goes out
2:15 – 3:00   Decision trace: WHY it chose that
3:00 – 4:00   It escalates on its own, one rung at a time
4:00 – 4:35   Payment always wins
4:35 – 5:00   Safety, and the honest close
```

---

## Before you start (2 minutes, off camera)

```bash
PORT=8555 .venv/Scripts/python.exe -m app.server    # dashboard + webhooks + worker
./scripts/start_tunnel.ps1                          # so Razorpay can reach you
```

- [ ] `curl -s localhost:8555/health` shows `followup_hour_seconds: 0.05` and `worker_interval_seconds: 2`
      — if it says `3600`/`60`, the server started before the demo settings and **your escalation will take 8 days on stage**
- [ ] **Run the benchmark once now**, on the Experiment tab, so results are on screen when you get there
- [ ] Board reset: *Reset the board* → tick confirm → **Clear N unpaid**. Keeps paid cases as evidence.
- [ ] Inbox open on a second screen, phone visible
- [ ] `demo_customers.csv` ready to drag

> **Dispatch is live.** Every upload sends a real email. Only ever use a CSV with your own address.

---

## 0:00 – 1:00 · What you're looking at

> "One engine that finds revenue at risk across four streams — failed payments, abandoned checkouts, failed renewals, overdue receivables — decides what to do about each one, and then runs the recovery to completion on its own.
>
> Five screens, and each exists to answer a different question a reviewer would ask."

**Do:** click each tab as you name it. About 10 seconds each.

**Decision trace** — *"Why did it do that?"*
> "One case, followed from raw event to final action. Eight stages, every value read from the executed decision record. This is where you audit a single choice."

**Experiment** — *"Does it work, and how do you know?"*
> "Five arms over an identical seeded batch, each isolating one capability. Confidence intervals and verdicts — including inconclusive ones."

**Live test (CSV)** — *"Show me it actually running."*
> "A merchant uploads their receivables and the real engine runs: diagnosis, expected-value ranking, safety filter — and then it actually sends what it chose. This is the one screen where a decision leaves the machine."

**Safety** — *"What stops it doing something stupid?"*
> "Invariants that execute when the page loads and report real pass or fail. Not a checklist — executed checks."

**About** — *"What's not built, and what's simulated."*
> "The limitations, stated by us rather than found by you."

---

## 1:00 – 1:30 · The result, including the one that went against us

**Do:** you are on **Experiment**, results already on screen from pre-flight.

> "We pre-registered a hypothesis: that the machine-learning model would beat the transparent heuristic once outcomes depended on context.
>
> **It was falsified.** A5 versus A3 — inconclusive, p = 0.96." *(point at the row)*
>
> "The finding is more useful than a win would have been: compliant escalation bounds the action space so tightly that scorer quality is nearly irrelevant. The two scorers disagree on **4 decisions in 1,000**.
>
> The one statistically significant result is the engine against doing nothing." *(point at `A5_vs_CONTROL`)* "That's where the value is — safety, cross-stream arbitration and contact efficiency, not a model being cleverer than a rule.
>
> Every comparison is on screen, including the four that are inconclusive. Showing only the flattering one is how an honest experiment becomes a marketing chart."

---

## 1:30 – 2:15 · Upload a CSV, a real email goes out

**Do:** **Live test (CSV)** tab. Drag `demo_customers.csv` in.

> "A merchant's receivables export. Six columns — and notice there is **no 'reason' column**. A merchant knows *what* is owed, not *why* it's unpaid. If they typed the reason in, the diagnosis would be a formality reading back its own input.
>
> One row is deliberately malformed. Rejected with a reason, not silently skipped — a dropped row is revenue the merchant thinks is being chased and nothing is chasing."

**Do:** switch to your inbox.

> "That email is real, sent over SMTP seconds ago. The amount, the name and the due date are read back from the row you just uploaded. Nothing downstream re-types a number."

---

## 2:15 – 3:00 · Why it chose that

**Do:** **Decision trace**.

> "Stage 1 diagnoses the cause. Candidate generation offers only actions this stream can legally take — a merchant-uploaded debt has no stored instrument, so a **retry is never even a candidate**.
>
> Then the safety filter." *(point at the amber SUPPRESSED steps)* "Three actions removed before any scoring — agent dial, WhatsApp, IVR — all `ESCALATION_CEILING`. The engine is not allowed to open a relationship with a phone call.
>
> And the answer: expected value **₹5,250**, from `EV = round(Δ̂ × amount) − cost`. `NO_ACTION` scores exactly zero by construction, so when nothing clears the bar the engine contacts nobody. **That abstention is the product** — it's what stops a recovery engine becoming a harassment engine."

---

## 3:00 – 4:00 · It escalates on its own

**Do:** back to the board. Wait ~10s, refresh. Again.

> "Nothing external triggers the next step. The engine scheduled its own review and a background worker wakes it.
>
> Timing is **derived, not configured**: `base(diagnosis) × multiplier(channel) × backoff(attempt)`. A gateway blip is retried in about 4 hours; an overdue invoice waits about 8 days, because chasing a finance team daily gets your domain filtered.
>
> I've compressed the clock — one policy hour is 0.05 seconds. **Only the unit changes; every ratio is exact.**"

**Do:** point at the ladder chips lighting.

> "One rung at a time. The ceiling is always the highest **confirmed** contact plus one — never plus two, whatever the score says. A message that failed to send earns nothing, because a lit rung is a claim that something actually arrived."

*(If the IVR rung fires, your phone rings. Let it. Best 10 seconds available.)*

---

## 4:00 – 4:35 · Payment always wins

**Do:** point at the green `PAID` row, then click **Open**.

> "A real ₹25,000 test payment. Razorpay's webhook hit this machine, HMAC-verified, and the case closed itself — PAID, open links cancelled, follow-ups stopped.
>
> Case state is re-read at the *moment of dispatch*, not when the action was queued. So money arriving cancels everything already in flight. A customer who has paid cannot be chased by something mid-air."

> "`CASE_CREATED → AGENT_DECIDED → PAYMENT_LINK_CREATED → MESSAGE_SENT → FOLLOWUP_SCHEDULED → PAYMENT_RECEIVED → CASE_CLOSED`"

---

## 4:35 – 5:00 · The honest close

**Do:** **Safety**.

> "These checks executed when the page loaded — that's what the count says. Below them, six more enforced structurally and covered by tests, listed deliberately **without ticks**, because this page didn't run them. A green tick not backed by a live check is the thing this screen exists to avoid.
>
> Every figure in the experiment is simulated and labelled as such. What's real is the loop: a real link, a real email, a real webhook, a real case closing.
>
> **521 tests. 24 architecture decision records. The evaluation reproduces bit-for-bit on a fresh clone.**"

---

## If something breaks

| Symptom | Say this, then move on |
|---|---|
| Email doesn't arrive | "SMTP is a live dependency — the dispatch log shows `SENT` with a provider id." Show the timeline. |
| No escalation appears | Check `/health`. If `followup_hour_seconds` is 3600, say "real-time timing" and show the *scheduled* next review. |
| WhatsApp shows FAILED | **Use it.** "Twilio's actual refusal — `ContentSid Required`, a paid feature. The engine records FAILED and does **not** advance the ladder, because a rung only lights on confirmed delivery." |
| SMS wording looks odd | "Trial accounts can only send predefined templates, so the link isn't included — and the record says exactly that rather than claiming success." |
| Payment doesn't close a case | Run `scripts/send_test_webhook.py`; the receiving path is independently provable. |

---

## Three lines worth landing

1. **"`NO_ACTION` scores exactly zero, so the engine abstains when nothing is worth sending."**
2. **"A lit rung is a claim that a message arrived — so a failed send earns no escalation."**
3. **"We pre-registered a prediction, it was falsified, and we report that."**

## Do not say

- Any recovery-uplift percentage attributable to the AI — your own experiment falsified it
- That the ₹13.6M figure is real money — it is a simulation, and the README says so
- That WhatsApp works — it is implemented and provider-gated
