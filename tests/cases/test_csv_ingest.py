"""Merchant CSV ingestion and CSV-to-email fidelity (ADR-0025).

Two things are being pinned. First, that nothing is silently dropped: a rejected row is
revenue the merchant believes is being chased, so it must come back with a reason. Second,
that the email cannot drift from the file - every figure in the message is read back from
the stored Case and Customer rather than re-entered anywhere downstream.
"""

import pytest

from app.cases.csv_ingest import (
    create_cases,
    normalise_phone,
    parse_amount,
    parse_csv,
    parse_due_date,
)
from app.cases.repository import CaseRepository
from app.db.init import init_db
from app.dispatch.copy import build_message, first_name
from app.domain.enums import ActionType

GOOD = """customer_id,name,email,phone,amount,due_date
CUST001,Rahul Sharma,rahul@example.com,9876543210,25000,2026-08-24
CUST002,Priya Nair,priya@example.com,+919812345678,"1,299.50",15/08/2026
"""


@pytest.fixture()
def repo():
    return CaseRepository(init_db(":memory:"))


# --- Nothing is silently dropped --------------------------------------------------------


@pytest.mark.parametrize("row, fragment", [
    ("CUST,Bad Email,not-an-email,9876543210,5000,2026-08-01", "malformed email"),
    ("CUST,No Contact,,,5000,2026-08-01", "no way to contact"),
    ("CUST,Bad Amount,x@y.com,9876543210,abc,2026-08-01", "invalid amount"),
    ("CUST,Zero,x@y.com,9876543210,0,2026-08-01", "invalid amount"),
    ("CUST,Bad Date,z@y.com,9876543210,900,31-31-2026", "unreadable due date"),
    ("CUST,Bad Phone,p@y.com,12345,700,2026-08-01", "unusable phone"),
])
def test_every_bad_row_is_rejected_with_a_reason(row, fragment):
    report = parse_csv("customer_id,name,email,phone,amount,due_date\n" + row + "\n")

    assert len(report.rejected) == 1
    assert fragment in report.rejected[0].reason
    assert report.rejected[0].line == 2


def test_a_duplicate_row_is_rejected_and_names_the_original_line():
    """Processing both would contact the same customer twice for one debt."""
    report = parse_csv(GOOD + "CUST001,Rahul Sharma,rahul@example.com,9876543210,25000,2026-08-24\n")

    assert len(report.valid) == 2
    assert "duplicate of line 2" in report.rejected[0].reason


def test_a_rejected_row_keeps_its_original_data_for_display():
    """The merchant has to be able to see and fix the row, not just be told a count."""
    report = parse_csv("customer_id,name,email,phone,amount,due_date\n"
                       "C1,Bad,not-an-email,9876543210,5000,2026-08-01\n")

    assert report.rejected[0].raw["name"] == "Bad"


def test_missing_required_columns_stops_the_whole_file():
    """Guessing which column held the amount would be worse than refusing."""
    report = parse_csv("name,email\nRahul,rahul@example.com\n")

    assert report.ok is False
    assert "amount" in report.missing_columns


def test_a_file_with_no_contact_column_at_all_is_refused():
    report = parse_csv("customer_id,name,amount\nC1,Rahul,5000\n")

    assert "email or phone" in report.missing_columns


# --- Real-world messiness parses --------------------------------------------------------


@pytest.mark.parametrize("raw, paise", [
    ("25000", 2_500_000),
    ("1,299.50", 129_950),
    ("Rs 25000", 2_500_000),
    ("₹25000", 2_500_000),
    (" 900 ", 90_000),
])
def test_amounts_survive_the_formats_a_real_export_uses(raw, paise):
    assert parse_amount(raw) == paise


@pytest.mark.parametrize("raw", ["abc", "", "-5", "0"])
def test_unusable_amounts_are_rejected(raw):
    assert parse_amount(raw) is None


@pytest.mark.parametrize("raw, iso", [
    ("2026-08-24", "2026-08-24"),
    ("24/08/2026", "2026-08-24"),
    ("24-08-2026", "2026-08-24"),
])
def test_dates_parse_in_the_formats_merchants_actually_use(raw, iso):
    assert parse_due_date(raw)[0] == iso


def test_a_blank_due_date_is_allowed_but_a_malformed_one_is_not():
    assert parse_due_date("") == (None, False)
    assert parse_due_date("31-31-2026") == (None, True)


@pytest.mark.parametrize("raw, e164", [
    ("9876543210", "+919876543210"),
    ("+919876543210", "+919876543210"),
    ("919876543210", "+919876543210"),
    ("09876543210", "+919876543210"),
    ("98765 43210", "+919876543210"),
])
def test_phones_normalise_to_e164(raw, e164):
    assert normalise_phone(raw) == e164


