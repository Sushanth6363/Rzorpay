# ADR-0024 — HTML email built for mail clients, not for browsers

- **Status:** ACCEPTED
- **Date:** 2026-09-05 *(recorded retrospectively; the decision was made when the module was written)*
- **Affects:** dispatch, deliverability
- **Code:** `app/dispatch/email_template.py`, `app/dispatch/copy.py`
- **Related:** ADR-0021 (rung-aware copy), ADR-0025 (CSV is the source of truth)

## Context

The email is not a side effect of the decision. For a merchant-uploaded receivable it **is**
the product: the only thing the customer ever sees, and the only surface where a correct
decision turns into money.

Email clients are not browsers. Gmail strips `<style>` blocks, Outlook renders through
Word's HTML engine, and most clients block remote images by default until the reader opts
in. A layout written the way a web page is written degrades in each of them differently,
and the usual result is a call-to-action that does not render.

That failure is silent and expensive. The engine records `SENT`, the dispatch log is green,
the ledger advances the escalation ladder — and the customer received a message with no
visible way to pay.

## Decision

Render the message as email, with the constraints that implies:

- **Table-based layout.** Not flexbox, not grid. Tables are the only layout primitive every
  major client renders consistently.
- **Inline styles only.** No `<style>` block, because Gmail removes it.
- **No remote images.** A button drawn as an image disappears behind the default
  image-blocking of most clients. The call to action is a styled table cell with a real
  link, so it renders whatever the client permits.
- **The payment URL appears twice**: once as the button, and once as visible plain text
  beneath it. If every style in the message is stripped, the customer can still see, copy
  and use the link. This is the single most important line in the file.
- **A plain-text alternative** accompanies every HTML body, so text-only clients and
  aggressive spam filters both see a coherent message.
- **Content comes from `copy.py`**, so tone-by-rung and ask-by-diagnosis (ADR-0021) apply
  identically across channels and the email cannot drift from the SMS.

Amounts, names and due dates are read back from the `Case` and `Customer` records created
from the merchant's CSV (ADR-0025). Nothing downstream re-enters a number by hand, so the
email cannot disagree with the file the merchant uploaded.

## Consequences

- The message survives style stripping, image blocking, and Outlook. In the degenerate case
  it is still a readable sentence with a usable URL.
- The template is testable without a mail client: the tests assert that the payment URL is
  present as text, that there is exactly one call to action, and that no remote resource is
  referenced.
- It is plainer than a marketing email. That is appropriate — this is a transactional
  message about money owed, and a designed-looking invoice chase reads as promotional,
  which is also how filters classify it.

## Alternatives considered

- **A templating library with a component framework.** Solves a problem this project does
  not have, and adds a dependency to render roughly forty lines of table.
- **Image-based button.** Better looking when it renders, invisible when it does not. The
  failure mode is the entire point of the email disappearing.
- **Plain text only.** Robust, and it forfeits the one-tap call to action that carries most
  of the conversion. The dual-format message keeps both properties.
