# 05 — SAFETY INVARIANTS

**These nine invariants are non-negotiable.** Changing any one requires an ADR with explicit approval — never a silent edit, never a refactor side-effect.

Status of all nine: **`PLANNED`** — specified and testable, none yet implemented or verified.

---

## INV-1 — Tenant isolation

> A merchant can never access or consume another merchant's recovery state or contact budget.

- **Reason**: the same email or phone at two merchants is two different people from the system's point of view. Merging them silently exhausts one merchant's budget with another's activity — a correctness bug with an embarrassing failure mode.
- **Implementation**: `merchant_id` in every tenant-scoped primary key; `TenantScopedDB` rejects any statement lacking a merchant predicate; cache keys prefixed `{merchant_id}:`; features merchant-local or on the cross-merchant whitelist; `merchant_id` excluded as a model feature.
- **Test**: same email/phone/external-id at two merchants → independent budgets, histories and features; unscoped query raises `TenantScopeViolation`.
- **Failure behaviour**: raise, never proceed.

## INV-2 — Atomic contact reservation

> The system must never exceed the configured contact budget because of concurrent reservations.

- **Reason**: this is the project's central claim. A read-then-write implementation defeats it silently — the system looks correct until stress-tested.
- **Implementation**: `BEGIN IMMEDIATE`; idempotency-key lookup **before** any counter movement; single conditional `UPDATE … WHERE reserved_count + consumed_count < cap`; DB `CHECK (reserved_count + consumed_count <= cap)`; every state transition a compare-and-swap whose rowcount decides the counter move.
- **Test**: cap binds after executions; same idempotency key → one slot; 2/10/100 concurrent workers; Hypothesis fuzz over arbitrary interleavings.
- **Failure behaviour**: reject the reservation; never over-grant.
- **Note**: `consumed_count` means *permanently unavailable for reuse* — confirmed sent **or** failed closed after an unresolved execution. It does **not** mean "confirmed sent"; `contacts_sent` is `COUNT(status='executed')`.

## INV-3 — Exploration safety

> Exploration can only select from actions already approved by the hard safety/policy layer.

- **Reason**: exploration is not permission to execute any action. A random seed must never be able to produce an unsafe contact.
- **Implementation**: the hard filter runs first and its output *is* the exploration pool. Abstention triggers are typed — exploration may override a **VALUE** trigger (`below_value_threshold`, `cost_exceeds_benefit`) but never a **SAFETY** trigger (`unexplained_shortfall`, `identity_unresolved`, `policy_indeterminate`, `payment_state_unknown`, `contact_cooldown`). When a SAFETY trigger fires the eligible set collapses to `{NO_ACTION}`.
- **Test**: property test over 2,000 seeds × 6 constraints — no seed produces an ineligible action; exploration never overrides a SAFETY abstention; exploration *does* produce variety under a VALUE abstention.
- **Failure behaviour**: fall back to `NO_ACTION`.

## INV-4 — Downtime safety

> A known gateway outage suppresses retry recommendations at the recovery layer.

- **Reason**: recommending retries into a bank that is down burns the retry cap and contacts customers for nothing.
- **Implementation**: outage state is a hard-filter input; suppression is scope-limited to the affected method/issuer; resolution triggers a staggered batch, never a simultaneous flood.
- **Test**: 40 failures on one issuer → suppressed; unaffected issuers unaffected; batched on resolution.
- **Failure behaviour**: on a stale or missing signal, poll-fallback and flag lower confidence.

## INV-5 — Retry ownership

> The Recovery Engine recommends or suppresses retries but never becomes the payment execution authority.

- **Reason**: Razorpay's own infrastructure retries independently, and no retry-state interface has been verified. An engine-side cap layered on an unknown processor-side count is an assumption presented as a safety property.
- **Implementation**: `RECOMMEND_RETRY` exists; `EXECUTE_RETRY` does not exist in the action enum; the executor holds no retry-capable credential; a static call-graph test asserts no path from engine code to a retry API.
- **Test**: `EXECUTE_RETRY` absent; credential scopes disjoint from retry scopes; no call path.
- **Failure behaviour**: unknown retry state → no engine-side retry recommendation (fail closed).

