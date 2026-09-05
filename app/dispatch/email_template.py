"""HTML email rendering — the PAY NOW message a customer actually receives (ADR-0024).

EMAIL HTML IS NOT WEB HTML
    Gmail strips <style> blocks in some contexts, Outlook renders through Word's engine,
    and neither flexbox nor grid is reliable. So this template is deliberately old
    fashioned: table layout, inline styles, fixed 600px width, no external assets. It looks
    like 2005 markup because that is what survives an email client in 2026.

    No remote images either. A tracking pixel or a hosted logo triggers "images are
    blocked" in most clients, which turns a payment request into a broken-looking message
    at exactly the moment trust matters most.

THE BUTTON
    Rendered as a table cell with a background colour rather than a styled <a>, because
    Outlook ignores padding on inline anchors and the button collapses to bare text. The
    URL is ALSO printed in full underneath: a button that fails to render must still leave
    the customer a way to pay, and some clients strip anchors entirely.

INVARIANTS:
1. THE LINK IS THE ONLY CALL TO ACTION. No upsell, no survey, no secondary link competing
   with payment.
2. NEVER FABRICATES URGENCY. No countdown, no invented deadline, no threatened
   consequence. Tone escalation is handled by copy.py and stays within what the merchant
   can actually say.
3. PLAIN TEXT IS A REAL FALLBACK, never a stub. A client that cannot render HTML must
   still receive a usable payment URL.
4. IDENTIFIABLE AND DECLINABLE. Sender is named; opting out is stated.
"""

from __future__ import annotations

import html as _html
import os

BRAND = "#4338CA"
INK = "#1F2937"
MUTED = "#6B7280"
HAIRLINE = "#E5E7EB"


def merchant_name() -> str:
    """Who the customer thinks is asking. Configurable; never invented per-message."""
    return os.environ.get("MERCHANT_NAME", "Unified Recovery Engine (demo)")


def render_payment_email(
    *,
    greeting: str,
    opener: str,
    ask: str,
    closer: str,
    amount_paise: int,
    payment_url: str = "",
    signature: str = "",
) -> str:
    """Compose the HTML body. Every caller-supplied string is escaped."""
    amount = f"&#8377;{amount_paise / 100:,.2f}"
    merchant = _html.escape(merchant_name())

    def e(text: str) -> str:
        """Escape, then render currency as the rupee sign.

        The shared copy says "Rs 25,000.00" because that string is also sent over SMS,
        where a non-GSM-7 character silently doubles the message cost. HTML has no such
        constraint, and a header reading Rs 25,000 next to a body reading Rs 25,000 while
        the heading shows the symbol looks like two systems wrote the message.
        """
        return _html.escape(text).replace("Rs ", "&#8377;")

    if payment_url:
        # Escaped with quote=True because it lands inside an href attribute, and WITHOUT
        # the currency substitution above - a URL is not prose.
        safe_url = _html.escape(payment_url, quote=True)
        # Table-cell button: survives Outlook, which ignores padding on inline anchors.
        button = f"""
      <table role="presentation" cellpadding="0" cellspacing="0" border="0"
             style="margin:28px auto 12px;">
        <tr>
          <td align="center" bgcolor="{BRAND}" style="border-radius:6px;">
            <a href="{safe_url}"
               style="display:inline-block;padding:15px 44px;font-family:Arial,Helvetica,sans-serif;
                      font-size:16px;font-weight:bold;color:#FFFFFF;text-decoration:none;
                      border-radius:6px;">PAY NOW</a>
          </td>
        </tr>
      </table>
      <p style="margin:0 0 22px;font-family:Arial,Helvetica,sans-serif;font-size:12px;
                line-height:1.6;color:{MUTED};text-align:center;word-break:break-all;">
        Or copy this link into your browser:<br>
        <a href="{safe_url}" style="color:{BRAND};">{safe_url}</a>
      </p>"""
    else:
        # No link is a real state, not an error to paper over. Say so plainly rather than
        # render a dead button the customer will click and blame themselves for.
        button = f"""
      <p style="margin:24px 0;padding:14px;background:#FEF3C7;border-radius:6px;
                font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#92400E;">
        A payment link could not be generated for this message. Please contact
        {merchant} directly to complete your payment.
      </p>"""

    return f"""<!-- plain, table-based markup: this has to survive an email client -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background:#F3F4F6;padding:24px 12px;">
  <tr><td align="center">
    <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
           style="max-width:600px;background:#FFFFFF;border:1px solid {HAIRLINE};
                  border-radius:10px;">
      <tr><td style="padding:28px 34px 0;">
        <p style="margin:0 0 4px;font-family:Arial,Helvetica,sans-serif;font-size:13px;
                  color:{MUTED};">{merchant}</p>
        <p style="margin:0 0 20px;font-family:Arial,Helvetica,sans-serif;font-size:22px;
                  font-weight:bold;color:{INK};">Payment pending &#183; {amount}</p>

        <p style="margin:0 0 14px;font-family:Arial,Helvetica,sans-serif;font-size:15px;
                  line-height:1.65;color:{INK};">{e(greeting)}</p>
        <p style="margin:0 0 14px;font-family:Arial,Helvetica,sans-serif;font-size:15px;
                  line-height:1.65;color:{INK};">{e(opener)}</p>
        <p style="margin:0 0 6px;font-family:Arial,Helvetica,sans-serif;font-size:15px;
                  line-height:1.65;color:{INK};">{e(ask)}</p>
      </td></tr>

      <tr><td style="padding:0 34px;">{button}</td></tr>

      <tr><td style="padding:0 34px 26px;">
        <p style="margin:0 0 18px;font-family:Arial,Helvetica,sans-serif;font-size:14px;
                  line-height:1.6;color:{MUTED};">{e(closer)}</p>
        <hr style="border:none;border-top:1px solid {HAIRLINE};margin:0 0 14px;">
        <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:11px;
                  line-height:1.6;color:{MUTED};">{e(signature).replace(chr(10), '<br>')}</p>
      </td></tr>
    </table>
  </td></tr>
</table>"""
