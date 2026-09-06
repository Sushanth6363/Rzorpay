"""The escalation ladder must actually climb, on both clocks, for the right reasons.

WHY THIS EXISTS
    On a compressed demo clock the ladder silently did not work. Observed live:

        14:15:57  EMAIL_LINK  EXECUTED
        14:16:11  EMAIL_LINK  EXECUTED     <- follow-up, same rung, no SMS

    `RECOVERY_FOLLOWUP_HOUR_SECONDS` compresses the follow-up SCHEDULE so a review that
    would take a week takes seconds. It does not touch the 24h quiet period, which is
    measured against real timestamps. So every follow-up landed seconds after the previous
    contact, the cooldown was permanently active, the ceiling was pinned at rung 0, and
    the engine re-sent the same rung forever.

    It took two fixes because the first and subsequent touches run through DIFFERENT
    orchestrators: `RecoveryAgent` for the first, `get_orchestrator()` in the webhook
    listener for every follow-up. Relaxing one left the other pinned, and the symptom did
    not change at all - which is exactly why the second fix needed a test rather than
    another look at the screen.

WHAT MUST NOT CHANGE
    The relaxation is conditional on the compressed clock. At real timing the quiet period
    binds exactly as in production: it protects customers from being escalated at within
    24 hours of the last contact, and it is not a demo inconvenience to be switched off.
"""

import pytest

from app.domain.enums import ActionType, LedgerStatus
from app.domain.models import ContactLedgerEntry
from app.pipeline.escalation import (
    ESCALATION_LADDER,
    MAX_ENTRY_RUNG,
    RUNG_OF,
    EscalationPolicy,
)

EMAIL = RUNG_OF[ActionType.EMAIL_LINK]
SMS = RUNG_OF[ActionType.SMS_LINK]
WHATSAPP = RUNG_OF[ActionType.WHATSAPP_LINK]
IVR = RUNG_OF[ActionType.IVR_CALL]
AGENT = RUNG_OF[ActionType.AGENT_DIAL]

DEMO = "OVERDUE_B2B_INVOICE"


def _contact(action, at, status=LedgerStatus.EXECUTED):
    return ContactLedgerEntry(
        ledger_id=f"l_{action.value}_{at}", merchant_id="m1", customer_id="c1",
        opportunity_id="o1", action_type=action,
        intervention_idempotency_key=f"k_{action.value}_{at}", status=status,
        created_at=at, updated_at=at, attempted_at=at, resolved_at=at,
    )


def _ceiling(history, at, cooldown_hours):
    return EscalationPolicy(cooldown_hours=cooldown_hours).assess(
        history=history, decision_timestamp=at, event_type_value=DEMO,
        has_email=True, has_phone=True,
    ).allowed_max_rung


# --- the whole ladder, seconds apart, as a demo runs it --------------------------------


def test_the_ladder_climbs_every_rung_on_a_compressed_clock():
    """The demo, start to finish. Each touch is seconds after the last, which is the
    entire point of the compressed clock and was exactly what pinned the ceiling."""
    history = []
    reached = []
    for second, action in enumerate(
        [ActionType.EMAIL_LINK, ActionType.SMS_LINK,
         ActionType.WHATSAPP_LINK, ActionType.IVR_CALL]
    ):
        at = f"2026-09-06T14:00:{second * 5:02d}Z"
        history.append(_contact(action, at))
        reached.append(_ceiling(history, f"2026-09-06T14:00:{second * 5 + 4:02d}Z", 0))

    assert reached == [SMS, WHATSAPP, IVR, AGENT], (
        f"ladder stalled: reached {reached}, expected every rung"
    )


def test_the_same_sequence_is_pinned_at_rung_zero_with_the_quiet_period_on():
    """The defect, reproduced. Identical history, cooldown left at 24h, nothing moves."""
    history = [_contact(ActionType.EMAIL_LINK, "2026-09-06T14:00:00Z")]

    assert _ceiling(history, "2026-09-06T14:00:14Z", 24) == EMAIL


def test_one_email_is_enough_to_unlock_sms():
    history = [_contact(ActionType.EMAIL_LINK, "2026-09-06T14:00:00Z")]

    assert _ceiling(history, "2026-09-06T14:00:05Z", 0) == SMS


def test_it_never_skips_a_rung():
    """One rung at a time is the compliance claim. A confirmed email must not unlock a
    phone call, however long ago it was."""
    history = [_contact(ActionType.EMAIL_LINK, "2026-09-01T10:00:00Z")]

    assert _ceiling(history, "2026-09-20T10:00:00Z", 0) == SMS


