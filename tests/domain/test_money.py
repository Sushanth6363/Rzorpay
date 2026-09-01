"""Unit tests for Money value object."""

from decimal import Decimal
import pytest
from hypothesis import given
import hypothesis.strategies as st
from app.domain.money import Money


def test_money_paise_initialization() -> None:
    m = Money(1050)
    assert m.amount_paise == 1050
    assert m.to_rupees_str() == "10.50"


def test_money_from_rupees() -> None:
    m1 = Money.from_rupees("10.50")
    assert m1.amount_paise == 1050

    m2 = Money.from_rupees(10)
    assert m2.amount_paise == 1000

    m3 = Money.from_rupees(Decimal("25.75"))
    assert m3.amount_paise == 2575


def test_money_rejects_floats() -> None:
    with pytest.raises(TypeError, match="Float input prohibited"):
        Money.from_rupees(10.50)  # type: ignore

    with pytest.raises(TypeError, match="integer"):
        Money(10.50)  # type: ignore


def test_money_rejects_negative() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        Money(-100)

    with pytest.raises(ValueError, match="cannot be negative"):
        Money.from_rupees("-5.00")


def test_money_exact_addition() -> None:
    m1 = Money.from_rupees("10.01")
    m2 = Money.from_rupees("20.02")
    m3 = m1.add(m2)
    assert m3.amount_paise == 3003
    assert m3.to_rupees_str() == "30.03"


def test_money_exact_subtraction() -> None:
    m1 = Money(5000)
    m2 = Money(2000)
    assert (m1 - m2).amount_paise == 3000

    with pytest.raises(ValueError, match="negative"):
        m2.subtract(m1)


def test_money_comparisons() -> None:
    m1 = Money(100)
    m2 = Money(200)
    m3 = Money(100)

    assert m1 < m2
    assert m2 > m1
    assert m1 <= m3
    assert m1 == m3
    assert m1 != m2


@given(st.integers(min_value=0, max_value=1_000_000_000))
def test_money_hypothesis_property(paise: int) -> None:
    m = Money(paise)
    assert m.amount_paise == paise
    assert m.add(Money.zero()).amount_paise == paise
    assert m.subtract(m) == Money.zero()
