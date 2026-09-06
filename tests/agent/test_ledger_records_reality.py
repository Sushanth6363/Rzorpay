"""The contact ledger records what the dispatcher did, not what the simulator imagined.

WHY THIS EXISTS
    A real live run produced this pair of rows, in the same database, about the same
    contact:

        contact_ledger  status=EXECUTED  resolved_at 17:12:44.292
                        metadata {"outcome": "PAYMENT_SUCCESS"}
        dispatch_log    status=SENT      dispatched_at 17:12:50.429

    The ledger declared the contact executed AND resolved with a payment outcome nine
    milliseconds after creation - six seconds before the email left, and nine minutes
    before the customer actually paid. That PAYMENT_SUCCESS came from the sandbox
    simulator, not from any real event.

    Dry runs were worse: rows reading EXECUTED for customers nobody had contacted.

    This is not cosmetic. `get_customer_ledger_history` drives the escalation ceiling and
    the contact budget, and the unrecovered handoff report lists EXECUTED rows as "already
    tried". A fabricated outcome escalates toward a phone call on the strength of an email
    that never left, and tells a collections agent not to re-send it.

WHAT MUST NOT CHANGE
    In the SANDBOX the simulator's outcome IS the observed outcome, and recording it is
    correct - that is what the experiment measures. Only the live path defers. The test at
    the bottom pins that separation, because "fixing" it everywhere would invalidate every
    number in results/RESULTS.md.
"""

from app.agent.loop import RecoveryAgent
from app.cases.csv_ingest import create_cases, parse_csv
from app.cases.repository import CaseRepository
from app.db.init import init_db
from app.dispatch.dispatcher import ChannelDispatcher
from app.domain.enums import LedgerStatus
from app.payments.link_service import PaymentLinkService

CSV = """customer_id,name,email,amount,due_date
U_A,Rahul,rahul@example.com,25000,2026-08-24
"""


class FakeRZP:
    key_id = "rzp_test_REAL"

    def create_payment_link(self, **kwargs):
        return {"id": "plink_1", "short_url": "https://rzp.io/rzp/D1", "is_simulated": False}

    def cancel_payment_link(self, payment_link_id):
        return {"id": payment_link_id, "status": "cancelled"}


def _build(dry_run):
    conn = init_db(":memory:")
    repo = CaseRepository(conn)
    case = create_cases(repo, parse_csv(CSV).valid, merchant_id="m1")[0]
    agent = RecoveryAgent(
        conn, repository=repo,
        payments=PaymentLinkService(conn, client=FakeRZP(), repository=repo),
        dispatcher=ChannelDispatcher(conn, repository=repo, dry_run=dry_run),
    )
    return conn, repo, case, agent


def _ledger_rows(conn):
    conn.row_factory = None
    return conn.execute(
        "SELECT status, metadata_json FROM contact_ledger ORDER BY rowid"
    ).fetchall()


def _sent_email(monkeypatch, status, detail="ok"):
    from app.dispatch import channels
    monkeypatch.setattr(
        channels, "send_email_smtp",
        lambda *a, **k: channels.DispatchResult("EMAIL_SMTP", status, detail,
                                                provider_id="MSG1"),
    )


# --- a dry run must not claim a contact ---------------------------------------------------


def test_a_dry_run_does_not_record_an_executed_contact():
    """The row that used to read EXECUTED for a message nobody was sent."""
    conn, _, case, agent = _build(dry_run=True)

    agent.run_cycle(case.case_id, random_seed=7)

    rows = _ledger_rows(conn)
    assert rows, "the cycle should still create a ledger row"
    assert all(status != LedgerStatus.EXECUTED.value for status, _ in rows), \
        "a dry run was recorded as a confirmed contact"


def test_a_dry_run_returns_the_contact_slot():
    """Nothing reached the customer, so the budget must not be spent on it."""
    conn, _, case, agent = _build(dry_run=True)

    agent.run_cycle(case.case_id, random_seed=7)

    assert any(status == LedgerStatus.RELEASED.value for status, _ in _ledger_rows(conn))


def test_a_dry_run_records_no_payment_outcome():
    """A payment outcome on a message that was never sent is a fabricated observation."""
    conn, _, case, agent = _build(dry_run=True)

    agent.run_cycle(case.case_id, random_seed=7)

    for _, metadata in _ledger_rows(conn):
        assert "PAYMENT_SUCCESS" not in (metadata or "")


# --- a real send must be recorded as one ---------------------------------------------------


def test_a_real_send_is_recorded_as_executed(monkeypatch):
    conn, _, case, agent = _build(dry_run=False)
    _sent_email(monkeypatch, "SENT", "delivered")

    agent.run_cycle(case.case_id, random_seed=7)

    assert any(status == LedgerStatus.EXECUTED.value for status, _ in _ledger_rows(conn))


def test_the_ledger_names_the_dispatcher_as_its_source(monkeypatch):
    """So a reader can tell a real observation from a simulated one without archaeology."""
    conn, _, case, agent = _build(dry_run=False)
    _sent_email(monkeypatch, "SENT", "delivered")

    agent.run_cycle(case.case_id, random_seed=7)

    blob = " ".join((m or "") for _, m in _ledger_rows(conn))
    assert "ChannelDispatcher" in blob
    assert "EMAIL_SMTP" in blob


def test_a_provider_failure_does_not_advance_the_ladder(monkeypatch):
    """A message that could not be sent has not earned the right to escalate."""
    conn, _, case, agent = _build(dry_run=False)
    _sent_email(monkeypatch, "FAILED", "smtp refused")

    agent.run_cycle(case.case_id, random_seed=7)

    assert all(status != LedgerStatus.EXECUTED.value for status, _ in _ledger_rows(conn))


# --- the ledger and the dispatch log must agree ---------------------------------------------


def test_the_two_records_no_longer_contradict_each_other():
    """The defect stated as an invariant: a contact confirmed in the ledger must correspond
    to a message the dispatch log says was actually sent."""
    conn, _, case, agent = _build(dry_run=True)

    agent.run_cycle(case.case_id, random_seed=7)

    executed = [s for s, _ in _ledger_rows(conn) if s == LedgerStatus.EXECUTED.value]
    sent = conn.execute("SELECT COUNT(*) FROM dispatch_log WHERE status='SENT'").fetchone()[0]

    assert len(executed) == sent == 0


# --- the sandbox is untouched ----------------------------------------------------------------


def test_the_sandbox_still_resolves_its_own_ledger_rows():
    """The experiment path must keep working exactly as before: there the simulator's
    result IS the observation, and every figure in results/RESULTS.md depends on it."""
    from app.orchestration.recovery_orchestrator import RecoveryOrchestrator

    conn = init_db(":memory:")
    result = RecoveryOrchestrator(db_conn=conn).process_and_execute(
        raw_event={"event_id": "pay_X", "merchant_id": "m1", "customer_id": "c1",
                   "event_type": "FAILED_PAYMENT", "amount_paise": 250000,
                   "failure_reason": "INSUFFICIENT_FUNDS",
                   "occurred_at": "2026-01-01T00:00:00Z"},
        merchant_id="m1", random_seed=7,
    )

    if result.ledger_entry is not None:
        assert result.ledger_entry.status in (
            LedgerStatus.EXECUTED, LedgerStatus.FAILED_CLOSED,
            LedgerStatus.EXECUTION_UNKNOWN, LedgerStatus.RECONCILED_DELIVERED,
            LedgerStatus.RECONCILED_NOT_SENT, LedgerStatus.RECONCILED_UNRESOLVED,
        ), "the sandbox path stopped resolving its ledger rows"
