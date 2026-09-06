"""Compliant Escalation Policy — bounded intensity, one rung at a time (ADR-0015).

WHAT "COMPLIANT ESCALATION" MEANS HERE
    Recovery outreach has an intensity ladder. An email is not a phone call; a human agent
    dialling a customer is not an SMS. A recovery system that jumps straight to the loudest
    channel because its model scored it highest is not recovering revenue, it is harassing
    a customer who may simply not have seen the first message.

    Compliant escalation is the constraint that intensity may only rise:
      - by ONE rung at a time, never skipping,
      - only after the previous rung was CONFIRMED delivered,
      - only after a quiet period has elapsed,
      - and never past the top of the ladder.

    All four are enforced here, before scoring sees the candidate set. The model chooses
    among what policy permits; it never chooses what policy permits.

INVARIANTS:
1. SUBTRACTIVE ONLY. This policy can REMOVE eligibility. It can never grant it. A candidate
   already SAFETY_REJECTED by the hard safety filter passes through untouched and rejected.
   Escalation is a VALUE control layered under SAFETY controls, never over them.
2. EVIDENCE-GATED. Only a contact in a confirmed-sent terminal ledger state raises the
   ceiling. An EXECUTION_UNKNOWN attempt does NOT: you may not escalate on a message you
   cannot prove reached anyone. This is the conservative direction - unknowns hold the
   ladder still rather than advance it.
3. ONE RUNG. ceiling = highest_confirmed_rung + 1. Never +2, whatever the score says.
4. NO CAPACITY CREATED. An escalated contact still reserves a slot against the same
   per-customer budget. Escalation changes WHICH action may be taken, never HOW MANY.
5. DETERMINISTIC. Same history and same decision timestamp produce the same ceiling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence

from app.domain.enums import ActionType, EligibilityStatus, LedgerStatus, SafetyRejectReason
from app.domain.models import ActionCandidate, ContactLedgerEntry

# The ladder, quietest first. Position in this list IS the rung number.
# NO_ACTION and RECOMMEND_RETRY are deliberately absent: NO_ACTION is the counterfactual
# anchor and RECOMMEND_RETRY is a message to the payment infrastructure, not to a person
# (ADR-0006). Neither has an intensity, so neither can be escalated to or through.
ESCALATION_LADDER: List[ActionType] = [
    ActionType.EMAIL_LINK,      # rung 0 - lowest intensity, asynchronous, ignorable
    ActionType.SMS_LINK,        # rung 1
    ActionType.WHATSAPP_LINK,   # rung 2 - interactive, expects a reply
    ActionType.IVR_CALL,        # rung 3 - interrupts the customer
    ActionType.AGENT_DIAL,      # rung 4 - a person calls a person
]

# What each rung physically requires to reach a person. A ladder that ignores this walks
# a phone-only customer up to a rung they can never receive and then stops forever: the
# contact is never confirmed, so the ceiling never rises, so nothing is ever sent. Observed
# before this was added - a customer with a valid phone and no email was contacted zero
# times, indefinitely, while their debt sat recoverable.
RUNG_REQUIRES: Dict[ActionType, str] = {
    ActionType.EMAIL_LINK: "email",
    ActionType.SMS_LINK: "phone",
    ActionType.WHATSAPP_LINK: "phone",
    ActionType.IVR_CALL: "phone",
    ActionType.AGENT_DIAL: "phone",
}


def reachable_rungs(has_email: Optional[bool], has_phone: Optional[bool]) -> List[int]:
    """Rungs this customer can actually receive, lowest first.

    Either argument being None means "not known" - which is the case for every synthetic
    event in the experiment, none of which carry contact details. Unknown is treated as
    reachable, so the evaluated path behaves exactly as it did before reachability existed.
    """
    if has_email is None and has_phone is None:
        return list(range(len(ESCALATION_LADDER)))
    out: List[int] = []
    for rung, action in enumerate(ESCALATION_LADDER):
        need = RUNG_REQUIRES.get(action)
        if need == "email" and has_email is False:
            continue
        if need == "phone" and has_phone is False:
            continue
        out.append(rung)
    return out


RUNG_OF: Dict[ActionType, int] = {a: i for i, a in enumerate(ESCALATION_LADDER)}
TOP_RUNG = len(ESCALATION_LADDER) - 1

# Ledger states that count as PROOF a contact reached the customer. Anything else -
# unknown, not-sent, released, expired, still reserved - does not advance the ladder.
CONFIRMED_SENT_STATES = frozenset({
    LedgerStatus.EXECUTED,
    LedgerStatus.RECONCILED_DELIVERED,
})

# Quiet period between rungs. A customer who has not answered an email in twenty minutes
# has not refused to pay; they have not read their email. Escalating inside this window
# converts a recovery attempt into pressure.
DEFAULT_COOLDOWN_HOURS = 24

# ENTRY RUNG — where a customer with no contact history may be met, per stream.
#
# A blanket "always open with email" is not more compliant, it is just less useful: a
# customer whose card declined ten seconds ago is mid-transaction, and an SMS carrying a
# retry link is the expected medium, not an escalation. A B2B invoice thirty days overdue
# is an accounts-payable matter and belongs in email. The rule that matters is the CEILING
# on how loud the FIRST touch can be, and that ceiling is hard:
#
#   INVARIANT: no stream may open above MAX_ENTRY_RUNG. IVR_CALL and AGENT_DIAL can only
#   ever be reached by earned escalation from a confirmed prior contact. The engine never
#   opens a relationship with a phone call.
MAX_ENTRY_RUNG = 1  # SMS_LINK. Rungs 2+ must be earned, never granted at entry.

STREAM_ENTRY_RUNG: Dict[str, int] = {
    "FAILED_PAYMENT": 1,                # mid-transaction; SMS retry link is the medium
    "FAILED_SUBSCRIPTION_RENEWAL": 1,   # active mandate; same reasoning
    "AUTOPAY_FAILURE": 1,
    "ABANDONED_CHECKOUT": 0,            # never completed a purchase; email only
    "OVERDUE_B2B_INVOICE": 0,           # accounts payable is an email relationship
    "PAYMENT_DOWNTIME": 0,
    "SIMULATED_FAILURE": 0,
}
DEFAULT_ENTRY_RUNG = 0


def entry_rung_for_stream(event_type_value: Optional[str]) -> int:
    """Resolve the first-touch ceiling for a stream, hard-capped at MAX_ENTRY_RUNG."""
    rung = STREAM_ENTRY_RUNG.get(str(event_type_value or ""), DEFAULT_ENTRY_RUNG)
    return min(rung, MAX_ENTRY_RUNG)


@dataclass(frozen=True)
class EscalationAssessment:
    """The escalation decision and the evidence behind it. Written to the audit trail."""

    highest_confirmed_rung: int          # -1 when no confirmed contact exists
    allowed_max_rung: int                # inclusive ceiling this decision may reach
    confirmed_contact_count: int
    last_confirmed_contact_at: Optional[str]
    cooldown_active: bool
    cooldown_hours: int
    ladder: List[str] = field(default_factory=lambda: [a.value for a in ESCALATION_LADDER])
    suppressed_actions: List[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ladder": list(self.ladder),
            "highest_confirmed_rung": self.highest_confirmed_rung,
            "highest_confirmed_action": (
                ESCALATION_LADDER[self.highest_confirmed_rung].value
                if self.highest_confirmed_rung >= 0
                else None
            ),
            "allowed_max_rung": self.allowed_max_rung,
            "allowed_max_action": (
                ESCALATION_LADDER[self.allowed_max_rung].value
                if 0 <= self.allowed_max_rung <= TOP_RUNG
                else None
            ),
            "confirmed_contact_count": self.confirmed_contact_count,
            "last_confirmed_contact_at": self.last_confirmed_contact_at,
            "cooldown_active": self.cooldown_active,
            "cooldown_hours": self.cooldown_hours,
            "suppressed_actions": list(self.suppressed_actions),
            "explanation": self.explanation,
        }


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp, returning None when it cannot be read.

    An unparseable timestamp must NOT silently disable the cooldown - the caller treats
    None as "cannot prove the quiet period has elapsed" and holds the ladder still.
    """
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


