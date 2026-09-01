# DATASET RESEARCH — REAL-WORLD / REAL-TIME DATA DISCOVERY

**Task**: determine whether publicly available, legally usable, sufficiently realistic data exists that would improve the credibility of the AI recovery demonstration.
**Researched**: 2026-08-31. All findings below were checked this session; items I could not verify myself are marked **UNVERIFIED** rather than asserted.
**Rule applied**: a dataset being real does not make it relevant. The recovery problem needs `P(incremental recovery | state, action)` — state **+** action **+** subsequent outcome. Transaction classification is not that.

---

## 0. Headline finding

**No public dataset exists that contains payment failure, a recorded recovery intervention, and the subsequent outcome.** I searched for it directly across Kaggle, Hugging Face, UCI, Google Dataset Search results, GitHub and the open payments/dunning literature. Every "failed payment recovery" search returns vendor marketing content (Recurly, Baremetrics, Chargebee, Slicker) quoting internal recovery rates — no data behind it.

That is a real result, not a failed search. It means:

- **Level 3 (real intervention + outcome) is not achievable.** Do not claim it.
- **Level 2 (real transactions with a valid recovery target) is not achievable either**, because no public payment dataset carries an attributable recovery outcome — the closest, LendingClub, records `recoveries` as an amount with no record of what was done to obtain it.
- **Level 1 (real distributions calibrating the synthetic generator) is achievable and worth doing.**

The synthetic environment remains the canonical controlled experiment. That was already the honest position; this research confirms it rather than rescuing it.

---

## 1. Dataset candidates

| Dataset | Source | Type | Recovery relevance | License | Recommendation |
|---|---|---|---|---|---|
| **NPCI UPI bank-wise TD/BD & uptime** | npci.org.in | PUBLIC_REAL (aggregate, monthly) | **3** — real Indian issuer-level *decline* rates; calibrates failure distribution and the outage/degradation signal | Government/industry body publication; terms **UNVERIFIED** | **USE for calibration**, pending licence check |
| **MSME Samadhaan / MSEFC public reports** | samadhaan.msme.gov.in | PUBLIC_REAL (aggregate) | **3** — real delayed-payment case counts, amounts, ageing buckets, buyer category | Government portal, public reports; terms **UNVERIFIED** | **USE for calibration** of B2B ageing |
| **Criteo Uplift Prediction** | ailab.criteo.com | PUBLIC_REAL | **2** for recovery, **5** for *estimator validation* — ~14M rows, real randomised treatment + exposure + visit/conversion | **CC BY-NC-SA 4.0** (explicit) | **Optional** — validate the measurement code only, never as recovery evidence |
| **UCI Bank Marketing** | archive.ics.uci.edu | PUBLIC_REAL | **3** — 45,211 rows with `campaign` (contacts this campaign), `pdays`, `previous`, `poutcome`, `contact` channel, and a contacted/converted target | **CC BY 4.0** (explicit, citation required) | **Optional** — calibrate contact-fatigue priors only |
| **Hillstrom MineThatData** | MineThatData blog / `scikit-uplift` | PUBLIC_REAL | 4 for estimator validation — 64,000 rows, real 3-arm randomised email test, visit/conversion/spend | **No explicit licence found** | **REJECT per §23A.10** — reference only |
| **KKBox WSDM churn** | Kaggle / WSDM 2018 | PUBLIC_REAL | 2 — subscription transactions with `auto_renew`, `is_cancel`, plan, expiry; closest to the subscription stream | **No explicit licence found**; competition terms | **REJECT per §23A.10** — reference only |
| **LendingClub loan data** | Kaggle (redistributed) | PUBLIC_REAL | 2 — has `recoveries`, `collection_recovery_fee`, `last_pymnt_d`, loan status | Redistributed; original terms unclear | **REJECT** — no intervention record; licence unclear |
| **IEEE-CIS Fraud / ULB Credit Card Fraud** | Kaggle | PUBLIC_REAL | **0–1** — transaction + fraud label; no intervention, no recovery, no response | Competition / DbCL | **REJECT** — real but irrelevant (the §23A.3 trap) |
| **Online Retail II** | UCI | PUBLIC_REAL | 1 — e-commerce baskets; no payment failure, no cart abandonment, no intervention | CC BY 4.0 | **REJECT** — not a recovery dataset |
| **HF finance/transaction sets** (`pointe77/credit-card-transaction`, transaction-categorisation corpora) | huggingface.co | PUBLIC_REAL | **0–1** — categorisation and fraud framing only | mixed | **REJECT** — no action or outcome dimension |
| **Public dunning / retry-outcome dataset** | — | — | — | — | **DOES NOT EXIST** (searched; only vendor blog statistics) |
| **Razorpay public status feed** | status.razorpay.com | would be PUBLIC_NEAR_REAL_TIME | would be 5 | — | **DOES NOT EXIST as a public API** — see §5 |

