"""Gateway Downtime Provider & Simulator for Unified Recovery Engine.

INVARIANT (INV-4): Known gateway outage suppresses retry recommendations and customer outreach.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple
from app.domain.enums import DataProvenance


class DowntimeProvider(ABC):
    """Abstract interface for checking payment gateway operational status."""

    @abstractmethod
    def is_gateway_down(self, gateway_name: str, method: Optional[str] = None, timestamp: Optional[str] = None) -> bool:
        """Return True if gateway or specific payment method is currently experiencing an outage."""
        pass

    @abstractmethod
    def get_provenance(self) -> DataProvenance:
        """Return data provenance mode of the provider."""
        pass


class SimulatedDowntimeProvider(DowntimeProvider):
    """Deterministic simulator for gateway downtime status in testing and sandbox mode."""

    def __init__(self, default_down: bool = False) -> None:
        self._default_down = default_down
        self._outages: Dict[Tuple[str, Optional[str]], bool] = {}

    def set_outage(self, gateway_name: str, method: Optional[str] = None, is_down: bool = True) -> None:
        """Explicitly set outage status for a gateway/method pair."""
        key = (gateway_name.lower().strip(), method.lower().strip() if method else None)
        self._outages[key] = is_down

    def is_gateway_down(self, gateway_name: str, method: Optional[str] = None, timestamp: Optional[str] = None) -> bool:
        """Check downtime status with method-level fallback to gateway-level status."""
        if not gateway_name:
            return False

        g_key = gateway_name.lower().strip()
        m_key = method.lower().strip() if method else None

        # Specific method check first
        if (g_key, m_key) in self._outages:
            return self._outages[(g_key, m_key)]

        # Gateway broad check second
        if (g_key, None) in self._outages:
            return self._outages[(g_key, None)]

        return self._default_down

    def get_provenance(self) -> DataProvenance:
        """Return provenance mode."""
        return DataProvenance.SIMULATED_EXTERNAL_STATE


class NullDowntimeProvider(DowntimeProvider):
    """Downtime signal DISABLED. Always reports the gateway as healthy.

    Used by experiment arms that must run WITHOUT the downtime signal (A1, A2ns, A2),
    so that A3 vs A2 isolates the contribution of downtime-signal consumption alone
    (ADR-0011, 07_EXPERIMENT_METHODOLOGY).

    This is not a claim that no outage occurred - it is the absence of the signal.
    """

    def is_gateway_down(self, gateway_name: str, method=None, timestamp=None) -> bool:
        return False

    def get_provenance(self) -> DataProvenance:
        return DataProvenance.SIMULATED_EXTERNAL_STATE
