"""Test-wide isolation from the operator's own .env.

WHY THIS FILE EXISTS
    `app/config_env.py` loads .env into os.environ at import time, and every module that
    reads a gate reads it from there. That is correct for running the engine. It is
    dangerous under pytest, because it means the test suite's safety posture is whatever
    the developer last set for a demo.

    It was not theoretical. Enabling RECOVERY_DISPATCH_ENABLED=true for a live demo made
    `test_dispatch_defaults_to_dry_run_when_not_explicitly_enabled` fail - the one test
    whose entire job is to prove the default is safe. That test caught it. Nothing
    guaranteed the others would: any test that exercised ChannelDispatcher without an
    explicit dry-run override would have had dispatch genuinely enabled, holding real
    SMTP and Razorpay credentials loaded from the same file.

    The rule this restores is absolute: A TEST RUN MAY NEVER SEND ANYTHING TO ANYONE, and
    that must not depend on the contents of an untracked file.

WHAT IS NEUTRALISED
    Every gate that permits an outbound side effect, and every credential that would make
    one succeed. A test that wants a specific value sets it itself with monkeypatch, which
    is explicit and local; nothing is inherited from the machine.
"""

import os

import pytest

# Gates: forced to their safe value, not merely unset, so a module reading them directly
# sees an explicit "no" rather than a default it might one day change.
SAFE_GATES = {
    "RECOVERY_DISPATCH_ENABLED": "false",
    "RECOVERY_ALLOW_LIVE_CREDENTIALS": "false",
    "RECOVERY_LINK_NOTIFY": "engine",
    "ALLOW_UNSIGNED_WEBHOOKS": "false",
    # Demo aids, pinned off for the same reason as the gates above: a test run must not
    # inherit whatever was last exported for a rehearsal. These two changed which rung a
    # follow-up took and whether an unpayable link was accepted, so tests passed alone and
    # failed in the suite depending on which file ran first - which reads as flakiness and
    # is really the machine leaking into the run.
    "RECOVERY_DEMO_FIXED_LADDER": "false",
    "RECOVERY_ALLOW_SIMULATED_LINKS": "false",
    "RECOVERY_DEMO_SKIP_RUNGS": "",
}

# Credentials: blanked. With the gates closed nothing should reach an adapter anyway, but
# an adapter that is reached must fail on a missing credential rather than succeed on a
# real one. Defence in depth, because the cost of being wrong is a message to a stranger.
BLANKED_CREDENTIALS = (
    "SMTP_USER", "SMTP_PASSWORD", "SMTP_HOST", "SMTP_FROM",
    "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN",
    "TWILIO_SMS_FROM", "TWILIO_WHATSAPP_FROM", "TWILIO_VOICE_FROM",
    "RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET",
)


@pytest.fixture(autouse=True, scope="session")
def _never_send_from_a_test_run():
    """Neutralise the operator's .env for the whole session."""
    # Importing this first means .env has already been read; we overwrite what it set.
    import app.config_env  # noqa: F401

    saved = {k: os.environ.get(k) for k in (*SAFE_GATES, *BLANKED_CREDENTIALS)}
    os.environ.update(SAFE_GATES)
    for name in BLANKED_CREDENTIALS:
        os.environ.pop(name, None)

    yield

    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