### Scored detail — the three that matter

Scale: 0 unusable · 1 weak · 2 moderate · 3 strong · 4 excellent · 5 directly relevant.

| Criterion | NPCI TD/BD | UCI Bank Marketing | Criteo Uplift |
|---|---|---|---|
| Payment data | 4 (aggregate, not transactional) | 0 | 0 |
| Failure data | **5** (decline rates by bank, by direction) | 0 | 0 |
| Recovery data | 0 | 0 | 0 |
| Customer behaviour | 0 | 3 | 2 (anonymised, projected) |
| Time dimension | 3 (monthly) | 2 (relative day offsets) | 1 (no timestamps) |
| Action information | 0 | **4** (`campaign`, `previous`, `contact` channel) | **5** (randomised treatment flag) |
| Outcome information | 0 | 3 (subscribed y/n, `poutcome`) | **5** (visit, conversion, with control arm) |
| Scale | 3 (bank × month) | 3 (45,211) | **5** (~14M) |
| Realism vs payment recovery | **4** | 2 (term-deposit marketing, not recovery) | 1 (ad targeting) |
| Recency | **5** (current monthly) | 0 (2008–2010 campaign) | 2 |
| Accessibility | 3 (web page; 403 to automated fetch) | **5** | 4 (form download) |
| Licence | **UNVERIFIED** | **5** (CC BY 4.0) | 3 (CC BY-NC-SA 4.0) |
| Privacy / PII | **5** (aggregate, no individuals) | 4 (anonymised individuals) | **5** (projected features) |
| Leakage risk | 5 (no future info) | 4 (`duration` is a known leaky field — must be dropped) | 4 |
| Integration effort | **5** (a rate table) | 4 | 3 |
| **Use** | **Calibration** | Optional prior | Optional estimator check |

---

## 2. Best candidate

### NPCI UPI bank-wise Technical Decline / Business Decline / uptime statistics

**Why it is relevant.** The prototype's generator currently authors its own failure-reason and issuer distribution. NPCI publishes, monthly, per-bank technical decline (TD) and business decline (BD) percentages for both remitter and beneficiary banks — real Indian payment-failure rates from the operator of the rails Razorpay sits on. Substituting real issuer decline rates for authored ones makes the failure side of the simulation empirical rather than invented, which is exactly the credibility gap the red-teams identified. It is also the only candidate that speaks directly to **D2**: TD is precisely the "bank-side problem, not customer-side problem" signal the engine claims to reason about, and per-bank variation (roughly 0.03% to ~1% across banks, per published reporting) gives the outage/degradation model a real dynamic range instead of a guessed one.

**Fields available**: bank name, remitter/beneficiary role, approved transaction count, technical decline %, business decline %, system uptime, reporting month.

**Fields missing**: everything downstream of the failure — no customer, no retry, no intervention, no recovery. This is a *rate table*, not an event log.

