"""A failed payment link must report what the provider actually said.

WHY THIS EXISTS
    A live demo produced this, on both cases, with no further detail anywhere:

        [BLOCKED] EMAIL_LINK
        status BLOCKED   reason FAILED: provider returned no payment link id

    That sentence describes the SHAPE of the response and not one thing about the cause.
    It is not recoverable from either: it cannot tell a rejected request from a timeout
    from an auth failure, so the only way forward was to call the API by hand.

    The reason was never missing. The Razorpay client does not raise on an HTTP error or
    a connection failure - it RETURNS a dict carrying `error` and `details`. Both were
    sitting in `result` and were discarded on the line that reported the failure.

    Credentials were fine and the API was reachable and fast (~0.8s) when this was
    investigated, which is exactly why the message mattered: every obvious explanation
    was wrong and the record ruled none of them out.
"""

import pytest

from app.cases.csv_ingest import create_cases, parse_csv
from app.cases.repository import CaseRepository
from app.db.init import init_db
from app.payments.link_service import PaymentLinkService

CSV = """customer_id,name,email,amount,due_date
U_A,Rahul,rahul@example.com,25000,2026-08-24
"""


class _Client:
    """Stands in for RazorpayIntegrationClient, which returns error dicts rather than
    raising. That behaviour is the whole reason this test exists."""

    key_id = "rzp_test_REAL"

    def __init__(self, response):
        self._response = response

    def create_payment_link(self, **kwargs):
        return self._response

    def cancel_payment_link(self, payment_link_id):
        return {"id": payment_link_id, "status": "cancelled"}


@pytest.fixture()
def case_and_conn(tmp_path):
    conn = init_db(str(tmp_path / "links.db"))
    repo = CaseRepository(conn)
    case = create_cases(repo, parse_csv(CSV).valid, merchant_id="m1")[0]
    return conn, repo, case


def _attempt(case_and_conn, response):
    conn, repo, case = case_and_conn
    service = PaymentLinkService(conn, client=_Client(response), repository=repo)
    link, message = service.get_or_create_link(case)
    assert link is None, "this response should not have produced a link"
    return message


# --- the reason has to survive ---------------------------------------------------------


def test_an_http_error_reports_the_status_the_provider_returned(case_and_conn):
    """The exact shape the client returns on a non-2xx response."""
    message = _attempt(case_and_conn, {
        "error": "Razorpay API HTTP 400",
        "details": '{"error":{"description":"Reference id is already present"}}',
        "is_simulated": True,
    })

    assert "HTTP 400" in message


def test_an_http_error_reports_the_providers_own_description(case_and_conn):
    """The line that actually tells you what to change."""
    message = _attempt(case_and_conn, {
        "error": "Razorpay API HTTP 400",
        "details": '{"error":{"description":"Reference id is already present"}}',
        "is_simulated": True,
    })

    assert "Reference id is already present" in message


def test_a_timeout_is_reported_as_a_connection_problem(case_and_conn):
    """A timeout and a rejected request are different problems with different fixes, and
    the old message could not tell them apart."""
    message = _attempt(case_and_conn, {
        "error": "Connection error: HTTPSConnectionPool read timed out",
        "is_simulated": True,
    })

    assert "Connection error" in message
    assert "timed out" in message


def test_the_old_uninformative_sentence_is_gone(case_and_conn):
    """The defect, stated directly."""
    message = _attempt(case_and_conn, {
        "error": "Razorpay API HTTP 500",
        "details": "upstream unavailable",
        "is_simulated": True,
    })

    assert message != "FAILED: provider returned no payment link id"


def test_a_response_with_no_error_field_at_least_names_what_came_back(case_and_conn):
    """The genuinely unexplained case. Listing the keys is not a diagnosis, but it is the
    difference between a lead and a dead end."""
    message = _attempt(case_and_conn, {"entity": "payment_link", "status": "created"})

    assert "entity" in message and "status" in message


def test_the_message_stays_short_enough_to_render(case_and_conn):
    """`details` is raw provider text and can be long. It is shown in a table cell."""
    message = _attempt(case_and_conn, {
        "error": "Razorpay API HTTP 400",
        "details": "x" * 5000,
        "is_simulated": True,
    })

    assert len(message) <= 400


# --- and the success path is untouched ---------------------------------------------------


def test_a_good_response_still_produces_a_link(case_and_conn):
    conn, repo, case = case_and_conn
    service = PaymentLinkService(conn, client=_Client({
        "id": "plink_OK", "short_url": "https://rzp.io/rzp/OK", "is_simulated": False,
    }), repository=repo)

    link, _ = service.get_or_create_link(case)

    assert link is not None and link.payment_link_id == "plink_OK"


def test_the_write_timeout_is_no_longer_five_seconds():
    """A create can be slower than a read, and a timeout produced exactly the symptom
    above with nothing pointing at the network."""
    from pathlib import Path

    source = (Path(__file__).resolve().parents[2]
              / "app" / "integrations" / "razorpay_client.py").read_text(encoding="utf-8")
    create = source[source.index("def create_payment_link"):]

    assert "timeout=5," not in create


# --- the simulated-link fallback ---------------------------------------------------------


def test_a_simulated_link_is_refused_by_default(case_and_conn):
    """The guard that matters: a simulated link fires no webhook, so the case can never
    close, and a demo dead-ending silently at its most important moment is worse than one
    that fails loudly."""
    message = _attempt(case_and_conn, {
        "id": "plink_mock", "short_url": "https://rzp.io/i/mock", "is_simulated": True,
    })

    assert "simulated link" in message


def test_the_refusal_names_the_flag_that_overrides_it(case_and_conn):
    """A workaround nobody can find is not a workaround."""
    message = _attempt(case_and_conn, {
        "id": "plink_mock", "short_url": "https://rzp.io/i/mock", "is_simulated": True,
    })

    assert "RECOVERY_ALLOW_SIMULATED_LINKS" in message


def test_it_is_accepted_when_explicitly_opted_in(case_and_conn, monkeypatch):
    """When the provider is unreachable, every other half of the engine still works and
    showing none of it is the worse outcome. The operator takes that trade knowingly."""
    from app.realtime import config as rt_config
    monkeypatch.setattr(rt_config, "ALLOW_SIMULATED_LINKS", True, raising=False)

    conn, repo, case = case_and_conn
    service = PaymentLinkService(conn, client=_Client({
        "id": "plink_mock", "short_url": "https://rzp.io/i/mock", "is_simulated": True,
    }), repository=repo)

    link, _ = service.get_or_create_link(case)

    assert link is not None and link.payment_link_id == "plink_mock"


def test_opting_in_does_not_also_accept_a_response_with_no_link_id(case_and_conn, monkeypatch):
    """The flag relaxes ONE check. A genuine provider error is still an error."""
    from app.realtime import config as rt_config
    monkeypatch.setattr(rt_config, "ALLOW_SIMULATED_LINKS", True, raising=False)

    message = _attempt(case_and_conn, {
        "error": "Razorpay API HTTP 429",
        "details": '{"error":{"description":"Too many requests"}}',
        "is_simulated": True,
    })

    assert "429" in message


def test_the_flag_is_off_unless_it_is_set():
    """Default-safe. A public deployment must not silently hand out unpayable links."""
    import importlib
    import os

    from app.realtime import config as rt_config
    os.environ.pop("RECOVERY_ALLOW_SIMULATED_LINKS", None)
    importlib.reload(rt_config)

    assert rt_config.ALLOW_SIMULATED_LINKS is False
