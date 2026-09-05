"""ChannelDispatcher — the boundary that makes "payment always wins" bite (ADR-0024).

The central test is `test_a_payment_between_decision_and_execution_blocks_the_send`. Every
other guarantee in this file is secondary to it: a decision taken at 17:00 must not reach a
customer who paid at 17:30, and only something that re-reads case state at execution time
can enforce that.
"""

import pytest

from app.cases.models import Case, CaseEventKind, CaseStatus, Customer, PaymentLink
from app.cases.repository import CaseRepository
from app.db.init import init_db
from app.dispatch.dispatcher import ChannelDispatcher
from app.domain.enums import ActionType
from app.payments.link_service import PaymentLinkService


class FakeRazorpay:
    key_id = "rzp_test_REAL"

    def cancel_payment_link(self, payment_link_id):
        return {"id": payment_link_id, "status": "cancelled"}


@pytest.fixture()
def env():
    conn = init_db(":memory:")
    repo = CaseRepository(conn)
    repo.upsert_customer(Customer(
        customer_id="c1", merchant_id="m1", name="Rahul",
        email="rahul@example.com", phone="+919876543210",
    ))
    repo.create_case(Case(
        case_id="case_1", merchant_id="m1", customer_id="c1",
        amount_paise=2_500_000, source_event_id="pay_ORIG",
    ))
    repo.save_payment_link(PaymentLink(
        payment_link_id="plink_A", case_id="case_1", merchant_id="m1",
        customer_id="c1", amount_paise=2_500_000, reference_id="ref_1",
    ))
    return {
        "conn": conn, "repo": repo,
        "dispatcher": ChannelDispatcher(conn, repository=repo, dry_run=True),
        "payments": PaymentLinkService(conn, client=FakeRazorpay(), repository=repo),
    }


# --- PAYMENT ALWAYS WINS ----------------------------------------------------------------


def test_a_payment_between_decision_and_execution_blocks_the_send(env):
    """17:00 decide -> 17:30 pay -> 18:00 scheduler fires. Nothing may go out.

    This is the race the dispatcher exists to lose safely.
    """
    assert env["dispatcher"].precheck("case_1", ActionType.WHATSAPP_LINK).allowed is True

    env["payments"].mark_paid_from_provider_event("plink_A", "payment_link.paid", 100)

    out = env["dispatcher"].dispatch("case_1", ActionType.WHATSAPP_LINK, "k1", body="hi")
    assert out.status == "BLOCKED"
    assert "PAID" in out.reason


def test_the_dispatcher_re_reads_state_and_ignores_a_stale_caller_copy(env):
    """A Case held from an earlier decision is stale by construction. Trusting it would
    reintroduce exactly the bug this layer removes."""
    stale = env["repo"].get_case("case_1")
    assert stale.may_contact is True          # caller's copy still says "go"

    env["payments"].mark_paid_from_provider_event("plink_A", "payment_link.paid", 100)

    assert env["dispatcher"].dispatch(
        "case_1", ActionType.EMAIL_LINK, "k_stale", body="x"
    ).status == "BLOCKED"


def test_a_closed_case_blocks_contact(env):
    env["repo"].set_status("case_1", CaseStatus.CLOSED, reason="wrong person")

    out = env["dispatcher"].dispatch("case_1", ActionType.EMAIL_LINK, "k2", body="x")

    assert out.status == "BLOCKED"
    assert "CLOSED" in out.reason


def test_a_blocked_send_is_recorded_on_the_timeline(env):
    """A cancellation nobody can see is indistinguishable from a message that was lost."""
    env["payments"].mark_paid_from_provider_event("plink_A", "payment_link.paid", 100)
    env["dispatcher"].dispatch("case_1", ActionType.WHATSAPP_LINK, "k3", body="x")

    kinds = [e.kind for e in env["repo"].timeline("case_1")]
    assert CaseEventKind.ACTION_CANCELLED in kinds


def test_an_unknown_case_is_blocked_not_guessed(env):
    assert env["dispatcher"].dispatch(
        "case_NOPE", ActionType.EMAIL_LINK, "k4", body="x"
    ).status == "BLOCKED"


# --- Idempotency at the adapter boundary -------------------------------------------------


