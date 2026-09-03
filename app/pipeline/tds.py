"""TDS Withholding Derivation — B2B receivables that are NOT customer debt.

THE PROBLEM THIS SOLVES
    A B2B invoice for Rs 1,00,000 is settled with a remittance of Rs 90,000. Every naive
    receivables system sees a Rs 10,000 shortfall and starts chasing the customer. But if
    the invoice falls under section 194J, Rs 10,000 IS the statutory withholding: the payer
    already remitted it to the government on the payee's behalf. The customer owes nothing.
    Chasing them is not just wasted contact - it is a demand for money the law says they
    were required to withhold.

    The inverse also matters. A Rs 1,00,000 invoice under 194C-company (2%) settled with
    Rs 85,000 has a Rs 15,000 shortfall of which Rs 2,000 is statutory. The recoverable
    debt is Rs 13,000, not Rs 15,000. An engine that chases the full shortfall is asking
    for money it cannot lawfully collect, and its "recovered" number is inflated by the
    portion it never could have recovered.

WHAT THIS MODULE DOES
    Derives the withholding position from the invoice's own facts - gross amount, section,
    payee constitution, PAN availability - and the amount actually received. It does NOT
    read a pre-computed `is_tds_withheld` boolean and trust it. The boolean is the answer;
    this computes the answer.

INVARIANTS:
1. INTEGER PAISE ONLY. Rates are basis points (integers); every product uses integer
   arithmetic with floor division. No float ever touches a money value.
2. DETERMINISTIC. Identical inputs always produce an identical position. No clock, no RNG.
3. CONSERVATIVE ON AMBIGUITY. If the section is unrecognised or the facts are incomplete,
   the position is UNDETERMINED and the opportunity remains recoverable. This module may
   never invent a withholding that suppresses a legitimate recovery.
4. NO TAX ADVICE. This derives a recovery decision, not a tax position. It does not compute
   a liability, file anything, or replace a finance team's determination.

RATE TABLE PROVENANCE — READ BEFORE RELYING ON THIS
    The rates below are the commonly-cited resident-payee rates and are used here to
    demonstrate the derivation, not to be authoritative. Rates change with each Finance Act
    and vary by payee constitution, threshold, and certificate. Before any production use,
    this table MUST be replaced by a finance-owned, versioned, dated source with an
    effective-from date per row. It is authored, it is approximate, and it is not verified
    against the current Act. That limitation is stated here rather than hidden.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

# Effective-from date this authored table claims to represent. Carried into evidence so a
# reviewer can see exactly which vintage produced a decision.
TDS_RATE_TABLE_VERSION = "authored-v1-fy2025-26"

# Section -> rate in BASIS POINTS (1 bp = 0.01%). Integers, so all arithmetic stays exact.
# Keys are (section, payee_type). payee_type "*" matches any constitution.
STATUTORY_RATE_BPS: Dict[tuple, int] = {
    ("194C", "INDIVIDUAL_HUF"): 100,   # 1%  - contractor payments to individual/HUF
    ("194C", "*"):              200,   # 2%  - contractor payments to others
    ("194J", "TECHNICAL"):      200,   # 2%  - technical services
    ("194J", "*"):             1000,   # 10% - professional / royalty fees
    ("194H", "*"):              200,   # 2%  - commission or brokerage
    ("194I_PLANT", "*"):        200,   # 2%  - rent of plant, machinery, equipment
    ("194I_BUILDING", "*"):    1000,   # 10% - rent of land, building, furniture
    ("194A", "*"):             1000,   # 10% - interest other than on securities
    ("194Q", "*"):               10,   # 0.1% - purchase of goods above threshold
}

# Section 206AA: where the payee has not furnished a PAN, withholding is at the higher of
# the section rate or 20%. This is the single most common cause of a shortfall that looks
# like a huge underpayment and is in fact compliant withholding.
NO_PAN_FLOOR_BPS = 2000  # 20%

# Rounding tolerance. s.288B rounds to the nearest rupee, and payers round independently at
# line and invoice level, so an exact-paise match is not achievable in practice. One rupee
# of slack per invoice absorbs that without absorbing a real shortfall.
TDS_TOLERANCE_PAISE = 100


class TdsPosition(str, Enum):
    """Derived withholding position for a B2B receivable."""

    NO_SHORTFALL = "NO_SHORTFALL"                    # paid in full; nothing at risk
    STATUTORY_WITHHOLDING = "STATUTORY_WITHHOLDING"  # shortfall IS the TDS; not customer debt
    PARTIAL_WITH_TDS = "PARTIAL_WITH_TDS"            # shortfall exceeds TDS; excess is recoverable
    UNDER_WITHHELD = "UNDER_WITHHELD"                # withheld less than statute; full shortfall recoverable
    UNDETERMINED = "UNDETERMINED"                    # facts incomplete; treat as fully recoverable


@dataclass(frozen=True)
class TdsDerivation:
    """The full working, not just the conclusion. Every field is auditable."""

    position: TdsPosition
    gross_amount_paise: int
    amount_received_paise: int
    shortfall_paise: int
    section: Optional[str]
    payee_type: str
    applied_rate_bps: int
    expected_tds_paise: int
    recoverable_amount_paise: int
    rate_source: str
    explanation: str

    @property
    def is_recoverable(self) -> bool:
        """True when there is customer debt left to chase after statutory withholding."""
        return self.recoverable_amount_paise > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": self.position.value,
            "gross_amount_paise": self.gross_amount_paise,
            "amount_received_paise": self.amount_received_paise,
            "shortfall_paise": self.shortfall_paise,
            "section": self.section,
            "payee_type": self.payee_type,
            "applied_rate_bps": self.applied_rate_bps,
            "applied_rate_percent": self.applied_rate_bps / 100.0,
            "expected_tds_paise": self.expected_tds_paise,
            "recoverable_amount_paise": self.recoverable_amount_paise,
            "rate_source": self.rate_source,
            "rate_table_version": TDS_RATE_TABLE_VERSION,
            "tolerance_paise": TDS_TOLERANCE_PAISE,
            "explanation": self.explanation,
        }


def lookup_rate_bps(
    section: Optional[str],
    payee_type: str,
    pan_available: bool,
) -> tuple:
    """Resolve the applicable rate in basis points. Returns (bps, source_description).

    Returns (0, ...) when the section is unknown - the caller must then treat the position
    as UNDETERMINED rather than assume zero withholding.
    """
    if not section:
        return 0, "no section supplied"

    key_specific = (section.upper(), payee_type.upper())
    key_any = (section.upper(), "*")

    if key_specific in STATUTORY_RATE_BPS:
        base_bps = STATUTORY_RATE_BPS[key_specific]
        source = f"s.{section.upper()} ({payee_type.upper()})"
    elif key_any in STATUTORY_RATE_BPS:
        base_bps = STATUTORY_RATE_BPS[key_any]
        source = f"s.{section.upper()}"
    else:
        return 0, f"section '{section}' not in rate table"

    # s.206AA: no PAN raises the rate to the higher of the section rate or 20%.
    if not pan_available and NO_PAN_FLOOR_BPS > base_bps:
        return NO_PAN_FLOOR_BPS, f"{source} raised to 20% under s.206AA (no PAN)"

    return base_bps, source


def derive_tds_position(
    gross_amount_paise: int,
    context: Dict[str, Any],
) -> TdsDerivation:
    """Derive the withholding position for a B2B receivable from the invoice's own facts.

    Expected context keys (all optional; absence yields UNDETERMINED, never suppression):
        tds_section        e.g. "194J", "194C", "194I_BUILDING"
        payee_type         "COMPANY" | "INDIVIDUAL_HUF" | "TECHNICAL" | ...
        pan_available      bool, default True
        amount_received_paise  integer paise actually remitted by the payer
    """
    received_raw = context.get("amount_received_paise")
    section = context.get("tds_section")
    payee_type = str(context.get("payee_type", "COMPANY"))
    pan_available = bool(context.get("pan_available", True))

    # -- Facts incomplete: never suppress on a guess -------------------------------------
    if received_raw is None:
        return TdsDerivation(
            position=TdsPosition.UNDETERMINED,
            gross_amount_paise=gross_amount_paise,
            amount_received_paise=0,
            shortfall_paise=gross_amount_paise,
            section=section,
            payee_type=payee_type,
            applied_rate_bps=0,
            expected_tds_paise=0,
            recoverable_amount_paise=gross_amount_paise,
            rate_source="not evaluated",
            explanation=(
                "No remittance figure available, so no withholding position can be derived. "
                "The full amount is treated as recoverable; TDS never suppresses on absent evidence."
            ),
        )

    received = int(received_raw)
    shortfall = gross_amount_paise - received

    if shortfall <= 0:
        return TdsDerivation(
            position=TdsPosition.NO_SHORTFALL,
            gross_amount_paise=gross_amount_paise,
            amount_received_paise=received,
            shortfall_paise=max(0, shortfall),
            section=section,
            payee_type=payee_type,
            applied_rate_bps=0,
            expected_tds_paise=0,
            recoverable_amount_paise=0,
            rate_source="not evaluated",
            explanation="Invoice settled in full or over-remitted. Nothing to recover.",
        )

    rate_bps, rate_source = lookup_rate_bps(section, payee_type, pan_available)

    if rate_bps == 0:
        return TdsDerivation(
            position=TdsPosition.UNDETERMINED,
            gross_amount_paise=gross_amount_paise,
            amount_received_paise=received,
            shortfall_paise=shortfall,
            section=section,
            payee_type=payee_type,
            applied_rate_bps=0,
            expected_tds_paise=0,
            recoverable_amount_paise=shortfall,
            rate_source=rate_source,
            explanation=(
                f"Withholding rate could not be resolved ({rate_source}). The entire "
                f"shortfall is treated as recoverable customer debt."
            ),
        )

    # Integer paise throughout. Floor division, never float multiplication.
    expected_tds = (gross_amount_paise * rate_bps) // 10_000

    if abs(shortfall - expected_tds) <= TDS_TOLERANCE_PAISE:
        return TdsDerivation(
            position=TdsPosition.STATUTORY_WITHHOLDING,
            gross_amount_paise=gross_amount_paise,
            amount_received_paise=received,
            shortfall_paise=shortfall,
            section=section,
            payee_type=payee_type,
            applied_rate_bps=rate_bps,
            expected_tds_paise=expected_tds,
            recoverable_amount_paise=0,
            rate_source=rate_source,
            explanation=(
                f"Shortfall of {shortfall} paise matches expected withholding of "
                f"{expected_tds} paise at {rate_bps / 100:.2f}% under {rate_source} "
                f"(tolerance {TDS_TOLERANCE_PAISE} paise). This is statutory withholding, "
                f"not customer debt. The correct action is to obtain Form 16A, not to "
                f"contact the customer for payment."
            ),
        )

    if shortfall > expected_tds:
        recoverable = shortfall - expected_tds
        return TdsDerivation(
            position=TdsPosition.PARTIAL_WITH_TDS,
            gross_amount_paise=gross_amount_paise,
            amount_received_paise=received,
            shortfall_paise=shortfall,
            section=section,
            payee_type=payee_type,
            applied_rate_bps=rate_bps,
            expected_tds_paise=expected_tds,
            recoverable_amount_paise=recoverable,
            rate_source=rate_source,
            explanation=(
                f"Shortfall of {shortfall} paise exceeds expected withholding of "
                f"{expected_tds} paise under {rate_source}. Only the excess of "
                f"{recoverable} paise is recoverable customer debt; the balance is with "
                f"the exchequer and cannot be collected from the customer."
            ),
        )

    # Withheld LESS than statute. The whole shortfall is a genuine short payment: the
    # payer's under-withholding is a matter between the payer and the department, and it
    # does not reduce what the payee is owed on this invoice.
    return TdsDerivation(
        position=TdsPosition.UNDER_WITHHELD,
        gross_amount_paise=gross_amount_paise,
        amount_received_paise=received,
        shortfall_paise=shortfall,
        section=section,
        payee_type=payee_type,
        applied_rate_bps=rate_bps,
        expected_tds_paise=expected_tds,
        recoverable_amount_paise=shortfall,
        rate_source=rate_source,
        explanation=(
            f"Shortfall of {shortfall} paise is below expected withholding of "
            f"{expected_tds} paise under {rate_source}. The shortfall is not explained by "
            f"withholding and is treated as recoverable in full."
        ),
    )