**Preprocessing required**: scrape or download the monthly table; normalise bank names to issuer codes; convert TD/BD percentages into per-issuer failure probabilities and an outage-severity prior for the generator; version and hash the extracted table so the generator config stays reproducible.

**Legal use**: **UNVERIFIED.** The NPCI page returned HTTP 403 to my automated fetch, so I could not read its terms of use myself. Reported values appear widely in press and analyst writing, which is consistent with public data, but that is not a licence. **Per §23A.10 this must be checked manually before use.** If terms are unclear, the fallback is to cite published *ranges* from secondary sources as generator priors rather than redistributing the table — which achieves most of the calibration benefit with none of the licence risk.

**Does it support causal recovery measurement?** **No.** It contains no intervention and no outcome. It can calibrate the world; it cannot evaluate the engine. That distinction is the whole point of the Level 1 classification.

### Runner-up: MSME Samadhaan / MSEFC public reports

Public age-category and amount-wise pendency reports by buyer category (State Govt, Central Govt, PSU, private). Calibrates the B2B stream's ageing distribution and dispute-rate priors against real Indian delayed-payment data — the same source `final.md` already cites for the ₹20,979 cr figure. Same limitation: aggregate, no interventions.

---

## 3. Decision

```
USE_EXTERNAL_DATA_FOR_CALIBRATION
```

**Level 1.** Real public aggregate distributions — NPCI issuer decline rates and MSME Samadhaan ageing/pendency — calibrate the synthetic generator's failure and ageing parameters. All outcomes, interventions and recovery labels remain synthetic and are labelled as such.

**Why not the alternatives:**

- **`USE_EXTERNAL_DATA` (Level 2/3)** — rejected because no public dataset carries an attributable payment-recovery outcome. Adopting LendingClub or KKBox would mean training on a target that is not incremental recovery, then implying it is. That trades experimental validity for the appearance of real data, which §23A.13 explicitly forbids.
- **`USE_REAL_TIME_SIGNAL_ONLY`** — rejected because no usable real-time signal was found (§5). Razorpay's status page exposes no public API; NPCI publishes monthly, not live.
- **`SYNTHETIC_ONLY`** — rejected because calibration is available at near-zero cost and near-zero risk, and it converts "I invented the failure distribution" into "the failure distribution comes from NPCI's published rates," which is a materially better answer to *"where did your numbers come from?"*

**What this decision does NOT change.** The experiment, the arms, the estimators and every claim stay exactly as frozen in `p0.2-closure.md`. Calibration changes the *parameters* of the data-generating process, not its status: the process remains authored, outcomes remain synthetic, and every reported number keeps the phrase **"under the synthetic data-generating process."** Calibrating a simulator with real inputs does not make its outputs real, and the README must say so in the same breath as it claims the calibration.

### Optional, separately scoped: estimator validation on real randomised data

Criteo Uplift (CC BY-NC-SA 4.0) contains a genuine randomised treatment/control split with real outcomes. Running the project's own incremental-measurement code against it — difference in means, cluster-correct intervals, Holm correction, uplift ranking — validates that **the measurement machinery is correct on real data with a real randomised assignment**, entirely separately from any recovery claim.

This is a unit test of the estimator, not evidence about recovery. It is worth doing if time permits because it answers "is your measurement code right?" with real data, while touching nothing in the recovery experiment. Conditions: non-commercial buildathon use only, attribution given, **downloaded at runtime and never vendored into the repo** (ShareAlike propagates to redistributed derivatives), and results reported in a clearly separate section titled *estimator validation*, never alongside recovery results.

If the non-commercial reading is uncomfortable for a Razorpay-hosted event, drop it. It is a stretch item; nothing depends on it.

---

## 4. Rejected, and why — the §23A.3 trap

