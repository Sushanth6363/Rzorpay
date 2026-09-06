"""Agent loop — observe, delegate, act, record (ADR-0026).

THIS IS NOT A SECOND DECISION ENGINE
    It contains no policy. It does not rank actions, weigh cost against uplift, decide when
    to escalate, or judge whether contacting someone is wise. Every one of those questions
    is answered by `RecoveryOrchestrator`, which is unchanged.

    What this does is the plumbing between a durable Case and that engine:

        observe    load the case and build the event the engine expects
        delegate   run the EXISTING pipeline - Stage 0, diagnosis, candidates, safety,
                   escalation ceiling, EV ranking, reservation
        act        obtain a payment link, compose the message, hand it to the dispatcher
        record     write what happened to the case timeline

    The temptation in a system like this is to put "just a little" logic in the loop -
    a special case for overdue invoices, a shortcut when the amount is small. That is how a
    second decision engine gets built by accident, and how the audited one stops being the
    one that decides. So the rule is absolute: if a question is about WHETHER or WHICH, it
    belongs upstream.

INVARIANTS:
1. THE ENGINE DECIDES. This module never selects or overrides an action.
2. THE DISPATCHER GUARDS. Every send goes through ChannelDispatcher, which re-reads case
   state, so a payment that lands between decision and execution still wins.
3. A MISSING LINK IS NOT A SILENT FAILURE. If no payment link can be created, the message
   is not sent with a dead button - it is recorded as blocked, with the reason.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.cases.models import Case, CaseEvent, CaseEventKind
from app.cases.repository import CaseRepository
from app.dispatch.copy import build_message
from app.dispatch.dispatcher import CONTACT_ACTIONS, ChannelDispatcher, DispatchOutcome
from app.domain.enums import ExperimentArm
from app.experiment.policies import build_orchestrator_for_arm
from app.domain.enums import ActionType
from app.ledger.engine import ContactLedgerEngine
from app.orchestration.recovery_orchestrator import RecoveryOrchestrator
from app.payments.link_service import PaymentLinkService

logger = logging.getLogger("recovery.agent")


@dataclass
class CycleResult:
    """One pass of the loop over one case."""

    case_id: str
    action: str = ""
    decision_mode: str = ""
    reasoning: str = ""
    diagnosis: str = ""
    payment_url: str = ""
    dispatch: Dict[str, Any] = field(default_factory=dict)
    skipped_reason: str = ""

    @property
    def contacted(self) -> bool:
        return self.dispatch.get("status") == "SENT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id, "action": self.action,
            "decision_mode": self.decision_mode, "reasoning": self.reasoning,
            "diagnosis": self.diagnosis, "payment_url": self.payment_url,
            "dispatch": self.dispatch, "skipped_reason": self.skipped_reason,
        }


class RecoveryAgent:
    """Runs the observe -> delegate -> act -> record cycle for a case."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        orchestrator: Optional[RecoveryOrchestrator] = None,
        repository: Optional[CaseRepository] = None,
        payments: Optional[PaymentLinkService] = None,
        dispatcher: Optional[ChannelDispatcher] = None,
    ) -> None:
        self.conn = conn
        self.repo = repository or CaseRepository(conn)
        # The live agent must run the SAME configuration that was evaluated. A bare
        # RecoveryOrchestrator carries an UNFITTED CatBoost, which falls back to cold-start
        # baselines and abstains with INSUFFICIENT_TRAINING_DATA - so the scorer being
        # demonstrated would not be the one any published figure describes.
        self.orchestrator = orchestrator or build_orchestrator_for_arm(
            ExperimentArm.A5, db_conn=conn
        )

        # THE QUIET PERIOD IS WALL-CLOCK, AND THE DEMO CLOCK IS NOT.
        #
        # `RECOVERY_FOLLOWUP_HOUR_SECONDS` compresses the follow-up schedule so a review
        # that would take a week takes seconds. It does NOT touch the 24h quiet period,
        # which is measured against real timestamps. So on a compressed clock the ladder
        # can never advance: every follow-up lands seconds after the last contact, the
        # cooldown is always active, the ceiling is held, and the engine re-sends the same
        # rung forever. Observed as two EMAIL_LINK rows and no climb to SMS.
        #
        # `csv_runner` already set cooldown_hours=0 for exactly this path, and the Live
        # test screen already tells the reader that the quiet period is one of the two
        # campaign-pacing controls relaxed there. The durable agent path simply never got
        # it, so the screen's claim was true of the old runner and false of this one.
        #
        # Only relaxed when the clock is compressed. At real timing the quiet period binds
        # exactly as it does in production - it is a customer-protection control, not a
        # demo inconvenience.
        from app.realtime import config as _rt_config
        if getattr(_rt_config, "FOLLOWUP_HOUR_SECONDS", 3600) < 3600:
            from app.pipeline.escalation import EscalationPolicy
            self.orchestrator.pipeline.escalation_policy = EscalationPolicy(cooldown_hours=0)
        self.payments = payments or PaymentLinkService(conn, repository=self.repo)
        self.dispatcher = dispatcher or ChannelDispatcher(conn, repository=self.repo)

    # -- observe ---------------------------------------------------------------------

    def _record_real_ledger_outcome(self, outcome, dispatch, merchant_id: str) -> None:
        """Write the dispatcher's real result into the contact ledger.

        WHY THIS IS NOT COSMETIC
            `get_customer_ledger_history` drives the escalation ceiling and the contact
            budget, and the unrecovered handoff report lists EXECUTED rows as "already
            tried". A row that says EXECUTED for a message nobody received would advance
            the ladder toward a phone call on the strength of an email that never left, and
            would tell a collections agent not to bother re-sending it.

        THE MAPPING
            SENT     -> EXECUTED. A real contact: the ladder may advance, the slot is spent.
            anything -> RELEASED. Nothing reached the customer, so the contact budget must
            else        get its slot back. A dry run, a missing credential and a provider
                        rejection are all the same fact here - no message arrived - and none
                        of them has earned the right to escalate.

        Failure to write is logged, never raised. A dispatch that succeeded must not be
        turned into a failed cycle by bookkeeping performed after it.
        """
        entry = getattr(outcome, "ledger_entry", None)
        if entry is None:
            return

        engine = ContactLedgerEngine(conn=self.conn, merchant_id=merchant_id)
        detail = {
            "channel": dispatch.channel,
            "dispatch_status": dispatch.status,
            "detail": dispatch.reason,
            "provider_id": dispatch.provider_id,
            "source": "ChannelDispatcher",
        }
        try:
            if dispatch.status == "SENT":
                engine.record_execution_result(
                    ledger_id=entry.ledger_id, success=True, metadata=detail,
                )
            else:
                engine.release_reservation(ledger_id=entry.ledger_id, metadata=detail)
        except Exception as exc:  # noqa: BLE001 - bookkeeping must not fail a real send
            logger.warning("could not record real ledger outcome for %s: %s",
                           entry.ledger_id, exc)

    def build_event(self, case: Case) -> Dict[str, Any]:
        """Translate a Case into the raw event the existing pipeline consumes."""
        now = datetime.now(timezone.utc).isoformat()
        # What we can actually reach this customer on. Without these the ladder would
        # offer a phone-only customer an email forever: the send is skipped, the contact
        # is never confirmed, the ceiling never rises, and they are never contacted at all.
        customer = self.repo.get_customer(case.merchant_id, case.customer_id)
        return {
            "has_email": bool(customer and customer.email),
            "has_phone": bool(customer and customer.phone),
            "merchant_id": case.merchant_id,
            "customer_id": case.customer_id,
            "event_id": case.source_event_id or case.case_id,
            "event_type": case.event_type,
            "amount_paise": case.amount_paise,
            "currency": case.currency,
            "occurred_at": case.created_at or now,
            "observed_at": now,
            "gateway": "razorpay",
        }

    # -- one cycle -------------------------------------------------------------------

    def run_cycle(self, case_id: str, random_seed: Optional[int] = None,
                  attempt: int = 0) -> CycleResult:
        """Observe, let the engine decide, act on what it decided, record the result.

        `attempt` distinguishes a follow-up from the first touch. It is 0 for the opening
        contact and 1, 2, 3 for each scheduled reconsideration.

        WHY IT HAS TO REACH THE IDEMPOTENCY KEY
            The payment link is REUSED for the same case and amount, deliberately, so a
            customer never receives two links for one debt. The dispatch key is built from
            case, action and link id - so a follow-up that re-runs the same case produced
            a key identical to the first touch, came back DUPLICATE, and silently sent
            nothing. The ladder then had no new confirmed contact to climb from.

            The original design avoided this by giving a follow-up its own opportunity id
            (`<origin>#f1`). Routing follow-ups through the agent, so that they actually
            dispatch, lost that distinction. Carrying the attempt into the key restores
            it: the same case may be contacted again, on a different rung, without a
            second payment link.
        """

        case = self.repo.get_case(case_id)
        if case is None:
            return CycleResult(case_id=case_id, skipped_reason="unknown case")

        # Cheap pre-check. The dispatcher re-checks again at send time, which is the one
        # that actually matters; this just avoids running the engine on a settled debt.
        if not case.may_contact:
            return CycleResult(
                case_id=case_id,
                skipped_reason=f"case is {case.status.value}; no further contact",
            )

        # DELEGATE. Every decision is made here, by the unchanged engine.
        # defer_execution_result: the orchestrator must NOT stamp the sandbox simulator's
        # outcome into the contact ledger on this path. Nothing has been sent yet, and what
        # eventually goes out is decided by ChannelDispatcher a few lines below. See
        # `_record_real_ledger_outcome`.
        outcome = self.orchestrator.process_and_execute(
            raw_event=self.build_event(case), arm="A5", random_seed=random_seed,
            defer_execution_result=True,
        )
        decision = outcome.decision
        action = decision.selected_action

        result = CycleResult(
            case_id=case_id,
            action=action.value,
            decision_mode=decision.decision_mode.value,
            diagnosis=self._diagnosis(outcome),
            reasoning=self._explain(decision, action),
        )

        self.repo.attach_opportunity(case_id, outcome.opportunity_id)
        self.repo.add_event(CaseEvent(
            case_id=case_id, kind=CaseEventKind.AGENT_DECIDED, actor="agent",
            summary=f"Agent selected {action.value}",
            detail={"reasoning": result.reasoning, "mode": result.decision_mode},
        ))

        if action not in CONTACT_ACTIONS:
            result.skipped_reason = (
                "engine chose not to contact"
                if action == ActionType.NO_ACTION
                else f"{action.value} is not a customer contact"
            )
            return result

        # ACT. A payment request needs somewhere to pay.
        customer = self.repo.get_customer(case.merchant_id, case.customer_id)
        link, note = self.payments.get_or_create_link(
            case,
            customer_name=customer.name if customer else "",
            customer_email=customer.email if customer else "",
            customer_phone=customer.phone if customer else "",
            description=f"Payment of Rs {case.amount_paise / 100:,.2f}",
        )
        if link is None:
            # Sending a payment request with no way to pay wastes the customer's attention
            # and a contact slot, and cannot possibly close the case.
            result.skipped_reason = f"no payment link: {note}"
            result.dispatch = {"status": "BLOCKED", "reason": note}
            self.repo.add_event(CaseEvent(
                case_id=case_id, kind=CaseEventKind.MESSAGE_FAILED, actor="agent",
                summary=f"{action.value} not sent - no payment link could be created",
                detail={"note": note},
            ))
            return result

        result.payment_url = link.short_url

        message = build_message(
            action=action,
            amount_paise=case.amount_paise,
            customer_name=customer.name if customer else "",
            diagnosis_code=result.diagnosis,
            payment_link=link.short_url,
            due_date=case.due_date,
            description=case.description,
        )

        dispatch = self.dispatcher.dispatch(
            case_id=case_id,
            action=action,
            idempotency_key=(
                f"{case_id}:{action.value}:{link.payment_link_id}"
                + (f":f{attempt}" if attempt else "")
            ),
            subject=message.subject,
            body=message.body,
            html_body=message.html,
            spoken=message.spoken,
            payment_url=link.short_url,
        )
        result.dispatch = dispatch.to_dict()

        # The ledger now learns what ACTUALLY happened, from the dispatcher rather than
        # from a simulator. This is what makes the audit trail true on the live path.
        self._record_real_ledger_outcome(outcome, dispatch, case.merchant_id)

        # SCHEDULE THE NEXT LOOK. Without this a CSV-originated case gets exactly ONE
        # contact and then nothing ever happens again - no second touch, no escalation to
        # SMS, no promise-to-pay. The webhook path scheduled follow-ups; this path did not,
        # so "closed loop" was true for webhook cases and false for the CSV path the demo
        # actually uses.
        #
        # Only after a real or dry-run send, never after a block: a message that did not go
        # out has not started a conversation to follow up on.
        if dispatch.status in ("SENT", "SKIPPED"):
            from app.realtime import followup

            due = followup.schedule(
                opportunity_id=case_id,
                merchant_id=case.merchant_id,
                customer_id=case.customer_id,
                origin_event_id=case.source_event_id or case_id,
                event=self.build_event(case),
                diagnosis_code=result.diagnosis or None,
                last_action=action,
                attempt=0,
            )
            if due:
                self.repo.add_event(CaseEvent(
                    case_id=case_id, kind=CaseEventKind.FOLLOWUP_SCHEDULED, actor="agent",
                    summary=f"Next review scheduled for {due[:16].replace('T', ' ')} UTC",
                    detail={"next_touch_at": due, "after_action": action.value},
                ))

        return result

    def run_batch(
        self, case_ids: List[str], random_seed: Optional[int] = None
    ) -> List[CycleResult]:
        return [self.run_cycle(cid, random_seed=random_seed) for cid in case_ids]

    # -- helpers ---------------------------------------------------------------------

    @staticmethod
    def _diagnosis(outcome: Any) -> str:
        """Stage 1's verdict, read off the result the orchestrator returned."""
        return str(getattr(outcome, "diagnosis_code", "") or "")

    @staticmethod
    def _explain(decision: Any, action: ActionType) -> str:
        """Read the reasoning off the executed decision rather than composing one."""
        if action == ActionType.NO_ACTION:
            reason = getattr(decision, "abstention_reason", None)
            value = getattr(reason, "value", "") if reason else ""
            if value and value != "NONE":
                return f"Abstained: {value.replace('_', ' ').lower()}."
            return "Abstained: no action had positive expected value over doing nothing."
        score = getattr(decision, "selected_action_score", None)
        if score is None:
            return f"Chose {action.value}."
        return (
            f"Chose {action.value}: estimated uplift {score.incremental_effect:+.1%} over "
            f"no action, worth Rs {score.incremental_value_paise / 100:,.0f}, minus Rs "
            f"{score.action_cost_paise / 100:,.2f} cost = EV Rs "
            f"{score.expected_value_paise / 100:,.0f}."
        )
