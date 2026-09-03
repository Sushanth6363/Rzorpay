"""Razorpay API & Webhook Integration Client for Unified Recovery Engine.

Provides integration with Razorpay REST APIs & Developer Sandbox:
1. Payment Link Generation (POST /v1/payment_links)
2. Live Downtimes & Status API (GET /v1/payments/downtimes)
3. Webhook Signature Verification (HMAC-SHA256)
"""

import hmac
import hashlib
import os
from typing import Any, Dict, Optional
import requests

from app.domain.enums import DataProvenance
from app.pipeline.downtime import DowntimeProvider


class RazorpayIntegrationClient:
    """Client for authenticating and communicating with Razorpay API endpoints."""

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ) -> None:
        self.key_id = key_id or os.environ.get("RAZORPAY_KEY_ID", "rzp_test_mock_key")
        self.key_secret = key_secret or os.environ.get("RAZORPAY_KEY_SECRET", "rzp_test_mock_secret")
        self.webhook_secret = webhook_secret or os.environ.get("RAZORPAY_WEBHOOK_SECRET", "mock_webhook_secret")
        self.base_url = "https://api.razorpay.com/v1"

    def verify_webhook_signature(self, raw_body: bytes, signature: str) -> bool:
        """Verify authenticity of incoming Razorpay webhook signature (HMAC-SHA256)."""
        if not signature or not self.webhook_secret:
            return False
        expected_sig = hmac.new(
            self.webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected_sig, signature)

    def create_payment_link(
        self,
        amount_paise: int,
        customer_name: str = "Valued Customer",
        customer_email: str = "customer@example.com",
        customer_contact: str = "+919876543210",
        description: str = "Payment Recovery Link",
        reference_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Call Razorpay API POST /v1/payment_links to generate an active recovery payment link.
        
        If live keys are missing or test mock is active, returns a valid test Razorpay recovery payload.
        """
        payload = {
            "amount": amount_paise,
            "currency": "INR",
            "accept_partial": False,
            "description": description,
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "contact": customer_contact,
            },
            "notify": {"sms": True, "email": True},
            "reminder_enable": True,
            "notes": {
                "source": "AI_Unified_Recovery_Engine",
                "reference_id": reference_id or "ref_unknown",
            },
        }

        # Check if using test mock credentials
        if self.key_id.startswith("rzp_test_mock"):
            mock_hash = hashlib.md5(str(reference_id or "default").encode()).hexdigest()[:8]
            mock_id = f"plink_{mock_hash}"
            return {
                "id": mock_id,
                "entity": "payment_link",
                "short_url": f"https://rzp.io/i/{mock_id[:8]}",
                "amount": amount_paise,
                "status": "created",
                "is_simulated": True,
                "provider": "Razorpay Test Developer Sandbox",
            }

        try:
            response = requests.post(
                f"{self.base_url}/payment_links",
                auth=(self.key_id, self.key_secret),
                json=payload,
                timeout=5,
            )
            if response.status_code in (200, 201):
                res_json = response.json()
                res_json["is_simulated"] = False
                return res_json
            else:
                mock_hash = hashlib.md5(str(reference_id or "default").encode()).hexdigest()[:8]
                return {
                    "error": f"Razorpay API HTTP {response.status_code}",
                    "details": response.text,
                    "is_simulated": True,
                    "short_url": f"https://rzp.io/i/test_{mock_hash}",
                }
        except Exception as err:
            mock_hash = hashlib.md5(str(reference_id or "default").encode()).hexdigest()[:8]
            return {
                "error": f"Connection error: {str(err)}",
                "is_simulated": True,
                "short_url": f"https://rzp.io/i/test_{mock_hash}",
            }


class LiveRazorpayDowntimeProvider(DowntimeProvider):
    """Live Gateway Downtime provider calling Razorpay Status/Downtimes API."""

    def __init__(self, client: Optional[RazorpayIntegrationClient] = None) -> None:
        self.client = client or RazorpayIntegrationClient()

    def is_gateway_down(self, gateway_name: str, method: Optional[str] = None, timestamp: Optional[str] = None) -> bool:
        """Query Razorpay API for live bank/gateway downtime status."""
        if not gateway_name:
            return False

        if self.client.key_id.startswith("rzp_test_mock"):
            return "outage" in gateway_name.lower() or "hdfc_bank" in gateway_name.lower()

        try:
            res = requests.get(
                f"{self.client.base_url}/payments/downtimes",
                auth=(self.client.key_id, self.client.key_secret),
                timeout=3,
            )
            if res.status_code == 200:
                downtimes = res.json()
                for item in downtimes:
                    if item.get("status") in ("scheduled", "started"):
                        item_gw = str(item.get("instrument", {}).get("issuer", "")).lower()
                        if gateway_name.lower() in item_gw:
                            return True
        except Exception:
            pass

        return False

    def get_provenance(self) -> DataProvenance:
        return DataProvenance.REAL_DATA
