"""Compliant escalation — bounded intensity, one rung at a time (ADR-0015).

The bar for Track 3 names "compliant escalation" explicitly. These tests define what the
word compliant is doing in that sentence: intensity rises only on evidence, only by one
rung, only after a quiet period, and never over the top of a safety rejection.
"""

from app.domain.enums import (
    ActionType,
    EligibilityStatus,
    EventType,
    LedgerStatus,
    SafetyRejectReason,
)
from app.domain.models import ActionCandidate, ContactLedgerEntry
from app.pipeline.escalation import (
    ESCALATION_LADDER,
    MAX_ENTRY_RUNG,
    TOP_RUNG,
    EscalationPolicy,
)

T0 = "2026-01-01T00:00:00+00:00"
T_PLUS_2H = "2026-01-01T02:00:00+00:00"
T_PLUS_2D = "2026-01-03T00:00:00+00:00"
T_PLUS_10D = "2026-01-11T00:00:00+00:00"


def _entry(action: ActionType, status: LedgerStatus, resolved_at: str) -> ContactLedgerEntry:
    return ContactLedgerEntry(
        ledger_id=f"led_{action.value}_{resolved_at}",
        merchant_id="m1",
        customer_id="c1",
        opportunity_id="opp1",
        action_type=action,
        intervention_idempotency_key=f"idem_{action.value}_{resolved_at}",
        status=status,
        created_at=resolved_at,
        updated_at=resolved_at,
        attempted_at=resolved_at,
        resolved_at=resolved_at,
    )


def _eligible(action: ActionType) -> ActionCandidate:
    return ActionCandidate(
        action_type=action,
        eligibility=EligibilityStatus.ELIGIBLE,
        reject_reason=SafetyRejectReason.NONE,
        reason_explanation="passed hard safety",
        evidence={},
        is_counterfactual=(action == ActionType.NO_ACTION),
    )


ALL_CANDIDATES = [_eligible(ActionType.NO_ACTION)] + [_eligible(a) for a in ESCALATION_LADDER]


def _eligible_actions(candidates):
    return {c.action_type for c in candidates if c.eligibility == EligibilityStatus.ELIGIBLE}


# --- Entry: the engine never opens with a phone call ------------------------------------


def test_first_touch_never_reaches_an_ivr_or_agent_call():
    """No history means no earned intensity. Rungs above the entry cap are unreachable."""
    policy = EscalationPolicy()

    out, assessment = policy.apply(
        candidates=ALL_CANDIDATES,
        history=[],
        decision_timestamp=T0,
        event_type_value=EventType.FAILED_PAYMENT.value,
    )

    eligible = _eligible_actions(out)
    assert ActionType.IVR_CALL not in eligible
    assert ActionType.AGENT_DIAL not in eligible
    assert assessment.allowed_max_rung <= MAX_ENTRY_RUNG


def test_entry_rung_is_stream_aware_but_hard_capped():
    """A mid-transaction failure may open with an SMS; an abandoned cart may not."""
    policy = EscalationPolicy()

    _, payment = policy.apply([], [], T0, EventType.FAILED_PAYMENT.value)
    _, cart = policy.apply([], [], T0, EventType.ABANDONED_CHECKOUT.value)
    _, invoice = policy.apply([], [], T0, EventType.OVERDUE_B2B_INVOICE.value)

    assert payment.allowed_max_rung == 1      # SMS_LINK
    assert cart.allowed_max_rung == 0         # EMAIL_LINK
    assert invoice.allowed_max_rung == 0      # EMAIL_LINK
    # Whatever the stream, entry is capped. Loud channels are earned, never granted.
    for a in (payment, cart, invoice):
        assert a.allowed_max_rung <= MAX_ENTRY_RUNG


# --- One rung at a time -----------------------------------------------------------------


def test_escalation_advances_exactly_one_rung_never_two():
    """A confirmed email earns an SMS. It does not earn a WhatsApp, and never an agent."""
    policy = EscalationPolicy()
    history = [_entry(ActionType.EMAIL_LINK, LedgerStatus.EXECUTED, T0)]

    out, assessment = policy.apply(
        candidates=ALL_CANDIDATES,
        history=history,
        decision_timestamp=T_PLUS_2D,
        event_type_value=EventType.ABANDONED_CHECKOUT.value,
    )

    assert assessment.highest_confirmed_rung == 0
    assert assessment.allowed_max_rung == 1
    eligible = _eligible_actions(out)
    assert ActionType.SMS_LINK in eligible
    assert ActionType.WHATSAPP_LINK not in eligible
    assert ActionType.AGENT_DIAL not in eligible


def test_ladder_never_advances_past_the_top():
    """At AGENT_DIAL there is nowhere louder to go, and the policy says so."""
    policy = EscalationPolicy()
    history = [_entry(ActionType.AGENT_DIAL, LedgerStatus.EXECUTED, T0)]

    _, assessment = policy.apply(ALL_CANDIDATES, history, T_PLUS_10D, EventType.FAILED_PAYMENT.value)

    assert assessment.allowed_max_rung == TOP_RUNG
    assert "top of the ladder" in assessment.explanation


