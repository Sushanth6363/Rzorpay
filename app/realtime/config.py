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

# Populate os.environ from .env before ANY value below is read. Without this the file is
# documentation: the engine reports NOT_CONFIGURED, refuses to send, and the operator
# concludes the integration is broken when nothing ever read the file. An already-exported
# variable always wins, so tests and CI are unaffected.
from app import config_env  # noqa: E402,F401  (import for side effect, must precede reads)


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

# --- Who is allowed to contact the customer ----------------------------------------------
# Razorpay Payment Links accept `notify: {sms, email}` and `reminder_enable`, which make
# RAZORPAY send its own message the moment a link is created and then run its own reminder
# cadence. That is a genuinely useful mode - it delivers a real SMS with no Twilio account
# - but it cannot be on at the same time as the engine's own sending, because then a
# single-rung decision produces three messages: the engine's email, Razorpay's email and
# Razorpay's SMS.
#
# More seriously, none of Razorpay's sends pass through ChannelDispatcher, so none reach
# contact_ledger. The escalation ladder, the contact budget and the quiet period (ADR-0015)
# are all bypassed by messages the engine cannot see and did not decide to send.
#
# So it is one or the other, stated explicitly:
#   "engine"   (default) the engine owns contact. Razorpay takes money and says nothing.
#   "razorpay"           Razorpay delivers the SMS and email for a link it creates, and
#                        the engine does not also send that rung itself.
LINK_NOTIFY_OWNER = (os.environ.get("RECOVERY_LINK_NOTIFY", "engine") or "engine").strip().lower()
if LINK_NOTIFY_OWNER not in ("engine", "razorpay"):
    LINK_NOTIFY_OWNER = "engine"

PROVIDER_NOTIFIES = LINK_NOTIFY_OWNER == "razorpay"


# --- a voice call leaves nothing behind ---------------------------------------------------
# A phone call is the only rung with no artifact. If the customer misses it, or answers and
# cannot write a URL down while driving, the contact produced nothing they can act on - and
# the engine has spent its most expensive and most intrusive action for no recoverable
# outcome.
#
# So a call is accompanied by an SMS carrying the payment link. This is NOT the uncontrolled
# double-contact that RECOVERY_LINK_NOTIFY exists to prevent: that was a provider sending
# messages the engine never decided on, which reached no ledger and bypassed the ladder.
# This is one decision, made by the engine, recorded in full, delivered over two media
# because one of them is transient by nature.
#
# It consumes ONE contact slot, not two. From the customer's side a call plus "here is the
# link we just discussed" is a single interaction, and charging it twice would make the
# engine give up sooner without protecting anyone.
VOICE_COMPANION_SMS = _flag("RECOVERY_VOICE_COMPANION_SMS", True)


# --- demo time compression ----------------------------------------------------------------
# The follow-up ladder is designed in real time: a gateway blip is re-checked in about four
# hours, an overdue invoice in about eight days. Correct for production and useless in a
# five-minute demo, where nobody can wait eight days to see the second rung.
#
# This scales the CLOCK, not the policy. One notional hour becomes this many real seconds,
# so every relative difference is preserved exactly - an invoice still waits twenty times
# longer than a gateway failure, and the backoff still widens each gap. Only the unit
# changes. A demo that instead flattened every delay to a constant would be showing a
# different engine from the one being described.
#
# 3600 is real time and the default. 0.2 turns an eight-day wait into about forty seconds.
FOLLOWUP_HOUR_SECONDS = float(os.environ.get("RECOVERY_FOLLOWUP_HOUR_SECONDS", "3600"))

# How often the background worker looks for due follow-ups. At demo speed a review falling
# due in ten seconds must not sit in the queue for a minute waiting to be noticed.
WORKER_INTERVAL_SECONDS = int(os.environ.get("RECOVERY_WORKER_INTERVAL_SECONDS", "60"))

# A DELIBERATE FALLBACK, NOT A CONVENIENCE.
#
# `rzp_test_mock` keys make the client return a locally generated link. `link_service`
# refuses those by default and should: a simulated link fires no webhook, so the case can
# never close, and a demo that dead-ends silently at its most important moment is worse
# than one that fails loudly.
#
# But when the provider is unreachable or rate limited, every OTHER half of the engine
# still works - decisions, real email, the escalation ladder, the board, the timeline -
# and being unable to show any of it is the worse outcome. This lets the operator accept
# that trade knowingly. It is off by default, and the refusal message says it exists.
# A FIXED LADDER FOR DEMONSTRATION. NOT THE ENGINE DECIDING.
#
# The engine ranks by expected value, and the ceiling is a CAP rather than an instruction:
# after one confirmed email, SMS becomes eligible but email may still score higher, so the
# engine correctly keeps emailing. That is the right behaviour and it is impossible to show
# on stage - the ladder never visibly climbs.
#
# With this on, the agent takes the next reachable rung above the highest confirmed contact
# instead of the highest-EV action. It is a SCRIPTED SEQUENCE, and everything it produces
# says so: the reasoning line, the case timeline, and the dispatch record. Off by default,
# because an audience shown a fixed sequence and told it is a decision has been misled.
DEMO_FIXED_LADDER = os.environ.get(
    "RECOVERY_DEMO_FIXED_LADDER", "false"
).strip().lower() in {"1", "true", "yes", "on"}


# Rungs the scripted demo ladder walks past, by name, comma separated.
#
# WhatsApp is the reason this exists. It cannot send on a Twilio trial - the API demands a
# pre-approved template and the Content API that creates one returns 20003, not available
# on a trial account - so the rung can only ever fail. Showing that failure is a legitimate
# choice and it is what happens by default. Skipping it is also legitimate when the point
# of the run is the sequence rather than the error handling.
#
# What is NOT legitimate is showing it as successful, so there is no setting for that. A
# rung turns green when a message was confirmed sent, and nothing here can change that.
DEMO_SKIP_RUNGS = {
    r.strip().upper()
    for r in os.environ.get("RECOVERY_DEMO_SKIP_RUNGS", "").split(",")
    if r.strip()
}


ALLOW_SIMULATED_LINKS = os.environ.get(
    "RECOVERY_ALLOW_SIMULATED_LINKS", "false"
).strip().lower() in {"1", "true", "yes", "on"}


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
        "link_notify_owner": LINK_NOTIFY_OWNER,
        "voice_companion_sms": VOICE_COMPANION_SMS,
        "followup_hour_seconds": FOLLOWUP_HOUR_SECONDS,
        "worker_interval_seconds": WORKER_INTERVAL_SECONDS,
        "webhook_max_age_seconds": WEBHOOK_MAX_AGE_SECONDS,
    }
