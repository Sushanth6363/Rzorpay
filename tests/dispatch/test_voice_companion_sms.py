"""A call never leaves the customer empty-handed (ADR-0015, ADR-0021).

WHY THIS EXISTS
    A voice call is the only rung with no artifact. The customer misses it, or answers while
    driving and cannot write a URL down, and the engine has spent its most intrusive and
    most expensive action for nothing they can act on.

    So a placed call is accompanied by an SMS carrying the payment link.

NOT THE DOUBLE-CONTACT WE JUST REMOVED
    Razorpay's `notify` was sending an unrequested email AND SMS for every link: messages
    the engine never decided on, absent from the ledger, bypassing the ladder. This is the
    opposite in every respect - one decision, made by the engine, recorded in dispatch_log
    and on the timeline, delivered over two media because one of them is transient.

    The tests below pin that difference, because "send a second message" is exactly the
    shape of the bug that was just fixed, and the distinction is intent and auditability
    rather than message count.
"""

import pytest

from app.cases.models import Case, CaseEventKind, CaseStatus, Customer, PaymentLink
from app.cases.repository import CaseRepository
from app.db.init import init_db
from app.dispatch import channels
from app.dispatch.dispatcher import ChannelDispatcher
from app.domain.enums import ActionType

URL = "https://rzp.io/rzp/DEMO"


@pytest.fixture()
def env(monkeypatch):
    monkeypatch.setenv("RECOVERY_DISPATCH_ENABLED", "true")
    import importlib
    from app.realtime import config as cfg
    importlib.reload(cfg)

    conn = init_db(":memory:")
    repo = CaseRepository(conn)
    repo.upsert_customer(Customer(customer_id="c1", merchant_id="m1", name="Rahul",
                                  email="rahul@example.com", phone="+919876543210"))
    repo.create_case(Case(case_id="case_1", merchant_id="m1", customer_id="c1",
                          amount_paise=2_500_000, source_event_id="pay_ORIG"))
    repo.save_payment_link(PaymentLink(
        payment_link_id="plink_A", case_id="case_1", merchant_id="m1",
        customer_id="c1", amount_paise=2_500_000, reference_id="ref_1", short_url=URL))

    sent = {"calls": [], "sms": []}

    def fake_call(to, spoken, twiml_url=""):
        sent["calls"].append((to, spoken))
        return channels.DispatchResult("TWILIO_VOICE", "SENT", "call placed", provider_id="CA1")

    def fake_sms(to, body):
        sent["sms"].append((to, body))
        return channels.DispatchResult("TWILIO_SMS", "SENT", "queued", provider_id="SM1")

    monkeypatch.setattr(channels, "send_ivr_call", fake_call)
    monkeypatch.setattr(channels, "send_sms", fake_sms)

    return {"repo": repo, "sent": sent,
            "dispatcher": ChannelDispatcher(conn, repository=repo, dry_run=False)}


def _dispatch(env, action=ActionType.IVR_CALL, key="k1"):
    return env["dispatcher"].dispatch(
        "case_1", action, key, spoken="we tried to reach you", payment_url=URL)


# --- the behaviour asked for -----------------------------------------------------------------


def test_a_placed_call_is_followed_by_the_link_over_sms(env):
    _dispatch(env)

    assert len(env["sent"]["calls"]) == 1
    assert len(env["sent"]["sms"]) == 1
    assert URL in env["sent"]["sms"][0][1]


def test_the_sms_references_the_call_rather_than_arriving_out_of_nowhere(env):
    _dispatch(env)

    body = env["sent"]["sms"][0][1].lower()
    assert "call" in body


def test_an_agent_dial_gets_the_same_treatment(env):
    _dispatch(env, action=ActionType.AGENT_DIAL, key="k_agent")

    assert len(env["sent"]["sms"]) == 1


