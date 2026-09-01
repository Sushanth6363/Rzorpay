"""Money representation for Unified Recovery Engine.

INVARIANT: All monetary amounts are strictly integer paise.
Floating-point representations for money are strictly forbidden.
"""

from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


class Money:
    """Integer paise monetary value object.

    Ensures zero floating-point arithmetic pollution across calculation,
    persistence, serialization, and logging boundaries.
    """

    __slots__ = ("_amount_paise",)

    def __init__(self, amount_paise: int) -> None:
        if isinstance(amount_paise, bool) or not isinstance(amount_paise, int):
            raise TypeError(f"Money amount_paise must be an integer, got {type(amount_paise).__name__}")
        if amount_paise < 0:
            raise ValueError(f"Money amount_paise cannot be negative, got {amount_paise}")
        self._amount_paise: int = amount_paise

    @property
    def amount_paise(self) -> int:
        """Return monetary value in integer paise."""
        return self._amount_paise

    @classmethod
    def zero(cls) -> Money:
        """Return zero paise Money instance."""
        return cls(0)

    @classmethod
    def from_rupees(cls, rupees: str | int | Decimal) -> Money:
        """Construct Money from rupees representation.

        Accepts string (e.g. "10.50"), integer (e.g. 10), or Decimal.
        Strictly rejects float inputs to prevent precision loss.
        """
        if isinstance(rupees, float):
            raise TypeError("Float input prohibited for Money. Use string or Decimal (e.g., Money.from_rupees('10.50'))")
        
        if isinstance(rupees, int):
            if rupees < 0:
                raise ValueError(f"Rupees amount cannot be negative, got {rupees}")
            return cls(rupees * 100)

        dec = Decimal(str(rupees))
        if dec < Decimal(0):
            raise ValueError(f"Rupees amount cannot be negative, got {rupees}")
        
        paise_dec = (dec * Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return cls(int(paise_dec))

    def to_rupees_decimal(self) -> Decimal:
        """Convert paise to exact Decimal rupees representation."""
        return Decimal(self._amount_paise) / Decimal(100)

    def to_rupees_str(self) -> str:
        """Format paise as rupees string (e.g., 1050 -> '10.50')."""
        return f"{self.to_rupees_decimal():.2f}"

    def add(self, other: Money) -> Money:
        """Add two Money instances."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot add Money and {type(other).__name__}")
        return Money(self._amount_paise + other._amount_paise)

    def subtract(self, other: Money) -> Money:
        """Subtract other Money instance from self."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot subtract {type(other).__name__} from Money")
        diff = self._amount_paise - other._amount_paise
        if diff < 0:
            raise ValueError(f"Subtraction resulted in negative Money ({diff} paise)")
        return Money(diff)

    def multiply(self, factor: int | Decimal) -> Money:
        """Multiply Money by an integer or Decimal scalar."""
        if isinstance(factor, float):
            raise TypeError("Float factor prohibited for Money multiplication.")
        if isinstance(factor, int):
            if factor < 0:
                raise ValueError(f"Multiplication factor cannot be negative ({factor})")
            return Money(self._amount_paise * factor)
        if isinstance(factor, Decimal):
            if factor < Decimal(0):
                raise ValueError(f"Multiplication factor cannot be negative ({factor})")
            result_dec = (Decimal(self._amount_paise) * factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            return Money(int(result_dec))
        raise TypeError(f"Unsupported multiplication factor type: {type(factor).__name__}")

    def __add__(self, other: Money) -> Money:
        return self.add(other)

    def __sub__(self, other: Money) -> Money:
        return self.subtract(other)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            return False
        return self._amount_paise == other._amount_paise

    def __lt__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            raise TypeError(f"Cannot compare Money and {type(other).__name__}")
        return self._amount_paise < other._amount_paise

    def __le__(self, other: Money) -> bool:
        return self < other or self == other

    def __gt__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            raise TypeError(f"Cannot compare Money and {type(other).__name__}")
        return self._amount_paise > other._amount_paise

    def __ge__(self, other: Money) -> bool:
        return self > other or self == other

    def __hash__(self) -> int:
        return hash(self._amount_paise)

    def __repr__(self) -> str:
        return f"Money({self._amount_paise} paise / ₹{self.to_rupees_str()})"
