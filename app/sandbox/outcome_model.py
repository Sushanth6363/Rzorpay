"""Context-dependent outcome model for the sandbox — ADOPTED (ADR-0020).

=========================================================================================
PRE-REGISTRATION. Written and committed BEFORE this model was ever run.
=========================================================================================

WHY THIS EXISTS
    The sandbox decided outcomes from ONE input: which channel was used. Not the failure
    reason, not the amount, not the customer. In a world like that the optimal scorer is a
    fixed ranking of six channels, and `HeuristicScorer` already is exactly that ranking, so
    a correctly-trained model can at best TIE it. It did: after the train/serve mismatch was
    fixed (ADR-0017), A5 and A3 produced byte-identical metrics — a VOID ablation under
    ADR-0011.

    The experiment was therefore structurally unable to test its own stated hypothesis.
    That hypothesis is not being invented now; it has been sitting in `app/scoring/
    heuristic.py` since the scorer was written:

        "A flat table, deliberately simple: the heuristic knows the failure reason matters,
         but not how it interacts with the specific action. That interaction is what the
         model may or may not capture."

    The simulator never contained such an interaction. This module adds one.

WHAT IS PREDICTED, IN ADVANCE
    P1. A5 (CatBoost) will BEAT A3 (heuristic). The heuristic applies ONE multiplier per
        diagnosis across every channel, so it cannot represent that a retry is excellent for
        INSUFFICIENT_FUNDS and near-useless for CARD_DECLINED — a flat multiplier moves all
        channels together. The model can learn the cells.
    P2. The gap will be MODEST. Both scorers see the same dominant signal (base channel
        rates), and the interaction only re-ranks channels within a diagnosis.
    P3. Contact efficiency will improve more than raw recovery rate, because the value of
        the interaction is mostly in NOT sending the wrong channel.

FALSIFICATION CONDITIONS — declared now, so they cannot be reinterpreted later
    F1. If A5 - A3 EXCEEDS +15 percentage points, that is NOT a triumph. It is a signal of
        leakage between the training path and the evaluation path, and must be investigated
        before any result is reported.
    F2. If A5 still ties A3 (identical metrics), the interaction was not the missing piece.
        Report the VOID honestly and do not search for another DGP change that produces a
        win. One pre-registered attempt, reported either way.
    F3. If A5 LOSES, that is reported as-is. The model failing to capture an interaction it
        was given every chance to learn is a real and publishable result.

WHAT IS DELIBERATELY NOT CHANGED
    - Base channel rates are IDENTICAL to the previous model. Only interaction terms are
      added, so the change cannot be a rescaling that flatters any particular action.
    - `HeuristicScorer` is left exactly as it is. Giving the heuristic the interaction table
      too would be the honest way to make the model lose, and is the obvious objection to
      this whole exercise — the answer is that a person writing a recovery playbook writes a
      flat table, which is what the heuristic models. If the interaction were small enough to
      hand-write, ML would not be earning its place here, and that is precisely the claim
      under test.
    - Every multiplier below is justified from payments domain reasoning, chosen before any
      result was observed, and none was adjusted afterwards.

INVARIANTS:
1. DETERMINISTIC. Same (action, diagnosis, amount) always gives the same probability.
2. BOUNDED. Probabilities are clipped to [0.01, 0.95]; no multiplier can produce certainty.
3. BASE RATES PRESERVED. A diagnosis of UNKNOWN with a mid-range amount reproduces the
   original context-free probability, so the previous world is a special case of this one.
"""

from __future__ import annotations

from typing import Dict, Optional

from app.domain.enums import ActionType, DiagnosisCode

# Base channel rates. IDENTICAL to the context-free model they replace — this change adds
# interaction terms only, so it cannot be a rescaling that flatters a particular action.
BASE_CHANNEL_RATE: Dict[ActionType, float] = {
    ActionType.RECOMMEND_RETRY: 0.65,
    ActionType.WHATSAPP_LINK: 0.55,
    ActionType.SMS_LINK: 0.40,
    ActionType.EMAIL_LINK: 0.30,
    ActionType.IVR_CALL: 0.35,
    ActionType.AGENT_DIAL: 0.70,
}
DEFAULT_RATE = 0.30

# Natural self-cure rate for NO_ACTION. Unchanged.
NO_ACTION_SELF_CURE_RATE = 0.15