# --- Evidence gating --------------------------------------------------------------------


def test_an_unknown_send_does_not_earn_an_escalation():
    """You may not escalate on a message you cannot prove reached anyone.

    EXECUTION_UNKNOWN is the state where the engine does not know whether the customer was
    contacted. Advancing the ladder on it would risk a louder second message to someone who
    has received nothing at all — exactly the harm escalation rules exist to prevent.
    """
    policy = EscalationPolicy()
    history = [_entry(ActionType.EMAIL_LINK, LedgerStatus.EXECUTION_UNKNOWN, T0)]

    _, assessment = policy.apply(
        ALL_CANDIDATES, history, T_PLUS_10D, EventType.ABANDONED_CHECKOUT.value
    )

    assert assessment.confirmed_contact_count == 0
    assert assessment.highest_confirmed_rung == -1
    assert assessment.allowed_max_rung == 0  # still at entry


def test_a_reconciled_delivery_does_earn_an_escalation():
    """A reconciled-delivered contact is proof, and proof advances the ladder."""
    policy = EscalationPolicy()
    history = [_entry(ActionType.EMAIL_LINK, LedgerStatus.RECONCILED_DELIVERED, T0)]

    _, assessment = policy.apply(
        ALL_CANDIDATES, history, T_PLUS_10D, EventType.ABANDONED_CHECKOUT.value
    )

    assert assessment.confirmed_contact_count == 1
    assert assessment.allowed_max_rung == 1


def test_a_not_sent_reconciliation_does_not_earn_an_escalation():
    """A message proven NOT sent cannot be the basis for a louder follow-up."""
    policy = EscalationPolicy()
    history = [_entry(ActionType.EMAIL_LINK, LedgerStatus.RECONCILED_NOT_SENT, T0)]

    _, assessment = policy.apply(
        ALL_CANDIDATES, history, T_PLUS_10D, EventType.ABANDONED_CHECKOUT.value
    )

    assert assessment.allowed_max_rung == 0


# --- Quiet period -----------------------------------------------------------------------


def test_no_escalation_inside_the_quiet_period():
    """Two hours after an email, the customer has not refused — they have not read it."""
    policy = EscalationPolicy(cooldown_hours=24)
    history = [_entry(ActionType.EMAIL_LINK, LedgerStatus.EXECUTED, T0)]

    out, assessment = policy.apply(
        ALL_CANDIDATES, history, T_PLUS_2H, EventType.ABANDONED_CHECKOUT.value
    )

    assert assessment.cooldown_active is True
    assert assessment.allowed_max_rung == 0
    assert ActionType.SMS_LINK not in _eligible_actions(out)
    suppressed = [c for c in out if c.action_type == ActionType.SMS_LINK][0]
    assert suppressed.reject_reason == SafetyRejectReason.ESCALATION_COOLDOWN


def test_escalation_resumes_once_the_quiet_period_has_elapsed():
    policy = EscalationPolicy(cooldown_hours=24)
    history = [_entry(ActionType.EMAIL_LINK, LedgerStatus.EXECUTED, T0)]

    _, assessment = policy.apply(
        ALL_CANDIDATES, history, T_PLUS_2D, EventType.ABANDONED_CHECKOUT.value
    )

    assert assessment.cooldown_active is False
    assert assessment.allowed_max_rung == 1


def test_unreadable_timestamps_hold_the_ladder_still():
    """Cannot prove the window elapsed -> assume it has not. Conservative direction."""
    policy = EscalationPolicy()
    bad = _entry(ActionType.EMAIL_LINK, LedgerStatus.EXECUTED, "not-a-timestamp")

    _, assessment = policy.apply(
        ALL_CANDIDATES, [bad], T_PLUS_10D, EventType.ABANDONED_CHECKOUT.value
    )

    assert assessment.cooldown_active is True
    assert assessment.allowed_max_rung == 0


# --- Subtractive only: escalation is a VALUE control under SAFETY controls ---------------


def test_escalation_can_never_revive_a_safety_rejected_candidate():
    """The single most important property. Escalation removes; it never grants.

    A candidate rejected by the hard safety filter — a gateway outage, an exhausted contact
    budget — stays rejected with its original reason, even when it sits well below the
    escalation ceiling. Escalation is layered UNDER safety, never over it (INV-4, ADR-0003).
    """
    policy = EscalationPolicy()
    safety_rejected = ActionCandidate(
        action_type=ActionType.EMAIL_LINK,   # rung 0 — below any ceiling
        eligibility=EligibilityStatus.SAFETY_REJECTED,
        reject_reason=SafetyRejectReason.KNOWN_GATEWAY_OUTAGE,
        reason_explanation="gateway outage",
        evidence={},
    )

    # A history that would justify escalating all the way to the top rung.
    history = [_entry(ActionType.AGENT_DIAL, LedgerStatus.EXECUTED, T0)]
    out, _ = policy.apply([safety_rejected], history, T_PLUS_10D, EventType.FAILED_PAYMENT.value)

    assert out[0].eligibility == EligibilityStatus.SAFETY_REJECTED
    assert out[0].reject_reason == SafetyRejectReason.KNOWN_GATEWAY_OUTAGE


