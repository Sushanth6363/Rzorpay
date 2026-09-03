"""TDS withholding derivation — the position is COMPUTED, never read off a flag.

These tests exist because the difference between "is_tds_withheld: true" and a derivation
is the whole claim. A flag is an answer someone else supplied; a derivation is an answer
this engine can defend, from the invoice's own facts, with the working attached.
"""

from app.clock import FakeClock
from app.domain.enums import EventSource, EventType, OpportunityStatus, Stage0Decision, Stage0Reason
from app.domain.models import RecoveryOpportunity
from app.domain.money import Money
from app.pipeline.stage0 import Stage0Evaluator
from app.pipeline.tds import (
    NO_PAN_FLOOR_BPS,
    TDS_TOLERANCE_PAISE,
    TdsPosition,
    derive_tds_position,
    lookup_rate_bps,
)

REF = "2026-01-01T00:00:00+00:00"


def _invoice(amount_paise: int, **context) -> RecoveryOpportunity:
    return RecoveryOpportunity(
        opportunity_id="opp_tds",
        merchant_id="m1",
        customer_id="c1",
        source_event_id="inv_1",
        event_type=EventType.OVERDUE_B2B_INVOICE,
        amount=Money(amount_paise),
        currency="INR",
        status=OpportunityStatus.NEW,
        source=EventSource.SIMULATED,
        occurred_at=REF,
        observed_at=REF,
        context_data=dict(context),
    )


# --- The core derivation ----------------------------------------------------------------


def test_shortfall_equal_to_statutory_withholding_is_not_customer_debt():
    """Rs 1,00,000 under s.194J settled at Rs 90,000 -> the gap IS the 10% TDS."""
    d = derive_tds_position(
        gross_amount_paise=10_000_000,
        context={"tds_section": "194J", "payee_type": "COMPANY", "amount_received_paise": 9_000_000},
    )

    assert d.position == TdsPosition.STATUTORY_WITHHOLDING
    assert d.expected_tds_paise == 1_000_000
    assert d.recoverable_amount_paise == 0
    assert d.is_recoverable is False


def test_shortfall_exceeding_withholding_recovers_only_the_excess():
    """Rs 15,000 short on a 2% s.194C invoice -> Rs 2,000 is statutory, Rs 13,000 is debt."""
    d = derive_tds_position(
        gross_amount_paise=10_000_000,
        context={"tds_section": "194C", "payee_type": "COMPANY", "amount_received_paise": 8_500_000},
    )

    assert d.position == TdsPosition.PARTIAL_WITH_TDS
    assert d.expected_tds_paise == 200_000
    assert d.recoverable_amount_paise == 1_300_000
    # The engine must never chase the full shortfall: the balance is with the exchequer.
    assert d.recoverable_amount_paise < d.shortfall_paise


def test_under_withholding_leaves_the_whole_shortfall_recoverable():
    """Withheld less than statute: the payer's under-deduction is not the payee's discount."""
    d = derive_tds_position(
        gross_amount_paise=10_000_000,
        context={"tds_section": "194J", "payee_type": "COMPANY", "amount_received_paise": 9_950_000},
    )

    assert d.position == TdsPosition.UNDER_WITHHELD
    assert d.recoverable_amount_paise == d.shortfall_paise == 50_000


def test_individual_huf_gets_a_different_rate_than_a_company_under_194c():
    """Payee constitution changes the rate, so the same shortfall means different things."""
    bps_individual, _ = lookup_rate_bps("194C", "INDIVIDUAL_HUF", pan_available=True)
    bps_company, _ = lookup_rate_bps("194C", "COMPANY", pan_available=True)

    assert bps_individual == 100  # 1%
    assert bps_company == 200     # 2%


def test_missing_pan_raises_the_rate_to_the_206aa_floor():
    """s.206AA: no PAN means withholding at the higher of the section rate or 20%."""
    bps, source = lookup_rate_bps("194C", "COMPANY", pan_available=False)

    assert bps == NO_PAN_FLOOR_BPS == 2000
    assert "206AA" in source


def test_rounding_slack_is_tolerated_within_one_rupee():
    """s.288B rounds to the nearest rupee; an exact-paise match is not achievable."""
    d = derive_tds_position(
        gross_amount_paise=10_000_000,
        context={
            "tds_section": "194J",
            "payee_type": "COMPANY",
            "amount_received_paise": 9_000_000 + TDS_TOLERANCE_PAISE,
        },
    )

    assert d.position == TdsPosition.STATUTORY_WITHHOLDING


# --- Never suppress on a guess ----------------------------------------------------------


def test_unknown_section_never_suppresses_a_recovery():
    """An unrecognised section must leave the debt fully chaseable, not silently zero it."""
    d = derive_tds_position(
        gross_amount_paise=10_000_000,
        context={"tds_section": "999Z", "amount_received_paise": 9_000_000},
    )

    assert d.position == TdsPosition.UNDETERMINED
    assert d.recoverable_amount_paise == 1_000_000


