"""Dataset Adapter & Compatibility Layer for Unified Recovery Engine.

Maps real-world and benchmark dataset fields to CanonicalEvent and RecoveryOpportunity models,
maintaining clean data provenance tagging (REAL_DATA, SYNTHETIC_DATA, SIMULATED_EXTERNAL_STATE).
"""

import uuid
from typing import Any, Dict, Tuple
from app.domain.enums import DataProvenance, EventSource, EventType
from app.domain.models import CanonicalEvent
from app.domain.money import Money


class DatasetAdapter:
    """Adapts external raw event dictionaries into normalized domain events and opportunities."""

    @staticmethod
    def adapt_raw_event(
        raw_data: Dict[str, Any],
        provenance: DataProvenance = DataProvenance.SIMULATED_EXTERNAL_STATE,
    ) -> Tuple[CanonicalEvent, DataProvenance]:
        """Convert raw input dictionary into provider-neutral CanonicalEvent."""
        merchant_id = str(raw_data.get("merchant_id", "merch_default")).strip()
        customer_id = str(raw_data.get("customer_id", raw_data.get("user_id", "cust_default"))).strip()
        source_event_id = str(raw_data.get("event_id", raw_data.get("payment_id", f"evt_{uuid.uuid4().hex[:8]}"))).strip()

        # Parse Event Stream Type
        raw_type = str(raw_data.get("event_type", raw_data.get("type", "FAILED_PAYMENT"))).upper()
        try:
            event_type = EventType(raw_type)
        except ValueError:
            event_type = EventType.FAILED_PAYMENT

        # Parse Amount strictly in integer paise or string/int rupees
        amount_paise = raw_data.get("amount_paise")
        if amount_paise is None:
            raw_rupees = raw_data.get("amount", raw_data.get("amount_rupees", 0))
            amount = Money.from_rupees(str(raw_rupees))
        else:
            amount = Money(int(amount_paise))

        currency = str(raw_data.get("currency", "INR")).upper()

        # Parse Timestamps
        occurred_at = str(raw_data.get("occurred_at", raw_data.get("timestamp", "2026-09-01T10:00:00+00:00")))
        observed_at = str(raw_data.get("observed_at", occurred_at))

        idempotency_key = f"idem_{merchant_id}_{source_event_id}"

        canonical_event = CanonicalEvent(
            event_id=f"can_{uuid.uuid4().hex[:10]}",
            merchant_id=merchant_id,
            customer_id=customer_id,
            source_event_id=source_event_id,
            event_type=event_type,
            amount=amount,
            currency=currency,
            source=EventSource.SIMULATED if provenance != DataProvenance.REAL_DATA else EventSource.RAZORPAY_TEST,
            idempotency_key=idempotency_key,
            occurred_at=occurred_at,
            observed_at=observed_at,
            raw_payload=raw_data,
        )

        return canonical_event, provenance