def test_off_ladder_actions_are_untouched_by_escalation():
    """NO_ACTION and RECOMMEND_RETRY have no intensity, so they have no rung.

    RECOMMEND_RETRY is a message to the payment infrastructure, not to a person (ADR-0006);
    suppressing it as though it were an escalation would confuse a safety control with a
    politeness control.
    """
    policy = EscalationPolicy()
    candidates = [_eligible(ActionType.NO_ACTION), _eligible(ActionType.RECOMMEND_RETRY)]

    out, _ = policy.apply(candidates, [], T0, EventType.FAILED_PAYMENT.value)

    assert _eligible_actions(out) == {ActionType.NO_ACTION, ActionType.RECOMMEND_RETRY}


def test_suppression_is_recorded_with_its_working_for_the_audit_trail():
    """A rejection a reviewer cannot reconstruct is not an audit trail."""
    policy = EscalationPolicy()

    out, assessment = policy.apply(
        ALL_CANDIDATES, [], T0, EventType.ABANDONED_CHECKOUT.value
    )

    agent = [c for c in out if c.action_type == ActionType.AGENT_DIAL][0]
    assert agent.reject_reason == SafetyRejectReason.ESCALATION_CEILING
    assert agent.evidence["candidate_rung"] == TOP_RUNG
    assert agent.evidence["allowed_max_rung"] == 0
    assert ActionType.AGENT_DIAL.value in assessment.suppressed_actions
    assert assessment.to_dict()["ladder"] == [a.value for a in ESCALATION_LADDER]


# --- End to end through the real orchestrator -------------------------------------------


def test_ladder_advances_one_rung_per_contact_through_the_full_engine():
    """The whole loop, not just the policy object.

    This test exists because of a real defect it now guards. The ledger stamped
    `resolved_at` from the wall clock while decisions ran on the batch's time axis, so
    every prior contact appeared to have happened in a different epoch, the quiet period
    was permanently active, and the ladder never moved. Escalation was present in the code
    and dead in every run. Nothing in the unit tests above could have caught it.
    """
    from app.domain.enums import ExperimentArm
    from app.experiment.policies import build_orchestrator_for_arm

    orch = build_orchestrator_for_arm(ExperimentArm.A3)
    base = {
        "merchant_id": "m_esc",
        "customer_id": "cust_esc",
        "event_type": EventType.ABANDONED_CHECKOUT.value,
        "amount_paise": 500_000,
        "cart_status": "ABANDONED",
    }
    # Three opportunities for one customer, well outside each other's quiet period.
    timestamps = [
        "2026-01-01T00:00:00+00:00",
        "2026-01-10T00:00:00+00:00",
        "2026-01-20T00:00:00+00:00",
    ]

    actions = []
    for i, ts in enumerate(timestamps):
        event = dict(base, event_id=f"esc_{i}", occurred_at=ts, observed_at=ts)
        result = orch.process_and_execute(
            raw_event=event, decision_timestamp=ts, random_seed=42, arm="A3"
        )
        actions.append(result.decision.selected_action)

    # Exactly one rung per confirmed contact, in order, no skipping.
    assert actions == [ActionType.EMAIL_LINK, ActionType.SMS_LINK, ActionType.WHATSAPP_LINK]


def test_the_engine_does_not_escalate_inside_the_quiet_period_end_to_end():
    """Same customer, same day: intensity is held even though the ladder could advance."""
    from app.domain.enums import ExperimentArm
    from app.experiment.policies import build_orchestrator_for_arm

    orch = build_orchestrator_for_arm(ExperimentArm.A3)
    base = {
        "merchant_id": "m_cool",
        "customer_id": "cust_cool",
        "event_type": EventType.ABANDONED_CHECKOUT.value,
        "amount_paise": 500_000,
        "cart_status": "ABANDONED",
    }
    timestamps = ["2026-01-01T00:00:00+00:00", "2026-01-01T02:00:00+00:00"]

    actions = []
    for i, ts in enumerate(timestamps):
        event = dict(base, event_id=f"cool_{i}", occurred_at=ts, observed_at=ts)
        result = orch.process_and_execute(
            raw_event=event, decision_timestamp=ts, random_seed=42, arm="A3"
        )
        actions.append(result.decision.selected_action)

    assert actions == [ActionType.EMAIL_LINK, ActionType.EMAIL_LINK]
