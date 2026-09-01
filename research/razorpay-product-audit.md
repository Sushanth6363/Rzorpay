# razorpay-product-audit.md — Did we actually check every Razorpay product?

Compiled 2026-08-25, in response to a direct question: *had the research checked all of Razorpay's
products?*

## Short answer: no

The earlier phases worked from a **20-product catalog** I extracted from the buildathon page's own
embedded data, plus Agent Studio, Vulcan and the MCP server. That felt comprehensive. It wasn't.

**Razorpay's own site navigation lists roughly 40 products.** I had examined about half, and
**three of the unexamined ones sit directly on top of my recommendations.**

This file lists every product, marks what was and wasn't checked, and records what the gap changed.

---

## 1. The full product list, with audit status

### Payments (accept money)

| Product | Checked before? | Relevant to our picks? |
|---|---|---|
| Payment Gateway | ✅ catalog | — |
| Payment Links | ✅ catalog + MCP | tool for #2/#3 |
| Payment Pages | ✅ catalog | — |
| Payment Buttons | ✅ catalog | — |
| QR Codes | ✅ catalog + MCP | — |
| Magic Checkout | ✅ | kills abandonment ideas |
| Optimizer | ✅ | kills routing ideas |
| Subscriptions | ✅ catalog | context for #2 |
| UPI AutoPay | ✅ catalog | context for #2 |
| e-Mandate / e-NACH | ✅ catalog | context for #2 |
| International Payments | ✅ catalog | — |
| Instant Settlements | ✅ | context for settlement timing |
| Route (split payments) | ✅ catalog | — |
| POS | ✅ catalog | — |
| **Invoices** | ❌ **NOT CHECKED** | ⚠️ relevant to #3 |
| **Smart Collect** | ❌ **NOT CHECKED** | 🔴 **relevant to #1** |
| **TokenHQ** | ❌ NOT CHECKED | low |
| **App Store** | ❌ NOT CHECKED | low |
| **Payments Mobile App** | ❌ NOT CHECKED | low |
| **Curlec** (Malaysia) | ❌ NOT CHECKED | out of scope |

### Banking+ (move money)

| Product | Checked before? | Relevant? |
|---|---|---|
| RazorpayX | ✅ catalog | — |
| Payouts / Payout Links | ✅ catalog + MCP | — |
| Vendor Payments | ✅ catalog | ⚠️ adjacent to #3 |
| Payroll | ✅ catalog | — |
| **Source to Pay (AP Automation)** | ❌ **NOT CHECKED** | 🔴 **relevant to #1 and tax ideas** |
| **Current Account** | ❌ NOT CHECKED | low |
| **Escrow+ Account** | ❌ NOT CHECKED (404 on the URL tried) | low |
| **Forex / FDI Transfers** | ❌ NOT CHECKED | low |
| **Bank Account Verification** | ❌ NOT CHECKED | low |
| **Tax Payments** | ❌ **NOT CHECKED** | ⚠️ relevant to tax ideas |

### Lending & other

| Product | Checked before? |
|---|---|
| Razorpay Capital / Line of Credit / Digital Lending 2.0 | ❌ NOT CHECKED |
| Rize (company registration) | ✅ catalog |
| Engage (loyalty) | ✅ catalog |

### AI layer

| Product | Checked | Note |
|---|---|---|
| Agent Studio (7 agents) | ⚠️ **from a 12 Mar 2026 blog, not the live page** | page is client-side rendered; still unverified |
| Vulcan | ✅ | |
| MCP server (45 tools) | ✅ | |
| Single View Recon | ✅ (via blog) | views settlements, does not resolve |
| Thirdwatch / Slash / Call-E | ⚠️ named only | not examined |

**Tally: ~14 products never examined.** Three of them matter.

---

## 2. What the three unchecked products actually do

### 🔴 Smart Collect 2.0 — *"Automated Reconciliation of Collections via Bank Transfer"*

Verbatim from the product page: *"Automatically reconcile incoming UPI, IMPS, NEFT and RTGS payments
and enjoy real-time, instant collections."* It works by issuing **a unique virtual identifier per
customer**, so an incoming bank transfer is unambiguously attributable. Tracked via dashboard and
webhooks.

**This is a reconciliation product I did not know existed while recommending a reconciliation
project.**

### 🔴 Source to Pay — RazorpayX AP Automation

