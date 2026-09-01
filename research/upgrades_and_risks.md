# upgrades_and_risks.md — Every Upgrade, Its Policy Position, and Whether It Can Harm the Merchant

Compiled 2026-08-25 for the AR agent (reconcile-then-collect, Track 3).

**Not legal advice.** Policy positions are reasoned from published rules and should be checked before
anything ships to a real merchant.

---

## The summary table

| # | Upgrade | Policy | **Harm risk to merchant** | Build |
|---|---|---|---|---|
| **U1** | Form 26AS / TDS credit reconciliation | 🟢 Clean | 🟠 **MEDIUM** — false accusation on timing | 1 day |
| **U2** | Multi-invoice payment allocation | 🟢 Clean | 🟡 LOW — misallocation under-collects | 1 day |
| **U3** | Escalation economics | 🟢 Clean | 🟢 **PROTECTIVE** | 0.5 day |
| **U4** | Buyer payment-pattern learning | 🟡 DPDP care | 🟡 LOW | 1 day |
| **U5** | Draft the Samadhaan filing | 🟢 Clean | 🔴 **HIGH — can end the relationship** | 0.5 day |
| **U6** | Phantom receivables report | 🟢 Clean | 🟢 **NONE** | 0.5 day |
| **U7** | MSMED §16 statutory interest | 🟢 Clean | 🔴 **HIGH — see §43B(h) below** | 1 day |
| **U8** | Relationship-value-aware aggression | 🟢 Clean | 🟢 **PROTECTIVE** | 0.5 day |
| **U9** | Silent-dispute detection → abstain | 🟢 Clean | 🟢 **PROTECTIVE** | 0.5 day |
| **U10** | Negotiation with an economic budget | 🟢 Clean | 🟠 **MEDIUM** — margin erosion | 1.5 days |
| **U11** | Rules-engine baseline | 🟢 Clean | 🟢 NONE | 0.5 day |

---

# 🔴 The two that can genuinely hurt the merchant

## U7 — Statutory interest · HIGH HARM RISK

**What it does.** Computes compound interest under MSMED Act Section 16 — monthly rests, three times
the RBI bank rate, non-waivable by contract — and can include it in the demand.

**Why it can backfire, and this is the part that matters:**

**1. The relationship.** In Indian B2B the supplier is usually the weaker party. Demanding statutory
interest from a buyer you need next month's order from can end the account. The law is on the
supplier's side; the commercial power is not.

**2. ⭐ Section 43B(h) — the one nobody sees coming.** Buyers cannot claim a tax deduction on payments
to micro and small enterprises that run beyond the statutory window. **Some buyers have responded by
preferring suppliers who are *not* MSME-registered.**

So an agent that loudly invokes MSMED protections **advertises that the supplier is MSME-registered**
— which, for some buyers, is a reason to source elsewhere. **You could win ₹14,000 of interest and
lose the customer entirely.**

**3. Interest received is taxable income**, which the merchant may not have planned for.

**Mitigations — build these in:**

- **Compute by default, include on instruction only.** The merchant sees the number; the buyer sees
  it only when the merchant says so
- Gate it behind the relationship-value check (U8)
- Show the trade-off explicitly: *"Claiming ₹14,200 interest. This buyer represents ₹8L of annual
  orders."*
- Never auto-include it in a first reminder

## U5 — Drafting the Samadhaan filing · HIGH HARM RISK

**What it does.** Generates a populated statutory complaint against the buyer.

**Why it can backfire.** This is a **formal legal action against your own customer.** Once filed the
buyer knows, and the relationship is effectively over. It is close to irreversible.

**Mitigations:**

- **Draft only. Never file.** Filing is a human decision, always
- Require explicit merchant confirmation with the consequence stated on screen
- Present it as the *last* rung, after the escalation economics (U3) have been shown
- Default to holding the draft rather than surfacing it

---

# 🟠 The two with moderate harm risk

## U1 — Form 26AS reconciliation · MEDIUM

**What it does.** Flags TDS the buyer deducted but appears never to have deposited — money the
supplier loses twice over, since they're short-paid *and* can't claim the credit.

