# compliance_review.md — Do the five proposed projects violate anything?

Compiled 2026-08-25, in response to a direct question. **This should have been done earlier.** Prior
phases analysed regulation as an explanation for *why Razorpay hasn't built something*; they never
audited the five proposals against the rules **you** would be operating under.

> ⚠️ **I am not a lawyer and this is not legal advice.** This is a documented review of published
> terms, regulations and contest rules, with the source quoted so you can check it yourself.

---

## 1. What was checked

| Source | Status |
|---|---|
| Razorpay Payment Terms & Conditions (merchant agreement) | ✅ fetched and read |
| Razorpay Privacy Policy | ✅ fetched |
| Razorpay MCP server licence | ✅ **MIT — fully permissive** |
| Buildathon rules (official page + form) | ✅ from Phase 0 capture |
| RBI PA Directions 2025 | ✅ from Phase 1 (full PDF) |
| RBI e-mandate framework 2026 | ✅ from Phase 1 |
| DPDP Act 2023 | ⚠️ known constraints only, statute not read in full |
| Collections / recovery-agent conduct rules | ⚠️ known constraints only, not read in full |
| Razorpay developer/API-specific terms | ❌ **`/terms/api` returns 404** — no separate API ToS found |

---

## 2. The two clauses that matter

### ⭐ Clause 2.30 — the competing-product clause

> *"You undertake not to use the APIs or software provided by Razorpay PA or Facility Provider(s)
> software in any form whatsoever to design, disassemble, adapt, modify, transform, realize,
> distribute, break down by integrated protection system, **or market a similar software program**,
> or allow unauthorised use or access to The Platform/checkout and/or Facility Provider software."*

**Reading it fairly:** the surrounding verbs — disassemble, break down by integrated protection
system — are classic anti-reverse-engineering language. The natural scope is *"don't use our APIs to
clone our platform or checkout."* It is almost certainly not intended to prohibit a merchant-side
tool that consumes their APIs for the merchant's own operations.

**But "market a similar software program" is broad**, and it is the clause a cautious reviewer would
point at.

### Clause 2.23 — Razorpay asserts the risk function as its own

> *"Razorpay PA may, at its reasonable discretion and in compliance with Applicable Laws, blacklist
> Your end users to manage fraud and risk… You acknowledge and agree that Razorpay PA may take such
> measures **to protect the integrity of the payment ecosystem**."*

Also relevant, clause **2.31**: Razorpay *"shall at all times monitor the transactions of You to
ensure that these transactions are in line with Your business profile"* — a Master Direction
obligation, not a preference.

**This matters for project #4.** Razorpay is contractually asserting risk management as its
prerogative and a regulatory duty. That doesn't prohibit a merchant from watching their own numbers
— but it gives a reviewer a hook if the framing looks adversarial.

---

## 3. Project-by-project verdict

### #1 Reconciliation Exception Resolver — 🟢 **LOW RISK**

| Check | Verdict |
|---|---|
| Clause 2.30 (similar software) | 🟡 **Mild.** It is adjacent to Single View Recon and Smart Collect. But it uses **read-only** endpoints, operates on **the merchant's own data**, and replicates no platform or checkout function |
| Data protection | 🟢 Synthetic data; no personal data required at all |
| Buildathon rules | 🟢 Track 4's spec *explicitly asks* for synthetic data |
| Regulatory | 🟢 None engaged |
| Ethics | 🟢 Proposes, never asserts — actively *reduces* the chance of a wrong entry in someone's books |

**Mitigations to state in the README:** read-only API scope · test-mode keys only · operates on the
merchant's own settlement data · outputs proposals for human approval, never writes to a ledger ·
not a payment-processing or checkout product.

### #2 Recovery Sequencer — 🟢 **LOW RISK**, with two live regulatory constraints

| Check | Verdict |
|---|---|
| Clause 2.30 | 🟢 Orchestration layer, not a similar program |
| **NPCI retry rules** | 🟠 **Real constraint.** Retry limits are set by NPCI circulars, not by the PSP. Aggressive retry is penalised at ecosystem level |
| **RBI e-mandate framework 2026** | 🟠 **Real constraint.** Mandatory 24-hour pre-debit notification with an opt-out; mandate terms are fixed at registration and changing them needs fresh AFA |
| Rail switching | 🔴 **Would be a violation.** A UPI AutoPay consent does not authorise a card debit. Do not build a silent cross-rail fallback |
| Ethics | 🟡 Repeated contact attempts have a harassment ceiling — the caps and quiet hours are the answer |

**This is a case where the constraints improve the project.** Building to NPCI retry limits and the
24-hour notification window is precisely the "compliant escalation" Track 3's bar asks for.

### #3 Promise-to-Pay Collections — 🟠 **MEDIUM RISK** — the regulated-conduct one

| Check | Verdict |
|---|---|
| **Debt-collection conduct** | 🟠 **The live issue.** Collections in India is regulated conduct: contact-hour restrictions, harassment prohibitions, recovery-agent norms. This is precisely why Razorpay ships nothing here |
| Who sends the message | ⭐ **Design-critical.** Must operate **in the merchant's name**, never Razorpay's |
| **DPDP Act 2023** | 🟠 Real buyer contact data is personal data. **Use synthetic only** |
| Statutory escalation | 🟢 Drafting an MSME Samadhaan filing is assisting a lawful process |
| Ethics | 🟠 The line between "systematic follow-up" and "automated harassment" is a design choice, and it is visible in the demo |