| Dataset | Real? | Relevant? | Why rejected |
|---|---|---|---|
| Credit-card fraud (ULB / IEEE-CIS) | Yes | **No** | `transaction → fraud_label`. No intervention, no customer response, no recovery outcome. Using it would let the project say "we used real payment data" while modelling a different problem entirely. This is precisely the example §23A.3 warns about. |
| Online Retail II | Yes | No | Completed baskets; no failure, no abandonment event, no intervention |
| LendingClub | Yes | Partly | Has `recoveries` and `collection_recovery_fee` — a recovered *amount* with no record of what was done to recover it. Attribution is impossible; every recovery would have to be `RECOVERED_UNATTRIBUTED`. Licence for redistributed copies also unclear |
| KKBox WSDM churn | Yes | Partly | Real subscription lifecycle (`auto_renew`, `is_cancel`, expiry) and the closest analogue to the subscription stream — but no dunning action recorded, and **no explicit licence found**, so §23A.10 forces rejection |
| Hillstrom MineThatData | Yes | Yes, methodologically | A genuine randomised contact experiment and an excellent estimator-validation set — but the documentation carries **no explicit licence statement**. §23A.10 is unambiguous: unclear licence, do not use. Referenced here as a candidate only |
| HF transaction/categorisation corpora | Yes | No | Classification framing; no action or outcome dimension |

---

## 5. Real-time signals — findings

The only real-time signal that would genuinely change a recovery decision is **gateway/issuer availability**, because it feeds a decision the engine actually makes:

```
outage detected  ->  retry recommendation suppressed, contact suppressed
```

| Source | Status | Verdict |
|---|---|---|
| **Razorpay Payment Downtime API + webhooks** | Real, documented, **support-request gated** (already flagged as a P0 risk) | The correct source. If access is granted, use it. If not, simulate the payload and say so on camera — unchanged from the existing plan |
| **status.razorpay.com** | **Verified myself this session**: `/api/v2/summary.json` and `/api/v2/status.json` both return HTTP 200 with `text/html` — the SPA shell, not JSON. It is **not** an Atlassian Statuspage and exposes no documented public JSON API | **Unusable.** Reverse-engineering an undocumented internal endpoint would violate §23A.10; not pursued |
| **NPCI UPI statistics** | Real and relevant, but **monthly**, not live | Calibration input, not a real-time signal |
| **RBI DBIE / bank rate** | Real and public. Genuinely feeds a computation — MSMED §16 interest is 3× the RBI bank rate — but it changes a few times a year | Fetch once, cache, treat as a **configuration parameter with a provenance stamp**, not a real-time signal. Keeps the statutory calculation honest without pretending to be live |
| Currency rates, stock prices, general economic APIs | Real | **Rejected.** No recovery decision depends on them. This is the "real-time for its own sake" failure mode §23A.4 warns about |

**Conclusion**: no new real-time integration is added. The downtime signal remains Razorpay's own API with a simulated fallback, exactly as already designed.

---

## 6. Adapter architecture

The core domain model does not change. Datasets map inward to the canonical `RecoveryOpportunity`; nothing maps outward.

```
app/data/
├── base.py                          # DatasetAdapter protocol + provenance types
├── synthetic_adapter.py             # canonical controlled experiment
└── external/
    ├── npci_decline_calibration.py  # rate table -> generator priors (NOT opportunities)
    └── samadhaan_ageing_calibration.py
```

```python
# app/data/base.py
class DatasetType(str, Enum):
    SYNTHETIC              = "SYNTHETIC"
    PUBLIC_REAL            = "PUBLIC_REAL"
    PUBLIC_NEAR_REAL_TIME  = "PUBLIC_NEAR_REAL_TIME"

@dataclass(frozen=True)
class DatasetProvenance:
    dataset_id: str
    dataset_version: str
    dataset_type: DatasetType
    source_url: str
    licence: str                 # explicit text, never "unknown" — unknown blocks use
    retrieved_at: str
    content_hash: str
    calibrates: tuple[str, ...]  # generator parameters this source informs

class DatasetAdapter(Protocol):
    provenance: DatasetProvenance
    def opportunities(self) -> Iterator[RecoveryOpportunity]: ...

class CalibrationSource(Protocol):
    """Informs generator PARAMETERS. Never emits opportunities or outcomes."""
    provenance: DatasetProvenance
    def parameters(self) -> dict[str, float]: ...
```

