# ADR-0020 — Context-dependent sandbox outcome model (prediction falsified)

- **Status:** ACCEPTED
- **Date:** 2026-09-04
- **Affects:** experiment, claims, sandbox
- **Code:** `app/sandbox/outcome_model.py`
- **Related:** ADR-0011 (arms), ADR-0015 (escalation), ADR-0017 (training source)

## Context

The sandbox decided outcomes from **one input**: which channel was used. Not the failure
reason, not the amount, not the customer. In such a world the optimal scorer is a fixed
ranking of six channels — and `HeuristicScorer` already *is* that ranking — so a correctly
trained model can at best tie it.

It did exactly that. After ADR-0017 fixed the train/serve mismatch, A5 and A3 produced
**byte-identical** metrics: a VOID ablation under ADR-0011.

The experiment was therefore structurally unable to test its own stated hypothesis. That
hypothesis was not invented for this ADR; it has been in `app/scoring/heuristic.py` since
the scorer was written:

> *"A flat table, deliberately simple: the heuristic knows the failure reason matters, but
> not how it interacts with the specific action. That interaction is what the model may or
> may not capture."*

## Decision

Add a diagnosis × channel interaction and an amount effect to the sandbox, so the world
contains the structure the hypothesis is about. Base channel rates are **identical** to the
context-free model, so that world is a strict special case and the change cannot be a
rescaling that flatters any action. `HeuristicScorer` is **left unchanged** — a person
writing a recovery playbook writes a flat table, which is what it models.

### Pre-registration

Predictions and falsification conditions were written into the module docstring and
committed **before the model was ever run**:

- **P1.** A5 will beat A3.
- **P2.** The gap will be modest.
- **P3.** Contact efficiency will improve more than raw recovery rate.
- **F1.** A gap above +15pp indicates leakage, not success — investigate before reporting.
- **F2.** If A5 still ties, report it and attempt **no further DGP change**.
- **F3.** If A5 loses, report as-is.

## Result: P1 FALSIFIED

**A5 − A3 = +0.0005 (0.05pp), INCONCLUSIVE.** The arms are no longer identical, so the
ablation is no longer void — but the model gains essentially nothing.

### Why, measured rather than guessed

The two scorers choose differently on **4 of 1000 decisions (0.4%)**, and only four actions
are ever selected by either arm:

```
A3: RECOMMEND_RETRY 578 · EMAIL_LINK 302 · NO_ACTION 91 · SMS_LINK 29
A5: RECOMMEND_RETRY 578 · EMAIL_LINK 306 · NO_ACTION 91 · SMS_LINK 25
```

`WHATSAPP_LINK`, `IVR_CALL` and `AGENT_DIAL` are **never chosen at all**. The compliant
escalation ceiling (ADR-0015) caps intensity at the stream's entry rung until a confirmed
contact plus an elapsed quiet period earns the next, and the contact budget bounds how often
that happens. The interaction added here lives mostly in the high rungs.

**The model can see the structure. Policy forbids acting on it.**

## The finding this produced

> **Compliant escalation bounds the action space so tightly that scorer quality is nearly
> irrelevant. Policy has already made the decision 99.6% of the time.**

This is the strongest available evidence that the engine's value is in its *controls*, not
its model — and it is measured, not asserted. It also independently corroborates the
contact-efficiency thesis.

Per F2, **no further DGP change was attempted** to manufacture a win.

## Consequences

- The sandbox is more realistic; a retry genuinely helps insufficient funds and is genuinely
  useless for a card needing replacement.
- All arms' recovery rates rise by roughly 1.5–2pp (a level shift, not a differential).
- The headline claim changes from "the AI loses" to "policy dominates the scorer", which is
  both more accurate and more defensible.
- A failed pre-registered prediction is reported as a failed prediction. That is the point
  of pre-registering.

## Honest caveat

Every figure remains synthetic. This ADR changes the *shape* of an authored simulation to
match payments domain reasoning; it does not make the simulation real, and no claim of
real-world recovery uplift follows from it.