class EscalationPolicy:
    """Bounds recovery intensity to one rung above the last CONFIRMED contact."""

    def __init__(self, cooldown_hours: int = DEFAULT_COOLDOWN_HOURS) -> None:
        self.cooldown_hours = cooldown_hours

    # -- Assessment -------------------------------------------------------------------

    def assess(
        self,
        history: Sequence[ContactLedgerEntry],
        decision_timestamp: str,
        event_type_value: Optional[str] = None,
        has_email: Optional[bool] = None,
        has_phone: Optional[bool] = None,
    ) -> EscalationAssessment:
        """Compute the permitted ceiling from confirmed contact history.

        `has_email` / `has_phone` bound the ladder to rungs that can actually reach this
        customer. Both default to None - not known - which preserves the previous
        behaviour exactly for callers that do not know, including every experiment arm.
        """
        reachable = reachable_rungs(has_email, has_phone)
        entry_rung = entry_rung_for_stream(event_type_value)
        # An unreachable entry rung is not a reason to contact nobody. Meet the customer at
        # the lowest rung that can actually reach them.
        if entry_rung not in reachable and reachable:
            entry_rung = min(r for r in reachable if r >= entry_rung) if any(
                r >= entry_rung for r in reachable) else max(reachable)
        highest = -1
        confirmed = 0
        last_at: Optional[str] = None

        for entry in history:
            if entry.status not in CONFIRMED_SENT_STATES:
                continue
            rung = RUNG_OF.get(entry.action_type)
            if rung is None:
                continue  # off-ladder action (e.g. RECOMMEND_RETRY): no intensity
            confirmed += 1
            if rung > highest:
                highest = rung
            stamp = entry.resolved_at or entry.attempted_at or entry.updated_at
            if stamp and (last_at is None or stamp > last_at):
                last_at = stamp

        # No confirmed contact yet: the customer may be met only at this stream's entry
        # rung, which is hard-capped at MAX_ENTRY_RUNG. A first touch is never a call.
        if highest < 0:
            return EscalationAssessment(
                highest_confirmed_rung=-1,
                allowed_max_rung=entry_rung,
                confirmed_contact_count=0,
                last_confirmed_contact_at=None,
                cooldown_active=False,
                cooldown_hours=self.cooldown_hours,
                explanation=(
                    f"No confirmed prior contact. First touch for stream "
                    f"'{event_type_value or 'UNKNOWN'}' is capped at rung {entry_rung} "
                    f"({ESCALATION_LADDER[entry_rung].value}); rungs above "
                    f"{MAX_ENTRY_RUNG} must be earned by escalation."
                ),
            )

        # Quiet period: escalation may not happen inside the cooldown window. The current
        # rung remains available - a repeat at the same intensity is not an escalation -
        # but the ladder does not advance.
        now = _parse_iso(decision_timestamp)
        last = _parse_iso(last_at)
        cooldown_active = False
        if now is not None and last is not None:
            cooldown_active = (now - last) < timedelta(hours=self.cooldown_hours)
        elif last_at is not None:
            # Timestamps present but unreadable: cannot prove the window elapsed, so
            # assume it has not. Conservative direction.
            cooldown_active = True

        # The entry rung is a floor as well as a first-touch cap: a customer whose only
        # confirmed contact was an email may still be sent the SMS their stream permits.
        # It never raises the ceiling above highest+1.
        highest = max(highest, entry_rung - 1)

        if cooldown_active:
            ceiling = highest
            explanation = (
                f"Last confirmed contact at rung {highest} "
                f"({ESCALATION_LADDER[highest].value}) was inside the "
                f"{self.cooldown_hours}h quiet period. Intensity is held; no escalation."
            )
        else:
            # The next rung the customer can actually receive, not merely the next
            # number. Skipping an unreachable rung is not escalating by two: the skipped
            # rung could never have delivered anything.
            above = [r for r in reachable if r > highest]
            ceiling = min(above) if above else min(highest, TOP_RUNG)
            if ceiling == highest:
                explanation = (
                    f"Already at the top of the ladder "
                    f"({ESCALATION_LADDER[TOP_RUNG].value}). No further escalation exists."
                )
            else:
                explanation = (
                    f"{confirmed} confirmed contact(s), highest at rung {highest} "
                    f"({ESCALATION_LADDER[highest].value}). Quiet period elapsed, so "
                    f"intensity may rise ONE rung to {ESCALATION_LADDER[ceiling].value}."
                )

        return EscalationAssessment(
            highest_confirmed_rung=highest,
            allowed_max_rung=ceiling,
            confirmed_contact_count=confirmed,
            last_confirmed_contact_at=last_at,
            cooldown_active=cooldown_active,
            cooldown_hours=self.cooldown_hours,
            explanation=explanation,
        )

    # -- Application ------------------------------------------------------------------

    def apply(
        self,
        candidates: List[ActionCandidate],
        history: Sequence[ContactLedgerEntry],
        decision_timestamp: str,
        event_type_value: Optional[str] = None,
        has_email: Optional[bool] = None,
        has_phone: Optional[bool] = None,
    ) -> tuple:
        """Return (candidates_with_ceiling_applied, assessment).

        SUBTRACTIVE ONLY (INV-1 of this module): a candidate that is already
        SAFETY_REJECTED is passed through unchanged. This policy never promotes.
        """
        assessment = self.assess(history, decision_timestamp, event_type_value,
                                 has_email=has_email, has_phone=has_phone)
        ceiling = assessment.allowed_max_rung
        suppressed: List[str] = []
        out: List[ActionCandidate] = []

        for candidate in candidates:
            rung = RUNG_OF.get(candidate.action_type)

            # Off-ladder (NO_ACTION, RECOMMEND_RETRY) or already rejected: untouched.
            if rung is None or candidate.eligibility != EligibilityStatus.ELIGIBLE:
                out.append(candidate)
                continue

            if rung <= ceiling:
                out.append(candidate)
                continue

            reason = (
                SafetyRejectReason.ESCALATION_COOLDOWN
                if assessment.cooldown_active
                else SafetyRejectReason.ESCALATION_CEILING
            )
            suppressed.append(candidate.action_type.value)
            out.append(
                ActionCandidate(
                    action_type=candidate.action_type,
                    eligibility=EligibilityStatus.SAFETY_REJECTED,
                    reject_reason=reason,
                    reason_explanation=(
                        f"'{candidate.action_type.value}' is rung {rung}; escalation "
                        f"ceiling for this customer is rung {ceiling} "
                        f"({ESCALATION_LADDER[ceiling].value}). {assessment.explanation}"
                    ),
                    evidence={
                        "candidate_rung": rung,
                        "allowed_max_rung": ceiling,
                        "highest_confirmed_rung": assessment.highest_confirmed_rung,
                        "cooldown_active": assessment.cooldown_active,
                    },
                    is_counterfactual=False,
                )
            )

        return out, EscalationAssessment(
            highest_confirmed_rung=assessment.highest_confirmed_rung,
            allowed_max_rung=assessment.allowed_max_rung,
            confirmed_contact_count=assessment.confirmed_contact_count,
            last_confirmed_contact_at=assessment.last_confirmed_contact_at,
            cooldown_active=assessment.cooldown_active,
            cooldown_hours=assessment.cooldown_hours,
            suppressed_actions=suppressed,
            explanation=assessment.explanation,
        )
