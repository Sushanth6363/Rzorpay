"""Case spine and payment-link resolution (ADR-0023).

The central test here is `test_a_payment_made_through_the_link_resolves_to_the_case`.
Before this layer existed, a customer who paid through a recovery link produced
`plink_...` while every scheduled follow-up was keyed on the original failure's `pay_...`.
The two never met, so "payment always wins" could not fire on the exact path the product
depends on, and a paying customer kept receiving reminders.
"""

import pytest

from app.cases.models import (
    Case,
    CaseEvent,
    CaseEventKind,
    CaseStatus,
    Customer,
    PaymentLink,
    PaymentLinkStatus,
)
from app.cases.repository import CaseRepository
from app.db.init import init_db
from app.payments.link_service import PaymentLinkService


class FakeRazorpay:
    """Stand-in for the Razorpay client. Records calls; never touches the network."""

    def __init__(self, key_id="rzp_test_REAL123", fail=False, simulated=False):
        self.key_id = key_id
        self.calls = []
        self._fail = fail
        self._simulated = simulated

    def create_payment_link(self, **kwargs):
        self.calls.append(kwargs)
        if self._fail:
            raise RuntimeError("provider timeout")
        return {
            "id": f"plink_{len(self.calls)}",
            "short_url": f"https://rzp.io/i/test{len(self.calls)}",
            "is_simulated": self._simulated,
        }


@pytest.fixture()
def env():
    conn = init_db(":memory:")
    repo = CaseRepository(conn)
    client = FakeRazorpay()
    svc = PaymentLinkService(conn, client=client, repository=repo)
    repo.upsert_customer(Customer(
        customer_id="c1", merchant_id="m1", name="Rahul",
        email="rahul@example.com", phone="+919876543210",
    ))
    case = repo.create_case(Case(
        case_id="case_1", merchant_id="m1", customer_id="c1", amount_paise=2_500_000,
        source_event_id="pay_ORIGINAL", opportunity_id="opp_1",
    ))
    return {"conn": conn, "repo": repo, "svc": svc, "client": client, "case": case}


# --- THE BLOCKER ---------------------------------------------------------------------


def test_a_payment_made_through_the_link_resolves_to_the_case(env):
    """`payment_link.paid` carries plink_..., the case was opened from pay_.... Without
    this mapping the payment is invisible and reminders keep going out."""
    link, _ = env["svc"].get_or_create_link(env["case"])

    assert env["svc"].resolve_case_id(link.payment_link_id) == "case_1"


def test_a_payment_on_the_original_attempt_also_resolves(env):
    """`payment.captured` on the failure that opened the case must close it too."""
    assert env["svc"].resolve_case_id("pay_ORIGINAL") == "case_1"


def test_our_own_reference_resolves(env):
    env["svc"].get_or_create_link(env["case"])
    reference = env["svc"].reference_for(env["case"])

    assert env["svc"].resolve_case_id("", reference) == "case_1"


def test_the_engine_opportunity_id_resolves(env):
    assert env["svc"].resolve_case_id("opp_1") == "case_1"


def test_an_unrelated_entity_resolves_to_nothing(env):
    """Closing the wrong case would stop chasing someone who never paid."""
    assert env["svc"].resolve_case_id("pay_SOMEONE_ELSE") is None


# --- Payment always wins --------------------------------------------------------------


def test_a_verified_payment_closes_the_case_and_forbids_contact(env):
    link, _ = env["svc"].get_or_create_link(env["case"])

    case_id = env["svc"].mark_paid_from_provider_event(
        link.payment_link_id, "payment_link.paid", 2_500_000
    )

    case = env["repo"].get_case(case_id)
    assert case.status == CaseStatus.PAID
    assert case.may_contact is False


def test_replaying_the_same_payment_event_is_idempotent(env):
    """Razorpay redelivers until it gets a 2xx; the second delivery must not double-log."""
    link, _ = env["svc"].get_or_create_link(env["case"])
    env["svc"].mark_paid_from_provider_event(link.payment_link_id, "payment_link.paid", 100)

    again = env["svc"].mark_paid_from_provider_event(
        link.payment_link_id, "payment_link.paid", 100
    )

    assert again == "case_1"
    received = [e for e in env["repo"].timeline("case_1")
                if e.kind == CaseEventKind.PAYMENT_RECEIVED]
    assert len(received) == 1