def test_it_stops_at_the_top_of_the_ladder():
    history = [_contact(ActionType.AGENT_DIAL, "2026-09-06T14:00:00Z")]

    assert _ceiling(history, "2026-09-06T14:00:05Z", 0) == len(ESCALATION_LADDER) - 1


# --- what still binds when the quiet period is relaxed ---------------------------------


def test_a_failed_send_earns_nothing():
    """The line in the demo script. Only a CONFIRMED contact advances the ceiling, so a
    Twilio refusal must leave the ladder where it was."""
    history = [
        _contact(ActionType.EMAIL_LINK, "2026-09-06T14:00:00Z"),
        _contact(ActionType.SMS_LINK, "2026-09-06T14:00:05Z", LedgerStatus.FAILED_CLOSED),
    ]

    assert _ceiling(history, "2026-09-06T14:00:10Z", 0) == SMS, \
        "a failed SMS advanced the ladder as though it had arrived"


def test_no_contact_at_all_still_enters_at_the_bottom():
    """Relaxing the quiet period must not let a first touch open on a phone call."""
    assert _ceiling([], "2026-09-06T14:00:00Z", 0) <= MAX_ENTRY_RUNG


def test_a_channel_the_customer_cannot_receive_is_still_skipped():
    """Reachability is a separate control and is not relaxed by the demo clock."""
    assessment = EscalationPolicy(cooldown_hours=0).assess(
        history=[_contact(ActionType.EMAIL_LINK, "2026-09-06T14:00:00Z")],
        decision_timestamp="2026-09-06T14:00:05Z", event_type_value=DEMO,
        has_email=True, has_phone=False,
    )

    assert assessment.allowed_max_rung == EMAIL


# --- production timing is untouched ------------------------------------------------------


def test_at_real_timing_the_quiet_period_still_holds_the_ladder():
    """The control this whole exercise must not have weakened. Two contacts an hour apart
    in the real world is precisely what the 24h window exists to prevent."""
    history = [_contact(ActionType.EMAIL_LINK, "2026-09-06T14:00:00Z")]

    assert _ceiling(history, "2026-09-06T15:00:00Z", 24) == EMAIL


def test_after_the_real_quiet_period_elapses_it_advances():
    history = [_contact(ActionType.EMAIL_LINK, "2026-09-06T14:00:00Z")]

    assert _ceiling(history, "2026-09-08T14:00:00Z", 24) == SMS


# --- both orchestrators, because only fixing one changed nothing -------------------------


@pytest.mark.parametrize("compressed,expected", [(True, 0), (False, 24)])
def test_the_first_touch_orchestrator_relaxes_only_on_a_compressed_clock(
        tmp_path, monkeypatch, compressed, expected):
    """RecoveryAgent handles the FIRST contact."""
    monkeypatch.setenv("RECOVERY_DB_PATH", str(tmp_path / "agent.db"))
    monkeypatch.setenv("RECOVERY_FOLLOWUP_HOUR_SECONDS", "0.02" if compressed else "3600")
    import importlib
    from app.realtime import config as cfg
    importlib.reload(cfg)
    from app.realtime import ingest as ing
    importlib.reload(ing)
    from app.agent.loop import RecoveryAgent
    from app.cases.repository import CaseRepository

    conn = ing.get_conn()
    agent = RecoveryAgent(conn, repository=CaseRepository(conn))

    assert agent.orchestrator.pipeline.escalation_policy.cooldown_hours == expected


@pytest.mark.parametrize("compressed,expected", [(True, 0), (False, 24)])
def test_the_follow_up_orchestrator_relaxes_only_on_a_compressed_clock(
        tmp_path, monkeypatch, compressed, expected):
    """Every touch AFTER the first re-enters through the webhook listener's orchestrator.
    Fixing the agent alone left this one pinned and the symptom did not change."""
    monkeypatch.setenv("RECOVERY_DB_PATH", str(tmp_path / "listener.db"))
    monkeypatch.setenv("RECOVERY_FOLLOWUP_HOUR_SECONDS", "0.02" if compressed else "3600")
    import importlib
    from app.realtime import config as cfg
    importlib.reload(cfg)
    from app.realtime import ingest as ing
    importlib.reload(ing)
    from app.api import webhook_listener as wl
    importlib.reload(wl)

    orch = wl.get_orchestrator()

    assert orch.pipeline.escalation_policy.cooldown_hours == expected
