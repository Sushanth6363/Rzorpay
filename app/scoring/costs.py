"""Action cost schedule in integer paise for Unified Recovery Engine (M5)."""

from app.domain.enums import ActionType

ACTION_COSTS_PAISE = {
    ActionType.NO_ACTION: 0,
    ActionType.WHATSAPP_LINK: 25,       # ₹0.25
    ActionType.SMS_LINK: 15,            # ₹0.15
    ActionType.EMAIL_LINK: 5,           # ₹0.05
    ActionType.IVR_CALL: 100,           # ₹1.00
    ActionType.AGENT_DIAL: 1500,        # ₹15.00
    ActionType.RECOMMEND_RETRY: 0,      # ₹0.00 (engine internal recommendation)
}


def get_action_cost_paise(action_type: ActionType) -> int:
    """Return cost of action in integer paise."""
    return ACTION_COSTS_PAISE.get(action_type, 0)
