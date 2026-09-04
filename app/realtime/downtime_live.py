"""Live gateway downtime, driven by Razorpay `payment.downtime.*` webhooks (ADR-0018).

This is the D2 signal with the simulation taken out. `SimulatedDowntimeProvider` is told
which gateways are down by the experiment harness; this one is told by Razorpay, in real
time, and reads the answer from durable state so an outage survives a process restart.

INV-4 UNCHANGED: a known outage suppresses retries and outbound contact. The rule is the
same rule — only the source of "known" has changed, from an authored fixture to a live
feed. That is the whole difference between demonstrating the control and operating it.

FAILS SAFE, NOT OPEN: if the outage store cannot be read, this reports the gateway as
healthy rather than raising. A downtime lookup that throws inside the decision path would
take the whole recovery pipeline down; reporting "not down" degrades to the pre-signal
behaviour (arm A2), which is a known, tested state. The trade is deliberate and is why the
suppression floor in the safety filter is diagnosis-based and independent of this provider.
"""

from __future__ import annotations

from typing import Optional

from app.domain.enums import DataProvenance
from app.pipeline.downtime import DowntimeProvider
from app.realtime import ingest


class LiveRazorpayDowntimeProvider(DowntimeProvider):
    """Reports outages that Razorpay has actually notified us about."""

    def is_gateway_down(
        self,
        gateway_name: str,
        method: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> bool:
        try:
            return ingest.is_down(gateway_name, method)
        except Exception:
            # See FAILS SAFE above: never let the downtime lookup break the decision path.
            return False

    def get_provenance(self) -> DataProvenance:
        """Real notifications from the payment provider, not an authored fixture."""
        return DataProvenance.REAL_DATA
