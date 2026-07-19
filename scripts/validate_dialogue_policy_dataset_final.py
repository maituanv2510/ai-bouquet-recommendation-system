import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

TRAIN_PATH = ROOT_DIR / "data" / "processed" / "dialogue_policy_train_final.jsonl"
VAL_PATH = ROOT_DIR / "data" / "processed" / "dialogue_policy_val_final.jsonl"


VALID_INTENTS = {
    "new_bouquet_request",
    "provide_missing_info",
    "ask_price_range",
    "ask_premium_option",
    "ask_budget_suggestion",
    "ask_flower_combination",
    "ask_flower_meaning",
    "ask_flower_colors",
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
    "unclear",
}


VALID_ACTIONS = {
    "ask_missing_info",
    "recommend_bouquet",
    "answer_price_info",
    "answer_premium_option",
    "answer_budget_suggestion",
    "answer_flower_pairing",
    "answer_flower_meaning",
    "answer_flower_colors",
    "check_inventory",
    "update_bouquet",
    "show_alternatives",
    "create_order",
    "collect_customer_info",
    "answer_delivery_info",
    "confirm_payment",
    "answer_general",
    "clarify_user_intent",
}


REQUIRED_SLOT_KEYS = {
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
    "order_id",
}


LIST_SLOT_KEYS = {
    "flower_preference",
    "flower_avoidance",
    "color_tone",
    "style",
}


def load_jsonl(path):
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {path}")

    rows = []

    with open(path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                rows.append((line_number, json.loads(line)))
            except json.JSONDecodeError as e:
                rows.append((line_number, {"__json_error__": str(e)}))

    return rows


def extract_expected_output(item):
    if "__json_error__" in item:
        return None

    expected_output = item.get("expected_output")

    if isinstance(expected_output, dict):
        return expected_output

    text = item.get("text", "")

    marker = "<|im_start|>assistant\n"

    if marker not in text:
        return None

    assistant_part = text.split(marker, 1)[1]
    assistant_part = assistant_part.replace("<|im_end|>", "").strip()

    try:
        return json.loads(assistant_part)
    except Exception:
        return None


def validate_item(item):
    errors = []

    if "__json_error__" in item:
        return [f"JSON error: {item['__json_error__']}"]

    text = item.get("text", "")

    if not isinstance(text, str) or not text.strip():
        errors.append("missing text")

    if "<|im_start|>system" not in text:
        errors.append("missing system marker")

    if "<|im_start|>user" not in text:
        errors.append("missing user marker")

    if "<|im_start|>assistant" not in text:
        errors.append("missing assistant marker")

    output = extract_expected_output(item)

    if output is None:
        errors.append("cannot extract expected output")
        return errors

    intent = output.get("intent")
    action = output.get("action")
    slots = output.get("slots")

    if intent not in VALID_INTENTS:
        errors.append(f"invalid intent: {intent}")

    if action not in VALID_ACTIONS:
        errors.append(f"invalid action: {action}")

    if not isinstance(slots, dict):
        errors.append("slots is not dict")
    else:
        missing_slots = REQUIRED_SLOT_KEYS - set(slots.keys())

        if missing_slots:
            errors.append(f"missing slots: {sorted(missing_slots)}")

        for key in LIST_SLOT_KEYS:
            if key in slots and not isinstance(slots[key], list):
                errors.append(f"{key} must be list")

    if not isinstance(output.get("should_update_state"), bool):
        errors.append("should_update_state must be bool")

    if not isinstance(output.get("should_recommend"), bool):
        errors.append("should_recommend must be bool")

    return errors


def validate_file(path):
    rows = load_jsonl(path)

    total = len(rows)
    invalid = []

    intent_counts = {}
    action_counts = {}

    for line_number, item in rows:
        errors = validate_item(item)

        if errors:
            invalid.append({
                "line": line_number,
                "errors": errors,
            })
            continue

        output = extract_expected_output(item)

        intent = output.get("intent")
        action = output.get("action")

        intent_counts[intent] = intent_counts.get(intent, 0) + 1
        action_counts[action] = action_counts.get(action, 0) + 1

    return {
        "path": str(path),
        "total": total,
        "valid": total - len(invalid),
        "invalid": len(invalid),
        "intent_counts": intent_counts,
        "action_counts": action_counts,
        "invalid_items": invalid,
    }


def print_report(report):
    print("=" * 70)
    print(f"File: {report['path']}")
    print(f"Total  : {report['total']}")
    print(f"Valid  : {report['valid']}")
    print(f"Invalid: {report['invalid']}")

    print("\nIntent counts:")
    for key, value in sorted(report["intent_counts"].items()):
        print(f"- {key}: {value}")

    print("\nAction counts:")
    for key, value in sorted(report["action_counts"].items()):
        print(f"- {key}: {value}")

    if report["invalid_items"]:
        print("\nInvalid items:")
        for item in report["invalid_items"][:20]:
            print(f"- Line {item['line']}: {item['errors']}")


def main():
    train_report = validate_file(TRAIN_PATH)
    val_report = validate_file(VAL_PATH)

    print_report(train_report)
    print_report(val_report)

    total_invalid = train_report["invalid"] + val_report["invalid"]

    print("=" * 70)

    if total_invalid == 0:
        print("All final dataset files are valid.")
    else:
        print(f"Final dataset has {total_invalid} invalid records.")


if __name__ == "__main__":
    main()