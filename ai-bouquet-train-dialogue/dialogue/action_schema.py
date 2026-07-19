INTENTS = [
    "new_bouquet_request",
    "provide_missing_info",
    "ask_price_range",
    "ask_premium_option",
    "ask_budget_suggestion",
    "ask_flower_combination",
    "ask_flower_meaning",
    "ask_inventory",
    "modify_flower",
    "modify_budget",
    "modify_style",
    "modify_color",
    "ask_alternative",
    "confirm_order",
    "provide_customer_info",
    "ask_delivery",
    "confirm_payment",
    "general_question",
    "unclear"
]

ACTIONS = [
    "ask_missing_info",
    "recommend_bouquet",
    "answer_price_info",
    "answer_premium_option",
    "answer_budget_suggestion",
    "answer_flower_pairing",
    "answer_flower_meaning",
    "check_inventory",
    "update_bouquet",
    "show_alternatives",
    "create_order",
    "collect_customer_info",
    "answer_delivery_info",
    "confirm_payment",
    "answer_general",
    "clarify_user_intent"
]

REQUIRED_SLOT_KEYS = [
    "occasion",
    "recipient",
    "budget",
    "budget_min",
    "budget_max",
    "budget_type",
    "flower_preference",
    "flower_avoidance",
    "color_tone",
    "style",
    "delivery_time",
    "customer_name",
    "customer_phone",
    "customer_address",
    "order_id"
]

DEFAULT_SLOTS = {
    "occasion": None,
    "recipient": None,
    "budget": None,
    "budget_min": None,
    "budget_max": None,
    "budget_type": None,
    "flower_preference": [],
    "flower_avoidance": [],
    "color_tone": [],
    "style": [],
    "delivery_time": None,
    "customer_name": None,
    "customer_phone": None,
    "customer_address": None,
    "order_id": None
}


def get_empty_policy_output():
    return {
        "intent": "unclear",
        "action": "clarify_user_intent",
        "slots": DEFAULT_SLOTS.copy(),
        "should_update_state": False,
        "should_recommend": False,
        "should_check_inventory": False,
        "should_create_order": False,
        "should_collect_customer_info": False,
        "response_goal": "Hỏi lại khách hàng để làm rõ nhu cầu."
    }


def validate_policy_output(output: dict):
    if not isinstance(output, dict):
        return False, "Output must be a dict"

    required_keys = [
        "intent",
        "action",
        "slots",
        "should_update_state",
        "should_recommend",
        "should_check_inventory",
        "should_create_order",
        "should_collect_customer_info",
        "response_goal"
    ]

    for key in required_keys:
        if key not in output:
            return False, f"Missing key: {key}"

    if output["intent"] not in INTENTS:
        return False, f"Invalid intent: {output['intent']}"

    if output["action"] not in ACTIONS:
        return False, f"Invalid action: {output['action']}"

    if not isinstance(output["slots"], dict):
        return False, "slots must be a dict"

    for slot_key in REQUIRED_SLOT_KEYS:
        if slot_key not in output["slots"]:
            return False, f"Missing slot: {slot_key}"

    boolean_keys = [
        "should_update_state",
        "should_recommend",
        "should_check_inventory",
        "should_create_order",
        "should_collect_customer_info"
    ]

    for key in boolean_keys:
        if not isinstance(output[key], bool):
            return False, f"{key} must be boolean"

    if not isinstance(output["response_goal"], str):
        return False, "response_goal must be string"

    return True, "valid"