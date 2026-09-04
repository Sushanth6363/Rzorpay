"""Unrecovered handoff report (ADR-0022).

The most important honest output of an automated recovery engine is the list of people it
could NOT recover. These tests pin the two properties that make it trustworthy: it never
lists someone who paid, and it reports the effort already spent truthfully.
"""

import importlib

import pytest

from app.domain.enums import ActionType, DiagnosisCode


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOVERY_DB_PATH", str(tmp_path / "rep.db"))
    from app.realtime import config as cfg
    importlib.reload(cfg)
    from app.realtime import ingest as ing
    importlib.reload(ing)
    from app.realtime import followup as f
    importlib.reload(f)
    f.ensure_schema()
    from app.reporting import unrecovered as u
    importlib.reload(u)
    return {"ingest": ing, "followup": f, "report": u, "conn": ing.get_conn()}


def _exhaust(env, opp, origin, customer, amount, stream, diagnosis, action, reason,
             contacts=("EMAIL_LINK", "SMS_LINK")):
    """Create a terminal, unpaid opportunity with real ledger history."""
    env["followup"].schedule(
        opportunity_id=opp, merchant_id="m1", customer_id=customer,
        origin_event_id=origin,
        event={"event_id": origin, "amount_paise": amount, "event_type": stream,
               "email": f"{customer}@x.com", "phone": "+911234567890"},
        diagnosis_code=diagnosis, last_action=action, attempt=0,
    )
    conn = env["conn"]
    conn.execute(
        "UPDATE followup_queue SET status='STOPPED', stop_reason=? WHERE opportunity_id=?;",
        (reason, opp),
    )
    conn.execute(
        "INSERT OR IGNORE INTO contact_budgets VALUES (?,?,?,?,?,?);",
        ("m1", customer, 9, 0, 0, "2026-01-01T00:00:00+00:00"),
    )
    for i, act in enumerate(contacts):
        stamp = f"2026-01-0{i + 1}T00:00:00+00:00"
        conn.execute(
            """INSERT OR IGNORE INTO contact_ledger
               (ledger_id, merchant_id, customer_id, opportunity_id, action_type,
                intervention_idempotency_key, status, created_at, updated_at, resolved_at)
               VALUES (?,?,?,?,?,?,?,?,?,?);""",
            (f"l_{opp}_{i}", "m1", customer, opp, act, f"k_{opp}_{i}",
             "EXECUTED", stamp, stamp, stamp),
        )
    conn.commit()


# --- INV-1: never list someone who paid ---------------------------------------------------


def test_a_customer_who_paid_is_never_listed(env):
    """The whole point is that this list is genuine remaining exposure."""
    _exhaust(env, "opp_paid", "pay_paid", "cust_paid", 500000, "FAILED_PAYMENT",
             DiagnosisCode.INSUFFICIENT_FUNDS.value, ActionType.EMAIL_LINK,
             "MAX_FOLLOWUPS reached")
    env["ingest"].record_resolution("pay_paid", "payment.captured", 500000)

    rows = env["report"].collect(env["conn"], "m1")

    assert all(r.customer_id != "cust_paid" for r in rows)


def test_an_opportunity_stopped_because_it_resolved_is_not_a_failure(env):
    """`cancel_for_entity` stops follow-ups on payment. That is success, not exhaustion."""
    _exhaust(env, "opp_r", "pay_r", "cust_r", 100000, "FAILED_PAYMENT",
             DiagnosisCode.CARD_DECLINED.value, ActionType.SMS_LINK,
             "resolved by payment.captured")

    rows = env["report"].collect(env["conn"], "m1")

    assert rows == []


def test_an_exhausted_unpaid_opportunity_is_listed(env):
    _exhaust(env, "opp_1", "pay_1", "cust_1", 450000, "FAILED_PAYMENT",
             DiagnosisCode.CARD_DECLINED.value, ActionType.WHATSAPP_LINK,
             "MAX_FOLLOWUPS reached")

    rows = env["report"].collect(env["conn"], "m1")

    assert len(rows) == 1
    assert rows[0].customer_id == "cust_1"
    assert rows[0].amount_paise == 450000


# --- INV-2: report effort honestly --------------------------------------------------------


def test_contact_history_comes_from_the_ledger_not_an_estimate(env):
    """A collections agent re-sending the email the engine already sent is worse than
    useless, so what was tried must be exact."""
    _exhaust(env, "opp_2", "pay_2", "cust_2", 90000, "ABANDONED_CHECKOUT",
             DiagnosisCode.CUSTOMER_ABANDONMENT.value, ActionType.WHATSAPP_LINK,
             "MAX_FOLLOWUPS reached",
             contacts=("EMAIL_LINK", "SMS_LINK", "WHATSAPP_LINK"))

    row = env["report"].collect(env["conn"], "m1")[0]

    assert row.contacts_made == 3
    assert "EMAIL_LINK" in row.channels_used
    assert "WHATSAPP_LINK" in row.channels_used