def test_absent_remittance_figure_never_suppresses_a_recovery():
    """No facts, no suppression. The conservative direction is to keep chasing."""
    d = derive_tds_position(
        gross_amount_paise=10_000_000,
        context={"tds_section": "194J"},
    )

    assert d.position == TdsPosition.UNDETERMINED
    assert d.recoverable_amount_paise == 10_000_000


def test_integer_paise_only_no_float_leaks_into_money():
    """Rates are basis points and every product uses floor division."""
    d = derive_tds_position(
        gross_amount_paise=3_333_333,
        context={"tds_section": "194Q", "payee_type": "COMPANY", "amount_received_paise": 0},
    )

    assert isinstance(d.expected_tds_paise, int)
    assert isinstance(d.recoverable_amount_paise, int)
    assert isinstance(d.shortfall_paise, int)


# --- Stage 0 integration ----------------------------------------------------------------


def test_stage0_declines_to_chase_an_invoice_settled_net_of_tds():
    """The engine must not contact a customer who paid exactly what the law left them to pay."""
    evaluator = Stage0Evaluator(clock=FakeClock(REF))
    opp = _invoice(
        10_000_000,
        tds_section="194J",
        payee_type="COMPANY",
        amount_received_paise=9_000_000,
        invoice_status="OVERDUE",
    )

    result = evaluator.evaluate(opportunity=opp, decision_timestamp=REF)

    assert result.decision == Stage0Decision.NOT_RECOVERABLE
    assert result.reason_code == Stage0Reason.TDS_WITHHOLDING_EXCLUSION
    # The working, not just the verdict — this is what makes the audit trail defensible.
    assert result.evidence["tds_derivation"]["position"] == "STATUTORY_WITHHOLDING"
    assert result.evidence["tds_derivation"]["expected_tds_paise"] == 1_000_000


def test_stage0_restates_the_chaseable_amount_on_a_partial_payment():
    """A genuinely overdue invoice is still chased — but only for the collectable part."""
    evaluator = Stage0Evaluator(clock=FakeClock(REF))
    opp = _invoice(
        10_000_000,
        tds_section="194C",
        payee_type="COMPANY",
        amount_received_paise=8_500_000,
        invoice_status="OVERDUE",
    )

    result = evaluator.evaluate(opportunity=opp, decision_timestamp=REF)

    assert result.decision == Stage0Decision.VALID_RECOVERY
    assert result.recoverable_amount_paise == 1_300_000
    assert result.recoverable_amount_paise < opp.amount.amount_paise


def test_derivation_beats_a_contradicting_declared_flag():
    """Where both are present the DERIVATION is the answer; the flag cannot pre-empt it.

    An invoice fully unpaid but flagged `is_tds_withheld` is still recoverable debt. If the
    flag won, a caller could suppress any recovery by asserting a withholding that the
    invoice's own numbers contradict.
    """
    evaluator = Stage0Evaluator(clock=FakeClock(REF))
    opp = _invoice(
        10_000_000,
        tds_section="194J",
        payee_type="COMPANY",
        amount_received_paise=0,       # nothing remitted: the whole invoice is owed
        is_tds_withheld=True,          # contradicted by the numbers above
        invoice_status="OVERDUE",
    )

    result = evaluator.evaluate(opportunity=opp, decision_timestamp=REF)

    # The flag claimed the whole invoice was withheld. The numbers say Rs 10,000 of it was
    # and Rs 90,000 was simply never paid. The arithmetic wins.
    assert result.decision == Stage0Decision.VALID_RECOVERY
    assert result.recoverable_amount_paise == 9_000_000


def test_declared_flag_still_suppresses_when_no_facts_are_available():
    """A flag may fill a silence. It may only ever fill a silence."""
    evaluator = Stage0Evaluator(clock=FakeClock(REF))
    opp = _invoice(10_000_000, is_tds_withheld=True, invoice_status="OVERDUE")

    result = evaluator.evaluate(opportunity=opp, decision_timestamp=REF)

    assert result.decision == Stage0Decision.NOT_RECOVERABLE
    assert result.reason_code == Stage0Reason.TDS_WITHHOLDING_EXCLUSION
    # And it says plainly that no derivation backed the suppression.
    assert result.evidence.get("basis") == "DECLARED_FLAG_NOT_DERIVED"


def test_withholding_is_not_derived_for_non_receivable_streams():
    """A stray remittance field on a failed payment must not suppress it."""
    evaluator = Stage0Evaluator(clock=FakeClock(REF))
    opp = RecoveryOpportunity(
        opportunity_id="opp_pay",
        merchant_id="m1",
        customer_id="c1",
        source_event_id="pay_1",
        event_type=EventType.FAILED_PAYMENT,
        amount=Money(10_000_000),
        currency="INR",
        status=OpportunityStatus.NEW,
        source=EventSource.SIMULATED,
        occurred_at=REF,
        observed_at=REF,
        context_data={"amount_received_paise": 10_000_000},
    )

    result = evaluator.evaluate(opportunity=opp, decision_timestamp=REF)

    assert result.decision == Stage0Decision.VALID_RECOVERY