**Mandatory guardrails:** contact-frequency caps · quiet hours · merchant's name on every message ·
opt-out honoured · hard stop into statutory process rather than escalating pressure · synthetic
contact data only.

### #4 Merchant Freeze Exposure Monitor — 🔴 **HIGHEST RISK OF THE FIVE**

This is the one the question was worth asking for.

| Check | Verdict |
|---|---|
| **Clause 2.23 / 2.31** | 🔴 Razorpay contractually asserts risk management as its prerogative *and* a Master Direction duty |
| Framing risk | 🔴 **"Helping merchants stay under the freeze threshold" can be read as helping them evade a risk control** |
| Is it actually prohibited? | 🟢 **No.** Nothing stops a merchant computing their own chargeback ratio from their own transactions. Razorpay itself **recommends merchants self-monitor at 0.5%** |
| AML | 🟢 So long as it never attempts to infer *why* an account was flagged |
| Ethics | 🟠 Depends entirely on whether it reduces genuine risk or merely conceals it |

**The distinction that decides it:**

| ✅ Defensible | 🔴 Indefensible |
|---|---|
| "Your chargeback rate is rising — here's the root cause, fix it" | "Your rate is near 1% — here's how to keep it under" |
| Targets Razorpay's own published 0.5% recommendation | Targets the threshold itself |
| Uses only the merchant's own data | Attempts to reverse-engineer the risk model |
| Aims at fewer disputes | Aims at fewer *detected* disputes |

**Verdict: buildable, but only with the framing fixed in advance** — and it must be said out loud in
the pitch, not left for a judge to infer. Combined with its data problems (Phase 9) and its fragility
(Phase 13), **this is now the weakest of the five, not the boldest.**

### #5 Agentic Purchase Intent Verifier — 🟢 **LOWEST RISK**

| Check | Verdict |
|---|---|
| Clause 2.30 | 🟢 Adds a control *before* payment; replicates nothing |
| Consent model | 🟡 Reimplements the UPI Reserve Pay *pattern* — do not claim to be integrated with it |
| Regulatory | 🟢 Nothing engaged; UAP isn't live so there's nothing to violate |
| Ethics | 🟢 Straightforwardly protective |

---

## 4. Rules that apply to all five

**Track 2's disqualifier** — *"Strictly defense-only: anything offense-capable is disqualified."*
None of the five is offense-capable. But note the rule applies to Track 2, and **#4 could be
misread** as adversarial to a control. Another reason to submit it under Open with careful framing.

**Public repo = published work.** Your submission is public. Don't include anything you wouldn't
publish: no real keys, no real merchant data, no scraped competitor files.

**Test-mode keys only.** Never live keys in a public repo. The MCP server auto-detects environment
from the key prefix, so a stray `rzp_live_` is both a security and a compliance incident.

**Synthetic data only.** It sidesteps DPDP entirely and is explicitly sanctioned by Track 4's spec.

**Trademark.** Using "Razorpay" in a project *name* is a mild trademark question. "Built for the
Razorpay AI Buildathon" as a description is fine. Many competitor repos do the former anyway.

---

## 5. Two things nobody has published, so plan around them

**Does Razorpay claim rights over submissions?** The buildathon page and the form say **nothing**
about IP ownership. A public repo under your own licence is the safest default. Unknown, not resolved.

**Is pre-existing code allowed?** Also unstated. Other major hackathons explicitly forbid it (UC
Berkeley 2026: *"Previous projects are not allowed"*). Razorpay is silent. **Safest: build fresh and
timestamp it with commit history.**

---

## 6. Summary

| Project | Risk | The one thing that decides it |
|---|---|---|
| **#1 Reconciliation** | 🟢 LOW | Read-only, merchant's own data, proposes rather than asserts |
| **#5 Intent verifier** | 🟢 LOW | Adds a safety control; replicates nothing |
| **#2 Recovery** | 🟢 LOW | Must respect NPCI retry limits and the 24h notification window; **no silent rail switching** |
| **#3 Collections** | 🟠 MEDIUM | Must act in the merchant's name with hard conduct guardrails |
| **#4 Freeze monitor** | 🔴 **HIGH** | Must reduce genuine risk, not help evade detection — and must say so |

**Nothing here is disqualifying.** But #4's risk is materially higher than I represented in Phase 14,
where I described it as a *perception* problem. It is also a **contractual-framing** problem, because
Razorpay explicitly asserts the risk function in clause 2.23 and is obliged to monitor under 2.31.

**Revised recommendation:** #1 remains the pick, and its low compliance risk is now another point in
its favour. **#4 should drop below #3** in your consideration order.

---

## 7. What I did not check

- The **DPDP Act 2023** statute itself — I worked from known constraints, not the text
- **RBI recovery-agent guidelines** in full — same caveat
- **NPCI circulars** on retry limits — referenced via secondary sources, not read directly
- Whether Razorpay has **separate developer/API terms** — `/terms/api` 404s and I found none
- **Curlec / international terms**, irrelevant unless you build cross-border

Each of these could shift a verdict at the margin. None is likely to move a 🟢 to a 🔴.
