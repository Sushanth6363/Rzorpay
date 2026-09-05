#!/usr/bin/env python3
"""Send a correctly-signed test webhook to your own endpoint.

WHY THIS EXISTS
    When a real payment produces no visible effect, the cause is almost never the engine.
    It is the tunnel being down, the webhook registered in Live Mode instead of Test Mode,
    or the secret in .env differing from the one pasted into the dashboard. Each of those
    fails the same silent way, and debugging them through an actual card payment is slow.

    This exercises the whole receiving path - tunnel, HMAC verification, replay window,
    idempotency, event mapping, case resolution - without needing Razorpay or a payment.
    If this works and a real payment does not, the problem is the dashboard registration,
    not the code.

Usage:
    python scripts/send_test_webhook.py                       # local, payment_link.paid
    python scripts/send_test_webhook.py --url https://x.trycloudflare.com
    python scripts/send_test_webhook.py --event payment.failed
    python scripts/send_test_webhook.py --entity plink_ABC123 --amount 2500000

    # simulate a gateway outage, then clear it
    python scripts/send_test_webhook.py --event payment.downtime.started  --instrument HDFC
    python scripts/send_test_webhook.py --event payment.downtime.resolved --instrument HDFC
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app import config_env  # noqa: E402,F401  (loads .env)

import requests  # noqa: E402

# Which payload key holds the entity, per Razorpay event family.
ENTITY_KEY = {
    "payment": "payment",
    "payment_link": "payment_link",
    "order": "order",
    "invoice": "invoice",
    "subscription": "subscription",
}


def build_downtime_payload(
    event: str, entity_id: str, method: str, instrument: str, severity: str
) -> dict:
    """Razorpay's real downtime shape, which is NOT the shape of a payment event.

    The entity sits under the literal key `payment.downtime`, and the affected thing is
    named by `method` (upi / card / netbanking) or by `instrument` (an issuing bank or
    wallet). Building a plain payment entity here stores an outage with no method and no
    instrument, so `is_gateway_down()` matches nothing and the outage is invisible to the
    engine - it looks like it worked and suppresses nothing.
    """
    now = int(time.time())
    return {
        "entity": "event",
        "account_id": "acc_TEST",
        "event": event,
        "contains": ["payment.downtime"],
        "created_at": now,
        "payload": {
            "payment.downtime": {
                "entity": {
                    "id": entity_id,
                    "entity": "payment.downtime",
                    "method": method,
                    "begin": now,
                    "end": now if event.endswith(".resolved") else None,
                    "status": "resolved" if event.endswith(".resolved") else "started",
                    "scheduled": False,
                    "severity": severity,
                    "instrument": {"issuer": instrument} if instrument else {},
                }
            }
        },
    }


def build_payload(event: str, entity_id: str, amount_paise: int) -> dict:
    family = event.split(".")[0]
    key = ENTITY_KEY.get(family, "payment")
    now = int(time.time())
    return {
        "entity": "event",
        "account_id": "acc_TEST",
        "event": event,
        "contains": [key],
        "created_at": now,  # fresh, so the replay window accepts it
        "payload": {
            key: {
                "entity": {
                    "id": entity_id,
                    "amount": amount_paise,
                    "amount_paid": amount_paise if "paid" in event else 0,
                    "currency": "INR",
                    "status": "paid" if "paid" in event else "failed",
                    "created_at": now,
                    "email": "test@example.com",
                    "contact": "+919876543210",
                }
            }
        },
    }


def default_base_url() -> str:
    """The public tunnel if one is recorded, otherwise the local server.

    NGROK_DOMAIN is a bare hostname in .env (no scheme), because that is the form the
    ngrok dashboard hands you and asking anyone to remember to prepend https:// is how
    the wrong string ends up in the Razorpay webhook registration.
    """
    domain = (os.environ.get("NGROK_DOMAIN") or "").strip()
    if not domain:
        return "http://localhost:8000"
    if domain.startswith(("http://", "https://")):
        return domain.rstrip("/")
    return f"https://{domain}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    # Defaults to the reserved tunnel domain when one is recorded in .env, because
    # localhost proves only that the engine works - it says nothing about whether
    # Razorpay can actually reach this machine, which is the failure this script exists
    # to diagnose. Pass --url http://localhost:8000 to deliberately bypass the tunnel.
    parser.add_argument("--url", default=default_base_url(),
                        help="base URL of the server (defaults to NGROK_DOMAIN from .env "
                             "if set, else http://localhost:8000)")
    parser.add_argument("--event", default="payment_link.paid")
    parser.add_argument("--entity", default="", help="e.g. plink_ABC. Defaults to a fake id.")
    parser.add_argument("--amount", type=int, default=2_500_000, help="integer paise")
    parser.add_argument("--secret", default="", help="overrides RAZORPAY_WEBHOOK_SECRET")
    parser.add_argument("--method", default="netbanking",
                        help="downtime only: upi | card | netbanking | wallet")
    parser.add_argument("--instrument", default="HDFC",
                        help="downtime only: the affected bank/issuer, e.g. HDFC")
    parser.add_argument("--severity", default="high", help="downtime only")
    args = parser.parse_args()

    secret = args.secret or os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
    if not secret:
        print("ERROR: RAZORPAY_WEBHOOK_SECRET is not set.")
        print("       Put it in .env, or pass --secret. The endpoint fails closed without it.")
        return 2

    is_downtime = args.event.startswith("payment.downtime")
    if is_downtime:
        entity_id = args.entity or "down_TEST_1"   # stable, so .resolved matches .started
        payload = build_downtime_payload(
            args.event, entity_id, args.method, args.instrument, args.severity
        )
    else:
        entity_id = args.entity or f"plink_TEST{int(time.time())}"
        payload = build_payload(args.event, entity_id, args.amount)
    body = json.dumps(payload).encode()
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    endpoint = args.url.rstrip("/") + "/webhooks/razorpay"
    print(f"POST {endpoint}")
    print(f"  event  : {args.event}")
    print(f"  entity : {entity_id}")
    if is_downtime:
        print(f"  method : {args.method}")
        print(f"  affects: {args.instrument}")
    else:
        print(f"  amount : Rs {args.amount / 100:,.2f}")
    print()

    try:
        response = requests.post(
            endpoint, data=body, timeout=30,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": signature,
                "X-Razorpay-Event-Id": f"evt_test_{int(time.time() * 1000)}",
            },
        )
    except Exception as exc:
        print(f"COULD NOT REACH THE SERVER: {exc}")
        print("  Is it running?  python -m app.api.webhook_listener")
        print("  If using a tunnel, is the tunnel still up?")
        return 1

    print(f"HTTP {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text[:500])

    print()
    if response.status_code == 401:
        print("401 means the SIGNATURE was rejected. The secret here and the secret the")
        print("server loaded are different. Check .env, and restart the server after editing it.")
    elif response.status_code in (200, 202):
        print("Accepted. Check /feed and /metrics to see what the engine did with it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
