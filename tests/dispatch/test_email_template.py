"""The PAY NOW email (ADR-0024).

This is the one artifact a customer actually reads, so the tests are about what survives an
email client and what must never appear in a payment request.
"""

import pytest

from app.dispatch.copy import build_message
from app.dispatch.email_template import render_payment_email
from app.domain.enums import ActionType, DiagnosisCode

LINK = "https://rzp.io/rzp/VetN7aJ"


def _email(amount=2_500_000, name="Rahul", diagnosis=DiagnosisCode.CARD_DECLINED.value,
           link=LINK):
    return build_message(ActionType.EMAIL_LINK, amount, name, diagnosis, payment_link=link)


# --- The call to action -------------------------------------------------------------------


def test_the_email_carries_a_pay_now_button_pointing_at_the_link():
    m = _email()

    assert "PAY NOW" in m.html
    assert f'href="{LINK}"' in m.html


def test_the_url_is_also_printed_in_full():
    """Some clients strip anchors entirely. A button that does not render must still leave
    the customer a way to pay."""
    m = _email()

    assert m.html.count(LINK) >= 2


def test_the_payment_link_is_the_only_call_to_action():
    """No upsell or survey competing with payment."""
    import re

    hrefs = re.findall(r'href="([^"]+)"', _email().html)

    assert hrefs, "the email must contain at least one link"
    assert set(hrefs) == {LINK}  # every href is the payment link, nothing else


def test_a_missing_link_says_so_instead_of_rendering_a_dead_button():
    """A dead button gets clicked, fails, and the customer blames themselves."""
    m = _email(link="")

    assert "PAY NOW" not in m.html
    assert "could not be generated" in m.html


# --- Surviving an email client -------------------------------------------------------------


def test_the_layout_is_table_based():
    """Flexbox and grid are not reliable in email clients."""
    assert "<table" in _email().html


def test_there_are_no_remote_images():
    """A blocked image turns a payment request into a broken-looking message at exactly
    the moment trust matters most."""
    assert "<img" not in _email().html


def test_styles_are_inline():
    m = _email()

    assert "style=" in m.html
    assert "<style" not in m.html


def test_html_uses_the_rupee_sign_while_plain_text_stays_ascii():
    """Plain text is also sent over SMS, where a non-GSM-7 character silently doubles the
    message cost. HTML has no such constraint."""
    m = _email()

    assert "&#8377;" in m.html
    assert "Rs 25,000.00" in m.body
    assert "₹" not in m.body


def test_the_plain_text_fallback_is_usable_on_its_own():
    """A client that cannot render HTML must still receive a payment URL, not a stub."""
    m = _email()

    assert LINK in m.body
    assert len(m.body) > 100


# --- Safety of content ----------------------------------------------------------------------


def test_a_hostile_customer_name_is_escaped():
    """A name arrives from a merchant CSV and is not trusted input."""
    m = _email(name="<script>alert(1)</script>")

    assert "<script>" not in m.html


def test_a_hostile_url_cannot_break_out_of_the_href():
    m = _email(link='https://x.com/" onclick="evil()')

    assert 'onclick="evil()"' not in m.html


def test_the_email_never_fabricates_urgency_or_a_threat():
    """The engine has no authority to threaten anything, and manufacturing pressure to
    lift a recovery rate is the behaviour these controls exist to prevent."""
    forbidden = ("final notice", "legal action", "penalty", "suspend",
                 "within 24 hours", "act now", "last chance")

    for diagnosis in (DiagnosisCode.CARD_DECLINED.value,
                      DiagnosisCode.INVOICE_OVERDUE.value,
                      DiagnosisCode.INSUFFICIENT_FUNDS.value):
        html = _email(diagnosis=diagnosis).html.lower()
        for phrase in forbidden:
            assert phrase not in html, f"{diagnosis} email contains '{phrase}'"


def test_the_sender_is_identified_and_opting_out_is_offered():
    m = _email()

    assert "on behalf of the merchant" in m.html
    assert "STOP" in m.html


def test_the_merchant_name_is_configurable(monkeypatch):
    monkeypatch.setenv("MERCHANT_NAME", "ABC Pvt Ltd")

    html = render_payment_email(
        greeting="Hi", opener="o", ask="a", closer="c",
        amount_paise=100, payment_url=LINK, signature="s",
    )

    assert "ABC Pvt Ltd" in html


# --- Only email gets HTML --------------------------------------------------------------------


@pytest.mark.parametrize("action", [
    ActionType.SMS_LINK, ActionType.WHATSAPP_LINK,
    ActionType.IVR_CALL, ActionType.AGENT_DIAL,
])
def test_non_email_channels_get_no_html(action):
    """Sending markup down an SMS would be nonsense."""
    m = build_message(action, 100_000, "Sam", DiagnosisCode.UNKNOWN.value, payment_link=LINK)

    assert m.html == ""