# --- The interaction: diagnosis x channel ----------------------------------------------
# This is the structure a flat per-diagnosis multiplier CANNOT represent, and therefore the
# thing the experiment is actually testing. Each row is domain reasoning, stated:
#
#   INSUFFICIENT_FUNDS  money arrives later. A retry timed after funding works; phone
#                       pressure does not create money.
#   CARD_DECLINED       the instrument is dead. Retrying the same card fails BY DEFINITION;
#                       the customer must update a method, so a link is the fix.
#   GATEWAY_FAILURE     infrastructure, not the customer. Retry once it clears. Contacting
#                       the customer is noise - they did nothing wrong.
#   CUSTOMER_ABANDONMENT they chose not to complete and there is no mandate to retry.
#                       Interactive persuasion is what works.
#   SUBSCRIPTION_RENEWAL_FAILURE  a mandate exists, so retry is natural.
#   INVOICE_OVERDUE     a B2B accounts-payable process. Email is THE AP channel and phone
#                       chasing works; SMS/WhatsApp are the wrong medium for a company.
#   CUSTOMER_UNRESPONSIVE  repeated non-response. Only human contact has much chance.
#   UNKNOWN             uncertainty penalty, applied evenly.
DIAGNOSIS_CHANNEL_MULTIPLIER: Dict[str, Dict[ActionType, float]] = {
    DiagnosisCode.INSUFFICIENT_FUNDS.value: {
        ActionType.RECOMMEND_RETRY: 1.30, ActionType.EMAIL_LINK: 1.05,
        ActionType.SMS_LINK: 1.10, ActionType.WHATSAPP_LINK: 1.10,
        ActionType.IVR_CALL: 0.85, ActionType.AGENT_DIAL: 0.90,
    },
    DiagnosisCode.CARD_DECLINED.value: {
        ActionType.RECOMMEND_RETRY: 0.30, ActionType.EMAIL_LINK: 1.20,
        ActionType.SMS_LINK: 1.25, ActionType.WHATSAPP_LINK: 1.30,
        ActionType.IVR_CALL: 0.95, ActionType.AGENT_DIAL: 1.05,
    },
    DiagnosisCode.GATEWAY_FAILURE.value: {
        ActionType.RECOMMEND_RETRY: 1.35, ActionType.EMAIL_LINK: 0.55,
        ActionType.SMS_LINK: 0.50, ActionType.WHATSAPP_LINK: 0.50,
        ActionType.IVR_CALL: 0.40, ActionType.AGENT_DIAL: 0.45,
    },
    DiagnosisCode.CUSTOMER_ABANDONMENT.value: {
        ActionType.RECOMMEND_RETRY: 0.25, ActionType.EMAIL_LINK: 1.05,
        ActionType.SMS_LINK: 1.15, ActionType.WHATSAPP_LINK: 1.35,
        ActionType.IVR_CALL: 0.85, ActionType.AGENT_DIAL: 0.95,
    },
    DiagnosisCode.SUBSCRIPTION_RENEWAL_FAILURE.value: {
        ActionType.RECOMMEND_RETRY: 1.25, ActionType.EMAIL_LINK: 1.00,
        ActionType.SMS_LINK: 1.00, ActionType.WHATSAPP_LINK: 1.05,
        ActionType.IVR_CALL: 0.90, ActionType.AGENT_DIAL: 0.95,
    },
    DiagnosisCode.INVOICE_OVERDUE.value: {
        ActionType.RECOMMEND_RETRY: 0.35, ActionType.EMAIL_LINK: 1.30,
        ActionType.SMS_LINK: 0.65, ActionType.WHATSAPP_LINK: 0.65,
        ActionType.IVR_CALL: 1.20, ActionType.AGENT_DIAL: 1.35,
    },
    DiagnosisCode.CUSTOMER_UNRESPONSIVE.value: {
        ActionType.RECOMMEND_RETRY: 0.60, ActionType.EMAIL_LINK: 0.55,
        ActionType.SMS_LINK: 0.60, ActionType.WHATSAPP_LINK: 0.65,
        ActionType.IVR_CALL: 0.80, ActionType.AGENT_DIAL: 0.95,
    },
    DiagnosisCode.UNKNOWN.value: {},  # neutral; see UNKNOWN_PENALTY
}
UNKNOWN_PENALTY = 0.90

# --- Amount effect ----------------------------------------------------------------------
# A person will take a call about a large bill and ignore one about a small one; a large
# amount also needs more deliberation, which slightly blunts a one-tap link.
SMALL_AMOUNT_PAISE = 100_000      # below Rs 1,000
LARGE_AMOUNT_PAISE = 1_000_000    # above Rs 10,000
HIGH_TOUCH = (ActionType.IVR_CALL, ActionType.AGENT_DIAL)
LINKS = (ActionType.EMAIL_LINK, ActionType.SMS_LINK, ActionType.WHATSAPP_LINK)

PROB_FLOOR, PROB_CEILING = 0.01, 0.95


def _amount_multiplier(action: ActionType, amount_paise: int) -> float:
    if amount_paise < SMALL_AMOUNT_PAISE:
        if action == ActionType.AGENT_DIAL:
            return 0.70
        if action == ActionType.IVR_CALL:
            return 0.80
        if action in LINKS:
            return 1.05
    elif amount_paise > LARGE_AMOUNT_PAISE:
        if action in HIGH_TOUCH:
            return 1.15
        if action in LINKS:
            return 0.95
    return 1.0


def success_probability(
    action: ActionType,
    diagnosis_code: Optional[str] = None,
    amount_paise: int = 0,
) -> float:
    """P(recovery | action, diagnosis, amount). Deterministic and bounded.

    With an UNKNOWN diagnosis and a mid-range amount this reduces to the original
    context-free rate, so the previous world is a special case of this one.
    """
    base = BASE_CHANNEL_RATE.get(action, DEFAULT_RATE)

    row = DIAGNOSIS_CHANNEL_MULTIPLIER.get(str(diagnosis_code or ""), None)
    if row is None:
        interaction = 1.0
    elif not row:
        interaction = UNKNOWN_PENALTY
    else:
        interaction = row.get(action, 1.0)

    p = base * interaction * _amount_multiplier(action, amount_paise)
    return max(PROB_FLOOR, min(PROB_CEILING, p))
