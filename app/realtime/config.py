"""Real-time runtime configuration (ADR-0018).

WHY THIS EXISTS
    The batch evaluator and the live server want opposite things from the same engine.
    Batch wants an in-memory database, a fixed seed and a simulator. Live wants durable
    shared state, no seed at all, and a hard guarantee that it cannot contact a real person
    by accident. Leaving those choices implicit is how a determinism seed ends up in a
    production decision path — which is exactly what `random_seed=42` in the webhook handler
    was.

    Every real-time behaviour that could surprise someone is named here, defaults to the
    safe option, and must be turned on deliberately through the environment.

SAFETY DEFAULTS (all of these fail closed):
    - Signature verification is REQUIRED. No secret configured means the endpoint refuses
      traffic; it never falls back to accepting unsigned requests.
    - Outbound side effects are DRY RUN. The engine decides and records, but sends nothing,
      until DISPATCH is explicitly enabled.
    - Live credentials are refused unless separately acknowledged, so a stray `rzp_live_`
      key cannot start billing real customers.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


# --- Durable shared state ---------------------------------------------------------------
# The webhook server and the dashboard are SEPARATE PROCESSES. With an in-memory database
# each holds a private copy, so nothing the server ingests can ever appear in the UI and
# everything is lost on restart. A file-backed database in WAL mode is what makes a
# real-time system observable at all.
DB_PATH = Path(os.environ.get("RECOVERY_DB_PATH", REPO_ROOT / "data" / "recovery.db"))

# --- Webhook security -------------------------------------------------------------------
WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "").strip()

# Escape hatch for local testing ONLY. Off by default, and the server logs loudly whenever
# it is on, because an unauthenticated endpoint that executes recovery actions is a way to
# make someone else's engine send messages.
ALLOW_UNSIGNED_WEBHOOKS = _flag("ALLOW_UNSIGNED_WEBHOOKS", False)

# Reject webhooks whose timestamp is older than this, to bound replay of a captured request.
WEBHOOK_MAX_AGE_SECONDS = int(os.environ.get("WEBHOOK_MAX_AGE_SECONDS", "300"))

# --- Outbound side effects --------------------------------------------------------------
# DRY RUN means: run the full engine, persist the decision and the audit trail, but do not
# create payment links or send messages. This is the default because the difference between
# a demo and contacting a stranger is one environment variable.
DISPATCH_ENABLED = _flag("RECOVERY_DISPATCH_ENABLED", False)

# A second, independent gate for live (non-test) Razorpay credentials.
ALLOW_LIVE_CREDENTIALS = _flag("RECOVERY_ALLOW_LIVE_CREDENTIALS", False)


def is_live_key(key_id: str) -> bool:
    return key_id.startswith("rzp_live")


def dispatch_permitted(key_id: str) -> tuple:
    """Return (allowed, reason). Both gates must open before anything leaves the process."""
    if not DISPATCH_ENABLED:
        return False, "DRY_RUN: RECOVERY_DISPATCH_ENABLED is not set"
    if is_live_key(key_id) and not ALLOW_LIVE_CREDENTIALS:
        return False, (
            "REFUSED: live Razorpay credentials detected without "
            "RECOVERY_ALLOW_LIVE_CREDENTIALS"
        )
    return True, "dispatch enabled"


def describe() -> dict:
    """Human-readable posture, surfaced on /health and in the dashboard."""
    return {
        "db_path": str(DB_PATH),
        "signature_required": not ALLOW_UNSIGNED_WEBHOOKS,
        "webhook_secret_configured": bool(WEBHOOK_SECRET),
        "dispatch_enabled": DISPATCH_ENABLED,
        "allow_live_credentials": ALLOW_LIVE_CREDENTIALS,
        "webhook_max_age_seconds": WEBHOOK_MAX_AGE_SECONDS,
    }