The split between `DatasetAdapter` and `CalibrationSource` is the architectural expression of the decision: real data enters as **parameters**, never as opportunities or outcomes. It is structurally impossible for a calibration source to contribute a recovery label.

**Real-time provider, with the mandatory fallback:**

```python
class RealTimeSignalProvider(Protocol):
    def get_current_state(self) -> SignalState: ...

class SyntheticSignalProvider:          # deterministic, seeded, always available
    def get_current_state(self): ...

class RazorpayDowntimeSignalProvider:   # requires granted API access
    def get_current_state(self):
        try:
            return self._fetch(timeout=2.0)
        except (Timeout, HTTPError, Unauthorized):
            metrics.increment("realtime_signal_fallback")
            return self._fallback.get_current_state()
```

The demo never depends on an external service: unavailable API → logged fallback → synthetic signal → run continues.

---

## 7. Provenance in results

Every experiment result identifies its data source. No result may render without a complete provenance block:

```
experiment_id · dataset_id · dataset_version · dataset_type · seed · model_version
+ calibration_sources[] (id, version, licence, content_hash)
```

```python
def test_no_result_renders_without_provenance():
    for r in report().runs:
        assert r.dataset_type in DatasetType.__members__
        assert r.dataset_id and r.dataset_version and r.seed is not None
        for c in r.calibration_sources:
            assert c.licence and c.licence.lower() not in ("unknown", "unclear", "")

def test_real_and_synthetic_are_never_silently_merged():
    for r in report().runs:
        if r.dataset_type is DatasetType.SYNTHETIC:
            assert all(s.role == "calibration" for s in r.calibration_sources)
            assert not any(s.contributes_outcomes for s in r.calibration_sources)

def test_calibration_sources_cannot_emit_outcomes():
    for src in all_calibration_sources():
        assert not hasattr(src, "opportunities")
        assert not hasattr(src, "outcomes")
```

---

## 8. Outcome label quality

No external source in this report contains an attributable recovery outcome, so the §23A.7 question is settled by absence rather than by judgement.

Recorded as a standing rule, in case a candidate appears later: a dataset showing only *payment failed → payment later succeeded* does **not** license the conclusion that an intervention caused the recovery. Self-cure may have occurred. Such outcomes are classified `RECOVERED_UNATTRIBUTED` unless intervention timing and causal attribution are both present. **Treatment/control labels are never manufactured** — if the source has no randomisation, it produces no treatment effect estimate.

---

## 9. Data quality gate

Applied to the accepted calibration sources.

| Gate item | NPCI TD/BD | Samadhaan | Criteo (optional) |
|---|---|---|---|
| Relevant to payment recovery | ✅ (failure side) | ✅ (B2B ageing) | ⚠️ estimator only |
| Legally usable | ⚠️ **UNVERIFIED — manual check required** | ⚠️ **UNVERIFIED** | ✅ CC BY-NC-SA 4.0, non-commercial reading |
| No prohibited PII | ✅ aggregate | ✅ aggregate | ✅ anonymised + projected |
| Sufficient sample size | ✅ bank × month | ✅ | ✅ ~14M |
| Correct temporal ordering | ✅ monthly stamps | ✅ | n/a — no timestamps |
| No obvious target leakage | ✅ no target | ✅ no target | ✅ (drop nothing; treatment is the feature of interest) |
| Outcome definition understood | n/a — no outcome | n/a | ✅ visit / conversion |
| Missingness understood | ⚠️ pending extraction | ⚠️ pending | ✅ |
| Provenance recorded | ✅ by design | ✅ | ✅ |
| Reproducible preprocessing | ✅ hashed rate table | ✅ | ✅ |