def test_a_paid_case_can_never_be_walked_back(env):
    """A later, weaker event must not un-pay a verified case."""
    link, _ = env["svc"].get_or_create_link(env["case"])
    env["svc"].mark_paid_from_provider_event(link.payment_link_id, "payment_link.paid", 100)

    ok = env["repo"].set_status("case_1", CaseStatus.IN_PROGRESS, reason="stale event")

    assert ok is False
    assert env["repo"].get_case("case_1").status == CaseStatus.PAID


def test_an_unmappable_payment_closes_nothing(env):
    """Better to close no case than the wrong one."""
    assert env["svc"].mark_paid_from_provider_event("plink_UNKNOWN", "payment_link.paid") is None


def test_a_payment_failure_leaves_the_case_open_for_re_evaluation(env):
    """Demo B depends on this: failure must not close the case."""
    case_id = env["svc"].record_payment_failure("pay_ORIGINAL", "payment.failed")

    assert case_id == "case_1"
    assert env["repo"].get_case("case_1").may_contact is True


# --- Idempotent link creation ---------------------------------------------------------


def test_a_second_request_reuses_the_live_link(env):
    """A retry or follow-up must not send a different link for the same debt."""
    first, _ = env["svc"].get_or_create_link(env["case"])
    second, note = env["svc"].get_or_create_link(env["case"])

    assert first.payment_link_id == second.payment_link_id
    assert len(env["client"].calls) == 1
    assert "reused" in note


def test_the_reference_id_contains_no_wall_clock_time(env):
    """A timestamped reference would defeat idempotency on every retry."""
    a = env["svc"].reference_for(env["case"])
    b = env["svc"].reference_for(env["case"])

    assert a == b
    assert "case_1" in a


def test_a_paid_link_is_not_reused(env):
    link, _ = env["svc"].get_or_create_link(env["case"])
    env["repo"].mark_link_paid(link.payment_link_id)

    assert env["repo"].find_reusable_link("case_1", 2_500_000) is None


# --- Honest failure -------------------------------------------------------------------


def test_placeholder_credentials_refuse_rather_than_fabricate(env):
    """A fabricated link fires no webhook, so the case could never close."""
    svc = PaymentLinkService(
        env["conn"], client=FakeRazorpay(key_id="rzp_test_mock_key"), repository=env["repo"]
    )

    link, note = svc.get_or_create_link(env["case"])

    assert link is None
    assert "NOT_CONFIGURED" in note


def test_a_simulated_link_is_refused(env):
    """It would silently dead-end the demo: no webhook, so the loop never closes."""
    svc = PaymentLinkService(
        env["conn"], client=FakeRazorpay(simulated=True), repository=env["repo"]
    )

    link, note = svc.get_or_create_link(env["case"])

    assert link is None
    assert "fires no webhook" in note


def test_a_provider_failure_is_reported_not_swallowed(env):
    svc = PaymentLinkService(
        env["conn"], client=FakeRazorpay(fail=True), repository=env["repo"]
    )

    link, note = svc.get_or_create_link(env["case"])

    assert link is None
    assert "FAILED" in note


def test_a_real_test_key_is_treated_as_configured(env):
    """rzp_test_... is a REAL key that hits the real API. Only rzp_test_mock is a stub."""
    assert env["svc"].is_configured is True
    assert env["svc"].is_test_mode is True


# --- Timeline -------------------------------------------------------------------------


def test_the_timeline_records_the_loop_in_order(env):
    link, _ = env["svc"].get_or_create_link(env["case"])
    env["svc"].mark_paid_from_provider_event(link.payment_link_id, "payment_link.paid", 100)

    kinds = [e.kind for e in env["repo"].timeline("case_1")]

    assert kinds == [
        CaseEventKind.CASE_CREATED,
        CaseEventKind.PAYMENT_LINK_CREATED,
        CaseEventKind.PAYMENT_RECEIVED,
        CaseEventKind.CASE_CLOSED,
    ]
