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
        self.payments = payments or PaymentLinkService(conn, repository=self.repo)
        self.dispatcher = dispatcher or ChannelDispatcher(conn, repository=self.repo)

    # -- observe ---------------------------------------------------------------------

    def build_event(self, case: Case) -> Dict[str, Any]:
        """Translate a Case into the raw event the existing pipeline consumes."""
        now = datetime.now(timezone.utc).isoformat()
        return {
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

    def run_cycle(self, case_id: str, random_seed: Optional[int] = None) -> CycleResult:
        """Observe, let the engine decide, act on what it decided, record the result.

        `random_seed` defaults to None, which is correct for live traffic: epsilon
        exploration is a real feature (ADR-0004) and live decisions are not a replay. It
        also means the agent is deliberately NON-DETERMINISTIC - on a small fraction of
        cases it will explore and abstain. Tests pass a seed so a probabilistic branch does
        not turn into an intermittent failure that gets "fixed" by rerunning.
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
        outcome = self.orchestrator.process_and_execute(
            raw_event=self.build_event(case), arm="A5", random_seed=random_seed,
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
        )

        dispatch = self.dispatcher.dispatch(
            case_id=case_id,
            action=action,
            idempotency_key=f"{case_id}:{action.value}:{link.payment_link_id}",
            subject=message.subject,
            body=message.body,
            html_body=message.html,
            spoken=message.spoken,
            payment_url=link.short_url,
        )
        result.dispatch = dispatch.to_dict()

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
