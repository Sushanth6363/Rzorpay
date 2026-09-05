"""Agent loop — observe, delegate, act, record (ADR-0026).

The loop is deliberately thin. These tests are mostly about what it must NOT do: decide
anything, send past a settled case, or send a payment request with no way to pay.
"""

import pytest

from app.agent.loop import RecoveryAgent
from app.cases.csv_ingest import create_cases, parse_csv
from app.cases.models import CaseEventKind, CaseStatus
from app.cases.repository import CaseRepository
from app.db.init import init_db
from app.dispatch.dispatcher import ChannelDispatcher
from app.payments.link_service import PaymentLinkService

CSV = """customer_id,name,email,phone,amount,due_date
CUST001,Rahul Sharma,rahul@example.com,9876543210,25000,2026-08-24
"""


class FakeRZP:
    key_id = "rzp_test_REAL"

    def __init__(self, fail=False):
        self._fail = fail
        self.created = 0

    def create_payment_link(self, **kwargs):
        if self._fail:
            raise RuntimeError("provider down")
        self.created += 1
        return {
            "id": f"plink_{self.created}",
            "short_url": f"https://rzp.io/rzp/D{self.created}",
            "is_simulated": False,
        }

    def cancel_payment_link(self, payment_link_id):
        return {"id": payment_link_id, "status": "cancelled"}


def _agent(conn, repo, client=None):
    return RecoveryAgent(
        conn, repository=repo,
        payments=PaymentLinkService(conn, client=client or FakeRZP(), repository=repo),
        dispatcher=ChannelDispatcher(conn, repository=repo, dry_run=True),
    )


@pytest.fixture()
def env():
    conn = init_db(":memory:")
    repo = CaseRepository(conn)
    case = create_cases(repo, parse_csv(CSV).valid, merchant_id="m1")[0]
    return {"conn": conn, "repo": repo, "case": case, "agent": _agent(conn, repo)}


# --- The engine decides, not the loop ----------------------------------------------------


def test_a_receivable_gets_a_contact_channel_not_a_retry(env):
    """A merchant-uploaded debt had no charge attempt, so there is nothing to retry.

    The candidate generator never offers RECOMMEND_RETRY for this stream, so typing the
    case correctly is what makes the engine reach the right answer on its own. Forcing the
    action in the loop would have hidden the modelling error instead of fixing it.
    """
    result = env["agent"].run_cycle(env["case"].case_id)

    assert result.action == "EMAIL_LINK"


def test_the_reasoning_is_read_off_the_decision_not_composed(env):
    """The explanation must be the engine's own arithmetic, not a story told afterwards."""
    result = env["agent"].run_cycle(env["case"].case_id)

    assert "uplift" in result.reasoning
    assert "EV" in result.reasoning


def test_the_opportunity_is_attached_back_to_the_case(env):
    """Without this the engine's decision cannot be traced from the case."""
    env["agent"].run_cycle(env["case"].case_id)

    assert env["repo"].get_case(env["case"].case_id).opportunity_id


# --- Payment always wins, even before the engine runs ------------------------------------


def test_a_paid_case_is_skipped_before_the_engine_even_runs(env):
    env["repo"].set_status(env["case"].case_id, CaseStatus.PAID, reason="paid")

    result = env["agent"].run_cycle(env["case"].case_id)

    assert result.action == ""
    assert "PAID" in result.skipped_reason


def test_a_closed_case_is_skipped(env):
    env["repo"].set_status(env["case"].case_id, CaseStatus.CLOSED, reason="wrong person")

    assert "CLOSED" in env["agent"].run_cycle(env["case"].case_id).skipped_reason


def test_an_unknown_case_is_reported_not_raised(env):
    assert env["agent"].run_cycle("case_NOPE").skipped_reason == "unknown case"


# --- A payment request needs somewhere to pay --------------------------------------------


def test_no_payment_link_means_no_message(env):
    """Sending a payment request with no way to pay wastes the customer's attention and a
    contact slot, and cannot possibly close the case."""
    agent = _agent(env["conn"], env["repo"], client=FakeRZP(fail=True))

    result = agent.run_cycle(env["case"].case_id)

    assert result.dispatch["status"] == "BLOCKED"
    assert "no payment link" in result.skipped_reason
    kinds = [e.kind for e in env["repo"].timeline(env["case"].case_id)]
    assert CaseEventKind.MESSAGE_FAILED in kinds


def test_the_link_is_reused_across_cycles_not_duplicated(env):
    """A second cycle must not send the customer a different link for the same debt."""
    client = FakeRZP()
    agent = _agent(env["conn"], env["repo"], client=client)

    first = agent.run_cycle(env["case"].case_id)
    second = agent.run_cycle(env["case"].case_id)

    assert first.payment_url == second.payment_url
    assert client.created == 1


# --- Recording ---------------------------------------------------------------------------


def test_the_decision_and_the_link_both_reach_the_timeline(env):
    env["agent"].run_cycle(env["case"].case_id)

    kinds = [e.kind for e in env["repo"].timeline(env["case"].case_id)]

    assert CaseEventKind.CASE_CREATED in kinds
    assert CaseEventKind.AGENT_DECIDED in kinds
    assert CaseEventKind.PAYMENT_LINK_CREATED in kinds


def test_dry_run_records_the_decision_without_sending(env):
    result = env["agent"].run_cycle(env["case"].case_id)

    assert result.dispatch["status"] == "SKIPPED"
    assert "DRY RUN" in result.dispatch["reason"]
    assert result.contacted is False


def test_a_batch_returns_one_result_per_case(env):
    cases = create_cases(env["repo"], parse_csv(
        "customer_id,name,email,amount\nC2,B,b@x.com,900\nC3,C,c@x.com,700\n"
    ).valid, merchant_id="m1")

    results = env["agent"].run_batch([c.case_id for c in cases])

    assert len(results) == 2
