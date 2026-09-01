# AGENT HANDOFF — HOW TO WORK ON THIS PROJECT

You are joining an existing project. **Do not assume anything.**

---

## The rule everything else follows from

> **Documentation is evidence, not truth. Code plus executed tests determine implementation status.**

This repository contains verified foundation code for **M1.1** (repository foundation & smoke tests) and **M1.2** (reproducibility & environment quality gate). The core domain model (M2), contact ledger (M3), recovery stages, and UI remain `PLANNED`.

Before claiming anything works, look at the code. Before claiming a test passes, run `python scripts/verify_environment.py` or `pytest`.


---

## Source-of-truth hierarchy

When sources conflict, **higher wins**, and the discrepancy must be logged in `progress/BUILD_LOG.md`.

```
1. Executed test / observed runtime behaviour
2. Current source code
3. Current database schema
4. Experiment artifacts and results
5. ADRs (refer/decisions/)
6. progress/CURRENT_STATUS.md
7. Other refer/ documentation
8. Historical documents (final.md, p0.*, strategy/, docs/)
9. Agent assumptions                          ← lowest, and usually wrong
```

**Do not silently reconcile conflicting information.** If `CURRENT_STATUS.md` says a component is implemented and the file does not exist, the file wins — and you report the conflict rather than quietly updating the document or quietly writing the missing code.

---

## Statement classification

Every claim you make about this project must carry one of these:

| Label | Means | Established by |
|---|---|---|
| `VERIFIED` | supported by code execution, a passing test, or direct inspection | you ran it or read it |
| `DOCUMENTED` | specified in project documentation, implementation status unknown | reading a document |
| `INFERRED` | reasoned from available evidence | your own reasoning |
| `PROPOSED` | a suggested future change | your suggestion |
| `UNKNOWN` | cannot currently be established | absence of evidence |

**Forbidden conversions:**

```
DOCUMENTED → VERIFIED     without running a test
PROPOSED   → IMPLEMENTED  without writing code
UNKNOWN    → TRUE         by assumption
EXPECTED   → OBSERVED     without a real experiment run
```

If you cannot establish something, write `UNKNOWN — REQUIRES VERIFICATION`. That is a complete and acceptable answer. Guessing is not.

---

## The working cycle

Every session follows this. No steps skipped.

```
READ → UNDERSTAND → VERIFY → PLAN → ASK/DECIDE → IMPLEMENT
     → TEST → REPRODUCE → LOG → UPDATE STATE → COMMIT
```

### Before making changes

1. Read `00_START_HERE.md`, `progress/CURRENT_STATUS.md`, `progress/NEXT_STEPS.md`
2. Read the ADRs relevant to what you are touching (`decisions/ADR_INDEX.md`)
3. Read `05_SAFETY_INVARIANTS.md` if the change is anywhere near the ledger, policy, exploration, attribution or features
4. **Inspect the actual code and tests** — do not trust the documentation about what exists

### After making changes

1. Run the tests. Record what actually ran and what actually passed
2. Update `testing/TEST_MATRIX.md` with real results, dates and commits
3. Update `progress/CURRENT_STATUS.md`
4. Append to `progress/BUILD_LOG.md`
5. Record any failure in `testing/FAILURE_LOG.md` with a regression test
6. Write an ADR if you made a decision that qualifies
7. Commit, and record the commit hash

---

## Never do these

- Fabricate progress, test results, experiment results, or dataset availability
- Write `PASS` in the test matrix for a test you did not run
- Overwrite an experiment result — a failed E001 stays failed; the next attempt is E002
- Delete a historical failure — mark it resolved
- Remove or weaken a safety invariant
- Claim production readiness
- Treat a plan as an implementation
- Treat a simulated outcome as real-world evidence
- Describe `Δ̂` (a model estimate) as a measured causal effect

## Never do these silently

If you believe any of the following is necessary, **stop, explain, write or update an ADR, obtain explicit approval, then implement**:

- reinterpreting the architecture
- changing the database
- replacing CatBoost with another model
- changing exploration behaviour
- changing experiment methodology, arms, seeds or randomisation
- changing attribution logic
- changing a dataset
- adding infrastructure because it "would be better"
- adding anything on the `08_TOOLCHAIN.md` deny-list

The deny-list items are not forbidden forever. They were each considered and rejected for stated reasons. Reversing one requires engaging with that reason, not overlooking it.

---

## Decision traceability

Every meaningful change must trace:

```
Decision → ADR → Implementation → Test → Commit → CURRENT_STATUS
```

You must be able to answer *"why is the system implemented this way?"* by pointing at an ADR. If you cannot, either the ADR is missing (write it) or the implementation drifted from the decision (report it).

---

## Project-specific traps

Things that have already gone wrong once, or are unusually easy to get wrong here:

1. **The contact cap is checked as `reserved_count + consumed_count < cap`.** Checking `reserved_count` alone makes the cap inoperative after the first execution cycle, and nothing looks broken. See F-0001.
2. **`consumed_count` does not mean "confirmed sent."** It means permanently unavailable for reuse. `contacts_sent` is `COUNT(status='executed')`. See F-0005.
3. **Exploration draws from the *eligible* set, never the candidate set**, and may never override a SAFETY abstention. See ADR-0004.
4. **`Δ̂` is a model estimate used for ranking.** Claims come only from the arm-level experiment. See ADR-0005.
5. **Self-cure is checked against delivery timestamps**, not send timestamps, and before any attribution window test. See INV-8.
6. **The response function must be git-tagged before either scorer exists.** This ordering is the anti-rigging evidence and cannot be reconstructed later. See ADR-0005, P1-1.
7. **Money is integer paise everywhere.** Floats break the reproducibility hash.
8. **No `datetime.now()`** outside the clock adapter. It breaks reproducibility silently.

---

## If you are asked for results that do not exist

Say `NOT YET RUN`. Point at `experiments/EXPERIMENT_INDEX.md`. Offer to run the experiment.

The illustrative numbers in `final.md` §4 (₹79.2L at risk, 13.1% phantom, 219 contacts, ₹21.4L recovered) are **explicitly labelled illustrative in that document** and are a target shape for the harness to produce. Reporting them as observed results would be the single most damaging error available in this project.
