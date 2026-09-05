"""Only one party may contact the customer for a given rung (ADR-0015).

WHY THIS TEST EXISTS
    Razorpay Payment Links accept `notify: {sms, email}` and `reminder_enable`, and the
    client hardcoded all three to True. So Razorpay sent its own email AND SMS the instant
    a link was created, plus ran its own reminder cadence - regardless of the single rung
    the engine had chosen, and without any of it passing through ChannelDispatcher.

    Confirmed against the live API on a real paid link:

        notify         : {'email': True, 'sms': True, 'whatsapp': False}
        reminder_enable: True

    One EMAIL_LINK decision therefore produced three messages, none of them written to
    contact_ledger. The escalation ladder, the contact budget and the quiet period were
    bypassed by sends the engine could not see and had not decided to make.

    It only escaped notice because the demo CSV carried a fake phone number.
"""

import pytest

from app.domain.enums import ActionType
from app.integrations.razorpay_client import RazorpayIntegrationClient


class _Response:
    status_code = 200

    @staticmethod
    def json():
        return {"id": "plink_x", "short_url": "https://rzp.io/rzp/X", "status": "created"}


@pytest.fixture()
def captured(monkeypatch):
    """Capture the payload without touching the network."""
    seen = {}

    def fake_post(url, **kwargs):
        seen["url"] = url
        seen["payload"] = kwargs.get("json")
        return _Response()

    monkeypatch.setattr("app.integrations.razorpay_client.requests.post", fake_post)
    return seen


def _reload_config(monkeypatch, owner):
    import importlib
    monkeypatch.setenv("RECOVERY_LINK_NOTIFY", owner)
    from app.realtime import config as cfg
    importlib.reload(cfg)
    return cfg


def _client():
    return RazorpayIntegrationClient(key_id="rzp_test_real", key_secret="s", webhook_secret="w")


# --- the default ---------------------------------------------------------------------------


def test_by_default_razorpay_is_told_not_to_contact_anyone(captured, monkeypatch):
    """The engine owns contact. Razorpay takes the money and says nothing."""
    _reload_config(monkeypatch, "engine")

    _client().create_payment_link(2_500_000, reference_id="r1")

    assert captured["payload"]["notify"] == {"sms": False, "email": False}


def test_by_default_razorpay_runs_no_reminder_cadence_of_its_own(captured, monkeypatch):
    """Razorpay's reminders would compete with the engine's dynamic follow-up timing,
    which is derived per case from the diagnosis, the action and the attempt number."""
    _reload_config(monkeypatch, "engine")

    _client().create_payment_link(2_500_000, reference_id="r1")

    assert captured["payload"]["reminder_enable"] is False


# --- the opt-in ----------------------------------------------------------------------------


def test_the_provider_can_be_given_delivery_explicitly(captured, monkeypatch):
    """A legitimate mode: a real SMS with no Twilio account. It must be asked for."""
    _reload_config(monkeypatch, "razorpay")

    _client().create_payment_link(2_500_000, reference_id="r1")

    assert captured["payload"]["notify"] == {"sms": True, "email": True}


def test_an_unrecognised_value_falls_back_to_the_safe_owner(monkeypatch):
    """A typo in an env var must not silently hand contact to the provider."""
    cfg = _reload_config(monkeypatch, "RAZORPAY_PLEASE")

    assert cfg.LINK_NOTIFY_OWNER == "engine"
    assert cfg.PROVIDER_NOTIFIES is False


def test_the_caller_can_still_override_per_link(captured, monkeypatch):
    _reload_config(monkeypatch, "engine")

    _client().create_payment_link(2_500_000, reference_id="r1", notify=True)

    assert captured["payload"]["notify"] == {"sms": True, "email": True}


# --- no double contact ---------------------------------------------------------------------


def test_the_dispatcher_does_not_also_send_what_razorpay_delivered(tmp_path, monkeypatch):
    """The whole point of the mode. Two messages for one decided rung is the bug."""
    import importlib
    monkeypatch.setenv("RECOVERY_DB_PATH", str(tmp_path / "d.db"))
    monkeypatch.setenv("RECOVERY_DISPATCH_ENABLED", "true")
    _reload_config(monkeypatch, "razorpay")

    from app.cases.csv_ingest import create_cases, parse_csv
    from app.cases.repository import CaseRepository
    from app.dispatch.dispatcher import ChannelDispatcher
    from app.realtime import ingest as ing
    importlib.reload(ing)

    repo = CaseRepository(ing.get_conn())
    case = create_cases(repo, parse_csv(
        "customer_id,name,email,amount,due_date\nU1,A,a@example.com,25000,2026-08-24\n"
    ).valid, merchant_id="m1")[0]

    sent = []
    monkeypatch.setattr("app.dispatch.channels.send_email_smtp",
                        lambda *a, **k: sent.append(a) or None)

    out = ChannelDispatcher(repo.conn, repository=repo).dispatch(
        case.case_id, ActionType.EMAIL_LINK, "k1", body="x")

    assert out.sent is True
    assert out.channel == "RAZORPAY_LINK"
    assert sent == [], "the engine sent its own copy on top of Razorpay's"


def test_a_voice_call_is_still_the_engines_to_place(tmp_path, monkeypatch):
    """Razorpay's notify covers email and SMS for a link. It does not make phone calls,
    so handing it link delivery must not silently disable the IVR rung."""
    import importlib
    monkeypatch.setenv("RECOVERY_DB_PATH", str(tmp_path / "d2.db"))
    monkeypatch.setenv("RECOVERY_DISPATCH_ENABLED", "true")
    _reload_config(monkeypatch, "razorpay")

    from app.cases.csv_ingest import create_cases, parse_csv
    from app.cases.repository import CaseRepository
    from app.dispatch.dispatcher import ChannelDispatcher
    from app.realtime import ingest as ing
    importlib.reload(ing)

    repo = CaseRepository(ing.get_conn())
    case = create_cases(repo, parse_csv(
        "customer_id,name,phone,amount,due_date\nU1,A,9876543210,25000,2026-08-24\n"
    ).valid, merchant_id="m1")[0]

    out = ChannelDispatcher(repo.conn, repository=repo).dispatch(
        case.case_id, ActionType.IVR_CALL, "k2", spoken="hello")

    assert out.channel != "RAZORPAY_LINK"