## INV-6 — Execution unknown

> `EXECUTION_UNKNOWN` cannot automatically trigger another retry or another send.

- **Reason**: an ambiguous provider response is exactly when a blind resend produces the duplicate contact the whole system exists to prevent.
- **Implementation**: `execution_unknown` is not re-executable; the slot stays held in `reserved_count`; a bounded reconciliation ladder (1m/5m/30m/2h/6h/24h) resolves to `executed`, `released`, or fail-closed `unresolved` with a human-review queue entry.
- **Conservative Slot Consumption Rationale**: If an execution attempt outcome remains ambiguous after the reconciliation ladder elapses (`RECONCILED_UNRESOLVED`), the system **cannot safely assume the intervention did not happen**. Releasing capacity back to the customer's budget could allow a subsequent automated decision to send another contact, permitting a duplicate intervention. The conservative safety policy is therefore to **consume the slot** (`reserved_count - 1, consumed_count + 1`) and send the case to the human-review queue. Note that `contacts_delivered` is computed strictly as `COUNT(status='EXECUTED' OR status='RECONCILED_DELIVERED')`, never from `consumed_count`.
- **Test**: attempt re-execute raises; send count stays 1 after 72 simulated hours; `unresolved_execution_rate` reported.
- **Failure behaviour**: fail closed — assume it may have been sent, consume slot, enqueue for human review.


## INV-7 — Point-in-time features

> `feature.observed_at <= decision_timestamp`, for every feature, every time.

- **Reason**: a model that sees the future looks excellent and means nothing.
- **Implementation**: `FeatureRecord.observed_at` is mandatory; `build_features` raises `LeakageError` on violation or on a denylisted field; labels must satisfy `observed_at > decision_timestamp`; splits grouped by customer and ordered by time.
- **Test**: `test_no_future_features`, `test_training_cutoff`, `test_inference_cutoff`, `test_outcome_not_available_at_decision_time`; permuted-label canary yields AUC ∈ (0.45, 0.55). **`pytest -m leakage` gates CI.**
- **Failure behaviour**: raise; a violation fails the build, it does not warn.

## INV-8 — Self-cure

> Payments occurring before an intervention are never attributed as intervention-generated recovery.

- **Reason**: it is the easiest way to inflate the headline number and the first thing a hostile reviewer tests.
- **Implementation**: ordering checked against **delivery** timestamps, not send timestamps, and evaluated *before* any attribution-window test. `SELF_CURED` carries zero attributed recovery and no decision id.
- **Test**: payment before first delivery → `SELF_CURED`; self-cure rate agrees across arms within 2pp (a validity check on the harness).
- **Failure behaviour**: attribute zero.

## INV-9 — NO_ACTION is a first-class decision

> `NO_ACTION` is generated, scored and ranked alongside interventions — never a fallback reached by exhaustion.

- **Reason**: it is the counterfactual baseline `Δ̂` is measured against. If it is not scored, the model has no incremental estimate to compute, and abstention becomes an accident rather than a decision.
- **Implementation**: always present in the candidate set; always scored; when it wins, `abstention_reason` and `abstention_kind` (SAFETY | VALUE) are recorded; consumes no budget slot.
- **Test**: present in every candidate set; seven triggers each produce their reason; abstention consumes no budget; `Δ̂` equals `selected_action_probability − no_action_probability`.
- **Failure behaviour**: absent `NO_ACTION` is a build failure.

---

## Enforcement

| | |
|---|---|
| Changing an invariant | **ADR mandatory**, with explicit human approval |
| Refactoring near one | run the invariant's test before and after |
| A failing invariant test | stop feature work; fix before proceeding |
| An agent that cannot find the test | status is `UNKNOWN — REQUIRES VERIFICATION`, never assumed passing |

**INV-2 is the one that fails silently.** Everything downstream of a broken ledger is void, and nothing will look wrong.
