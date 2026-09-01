"""Standardized Golden Scenarios Fixtures (S001 - S010) for Unified Recovery Engine.

Provides deterministic regression scenarios for M4 verification, trace UI, and judge demonstrations.
"""

from typing import Dict, Any, List
from app.domain.enums import EventType, EventSource, DataProvenance
from app.domain.models import CanonicalEvent
from app.domain.money import Money


def get_golden_scenarios() -> Dict[str, Dict[str, Any]]:
    """Return dictionary of 10 golden scenarios S001..S010 with inputs and expected outcomes."""
    return {
        "S001": {
            "name": "Genuine failed payment",
            "description": "Standard failed payment due to insufficient funds; gateway available.",
            "raw_event": {
                "merchant_id": "merch_alpha",
                "customer_id": "cust_101",
                "event_id": "evt_s001",
                "event_type": EventType.FAILED_PAYMENT.value,
                "amount_paise": 1000000,  # ₹10,000
                "currency": "INR",
                "occurred_at": "2026-09-01T10:00:00+00:00",
                "failure_reason": "INSUFFICIENT_FUNDS",
                "gateway": "razorpay",
            },
            "expected_stage0": "VALID_RECOVERY",
            "expected_diagnosis": "INSUFFICIENT_FUNDS",
            "expected_eligible_actions": ["NO_ACTION", "RECOMMEND_RETRY", "WHATSAPP_LINK", "SMS_LINK", "EMAIL_LINK"],
        },
        "S002": {
            "name": "Self-cured payment",
            "description": "Payment failed initially but was subsequently paid before decision.",
            "raw_event": {
                "merchant_id": "merch_alpha",
                "customer_id": "cust_102",
                "event_id": "evt_s002",
                "event_type": EventType.FAILED_PAYMENT.value,
                "amount_paise": 500000,  # ₹5,000
                "currency": "INR",
                "occurred_at": "2026-09-01T10:00:00+00:00",
                "is_paid": True,
                "paid_at": "2026-09-01T10:05:00+00:00",
                "payment_status": "SUCCESS",
            },
            "expected_stage0": "NOT_RECOVERABLE",
            "expected_stage0_reason": "SELF_CURED",
        },
        "S003": {
            "name": "Gateway outage",
            "description": "Failed payment occurring during an active bank/gateway downtime outage.",
            "raw_event": {
                "merchant_id": "merch_alpha",
                "customer_id": "cust_103",
                "event_id": "evt_s003",
                "event_type": EventType.FAILED_PAYMENT.value,
                "amount_paise": 200000,  # ₹2,000
                "currency": "INR",
                "occurred_at": "2026-09-01T10:00:00+00:00",
                "failure_reason": "GATEWAY_TIMEOUT",
                "gateway": "hdfc_bank",
                "is_downtime": True,
            },
            "expected_stage0": "VALID_RECOVERY",
            "expected_diagnosis": "GATEWAY_FAILURE",
            "expected_safety_rejected_actions": ["RECOMMEND_RETRY", "WHATSAPP_LINK", "SMS_LINK", "EMAIL_LINK"],
            "expected_safety_reject_reason": "KNOWN_GATEWAY_OUTAGE",
        },
        "S004": {
            "name": "Abandoned checkout",
            "description": "Customer abandoned checkout cart before submitting payment details.",
            "raw_event": {
                "merchant_id": "merch_alpha",
                "customer_id": "cust_104",
                "event_id": "evt_s004",
                "event_type": EventType.ABANDONED_CHECKOUT.value,
                "amount_paise": 350000,  # ₹3,500
                "currency": "INR",
                "occurred_at": "2026-09-01T10:00:00+00:00",
                "cart_status": "ABANDONED",
            },
            "expected_stage0": "VALID_RECOVERY",
            "expected_diagnosis": "CUSTOMER_ABANDONMENT",
        },
        "S005": {
            "name": "Failed subscription renewal",
            "description": "Automated recurring subscription debit mandate failed.",
            "raw_event": {
                "merchant_id": "merch_alpha",
                "customer_id": "cust_105",
                "event_id": "evt_s005",
                "event_type": EventType.FAILED_SUBSCRIPTION_RENEWAL.value,
                "amount_paise": 99900,  # ₹999
                "currency": "INR",
                "occurred_at": "2026-09-01T10:00:00+00:00",
                "failure_reason": "AUTOPAY_DEBIT_FAILED",
            },
            "expected_stage0": "VALID_RECOVERY",
            "expected_diagnosis": "SUBSCRIPTION_RENEWAL_FAILURE",
        },
        "S006": {
            "name": "Overdue B2B invoice",
            "description": "B2B invoice payment term elapsed without payment receipt.",
            "raw_event": {
                "merchant_id": "merch_beta",
                "customer_id": "cust_201",
                "event_id": "evt_s006",
                "event_type": EventType.OVERDUE_B2B_INVOICE.value,
                "amount_paise": 7500000,  # ₹75,000
                "currency": "INR",
                "occurred_at": "2026-09-01T10:00:00+00:00",
                "invoice_status": "OVERDUE",
            },
            "expected_stage0": "VALID_RECOVERY",
            "expected_diagnosis": "INVOICE_OVERDUE",
            "expected_has_assisted_channels": True,  # IVR & AGENT_DIAL
        },
        "S007": {
            "name": "Duplicate event",
            "description": "Re-ingested duplicate webhook event.",
            "raw_event": {
                "merchant_id": "merch_alpha",
                "customer_id": "cust_101",
                "event_id": "evt_s001",  # Same as S001
                "event_type": EventType.FAILED_PAYMENT.value,
                "amount_paise": 1000000,
                "currency": "INR",
                "occurred_at": "2026-09-01T10:00:00+00:00",
                "is_duplicate": True,
            },
            "expected_stage0": "NOT_RECOVERABLE",
            "expected_stage0_reason": "DUPLICATE_EVENT",
        },
        "S008": {
            "name": "Cross-tenant identical customer",
            "description": "Identical customer_id under distinct merchant_id.",
            "raw_event": {
                "merchant_id": "merch_gamma",
                "customer_id": "cust_101",  # Same customer_id as Merchant Alpha
                "event_id": "evt_s008",
                "event_type": EventType.FAILED_PAYMENT.value,
                "amount_paise": 400000,
                "currency": "INR",
                "occurred_at": "2026-09-01T10:00:00+00:00",
                "failure_reason": "CARD_DECLINED",
            },
            "expected_stage0": "VALID_RECOVERY",
            "expected_diagnosis": "CARD_DECLINED",
        },
        "S009": {
            "name": "No eligible intervention (Budget exhausted)",
            "description": "Customer has reached monthly contact cap limit.",
            "raw_event": {
                "merchant_id": "merch_alpha",
                "customer_id": "cust_109",
                "event_id": "evt_s009",
                "event_type": EventType.FAILED_PAYMENT.value,
                "amount_paise": 300000,
                "currency": "INR",
                "occurred_at": "2026-09-01T10:00:00+00:00",
                "failure_reason": "INSUFFICIENT_FUNDS",
                "is_budget_exhausted": True,
            },
            "expected_stage0": "VALID_RECOVERY",
            "expected_eligible_actions": ["NO_ACTION", "RECOMMEND_RETRY"],  # Direct outreach rejected
            "expected_safety_reject_reason": "CONTACT_BUDGET_UNAVAILABLE",
        },
        "S010": {
            "name": "Multiple eligible candidates",
            "description": "High-value opportunity with all safety constraints cleared.",
            "raw_event": {
                "merchant_id": "merch_alpha",
                "customer_id": "cust_110",
                "event_id": "evt_s010",
                "event_type": EventType.FAILED_PAYMENT.value,
                "amount_paise": 1500000,  # ₹15,000
                "currency": "INR",
                "occurred_at": "2026-09-01T10:00:00+00:00",
                "failure_reason": "INSUFFICIENT_FUNDS",
            },
            "expected_stage0": "VALID_RECOVERY",
            "expected_multiple_eligible": True,
        },
    }