def test_an_unconfirmed_contact_is_not_counted_as_effort(env):
    """Only confirmed delivery counts, exactly as the escalation ladder requires."""
    _exhaust(env, "opp_3", "pay_3", "cust_3", 50000, "FAILED_PAYMENT",
             DiagnosisCode.UNKNOWN.value, ActionType.EMAIL_LINK,
             "MAX_FOLLOWUPS reached", contacts=())
    conn = env["conn"]
    conn.execute(
        """INSERT INTO contact_ledger
           (ledger_id, merchant_id, customer_id, opportunity_id, action_type,
            intervention_idempotency_key, status, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?);""",
        ("l_unknown", "m1", "cust_3", "opp_3", "EMAIL_LINK", "k_unknown",
         "EXECUTION_UNKNOWN", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
    )
    conn.commit()

    row = env["report"].collect(env["conn"], "m1")[0]

    assert row.contacts_made == 0
    assert row.channels_used == "none confirmed"


# --- Ordering, suggestions, workbook ------------------------------------------------------


def test_biggest_exposure_is_listed_first(env):
    _exhaust(env, "opp_small", "pay_s", "cust_small", 10000, "FAILED_PAYMENT",
             DiagnosisCode.UNKNOWN.value, ActionType.EMAIL_LINK, "MAX_FOLLOWUPS reached")
    _exhaust(env, "opp_big", "pay_b", "cust_big", 24000000, "OVERDUE_B2B_INVOICE",
             DiagnosisCode.INVOICE_OVERDUE.value, ActionType.AGENT_DIAL, "MAX_FOLLOWUPS reached")

    rows = env["report"].collect(env["conn"], "m1")

    assert rows[0].customer_id == "cust_big"


def test_the_suggested_step_is_derived_from_what_happened(env):
    """No invented recommendation: a declined card gets a payment-method suggestion."""
    _exhaust(env, "opp_d", "pay_d", "cust_d", 300000, "FAILED_PAYMENT",
             DiagnosisCode.CARD_DECLINED.value, ActionType.SMS_LINK, "MAX_FOLLOWUPS reached")

    row = env["report"].collect(env["conn"], "m1")[0]

    assert "payment method" in row.suggested_next_step.lower()


def test_a_never_contacted_customer_is_flagged_as_such(env):
    """Zero confirmed contacts means the contact details are the likely problem."""
    _exhaust(env, "opp_n", "pay_n", "cust_n", 70000, "FAILED_PAYMENT",
             DiagnosisCode.UNKNOWN.value, ActionType.EMAIL_LINK,
             "MAX_FOLLOWUPS reached", contacts=())

    row = env["report"].collect(env["conn"], "m1")[0]

    assert "never contacted" in row.suggested_next_step.lower()


def test_the_summary_totals_only_unrecovered_money(env):
    _exhaust(env, "opp_a", "pay_a", "cust_a", 100000, "FAILED_PAYMENT",
             DiagnosisCode.UNKNOWN.value, ActionType.EMAIL_LINK, "MAX_FOLLOWUPS reached")
    _exhaust(env, "opp_b", "pay_b2", "cust_b", 250000, "FAILED_PAYMENT",
             DiagnosisCode.UNKNOWN.value, ActionType.EMAIL_LINK, "MAX_FOLLOWUPS reached")

    summary = env["report"].summarise(env["report"].collect(env["conn"], "m1"))

    assert summary["customers"] == 2
    assert summary["total_unrecovered_paise"] == 350000


def test_a_real_xlsx_workbook_is_produced(env):
    _exhaust(env, "opp_x", "pay_x", "cust_x", 120000, "FAILED_PAYMENT",
             DiagnosisCode.CARD_DECLINED.value, ActionType.SMS_LINK, "MAX_FOLLOWUPS reached")

    data = env["report"].build_workbook(env["report"].collect(env["conn"], "m1"), "m1")

    # xlsx is a zip archive; PK is its magic number.
    assert data[:2] == b"PK"
    assert len(data) > 1000


def test_an_empty_report_still_produces_a_valid_workbook(env):
    """A merchant with nothing outstanding must not get a crash."""
    data = env["report"].build_workbook([], "m1")

    assert data[:2] == b"PK"
