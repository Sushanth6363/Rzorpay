"""Demo speed changes the clock, never the policy.

WHY THIS EXISTS
    The follow-up ladder is designed in real time: a gateway blip re-checked in about four
    hours, an overdue invoice in about eight days. That is correct for production and
    useless in a five-minute demo, where the second rung would arrive a week after the
    judges left.

    The tempting shortcut is to flatten every delay to a constant - "all follow-ups fire in
    10 seconds". That would demo a DIFFERENT ENGINE from the one being described, and the
    thing being described is precisely that timing is derived per case.

    So the scale multiplies the clock and nothing else. Every ratio the policy produces
    survives exactly: an invoice still waits fifty times longer than a gateway failure, and
    the backoff still widens each successive gap. Only the unit changes.
"""

import importlib

import pytest

from app.domain.enums import ActionType

CASES = [
    ("GATEWAY_FAILURE", ActionType.RECOMMEND_RETRY, 0),
    ("CUSTOMER_ABANDONMENT", ActionType.EMAIL_LINK, 0),
    ("INVOICE_OVERDUE", ActionType.EMAIL_LINK, 0),
    ("INVOICE_OVERDUE", ActionType.SMS_LINK, 1),
    ("INVOICE_OVERDUE", ActionType.IVR_CALL, 3),
]


def _reload(monkeypatch, scale):
    monkeypatch.setenv("RECOVERY_FOLLOWUP_HOUR_SECONDS", str(scale))
    from app.realtime import config as cfg
    importlib.reload(cfg)
    from app.realtime import followup as f
    importlib.reload(f)
    return cfg, f


def _seconds(cfg, f):
    return [f.compute_delay_hours(d, a, n) * cfg.FOLLOWUP_HOUR_SECONDS for d, a, n in CASES]


def test_the_default_is_real_time(monkeypatch):
    """An unset variable must not quietly put production on demo speed."""
    monkeypatch.delenv("RECOVERY_FOLLOWUP_HOUR_SECONDS", raising=False)
    cfg, _ = _reload(monkeypatch, 3600)
    monkeypatch.delenv("RECOVERY_FOLLOWUP_HOUR_SECONDS", raising=False)
    importlib.reload(cfg)

    assert cfg.FOLLOWUP_HOUR_SECONDS == 3600.0


def test_every_ratio_survives_compression(monkeypatch):
    """The property that makes this honest. If the ratios changed, the demo would be
    showing timing the engine does not actually produce."""
    cfg_real, f_real = _reload(monkeypatch, 3600)
    real = _seconds(cfg_real, f_real)

    cfg_demo, f_demo = _reload(monkeypatch, 0.05)
    demo = _seconds(cfg_demo, f_demo)

    baseline_real, baseline_demo = real[0], demo[0]
    for r, d in zip(real, demo):
        assert r / baseline_real == pytest.approx(d / baseline_demo, rel=1e-9)


def test_compression_actually_compresses(monkeypatch):
    """A full four-rung invoice ladder has to fit inside a five-minute demo."""
    cfg, f = _reload(monkeypatch, 0.05)
    ladder = [(ActionType.EMAIL_LINK, 0), (ActionType.SMS_LINK, 1),
              (ActionType.WHATSAPP_LINK, 2), (ActionType.IVR_CALL, 3)]
    total = sum(f.compute_delay_hours("INVOICE_OVERDUE", a, n) * cfg.FOLLOWUP_HOUR_SECONDS
                for a, n in ladder)

    assert total < 120, f"the full ladder takes {total:.0f}s, too long to narrate"


def test_an_invoice_still_waits_far_longer_than_a_gateway_blip(monkeypatch):
    """The headline distinction the demo explains out loud. It must remain visible even
    when both are measured in seconds."""
    cfg, f = _reload(monkeypatch, 0.05)
    blip = f.compute_delay_hours("GATEWAY_FAILURE", ActionType.RECOMMEND_RETRY, 0)
    invoice = f.compute_delay_hours("INVOICE_OVERDUE", ActionType.EMAIL_LINK, 0)

    assert invoice > blip * 10


def test_the_scale_does_not_touch_the_policy(monkeypatch):
    """compute_delay_hours returns POLICY hours. Those are the engine's decision and are
    identical at any clock speed; only their conversion to real time differs."""
    _, f_real = _reload(monkeypatch, 3600)
    policy_real = [f_real.compute_delay_hours(d, a, n) for d, a, n in CASES]

    _, f_demo = _reload(monkeypatch, 0.05)
    policy_demo = [f_demo.compute_delay_hours(d, a, n) for d, a, n in CASES]

    assert policy_real == policy_demo