@pytest.mark.parametrize("raw", ["12345", "abcdefghij", "0"])
def test_an_unusable_phone_is_rejected_rather_than_guessed(raw):
    """A wrong number messages a stranger and burns the real customer's contact slot."""
    assert normalise_phone(raw) is None


def test_alias_column_names_are_accepted():
    """Real exports say 'customer_name' or 'mobile', not our canonical names."""
    report = parse_csv("customer_name,mobile,amount_due\nRahul,9876543210,5000\n")

    assert len(report.valid) == 1
    assert report.valid[0].name == "Rahul"


# --- The CSV is the single source -------------------------------------------------------


def test_cases_are_created_with_the_csv_values(repo):
    report = parse_csv(GOOD)

    cases = create_cases(repo, report.valid, merchant_id="m1")

    assert len(cases) == 2
    assert cases[0].amount_paise == 2_500_000
    assert cases[0].due_date == "2026-08-24"
    assert cases[1].amount_paise == 129_950


def test_the_customer_record_carries_the_csv_contact_details(repo):
    create_cases(repo, parse_csv(GOOD).valid, merchant_id="m1")

    customer = repo.get_customer("m1", "CUST001")

    assert customer.name == "Rahul Sharma"
    assert customer.email == "rahul@example.com"
    assert customer.phone == "+919876543210"


def test_the_email_is_built_from_the_stored_case_not_re_entered(repo):
    """The email cannot drift from the file because nothing downstream retypes the numbers."""
    case = create_cases(repo, parse_csv(GOOD).valid, merchant_id="m1")[0]
    customer = repo.get_customer("m1", case.customer_id)

    message = build_message(
        ActionType.EMAIL_LINK, case.amount_paise, customer.name,
        payment_link="https://rzp.io/x", due_date=case.due_date,
    )

    assert "Rahul" in message.body
    assert "25,000.00" in message.body
    assert "24 August 2026" in message.body


def test_the_greeting_uses_the_first_name():
    """"Hi Rahul Sharma," reads like a form letter."""
    assert first_name("Rahul Sharma") == "Rahul"
    assert "Hi Rahul," in build_message(ActionType.EMAIL_LINK, 100, "Rahul Sharma").body


def test_overdue_context_is_stated_as_fact_not_pressure():
    message = build_message(ActionType.EMAIL_LINK, 100, "Rahul", due_date="2026-08-24")

    assert "days ago" in message.body
    for pressure in ("immediately", "act now", "final", "or else"):
        assert pressure not in message.body.lower()


def test_a_missing_due_date_simply_omits_the_sentence():
    message = build_message(ActionType.EMAIL_LINK, 100, "Rahul", due_date="")

    assert "due on" not in message.body


# --- what the debt is FOR (distinct from why it is unpaid) ----------------------------------


def test_the_description_column_says_what_is_owed_for():
    """A merchant knows what an invoice covers - it is on the invoice. That is a different
    question from WHY it is unpaid, which they cannot know and Stage 1 diagnoses (ADR-0025).
    Someone who owes several invoices cannot act on "an outstanding payment of Rs 25,000";
    they need to know which one."""
    report = parse_csv(
        "customer_id,name,email,amount,due_date,description\n"
        "C1,Aarti,a@example.com,25000,2026-08-24,Invoice INV-2043 - October consulting\n"
    )

    assert report.valid[0].description == "Invoice INV-2043 - October consulting"


def test_the_description_is_optional():
    """A merchant without invoice particulars must still be able to upload."""
    report = parse_csv(
        "customer_id,name,email,amount,due_date\nC1,Aarti,a@example.com,25000,2026-08-24\n"
    )

    assert report.valid[0].description == ""


def test_common_column_names_for_it_are_accepted():
    for header in ("particulars", "invoice", "for", "item", "details"):
        report = parse_csv(
            f"customer_id,name,email,amount,{header}\nC1,A,a@example.com,100,INV-1\n"
        )
        assert report.valid[0].description == "INV-1", header


def test_the_description_reaches_the_case():
    """A column that changes nothing downstream is decoration."""
    import sqlite3

    from app.cases.repository import CaseRepository
    from app.db.init import init_db

    repo = CaseRepository(init_db(":memory:"))
    rows = parse_csv(
        "customer_id,name,email,amount,due_date,description\n"
        "C1,Aarti,a@example.com,25000,2026-08-24,Invoice INV-2043\n"
    ).valid
    case = create_cases(repo, rows, merchant_id="m1")[0]

    assert repo.get_case(case.case_id).description == "Invoice INV-2043"
