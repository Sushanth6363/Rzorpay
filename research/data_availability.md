# data_availability.md — Phase 9: Can the Data Actually Be Obtained?

Compiled 2026-08-25. Assesses the opportunities in
[agentic_opportunities.md](agentic_opportunities.md) against what is genuinely obtainable in ~10
days, using the test-mode findings in `requirements.md` §3.6.

**Scoring:** 1 = almost impossible · 5 = possible with significant effort · 10 = easily demonstrable.
**Classification:** 🟢 GREEN readily buildable · 🟡 YELLOW possible with synthetic/simulated data ·
🔴 RED dependent on inaccessible data.

---

## 0. The three facts that decide this phase

**1. Razorpay test mode can simulate payment failure but NOT disputes.** [A]

| Capability | Status |
|---|---|
| Card success/failure | ✅ Mock bank page; OTP of 4–10 digits succeeds, under 4 fails |
| UPI success/failure | ✅ `success@razorpay` / `failure@razorpay` |
| Webhooks | ✅ Fire on test-mode transactions |
| Refunds, orders, payment links, QR | ✅ Full CRUD |
| Settlements + recon report | ⚠️ Endpoints exist; **test-mode data is thin** |
| **Disputes / chargebacks** | ❌ **Cannot be created via the test API** — raised by banks and networks, not merchants |
| UPI cancellation | ⚠️ **Returns SUCCESS in test mode** — a trap that passes in test and breaks in live |
| Card tokens (subscriptions) | ⚠️ Valid **3 days only** |

**2. Razorpay publishes the schemas you need to generate faithful synthetic data.** The settlement
report's 11 named fields, the per-method error taxonomy (10 UPI codes, card codes), the error-object
schema with an **enumerated `source` field**, and a downloadable reason → next-best-action
spreadsheet. **A generator built against published schemas is not "fake data" — it is
structurally faithful data with ground truth you control.**

**3. Synthetic data is explicitly sanctioned.** Track 4's build spec says *"a 50+ record batch of
**synthetic data**"* in Razorpay's own words. Nothing on the page forbids synthetic or public data
for any track.

> ⚠️ **An honest gap in this research.** The public-dataset survey (Phase 1, Gap C) **never produced
> a single verified dataset with a checked licence.** So this file does not name datasets I have not
> verified. Treat any dataset you find as requiring a licence check before use — and note that the
> obvious hackathon choices (Kaggle credit-card fraud and similar) are exactly the generic ones
> `requirements.md` says trigger an automatic downgrade.

---

## 1. Opportunity assessments

### 🟢 A1 — Reconciliation Exception Resolver · **9/10**

| Question | Answer |
|---|---|
| **1. Data required** | Settlement reports (MDR, GST on MDR, refund offsets, chargeback deductions, net settled, UTR), payment ledger, refunds, a bank-statement/ERP export, and a second PSP's export for the multi-gateway case |
| **2. Razorpay provides?** | **Partially.** `fetch_settlement_recon_details`, `fetch_all_settlements`, `fetch_settlement_with_id`, `fetch_all_payments`, `fetch_all_refunds`, `fetch_order_payments` all exist and work with test keys — but test-mode settlement data is thin, so it demonstrates the *integration*, not the *volume* |
| **3. Synthetic available?** | ✅ **Explicitly sanctioned by the track's own build spec** |
| **4. Realistic synthetic generable?** | ✅ **Best in class.** The settlement schema is published field-by-field, and the failure modes Razorpay names (net-only reporting, missing UTRs, cross-period deductions, late authorisation) tell you exactly which defects to inject |
| **5. Public datasets?** | Not needed |
| **6. APIs** | 8+ relevant MCP tools; all read-only, so no risk of side effects |
| **7. Demonstrable in a hackathon?** | ✅ **Fully.** Ground truth is yours by construction, so match rate and precision are exact rather than estimated |

**Why this scores highest:** it is the only opportunity where **the demo metric and the business
metric are the same number**, and where Razorpay has published both the schema and the defect list.

---

### 🟢 A2 — Headroom-Aware Recovery Sequencer · **8/10**

| Question | Answer |
|---|---|
| **1. Data required** | Failed payments with error codes, per-customer failure history over time, mandate state, merchant chargeback ratio |
| **2. Razorpay provides?** | **Failure simulation: yes** (`failure@razorpay`, sub-4-digit OTP). **Error taxonomy: yes, published.** **Chargeback ratio: no** — disputes cannot be created in test mode, so the headroom signal must be synthetic |
| **3. Synthetic available?** | ✅ Necessary for the longitudinal part |
| **4. Realistic synthetic generable?** | ✅ **Yes, and faithfully** — the 10 UPI codes, the `source` enum and the reason → next-best-action mapping mean your generator emits real Razorpay failure semantics, not invented ones |
| **5. Public datasets?** | None verified for Indian mandate failure |
| **6. APIs** | `fetch_all_payments`, `fetch_payment`, `create_payment_link`, `create_payment_link_upi`, `send_payment_link`, `create_registration_link`, `fetch_tokens` |
| **7. Demonstrable?** | ✅ Mostly. The classify → decide → act loop runs live against test mode. The **timing** element is inherently synthetic — you cannot wait weeks, and test-mode card tokens expire in 3 days |