**Gate verdict: CONDITIONAL PASS.** Both primary calibration sources are blocked on one item — a manual licence/terms check. Until that is done:

> Use published *ranges* from secondary reporting as generator priors, cited inline, and do not redistribute either table in the repository.

That fallback captures most of the calibration value with none of the licence exposure, and it is what ships if the check is not completed before the build freeze.

---

## 10. What could not be verified

Stated explicitly so nothing here is mistaken for a checked fact:

1. **NPCI page terms of use** — the page returned HTTP 403 to automated fetch. Format, download availability and licence all need a manual browser visit.
2. **Kaggle dataset licences** — the licence field requires a signed-in dataset page; not checked for LendingClub or KKBox. Both are rejected on other grounds anyway.
3. **Hillstrom licence** — no explicit statement found on the `scikit-uplift` documentation page. Absence of a found licence is not absence of a licence, but §23A.10 treats it the same way.
4. **Samadhaan report terms** — public report pages resolve, but terms of reuse were not read.
5. **Criteo non-commercial applicability** — whether a Razorpay-hosted buildathon submission counts as non-commercial is a judgement call, not a verified fact. Flagged for the user's decision.

---

## 11. Bottom line

The research did not find data that changes the experiment, and it was never likely to — recovery-intervention data is exactly the kind of data companies do not publish. What it did find is enough to stop the failure distribution being invented:

- **Decision: `USE_EXTERNAL_DATA_FOR_CALIBRATION`** (Level 1), pending one manual licence check with a defined fallback.
- **The controlled synthetic experiment remains canonical.** Arms, estimators, primary metric and every frozen claim are unchanged.
- **Nothing in the architecture changes.** Two new calibration modules and a provenance block; the engine, the ledger, the arbitration and the experiment runner are untouched.
- **The honest sentence for the README**: *"Issuer failure rates and B2B ageing distributions are calibrated against published NPCI and MSME Samadhaan figures. All interventions, customer responses and recovery outcomes are synthetic. Calibrating a simulator with real inputs does not make its outputs real."*

---

## Sources

- [Criteo Uplift Prediction Dataset — Criteo AI Lab](https://ailab.criteo.com/criteo-uplift-prediction-dataset/)
- [scikit-uplift — Criteo dataset description](https://github.com/maks-sh/scikit-uplift/blob/master/sklift/datasets/descr/criteo.rst)
- [scikit-uplift — `fetch_hillstrom` documentation](https://www.uplift-modeling.com/en/latest/api/datasets/fetch_hillstrom.html)
- [UCI Machine Learning Repository — Bank Marketing](https://archive.ics.uci.edu/dataset/222/bank+marketing)
- [NPCI — UPI Ecosystem Statistics](https://www.npci.org.in/what-we-do/upi/upi-ecosystem-statistics)
- [D91 Labs — Why UPI Success Rate matters](https://d91labs.substack.com/p/why-upi-success-rate-matters)
- [MSME SAMADHAAN — Delayed Payment Monitoring System](https://samadhaan.msme.gov.in/)
- [MSEFC — Age/Category amount-wise pendency report](https://samadhaan.msme.gov.in/MyMsme/MSEFC/MSEFC_CategoryAmtAge_Rpt2.aspx?Sid=3&CatName=State+Govt.)
- [RBI — Database on the Indian Economy (DBIE)](https://data.rbi.org.in/DBIE/)
- [Razorpay Status Page](https://status.razorpay.com/)
- [WSDM 2018 — KKBox's Churn Prediction Challenge](https://github.com/jason-learn/WSDM-KKBoxs-Churn-Prediction-Challenge)
- [Kaggle — All LendingClub loan data](https://www.kaggle.com/datasets/wordsforthewise/lending-club)