**Why it can backfire.** ⚠️ **26AS updates on a quarterly cycle.** A gap you see in month one may
simply be a deposit that hasn't been filed yet. **Flag it too early and your merchant accuses a
customer of tax default — for something entirely routine.**

That's a false accusation with legal overtones, and it's worse than not flagging at all.

**Mitigations:**

- **Hard timing buffer** — never flag until the relevant filing deadline has passed, plus a margin
- Frame as *"not yet appearing in 26AS"*, never *"the buyer has not deposited"*
- Surface to the **merchant only** — never generate buyer-facing text from this
- Confidence must be explicit, and abstain where the deduction rate itself was uncertain

## U10 — Negotiation with an economic budget · MEDIUM

**What it does.** Lets the agent evaluate part-payment offers and early-payment discounts.

**Why it can backfire.** An agent authorised to concede can concede too much, set precedents
(this buyer now expects a discount every time), and erode margin invisibly across many invoices.

**Mitigations:**

- **Hard caps** on discount percentage and instalment length, set by the merchant
- Every concession requires approval above a threshold
- Track precedent explicitly — flag when a buyer has been given terms before
- Report cumulative margin conceded as a first-class metric, not a footnote

---

# 🟢 The protective ones — these exist to prevent harm

**U3 Escalation economics** — computes expected recovery against relationship value before stepping
up. This is the safeguard that stops U5 and U7 from being used carelessly.

**U8 Relationship-value-aware aggression** — a buyer worth ₹8L a year who has kept two promises gets
soft touch. Encodes the judgement a good credit controller applies instinctively.

**U9 Silent-dispute detection** — recognises when silence means a genuine complaint rather than
avoidance, and **stops**. Prevents the worst outcome: chasing someone with a legitimate grievance.

**U6 Phantom receivables** — pure clarity. *"₹1.6L of your ₹18.4L outstanding was TDS, already
lawfully settled."* No downside.

**U11 Rules-engine baseline** — evaluation infrastructure. Proves the agent is necessary.

---

# Policy positions

| Area | Position |
|---|---|
| **RBI** | Nothing engaged. No lending, no payment processing, no risk decisioning. Advisory over the merchant's own receivables |
| **Collections conduct** | RBI recovery-agent rules bind regulated lenders; a supplier chasing their own receivable is different. **But harassment law applies to anyone.** Contact caps, quiet hours, opt-out honoured, merchant's name on every message |
| **DPDP Act 2023** | Buyer contact details are personal data where a named individual is involved. Use synthetic data throughout; state data minimisation in the design |
| **Razorpay ToS 2.30** | Read-only API use, no "similar software" concern — this is a merchant-side tool, not a payments platform |
| **Tax law** | Computing TDS and statutory interest is arithmetic. **Advising on tax treatment is not.** Label all tax output *indicative, not advice*, and make rates configurable |
| **Track 2 disqualifier** | Not applicable — nothing offense-capable |

---

# Recommended build order

**Days 1–3 — foundation and the safe core**
U6 phantom receivables · U11 rules baseline · U2 multi-invoice allocation
*All zero-harm, all structural ground truth.*

**Days 4–5 — the protective layer, before anything that can hurt**
U9 dispute abstention · U8 relationship weighting · U3 escalation economics

⭐ **Build the safeguards before the sharp instruments.** If you run out of time, you ship a cautious
agent rather than an aggressive one — and that is the right failure mode for something touching a
merchant's customer relationships.

**Days 6–7 — the differentiators, now safely gated**
U7 statutory interest *(compute by default, include on instruction)* · U1 26AS *(with timing buffer)*

**Day 8, if time allows**
U5 Samadhaan draft *(draft only, never file)* · U10 negotiation *(hard caps)*

---

# The line for the video

> *"Three of these upgrades can hurt the merchant if used carelessly. Statutory interest can cost
> them the customer — and because of Section 43B(h), invoking MSMED protections tells the buyer
> they're dealing with a registered MSME, which some buyers actively avoid. So interest is computed
> by default and included only when the merchant says so, and the Samadhaan filing is drafted but
> never filed. The safeguards were built before the sharp instruments."*

**Almost nobody will demonstrate that they thought about how their own agent could backfire.** Under
a bar that asks for bounded, gated actions and honest failure reporting, that is the strongest
thirty seconds you have.
