"""A verified payment must find its case, whichever event carried it (ADR-0023).

WHY THIS TEST EXISTS
    A real Rs 25,000 test payment was made through a real recovery link. Razorpay
    delivered `payment.captured` and `order.paid`, both verified, both recorded - and the
    case stayed IN_PROGRESS with a follow-up still scheduled against it. The customer had
    paid and the engine was still going to chase them.

    Nothing was broken in the resolution logic. The repository could already map a
    reference back to a case; the listener never handed it one, because it read
    `reference_id` from the top level of the entity and a PAYMENT entity keeps ours inside
    `notes`. The identifier was in the payload the entire time.

    The fixture is the ACTUAL payload Razorpay sent, with contact details scrubbed. A
    hand-written mock would have encoded my assumption about where the reference lives,
    which is exactly the assumption that was wrong.
"""

import json
from pathlib import Path

import pytest

from app.cases.csv_ingest import create_cases, parse_csv
from app.cases.models import CaseStatus, PaymentLink
from app.cases.repository import CaseRepository
from app.payments.link_service import PaymentLinkService
from app.realtime.event_mapper import extract_case_hints

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "razorpay_payment_captured.json"

CSV = """customer_id,name,email,amount,due_date
CUST001,Sushanth,a@example.com,25000,2026-08-24
"""

# The exact strings from the real event.
REAL_PLINK = "plink_TYQwevtIn7Imdx"
REAL_REFERENCE = "case_case_merch_demo_CUST001_20260905171244_2_2500000"
REAL_PAYMENT = "pay_TYR5bmfIqEsc4x"


@pytest.fixture()
def payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOVERY_DB_PATH", str(tmp_path / "pay.db"))
    import importlib
    from app.realtime import config as cfg
    importlib.reload(cfg)
    from app.realtime import ingest as ing
    importlib.reload(ing)
    r = CaseRepository(ing.get_conn())
    case = create_cases(r, parse_csv(CSV).valid, merchant_id="merch_demo")[0]
    r.save_payment_link(PaymentLink(
        payment_link_id=REAL_PLINK, case_id=case.case_id, merchant_id="merch_demo",
        customer_id=case.customer_id, amount_paise=case.amount_paise,
        short_url="https://rzp.io/rzp/2Wv0feSG", reference_id=REAL_REFERENCE,
    ))
    return r, case


# --- what the payload actually contains ----------------------------------------------------


def test_the_reference_is_found_inside_notes_not_at_the_top_level(payload):
    """The specific oversight: a payment entity has no top-level reference_id."""
    entity = payload["payload"]["payment"]["entity"]

    assert "reference_id" not in entity
    assert entity["notes"]["reference_id"] == REAL_REFERENCE


def test_the_payment_link_is_recoverable_from_the_description(payload):
    """Razorpay writes it as '#<id without the plink_ prefix>'."""
    assert payload["payload"]["payment"]["entity"]["description"] == "#TYQwevtIn7Imdx"

    assert REAL_PLINK in extract_case_hints(payload)


def test_every_identifier_in_the_event_is_offered(payload):
    hints = extract_case_hints(payload)

    assert REAL_REFERENCE in hints
    assert REAL_PLINK in hints
    assert REAL_PAYMENT in hints


def test_the_entity_id_is_tried_last(payload):
    """`pay_...` names nothing we store unless the case opened from that exact attempt,
    so a reference that DOES name the case must be preferred over it."""
    hints = extract_case_hints(payload)

    assert hints.index(REAL_REFERENCE) < hints.index(REAL_PAYMENT)


# --- the fix, against the real event -------------------------------------------------------


def test_the_real_captured_payment_closes_the_real_case(repo, payload):
    """The regression, end to end: this exact payload left the case open."""
    r, case = repo
    entity = payload["payload"]["payment"]["entity"]

    resolved = PaymentLinkService(r.conn, client=object(), repository=r).mark_paid_from_provider_event(
        entity_id=entity["id"],                                # pay_... resolves nothing
        event_name="payment.captured",
        amount_paise=entity["amount"],
        reference_id=str(entity.get("reference_id") or ""),    # absent on a payment entity
        hints=extract_case_hints(payload),
    )

    assert resolved == case.case_id
    assert r.get_case(case.case_id).status == CaseStatus.PAID


def test_without_the_hints_it_still_fails_which_is_what_happened(repo, payload):
    """Pins the cause. If this ever starts passing, the entity id began resolving on its
    own and this test is measuring something other than the bug it was written for."""
    r, case = repo

    resolved = PaymentLinkService(r.conn, client=object(), repository=r).mark_paid_from_provider_event(
        entity_id=REAL_PAYMENT, event_name="payment.captured",
        amount_paise=2_500_000, reference_id="",
    )

    assert resolved is None
    assert r.get_case(case.case_id).status != CaseStatus.PAID


def test_resolution_does_not_depend_on_which_event_the_merchant_ticked(repo, payload):
    """payment.captured, order.paid and payment_link.paid must all close the case. A
    merchant who subscribes to two of the three must not get a half-working engine."""
    r, case = repo
    hints = extract_case_hints(payload)

    for event_name in ("payment.captured", "order.paid", "payment_link.paid"):
        assert PaymentLinkService(r.conn, client=object(), repository=r).mark_paid_from_provider_event(
            entity_id=REAL_PAYMENT, event_name=event_name,
            amount_paise=2_500_000, hints=hints,
        ) == case.case_id


def test_applying_the_same_payment_twice_records_one_receipt(repo, payload):
    """Razorpay sends captured AND order.paid for a single payment, so double application
    is the normal case, not an edge case."""
    r, case = repo
    hints = extract_case_hints(payload)
    service = PaymentLinkService(r.conn, client=object(), repository=r)

    first = service.mark_paid_from_provider_event(
        entity_id=REAL_PAYMENT, event_name="payment.captured",
        amount_paise=2_500_000, hints=hints)
    second = service.mark_paid_from_provider_event(
        entity_id=REAL_PAYMENT, event_name="order.paid",
        amount_paise=2_500_000, hints=hints)

    assert first == second == case.case_id
    receipts = [e for e in r.timeline(case.case_id) if e.kind.value == "PAYMENT_RECEIVED"]
    assert len(receipts) == 1