**Watch:** the 3-day token limit is a real constraint on any subscription demo, and UPI cancellation
returning success in test mode will silently corrupt a cancellation path. Say both in the README.

---

### 🟢 A4 — Promise-to-Pay Collections Agent · **8/10**

| Question | Answer |
|---|---|
| **1. Data required** | Invoice ledger with ageing buckets, payer payment history, commitment log, contact log |
| **2. Razorpay provides?** | Invoices and payment links exist; there is no meaningful B2B receivables corpus in test mode |
| **3. Synthetic available?** | ✅ |
| **4. Realistic synthetic generable?** | ✅ **Yes, and it is well-anchored:** 73-day mean DSO, 82.6% of invoices on 0–30 day terms, and the >360-day tail give you real distribution parameters to generate against |
| **5. Public datasets?** | MSME Samadhaan is **aggregate only** — it sizes the problem, it is not transaction-level. No usable public invoice dataset verified |
| **6. APIs** | `create_payment_link`, `send_payment_link`, `fetch_payment_link`, `fetch_all_payment_links` |
| **7. Demonstrable?** | ✅ DSO curves, promise-kept rates and collection sequencing all demonstrate cleanly on a generated ledger |

---

### 🟡 A5 — Agentic Purchase Intent Verification · **8/10** *(Level 3)*

| Question | Answer |
|---|---|
| **1. Data required** | Agent instruction, resulting cart, merchant catalog, consent token and caps |
| **2. Razorpay provides?** | ✅ **Track 1 is the only track native to test mode** — orders, payments and capture work end to end. **But UPI Reserve Pay is a closed pilot and is not available to you**, so the consent model must be reimplemented, not called |
| **3–4. Synthetic** | ✅ Catalog and instruction sets are easy to generate faithfully |
| **6. APIs** | `create_order`, `fetch_order`, `capture_payment`, `initiate_payment`, plus the MCP server as the agent's tool surface |
| **7. Demonstrable?** | ✅ Very — this is the most visually compelling demo in the set |

**Caveat:** ~100 competitor repos are in this track.

---

### 🟡 A3 — Merchant Freeze Navigator · **5/10** ← *the phase's casualty*

| Question | Answer |
|---|---|
| **1. Data required** | Hold events with triggers, document state, resolution timelines, chargeback trend |
| **2. Razorpay provides?** | ❌ **No.** A "settlements on hold" state exists in the docs and dashboard, but **you cannot cause a hold in test mode**, there is no hold API, and no trigger data is exposed |
| **3. Synthetic available?** | ⚠️ You must invent the hold *process itself*, not just the records. The published bands (2–5 days / 1–3 weeks / 30+ days) and the four triggers make the timeline faithful, but the event generation is entirely your model |
| **5. Public datasets?** | Complaint corpora (Trustpilot, PissedConsumer) are **qualitative narratives**, not structured events |
| **6. APIs** | `fetch_all_settlements` for status. Essentially nothing else |
| **7. Demonstrable?** | ⚠️ You can demo document assembly, band tracking and escalation drafting. You **cannot** demo the outcome — Phase 8 already established there is no feedback loop |

**Verdict: the novelty score does not rescue it.** A3 had the cleanest gap in the corpus (novelty 9,
competition 2) and it is undone by data. You would be simulating the event, simulating the trigger,
and unable to measure the outcome. **This is exactly the "theoretically brilliant, practically
unobtainable" case Phase 9 exists to catch.**

---

## 2. Supporting components

| Component | Score | Notes |
|---|---|---|
| **Self-cure attribution harness** (Level 1) | 🟢 **9** | Pure holdout design on your own generator. Trivially demonstrable — and it is what makes A2's numbers honest |
| **FP cost in frozen-capital days** (Level 1) | 🔴 **4** | Requires fraud labels *and* hold outcomes. The hold half is unobtainable, same as A3 |
| **Joint RTO/conversion curve** (Level 1) | 🔴 **3** | Needs paired RTO and conversion data for the same sessions. No verified public India source; delivery data belongs to the merchant's courier |

---

## 3. Eliminated on data grounds