def test_the_same_idempotency_key_sends_once(env):
    """A provider timeout retried with the same key must not produce a second message."""
    first = env["dispatcher"].dispatch("case_1", ActionType.EMAIL_LINK, "same", body="x")
    second = env["dispatcher"].dispatch("case_1", ActionType.EMAIL_LINK, "same", body="x")

    assert first.status == "SKIPPED"        # dry run
    assert second.status == "DUPLICATE"


def test_different_keys_are_independent(env):
    env["dispatcher"].dispatch("case_1", ActionType.EMAIL_LINK, "a", body="x")

    assert env["dispatcher"].dispatch(
        "case_1", ActionType.EMAIL_LINK, "b", body="x"
    ).status != "DUPLICATE"


# --- Dry run is the default --------------------------------------------------------------


def test_dry_run_sends_nothing_but_still_reports_the_decision(env):
    out = env["dispatcher"].dispatch("case_1", ActionType.EMAIL_LINK, "k5", body="x")

    assert out.sent is False
    assert "DRY RUN" in out.reason


def test_dispatch_defaults_to_dry_run_when_not_explicitly_enabled(env, monkeypatch):
    """Tests must never accidentally send. The default has to be safe, not convenient."""
    monkeypatch.delenv("RECOVERY_DISPATCH_ENABLED", raising=False)
    import importlib
    from app.realtime import config as cfg
    importlib.reload(cfg)

    assert ChannelDispatcher(env["conn"], repository=env["repo"]).dry_run is True


# --- No policy of its own ----------------------------------------------------------------


def test_no_action_is_skipped_not_blocked(env):
    """NO_ACTION is the engine choosing not to contact. That is not a dispatcher veto."""
    out = env["dispatcher"].precheck("case_1", ActionType.NO_ACTION)

    assert out.status == "SKIPPED"


def test_recommend_retry_never_reaches_a_customer_channel(env):
    """ADR-0006: it targets the payment infrastructure, not a person."""
    out = env["dispatcher"].precheck("case_1", ActionType.RECOMMEND_RETRY)

    assert out.allowed is False
    assert "infrastructure" in out.reason


def test_an_open_case_is_allowed_through(env):
    """The dispatcher must not invent reasons to suppress. Safety already ran upstream."""
    for action in (ActionType.EMAIL_LINK, ActionType.SMS_LINK,
                   ActionType.WHATSAPP_LINK, ActionType.IVR_CALL):
        assert env["dispatcher"].precheck("case_1", action).allowed is True


def test_a_successful_send_advances_an_open_case_to_in_progress(env):
    d = ChannelDispatcher(env["conn"], repository=env["repo"], dry_run=False)
    import app.dispatch.channels as ch
    from app.dispatch.channels import DispatchResult
    original = ch.send_email_smtp
    ch.send_email_smtp = lambda *a, **k: DispatchResult("EMAIL_SMTP", "SENT", "ok", "id_1")
    try:
        out = d.dispatch("case_1", ActionType.EMAIL_LINK, "k6", subject="s", body="b")
    finally:
        ch.send_email_smtp = original

    assert out.sent is True
    assert env["repo"].get_case("case_1").status == CaseStatus.IN_PROGRESS


# --- Link cancellation on closure --------------------------------------------------------


def test_paying_cancels_any_other_live_link_on_the_case(env):
    """A live link on a settled debt lets a customer pay twice."""
    env["repo"].save_payment_link(PaymentLink(
        payment_link_id="plink_B", case_id="case_1", merchant_id="m1",
        customer_id="c1", amount_paise=2_500_000, reference_id="ref_2",
    ))

    env["payments"].mark_paid_from_provider_event("plink_A", "payment_link.paid", 100)

    assert env["repo"].get_payment_link("plink_B").status.value == "CANCELLED"


def test_cancellation_survives_a_provider_error(env):
    """The case is already correctly closed; a provider failure must not unwind that."""
    class Broken:
        key_id = "rzp_test_REAL"

        def cancel_payment_link(self, _):
            raise RuntimeError("provider down")

    svc = PaymentLinkService(env["conn"], client=Broken(), repository=env["repo"])
    env["repo"].save_payment_link(PaymentLink(
        payment_link_id="plink_C", case_id="case_1", merchant_id="m1",
        customer_id="c1", amount_paise=100, reference_id="ref_3",
    ))

    cancelled = svc.cancel_open_links("case_1", "test")

    assert cancelled >= 1
    assert env["repo"].get_payment_link("plink_C").status.value == "CANCELLED"
