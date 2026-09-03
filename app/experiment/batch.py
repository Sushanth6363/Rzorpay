"""Deterministic evaluation batch generation — shared by the CLI runner and the dashboard.

Lives in `app/` rather than `scripts/` because the judge dashboard and the batch evaluation
MUST draw from the same generator. Two generators drift, and the moment they do, the numbers
on screen stop describing the numbers in `results/report.json`.

INVARIANTS:
1. DETERMINISTIC: identical (num_events, batch_seed, reference_timestamp) always produces a
   byte-identical batch. One RNG substream per event, so generation is order-independent.
2. INTEGER PAISE: no float ever enters a money value.
3. MIXED STREAMS: the batch spans all four recovery streams. A unified engine cannot be
   demonstrated on a single-stream batch.
4. REAL TIME AXIS: events are spread across a window and returned in chronological order.
   Without elapsed time between a customer's opportunities, every quiet-period rule is
   permanently active and the escalation ladder silently tests nothing.
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.domain.enums import EventType
from app.pipeline.tds import lookup_rate_bps


# --- Batch generation parameters (authored; see docs/EXPERIMENT_METHODOLOGY.md) -------------
FAILURE_REASONS = [
    "INSUFFICIENT_FUNDS",
    "PAYMENT_METHOD_FAILURE",
    "AUTHENTICATION_FAILURE",
    "EXPIRED_METHOD",
    "GATEWAY_FAILURE",
]
# Amount bands in integer paise. Right-skewed, as real recovery populations are.
AMOUNT_BANDS_PAISE = [
    (50_000, 200_000),      # Rs 500 - Rs 2,000
    (200_000, 1_000_000),   # Rs 2,000 - Rs 10,000
    (1_000_000, 5_000_000),  # Rs 10,000 - Rs 50,000
]
AMOUNT_BAND_WEIGHTS = [0.55, 0.35, 0.10]
MERCHANTS = ["merch_alpha", "merch_beta"]

# Batch composition. Declared here and echoed into the report, because an ablation can
# only measure a capability if the batch contains cases that capability acts on.
PHANTOM_SHARE = 0.15    # already-paid: Stage 0 gate should decline to chase these
OUTAGE_SHARE = 0.15     # inside a gateway outage: downtime signal should suppress
OUTAGE_GATEWAY = "razorpay_outage_sim"

# --- STREAM MIX -----------------------------------------------------------------------
# Track 3 names three sources by name: "from payment failures and checkout abandonment to
# overdue receivables". A batch drawn entirely from one stream cannot demonstrate a UNIFIED
# engine - it demonstrates a payment-failure engine with three unused enum members. These
# weights are authored to resemble a mid-size Indian merchant's mix (checkout abandonment
# is by far the largest count, B2B receivables the largest by value), not measured.
STREAM_WEIGHTS = {
    EventType.FAILED_PAYMENT: 0.40,
    EventType.ABANDONED_CHECKOUT: 0.30,
    EventType.FAILED_SUBSCRIPTION_RENEWAL: 0.18,
    EventType.OVERDUE_B2B_INVOICE: 0.12,
}

# --- TIME AXIS ------------------------------------------------------------------------
# Events are spread across a window rather than stamped at one instant. Without elapsed
# time between a customer's opportunities, every quiet-period rule is permanently active
# and the escalation ladder can never advance - the batch would silently test nothing.
BATCH_WINDOW_DAYS = 45

# B2B receivables carry the facts the TDS derivation needs. A share of them are settled
# net of statutory withholding: a shortfall that IS the TDS and therefore is not customer
# debt at all. Only a derivation can tell those apart from a genuine short payment.
TDS_SECTIONS = ["194C", "194J", "194H", "194I_BUILDING", "194Q"]
TDS_NET_SETTLED_SHARE = 0.45   # shortfall == statutory withholding -> nothing to chase
TDS_PARTIAL_SHARE = 0.25       # shortfall exceeds withholding -> chase only the excess


def parse_seeds(spec: str) -> List[int]:
    """Parse '21-40' or '21,22,23' into a seed list."""
    spec = spec.strip()
    if "-" in spec and "," not in spec:
        lo, hi = spec.split("-", 1)
        return list(range(int(lo), int(hi) + 1))
    return [int(s) for s in spec.split(",") if s.strip()]


def generate_batch(
    num_events: int,
    batch_seed: int,
    reference_timestamp: str,
) -> List[Dict[str, Any]]:
    """Generate a deterministic synthetic opportunity batch.

    Determinism: one RNG substream per event, keyed by (batch_seed, index), so generation
    is order-independent and reproducible across processes and calendar days.
    """
    base_time = datetime.fromisoformat(reference_timestamp)
    events: List[Dict[str, Any]] = []
    for i in range(num_events):
        stream = hashlib.sha256(f"{batch_seed}|evt_{i}".encode()).hexdigest()
        rng = random.Random(int(stream[:16], 16))

        merchant_id = MERCHANTS[rng.randrange(len(MERCHANTS))]
        band = rng.choices(AMOUNT_BANDS_PAISE, weights=AMOUNT_BAND_WEIGHTS, k=1)[0]
        amount_paise = rng.randrange(band[0], band[1])  # int paise, never float

        # Stream selection. A unified engine is only unified if the batch is mixed.
        streams = list(STREAM_WEIGHTS.keys())
        weights = [STREAM_WEIGHTS[s] for s in streams]
        event_type = rng.choices(streams, weights=weights, k=1)[0]

        # Time axis: events are spread across the window, so a customer's second
        # opportunity genuinely occurs days after their first and the escalation ladder
        # has real elapsed time to advance against.
        offset_minutes = rng.randrange(0, BATCH_WINDOW_DAYS * 24 * 60)
        occurred_at = (base_time + timedelta(minutes=offset_minutes)).isoformat()

        event: Dict[str, Any] = {
            "merchant_id": merchant_id,
            "customer_id": f"cust_{i % max(1, num_events // 3):04d}",
            "event_id": f"evt_{i:05d}",
            "event_type": event_type.value,
            "amount_paise": amount_paise,
            "currency": "INR",
            "occurred_at": occurred_at,
            "observed_at": occurred_at,
            # The decision is taken when the event is observed, never before it (INV-7).
            "decision_timestamp": occurred_at,
            "gateway": "razorpay",
        }

        # The batch MUST contain the cases each ablation is meant to catch, or the
        # comparison measures nothing. Composition is fixed and declared in the report.
        draw = rng.random()

        # --- Stream-specific fields -----------------------------------------------------
        if event_type == EventType.OVERDUE_B2B_INVOICE:
            # Receivables carry the facts the TDS derivation needs. Amounts are larger.
            event["amount_paise"] = amount_paise * 4
            event["invoice_status"] = "OVERDUE"
            event["days_overdue"] = rng.randrange(15, 120)
            event["tds_section"] = TDS_SECTIONS[rng.randrange(len(TDS_SECTIONS))]
            event["payee_type"] = "COMPANY"
            event["pan_available"] = True
            gross = event["amount_paise"]
            rate_bps, _ = lookup_rate_bps(event["tds_section"], "COMPANY", True)

            tds_draw = rng.random()
            if tds_draw < TDS_NET_SETTLED_SHARE:
                # Settled net of withholding. The "shortfall" IS the TDS: the payer already
                # remitted it to the government. There is no customer debt here at all, and
                # only a DERIVED position can tell that from a genuine short payment. An
                # engine reading a boolean flag would either chase this or need to be told.
                event["amount_received_paise"] = gross - (gross * rate_bps) // 10_000
                event["batch_case"] = "B2B_SETTLED_NET_OF_TDS"
            elif tds_draw < TDS_NET_SETTLED_SHARE + TDS_PARTIAL_SHARE:
                # Genuine arrears PLUS withholding. Only the excess above the statutory
                # amount is recoverable; chasing the whole shortfall demands money the
                # customer was required by law to withhold.
                extra_short = rng.randrange(gross // 20, gross // 4)
                event["amount_received_paise"] = gross - (gross * rate_bps) // 10_000 - extra_short
                event["batch_case"] = "B2B_PARTIAL_PAYMENT_WITH_TDS"
            else:
                # Nothing remitted at all: the full invoice is recoverable debt.
                event["amount_received_paise"] = 0
                event["batch_case"] = "B2B_FULLY_UNPAID"

        elif event_type == EventType.ABANDONED_CHECKOUT:
            event["cart_status"] = "ABANDONED"
            event["cart_id"] = f"cart_{i:05d}"
            if draw < PHANTOM_SHARE:
                # Customer completed the purchase elsewhere/later before any decision.
                event["checkout_completed"] = True
                event["cart_status"] = "COMPLETED"
                event["batch_case"] = "PHANTOM_CHECKOUT_COMPLETED"
            else:
                event["batch_case"] = "GENUINE_ABANDONMENT"

        else:
            # FAILED_PAYMENT and FAILED_SUBSCRIPTION_RENEWAL share the gateway-failure shape.
            event["failure_reason"] = FAILURE_REASONS[rng.randrange(len(FAILURE_REASONS))]
            if event_type == EventType.FAILED_SUBSCRIPTION_RENEWAL:
                event["subscription_id"] = f"sub_{i:05d}"
                event["renewal_attempt"] = rng.randrange(1, 4)

            if draw < PHANTOM_SHARE:
                # Already paid before any decision. Only an arm with the Stage 0 GATE
                # active declines to chase this -> makes A2 vs A2ns measurable.
                event["is_paid"] = True
                event["paid_at"] = occurred_at
                event["payment_status"] = "SUCCESS"
                event["batch_case"] = "PHANTOM_ALREADY_PAID"
            elif draw < PHANTOM_SHARE + OUTAGE_SHARE:
                # Failure occurring inside a gateway outage window, but reported with an
                # ORDINARY failure code. This is the only case where the downtime signal is
                # worth anything: if the error already said GATEWAY_FAILURE, any scorer that
                # respects the diagnosis reaches the same decision without the signal, and
                # A3 vs A2 measures zero. The signal earns its place precisely when the
                # outage is NOT evident from the error code (the narrow form of D2:
                # detection is not the gap - consuming it at the recovery layer is).
                event["failure_reason"] = "INSUFFICIENT_FUNDS"
                event["gateway"] = OUTAGE_GATEWAY
                event["batch_case"] = "OUTAGE_MASKED_AS_ORDINARY_FAILURE"
            else:
                event["batch_case"] = "GENUINE_FAILURE"

        events.append(event)

    # CHRONOLOGICAL ORDER. The batch is processed as a stream, so a customer's second
    # opportunity must be decided AFTER their first. Left in generation order, a "prior"
    # contact could sit in the future relative to the decision being taken, the quiet
    # period would never clear, and the escalation ladder could never advance - the
    # compliance control would be present in code and dead in the batch.
    # Sorting is deterministic (event_id breaks ties), so the batch hash stays stable.
    events.sort(key=lambda e: (e["occurred_at"], e["event_id"]))
    return events


def _case_counts(events: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count each declared batch case, so the report proves the batch contained them."""
    counts: Dict[str, int] = {}
    for e in events:
        key = str(e.get("batch_case", "UNLABELLED"))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _stream_counts(events: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for e in events:
        key = str(e.get("event_type", "UNKNOWN"))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))
