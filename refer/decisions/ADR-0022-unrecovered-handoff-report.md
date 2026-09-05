# ADR-0022 — The unrecovered handoff report is a first-class output

- **Status:** ACCEPTED
- **Date:** 2026-09-05 *(recorded retrospectively; the decision was made when the module was written)*
- **Affects:** reporting, claims, operations
- **Code:** `app/reporting/unrecovered.py`
- **Related:** ADR-0015 (escalation ladder), ADR-0021 (follow-up timing), ADR-0027 (case board)

## Context

Every recovery product demonstrates the same thing: the customers it recovered. That number
is the easy half, and on its own it is close to meaningless, because a system that contacts
everyone forever will also show a recovery number.

The harder and more useful output is the **list of people the engine could not recover**.
It is what a merchant actually has to act on, it is where the residual money is, and it is
the only output that a system cannot fake by trying harder.

It also matters for a reason specific to this design. ADR-0015 makes the engine *stop*:
four follow-ups, a 30-day window, a contact budget, an escalation ceiling. Stopping is
correct, but stopping silently would mean the debt simply evaporates from view. A bounded
engine that does not hand over what it abandoned has not been careful; it has been
forgetful.

## Decision

Export every case that has been contacted as far as policy allows and remains unpaid, with
**what was already tried** attached: the channels used, how many confirmed contacts were
made, the last contact time, and the amount outstanding.

Customers who paid are excluded **by construction** rather than by filtering, so the report
cannot drift into listing someone who settled while it was being generated.

The report is a spreadsheet because its reader is a collections agent, not an engineer.

## Consequences

- A human picking up the case does not re-send the email the engine already sent three
  times. That is the difference between a handoff and a dump.
- The report doubles as an honest measure of the engine's ceiling: its length is the part
  of the funnel automation did not solve.
- Because it reads the contact ledger rather than the dispatch log, its "already tried"
  column inherits whatever the ledger records. See the limitation below.

## Known limitation, stated

The report's "channels tried" column is built from `contact_ledger` rows whose status is
`EXECUTED` or `RECONCILED_DELIVERED`. In the **live** path the ledger currently records the
sandbox simulator's execution result rather than the dispatcher's, which means a dry-run
case can appear in this report as though it had been contacted.

The consequence is bounded but real: a collections agent could be told an email was sent
that was never sent. That is the wrong direction of error for this particular artifact,
whose entire value is that its "already tried" column is trustworthy.

This is a known defect against the audit-trail bar, recorded here rather than left for a
reviewer to find. The fix is to source the ledger's execution result from
`ChannelDispatcher` in the live path while leaving the experiment path untouched, since in
the sandbox the simulator's outcome genuinely *is* the observed outcome.

## Alternatives considered

- **No handoff at all.** The default in most demos. It makes the recovery number look
  better and makes the product less useful, which is the wrong trade for a track judged on
  an audit trail.
- **Handing over everything unpaid, immediately.** Defeats the purpose: the point is that
  automation exhausted its options first, so a person's time goes to cases automation
  cannot reach.
- **A dashboard view instead of an export.** A collections team does not work inside our
  dashboard. The output has to leave the system in a format their process already accepts.