def test_the_companion_is_recorded_on_the_timeline(env):
    _dispatch(env)

    sent_events = [e for e in env["repo"].timeline("case_1")
                   if e.kind == CaseEventKind.MESSAGE_SENT]
    companions = [e for e in sent_events if e.detail.get("companion_to")]

    assert len(companions) == 1
    assert companions[0].detail["channel"] == "TWILIO_SMS"


# --- the boundaries that keep it from becoming the bug we just removed -----------------------


def test_a_call_that_was_never_placed_gets_no_sms(env, monkeypatch):
    """Substituting a channel is a policy decision. The dispatcher carries out the engine's
    instruction; it does not quietly choose a different one when that instruction fails."""
    monkeypatch.setattr(channels, "send_ivr_call",
                        lambda to, spoken, twiml_url="": channels.DispatchResult(
                            "TWILIO_VOICE", "NOT_CONFIGURED", "set TWILIO_VOICE_FROM"))

    out = _dispatch(env)

    assert out.sent is False
    assert env["sent"]["sms"] == []


def test_a_non_voice_action_gets_no_companion(env, monkeypatch):
    """Email and SMS already leave an artifact. Only a call does not."""
    monkeypatch.setattr(channels, "send_email_smtp",
                        lambda *a, **k: channels.DispatchResult("EMAIL_SMTP", "SENT", "ok"))

    env["dispatcher"].dispatch("case_1", ActionType.EMAIL_LINK, "k_email",
                               body="x", payment_url=URL)

    assert env["sent"]["sms"] == []


def test_a_payment_landing_between_call_and_sms_stops_the_sms(env, monkeypatch):
    """The window is milliseconds, and milliseconds is exactly when payments land. Payment
    always wins applies to the companion too, not just to the action that was decided."""
    real_call = channels.send_ivr_call

    def call_then_pay(to, spoken, twiml_url=""):
        result = real_call(to, spoken, twiml_url)
        env["repo"].set_status("case_1", CaseStatus.PAID, reason="paid mid-dispatch")
        return result

    monkeypatch.setattr(channels, "send_ivr_call", call_then_pay)

    _dispatch(env)

    assert len(env["sent"]["calls"]) == 1
    assert env["sent"]["sms"] == [], "texted a customer who had just paid"


def test_the_companion_is_not_sent_twice_on_a_redelivery(env):
    _dispatch(env, key="k_same")
    _dispatch(env, key="k_same")

    assert len(env["sent"]["sms"]) == 1


def test_it_can_be_switched_off(env, monkeypatch):
    import importlib
    monkeypatch.setenv("RECOVERY_VOICE_COMPANION_SMS", "false")
    from app.realtime import config as cfg
    importlib.reload(cfg)

    _dispatch(env, key="k_off")

    assert len(env["sent"]["calls"]) == 1
    assert env["sent"]["sms"] == []


def test_a_customer_with_no_phone_is_not_a_crash(env):
    """A separate customer, because upsert deliberately refuses to erase a known phone with
    a blank one - a re-uploaded CSV missing a column must not wipe contact details."""
    env["repo"].upsert_customer(Customer(customer_id="c_nophone", merchant_id="m1",
                                         name="Priya", email="p@example.com", phone=""))
    env["repo"].create_case(Case(case_id="case_nophone", merchant_id="m1",
                                 customer_id="c_nophone", amount_paise=100_000,
                                 source_event_id="pay_NP"))

    out = env["dispatcher"].dispatch("case_nophone", ActionType.IVR_CALL, "k_nophone",
                                     spoken="hello", payment_url=URL)

    assert out.sent is True
    assert env["sent"]["sms"] == []


def test_a_failed_companion_does_not_fail_the_call(env, monkeypatch):
    """The call happened and the contact is real. A companion that could not be delivered
    is recorded, not promoted into failing a successful contact."""
    monkeypatch.setattr(channels, "send_sms",
                        lambda to, body: channels.DispatchResult(
                            "TWILIO_SMS", "FAILED", "twilio rejected it"))

    out = _dispatch(env, key="k_smsfail")

    assert out.sent is True
    assert out.channel == "TWILIO_VOICE"