| Idea | Score | Why it dies |
|---|---|---|
| **Chargeback evidence responder** | 🔴 **3** | ⭐ **Disputes cannot be created in Razorpay test mode.** You would simulate the dispute, the evidence and the outcome — three layers of invention under a bar demanding measured results. Six competitor repos are walking into this |
| **RTO / return-risk scorer** | 🔴 **3** | No verified public India RTO dataset; the delivery data that gates accuracy belongs to the merchant's courier; and Razorpay ships three products against it |
| **Generic fraud detection** | 🔴 **4** | The only accessible datasets are the generic ones `requirements.md` flags for automatic downgrade, and no India merchant-side rate exists to calibrate against |
| **Cross-merchant fraud rings** | 🔴 **1** | Needs cross-merchant consumer data. Legally unobtainable — DPDP purpose limitation |
| **Payment routing optimisation** | 🔴 **2** | Needs bank-level real-time health across PSPs. Not exposed to anyone outside Razorpay |

---

## 4. Final data ranking

| Rank | Opportunity | Score | Class | Binding constraint |
|---|---|---|---|---|
| **1** | **A1 Reconciliation Exception Resolver** | **9** | 🟢 GREEN | None material — schema published, synthetic sanctioned, ground truth exact |
| **2** | **A2 Recovery Sequencer** | **8** | 🟢 GREEN | Chargeback headroom must be synthetic; 3-day token limit |
| **2=** | **A4 Promise-to-Pay Collections** | **8** | 🟢 GREEN | No transaction-level public data; distribution anchors are good |
| **2=** | **A5 Intent Verification** | **8** | 🟡 YELLOW | Reserve Pay is a closed pilot; heavy competition |
| **5** | **A3 Freeze Navigator** | **5** | 🟡 YELLOW | Cannot generate the event or observe the outcome |

---

```
PHASE 9 VALIDATION

GREEN - readily buildable:
  A1 Reconciliation Exception Resolver (9)   - published schema, published defect list,
                                               synthetic explicitly sanctioned by the spec
  A2 Headroom-Aware Recovery Sequencer (8)   - real failure simulation + published error taxonomy
  A4 Promise-to-Pay Collections (8)          - strong distribution anchors (73-day DSO, 82.6%
                                               on 0-30 day terms)
  Self-cure attribution harness (9)          - pure holdout design, supports A2

YELLOW - possible with synthetic/simulated data:
  A5 Intent Verification (8)  - test mode is native to Track 1, but Reserve Pay is a closed
                                pilot so the consent model must be reimplemented
  A3 Freeze Navigator (5)     - the event itself must be invented and the outcome cannot be
                                observed

RED - dependent on inaccessible data:
  Chargeback evidence responder (3)   - disputes CANNOT be created in test mode
  RTO / return-risk scorer (3)        - no verified India dataset; delivery data is the
                                        courier's; three Razorpay products already ship
  Generic fraud detection (4)         - only generic datasets available, no India calibration
  FP cost in frozen days (4)          - the hold half is unobtainable
  Joint RTO/conversion curve (3)      - needs paired data nobody publishes
  Cross-merchant fraud rings (1)      - legally unobtainable under DPDP
  Payment routing optimisation (2)    - bank-level health is not exposed outside Razorpay

Opportunities eliminated due to data:
  A3 Merchant Freeze Navigator is DOWNGRADED OUT of the top tier. It carried the best novelty
  score in the corpus (9) and near-zero competition (2), and it fails here: you cannot cause a
  hold in test mode, no hold API exists, no trigger data is exposed, and Phase 8 already
  established there is no feedback loop to measure the outcome. Simulating the event, the
  trigger AND the outcome, under a bar that demands measured results on a batch, is three
  layers of invention. This is precisely the case Phase 9 exists to catch.

  Chargeback evidence responder is eliminated for the same class of reason and is more
  dangerous, because it is an official example direction that reads as endorsed - six
  competitor repos are building it, and disputes cannot be created in test mode.

Best data-accessible opportunities:
  A1 (9) is the clear leader and the only one where the demo metric and the business metric
  coincide. A2 (8) and A4 (8) follow, both fully generable against published or well-sourced
  distribution parameters.

Honest gap in this assessment:
  The public-dataset survey from Phase 1 (Gap C) never produced a single verified dataset with
  a checked licence. This file therefore names no datasets it has not verified, and treats
  synthetic generation against published schemas as the primary route - which is defensible
  because Razorpay's own Track 4 spec sanctions exactly that.

Confidence: 9/10

READY FOR PHASE 10: YES
```

**Why 9/10 — the highest of any phase so far.** The decisive facts are first-hand and verified: I
fetched Razorpay's test-mode documentation directly, confirmed the dispute-creation limitation and
the exact test VPAs, counted the MCP tools in the repo, and confirmed the synthetic-data sanction in
the verbatim track text. Data availability is the one dimension in this research that can be checked
rather than inferred. It is not 10/10 because no public dataset was ever licence-verified, and
because test-mode settlement depth is described as "thin" without my having measured how thin.
