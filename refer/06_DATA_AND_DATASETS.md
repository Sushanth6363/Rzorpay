# 06 — DATA AND DATASETS

Consolidated from `docs/DATASET_RESEARCH.md` (research performed 2026-08-31, sources listed there).

**Decision on record: `USE_EXTERNAL_DATA_FOR_CALIBRATION` (Level 1)** — ADR-0009.

---

## The finding that shapes everything

**No public dataset exists containing payment failure + a recorded intervention + the subsequent outcome.** This was searched for directly across Kaggle, Hugging Face, UCI, GitHub and the dunning literature. Every "failed payment recovery" query returns vendor marketing quoting internal recovery rates with no data behind it.

Consequences, stated as facts rather than preferences:

- **Level 3** (real intervention + outcome) — **not achievable**. Never claim it.
- **Level 2** (real transactions with a valid recovery target) — **not achievable**. No public payment dataset carries an attributable recovery outcome.
- **Level 1** (real distributions calibrating the generator) — achievable, and worth doing.

Recovery-intervention data is exactly the kind companies do not publish. That is not a gap in the research.

---

## Dataset inventory

| Name | Source | Licence | Access | Free? | Real/Synthetic | Can support | Cannot support | Used where |
|---|---|---|---|---|---|---|---|---|
| **NPCI UPI bank-wise TD/BD & uptime** | npci.org.in | **UNVERIFIED** (page returned HTTP 403 to automated fetch) | manual page visit | Yes | REAL, aggregate | issuer failure probability, failure-type mix, issuer share, outage severity | any customer-level claim; any recovery outcome | `app/data/external/npci_decline_calibration.py` |
| **MSME Samadhaan / MSEFC reports** | samadhaan.msme.gov.in | **UNVERIFIED** | manual page visit | Yes | REAL, aggregate | B2B ageing and pendency distribution | any customer-level claim; any recovery outcome | `app/data/external/samadhaan_ageing_calibration.py` |
| **Criteo Uplift** | ailab.criteo.com | **CC BY-NC-SA 4.0** (explicit) | form download | Yes | REAL, randomised | validating the estimator / CI machinery | anything about payment recovery | optional, `estimator validation` section only |
| **UCI Bank Marketing** | archive.ics.uci.edu | **CC BY 4.0** (explicit) | direct download | Yes | REAL | optional contact-fatigue prior | recovery outcomes | optional |
| **Synthetic generator output** | this project | n/a | `make generate` | n/a | **SYNTHETIC** | the controlled experiment | real-world uplift | everywhere |
| **Model training data** | derived from `EXPERIMENT_SET` outcomes | n/a | derived | n/a | **SYNTHETIC** | training v1 / v2 | real payer behaviour | `app/models/` |

### Rejected, and why

| Dataset | Reason |
|---|---|
| Hillstrom MineThatData | methodologically excellent (real 3-arm randomised contact experiment) but **no explicit licence found** → rejected under the unclear-licence rule |
| KKBox WSDM churn | closest analogue to the subscription stream, but no dunning action recorded and **no explicit licence found** |
| LendingClub | has `recoveries` as an *amount* with no record of what was done to obtain it → attribution impossible; licence unclear for redistributed copies |
| Credit-card fraud (ULB / IEEE-CIS) | real and completely irrelevant: `transaction → fraud_label`, no action, no response, no recovery. Using it would let the project say "real payment data" while modelling a different problem |
| Online Retail II | completed baskets; no failure, no abandonment, no intervention |
| HF transaction/categorisation corpora | classification framing; no action or outcome dimension |

---

## Classification discipline

```
REAL DATA          observed in the world by someone other than us
CALIBRATION DATA   real aggregate distributions used to set generator PARAMETERS
TRAINING DATA      what a model learns from — here, synthetic
SYNTHETIC DATA     produced by our generator and response function
```

> **Aggregate public payment statistics must not be presented as customer-level recovery outcomes.**

The `CalibrationSource` protocol is deliberately separate from `DatasetAdapter`: a calibration source has **no** `opportunities()` and **no** `outcomes()` method, so it is structurally impossible for real data to contribute a recovery label.

## Provenance

Every run records `dataset_type` ∈ `{SYNTHETIC, PUBLIC_REAL, PUBLIC_NEAR_REAL_TIME}` plus `calibration_sources[]` with id, version, licence and content hash. A run whose calibration source has licence `unknown` must not render results.

## Why synthetic recovery outcomes

Not a shortcut — a consequence. No public source contains what the project needs (state + action + outcome), and no real merchant traffic is available to a student build. The alternative to synthetic outcomes is *no outcomes*, not real ones.

What the synthetic environment can and cannot support is enumerated in `07_EXPERIMENT_METHODOLOGY.md` and `docs/EXPERIMENT_METHODOLOGY.md`.

## The sentence for the README

> Issuer failure rates and B2B ageing distributions are calibrated against published NPCI and MSME Samadhaan figures. All interventions, customer responses and recovery outcomes are synthetic. Calibrating a simulator with real inputs does not make its outputs real.

## Blockers

Both primary calibration sources are `BLOCKED` on one manual licence/terms check. **Fallback, already decided**: use published *ranges* from secondary reporting as priors, cite inline, redistribute nothing. That captures most of the calibration value with none of the licence exposure and does not block the build.
