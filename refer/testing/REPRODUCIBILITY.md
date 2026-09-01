# REPRODUCIBILITY

Every experiment must be reproducible from recorded inputs alone.

## Recorded for every run

```
Python version           UNKNOWN - record at first run
Package versions         UNKNOWN - requirements.txt does not exist yet
OS                       Windows 11 (dev machine)
Random seeds             see 07_EXPERIMENT_METHODOLOGY.md seed roles
reference_timestamp      explicit generator input, never datetime.now()
Dataset version + hash   dataset_hash = sha256(canonical_json(config + opportunities))
Model version + hash     models/vN.meta.json artifact_hash
Git commit               code_version on every decision and outcome
Experiment configuration experiments/preregistration.json (git-tagged)
Database schema version  schema_version row
Calibration sources      id, version, licence, content_hash
```

## Guarantee

```
same seed + same reference_timestamp + same config  =  identical opportunity set
```

Asserted by three tests: identical hash across processes, across simulated calendar days, and across generation orders. A fourth test AST-scans the package for wall-clock calls and fails if any exist outside the clock adapter.

## Money

All amounts are **integer paise**. Floats are not bit-reproducible across platforms and summation orders, which would make the content hash and the reported figures drift.

## Randomness

Never a global RNG. One substream per entity: `Random(sha256(seed | entity_id))`. This makes generation order-independent and gives common random numbers across arms for free.

## Regeneration

```
make setup && make eval
```

must reproduce every number in the submission from the seed list alone, on a fresh clone, with no account and no key. **This is the single highest-signal test a reviewer can run.**

## Current status

`UNKNOWN — REQUIRES VERIFICATION`. Nothing has been run. Python and package versions will be recorded when the environment is first created.
