# comparison_old_vs_new.md — The Original Five vs What the Merchant Data Produced

Compiled 2026-08-25. Re-scores everything on the **identical Phase 13 weights** so the comparison is
apples to apples: priority 20% · impact 20% · novelty 15% · data 15% · feasibility 10% · agentic 10%
· demo 5% · headroom 5%.

---

## 1. The result

| Rank | Project | Score | Reach | Type | Origin |
|---|---|---|---|---|---|
| **=1** | **Agent-readable catalog (G1)** | **7.35** | **98.9%** | 💰 **creates revenue** | 🆕 NEW |
| **=1** | **Reconciliation Exception Resolver** | **7.35** | 1.1% | 💸 cost saving | original |
| **=3** | **Volume-blind risk (reframed #4)** | **7.30** | **98.9%** | 🛡️ prevents harm | 🆕 NEW |
| **=3** | Recovery Sequencer + headroom veto | 7.30 | <1% | ♻️ recovers loss | original |
| 5 | Promise-to-Pay + MSME statutory | 7.10 | <1% | ♻️ recovers loss | original |
| 6 | Freeze monitor *(original framing)* | 7.05 | 98.9% | 🛡️ prevents harm | original |
| 7 | Agentic Intent Verifier | 6.95 | 0.08% tier | 🛡️ prevents harm | original |
| 8 | Repeat-purchase engine (G2) | 6.65 | 98.9% | 💰 creates revenue | 🆕 NEW |

**Original five: best 7.35, mean 7.15. New three: best 7.35, mean 7.10.**

### ⭐ The honest headline: on the scoring model, nothing changed

The new work did **not** produce a better project by the weights. It produced **an equally good one
that reaches 90× more merchants and makes them money instead of saving them money.**

That difference is invisible to the scoring model — because **reach and profit-vs-loss were never
dimensions in it.**

---

## 2. What the model can't see

The Phase 13 weights measure *how good a submission is*. They never asked *how many merchants it
helps* or *whether it creates value or merely preserves it*. Add reach as a crude multiplier
(98.9% ≈ 1.35×, 1.1% ≈ 1.0×) and the order inverts:

| Project | Raw | Reach-weighted |
|---|---|---|
| **Agent-readable catalog** | 7.35 | **9.92** |
| **Volume-blind risk** | 7.30 | **9.86** |
| Freeze monitor (old framing) | 7.05 | 9.52 |
| Reconciliation | 7.35 | 7.35 |
| Recovery sequencer | 7.30 | 7.30 |

**Three of the top three become merchant-tier projects.** Reconciliation drops from joint-first to
fourth.

⚠️ **But do not over-read this.** The 1.35× multiplier is arbitrary — it is a thinking device, not a
measurement. And there is a genuine counter-argument in §5.

---

## 3. Which covers the huge gap

Two gaps, and they are different.

### Gap 1 — Reach: 1.1% → 98.9%

Four of the original five assume the merchant has a second gateway, a finance employee, a
subscription base, wholesale receivables or an ERP. **The average Razorpay merchant — ₹12.45 lakh a
year, ~208 transactions a month — has none of them.**

| Covers the reach gap | Doesn't |
|---|---|
| Volume-blind risk · Agent-readable catalog · Repeat-purchase engine | Reconciliation · Recovery · Promise-to-Pay · Intent verifier |

### Gap 2 — Type: everything was defensive

Of the original five: two recover losses, two prevent harm, one saves cost. **None creates revenue.**

That is a strange blind spot given **Track 1 is titled "Grow the merchant's revenue"** — a whole
track this research effectively conceded.

| Creates revenue | Preserves value |
|---|---|
| **Agent-readable catalog · Repeat-purchase engine** | all seven others |

**Agent-readable catalog is the only project that closes both gaps at once.** That is the single
strongest argument for it, and it isn't in the score.

---

## 4. What actually changed, item by item

| # | Original | What changed | Now |
|---|---|---|---|
| 1 | Reconciliation | Unchanged in quality. **Context changed:** three adjacent Razorpay products surfaced, and its reach was revealed as 1.1% | Still joint-best. **Safest**, not broadest |
| 2 | Recovery sequencer | Unchanged | Highest priority; worst competition; <1% reach |
| 3 | Promise-to-Pay | Unchanged | Emptiest competitive space; tiny reach |
| 4 | Freeze monitor | 🔄 **Materially reframed.** Was "help merchants stay under the threshold" — a compliance risk. Now **"the threshold is volume-blind; here's a rule that isn't"** | **7.05 → 7.30**, compliance risk 🔴 → 🟢, data 4 → 7 |
| 5 | Intent verifier | 🔄 **Partially superseded.** Its consumer-protection framing serves the 0.08% tier. G1 uses the same rail to serve 98.9% | Weakest of the originals |
| — | **Agent-readable catalog** | 🆕 **Reverses my Phase 3 advice.** I called it "no evidenced problem." The CAC data — **₹502 CAC vs ₹500 AOV** — evidenced it | **Joint-best, and the only revenue-creating option** |
| — | **Repeat-purchase engine** | 🆕 New | Good economics, but a crowded commercial category and Razorpay Engage exists |

### The two real reversals

**#4 was rescued by the data.** It went from "highest novelty but compliance-risky and unmeasurable"
to a defensible statistical claim with a testable decision rule. The merchant lens didn't just add
projects — it **fixed one that was nearly discarded.**

**G1 was resurrected by the data.** I explicitly advised against it in Phase 3 for having no
evidenced problem. The CAC arithmetic supplied one.

---

## 5. The counter-argument — why reach may not matter as much as it looks

**A judge is grading your submission, not your addressable market.**

`requirements.md` §6b puts only 10 of 100 points on "problem truth", and even there the ask is
*grounded and quantified* — not *widely applicable*. Nothing in Razorpay's published bars rewards
serving more merchants. What they reward is measured outcomes on a batch, honest failure reporting,
and bounded action.

**So reach improves your narrative, not your grade.**

That materially weakens the reach-weighted ranking, and it is why I am not simply declaring the new
projects winners. Reconciliation still has:

- the **best data** in the corpus (published schema + published defect list + synthetic explicitly sanctioned)
- the **lowest build risk** (MVP in under half the window)
- the **least crowded track** (24 repos vs ~100 in Track 1)
- a novelty claim that survives every sensitivity scenario tested

G1 has none of those advantages. It has ~100 competing repos in its track, and its demand side is
genuinely unproven — agentic commerce is a three-merchant pilot.

---

## 6. The verdict

**Which helps more?** Depends on "help":

| Definition | Winner |
|---|---|
| Helps the most merchants | **Agent-readable catalog** or **volume-blind risk** (98.9% each) |
| Helps a merchant *earn* rather than *not lose* | **Agent-readable catalog** — the only one |
| Helps you get hired | **Reconciliation** — best data, lowest risk, least crowded |
| Helps Razorpay's stated strategy | **Agent-readable catalog** — their volume plan needs new volume |
| Most defensible under hostile questioning | **Volume-blind risk** — every number is Razorpay's, NPCI's or the Ministry's |

**My recommendation, revised:**

**Build reconciliation if you optimise for the offer.** Nothing changed about why it was first: the
data is unmatched, the track is empty, and the MVP fits.

**Build the agent-readable catalog if you optimise for impact and are willing to carry risk.** It is
the only option that closes both gaps, it reverses my own earlier advice, and it is the only Track 1
direction with no Razorpay product behind it.

**Build volume-blind risk if you want the most defensible single claim in this research** —
*"your own threshold has a 19% annual false-positive rate on your own average merchant"* — with a
tested fix that still catches bad actors in month one.

**What I would not now build:** the intent verifier (superseded by G1 on the same rail with 1,000×
the reach) and the repeat-purchase engine (crowded, and Razorpay Engage occupies it).

---

## 7. Honest limits

- **The 1.35× reach multiplier is invented.** It illustrates a point; it does not measure one.
- **Scores for the three new projects were assigned by me in one pass**, not blind-scored across
  phases like the originals. They may carry optimism from having just been discovered.
- **G1's demand side is unproven** and no public data on Indian AI-agent shopping volume exists.
- **The reach figures use the national Udyam distribution**, not Razorpay's actual merchant book,
  which is not published.