Verbatim capabilities: OCR invoice capture · **"automates 3-way matching"** (PO ↔ invoice ↔ goods
receipt) · **"Auto-deduct and pay TDS"** on line items · **"Catch GST ITC misses"** ·
**"Auto-synced to General Ledgers for automatic reconciliation"** · discrepancy detection · audit
trail · smart rules for bookkeeping and transaction categorisation.

**Razorpay already ships automated tax-line handling and 3-way matching.**

### ⚠️ Invoices

GST invoicing and billing software — invoice *creation*, not collection.

---

## 3. What this changes

### ✅ #1 Reconciliation Exception Resolver — **SURVIVES, but the pitch must change**

The three adjacent products solve **different reconciliation problems**:

| Product | Reconciles what | Direction |
|---|---|---|
| **Smart Collect** | *Incoming bank transfers* → which customer paid? Solved by giving each payer a unique identifier — **prevention by design**, not exception resolution | money **in** |
| **Source to Pay** | *Supplier invoices* → PO ↔ invoice ↔ goods receipt (3-way match) | money **out** |
| **Single View Recon** | *Settlements* → displays status, UTRs, Settlement IDs across aggregators | money **in**, but **view only** |
| **Our #1** | *Settlement lines* → payout ↔ orders, net of MDR, GST-on-MDR, refund offsets, chargeback deductions, across PSPs and across settlement cycles | money **in**, **resolution** |

None of the three touches the settlement line's fee/tax/deduction composition, and none links a
deduction back to a sale from an earlier cycle.

**But the required framing is now materially different.** Previously: *"Razorpay has a viewer, not a
resolver."* That was incomplete and a judge could have destroyed it with one sentence — *"we have
Smart Collect."*

**Corrected framing:** *"Razorpay has three reconciliation surfaces — Smart Collect prevents
ambiguity on incoming transfers by assigning identifiers, Source to Pay 3-way-matches supplier
invoices, and Single View Recon displays settlement status. None of them resolves an unmatched
settlement line, where the amount differs because of MDR, GST on that MDR, a refund offset and a
chargeback deduction from three cycles ago."*

That is a **stronger** pitch than the original, because it demonstrates you surveyed the stack.

### ❌ Tax-line matcher (ranked #10) — **DEAD**

I classified GST/TDS line matching as OPEN with "no Razorpay product". **Wrong.** Source to Pay
auto-deducts TDS on line items and catches GST ITC misses. Remove it from consideration.

### ⚠️ #3 Promise-to-Pay / receivables — **weakened, not killed**

Razorpay ships Invoices (creation), Vendor Payments and Source to Pay (payables). There is still no
**accounts-receivable collections** product. But the assumption that finance-ops automation is
outside their interest is now clearly false — they have OCR, matching and GL-sync infrastructure
already, so AR is a natural extension they could ship at any time. Novelty drops.

### Unaffected

**#2 Recovery**, **#4 Freeze monitor**, **#5 Intent verifier** — no unchecked product touches them.

---

## 4. Why the gap happened

The 20-product catalog came from structured data embedded in Razorpay's own page, which made it look
authoritative and complete. It was neither — it was the subset wired into their site assistant.
**A machine-readable list is not the same as a complete list**, and I treated it as one.

The site's own navigation menu — plain HTML, which I had already captured — carried the fuller list
the whole time. I extracted it for a different purpose and never cross-checked it against my
"no product exists" claims.

---

## 5. Still unchecked, and honestly so

Roughly 11 products remain unexamined: TokenHQ, App Store, Payments Mobile App, Curlec, Current
Account, Escrow+, Forex/FDI, Bank Account Verification, Tax Payments (partial), Capital / Line of
Credit / Digital Lending.

I judge these low-risk to the surviving recommendations — none is a reconciliation, recovery,
freeze-monitoring or agentic-commerce product. **But that is a judgement, not a verification**, and
this file exists precisely because the last such judgement was wrong.

**And the biggest gap is unchanged:** the live Agent Studio roster still could not be read. The
seven-agent list remains sourced from a five-month-old blog post.

---

## 6. Confidence after this audit

| Claim | Before | After |
|---|---|---|
| #1 has no Razorpay equivalent | 8/10 | **7/10** — three adjacent products, none overlapping, but the space is more populated than described |
| #3 has no Razorpay equivalent | 7/10 | **6/10** — AR still absent, but adjacent infrastructure exists |
| Tax-line matching is open | 7/10 | **0/10 — refuted** |
| #2, #4, #5 unaffected | unchanged | unchanged |
