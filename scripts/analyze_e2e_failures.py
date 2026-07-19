import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

REPORT_PATH = ROOT_DIR / "outputs" / "e2e_chatbot_test_report.json"
OUTPUT_PATH = ROOT_DIR / "outputs" / "e2e_failed_cases.json"


def load_report():
    if not REPORT_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy report: {REPORT_PATH}\n"
            "Hãy chạy trước: python scripts\\test_e2e_chatbot.py"
        )

    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_failed_cases(report):
    results = report.get("results", [])

    failed_cases = []

    for case in results:
        if case.get("passed") is True:
            continue

        checks = case.get("checks", {})
        failed_checks = {}

        for check_name, check_value in checks.items():
            if check_value.get("passed") is False:
                failed_checks[check_name] = {
                    "expected": check_value.get("expected"),
                    "actual": check_value.get("actual"),
                }

        conversation_results = case.get("conversation_results", [])

        simplified_turns = []

        for turn in conversation_results:
            policy_output = turn.get("policy_output", {}) or {}
            state = turn.get("state", {}) or {}

            simplified_turns.append({
                "user_message": turn.get("user_message"),
                "result_type": turn.get("result_type"),
                "bot_message": turn.get("bot_message"),
                "policy_intent": policy_output.get("intent"),
                "policy_action": policy_output.get("action"),
                "policy_slots": policy_output.get("slots"),
                "should_update_state": policy_output.get("should_update_state"),
                "should_recommend": policy_output.get("should_recommend"),
                "state_after_turn": state,
            })

        failed_cases.append({
            "case_id": case.get("case_id"),
            "name": case.get("name"),
            "failed_checks": failed_checks,
            "final_state": case.get("final_state"),
            "turns": simplified_turns,
        })

    return failed_cases


def classify_error_type(failed_check_name):
    mapping = {
        "final_occasion": "slot_occasion_error",
        "final_recipient": "slot_recipient_error",
        "budget": "slot_budget_error",
        "budget_type": "slot_budget_type_error",
        "flower_preference_contains": "slot_flower_preference_error",
        "flower_avoidance_contains": "slot_flower_avoidance_error",
        "color_tone_contains": "slot_color_tone_error",
        "must_recommend": "recommendation_flow_error",
        "must_collect_customer_info": "confirm_order_flow_error",
        "must_create_order": "create_order_flow_error",
        "must_have_payment_code": "payment_code_error",
        "must_check_inventory": "inventory_action_error",
        "must_answer_flower_colors": "flower_color_action_error",
        "must_block_payment_confirm": "security_guardrail_error",
        "must_answer_budget_suggestion": "budget_suggestion_action_error",
        "must_answer_flower_pairing": "flower_pairing_action_error",
        "must_answer_flower_meaning": "flower_meaning_action_error",
        "must_ask_missing_info": "missing_info_action_error",
    }

    return mapping.get(failed_check_name, "unknown_error")


def build_training_candidates(failed_cases):
    """
    Tạo danh sách candidate để sau này đưa vào dataset v3.
    Chưa sinh dataset train ngay ở bước này.
    Bước này chỉ gom lỗi và gợi ý loại lỗi.
    """

    candidates = []

    for case in failed_cases:
        failed_checks = case.get("failed_checks", {})
        turns = case.get("turns", [])

        for failed_check_name, check_detail in failed_checks.items():
            error_type = classify_error_type(failed_check_name)

            # Lấy turn cuối làm default.
            # Khi cần tinh chỉnh dataset v3, ta sẽ xem lại turn nào sai nhất.
            last_turn = turns[-1] if turns else {}

            candidates.append({
                "case_id": case.get("case_id"),
                "case_name": case.get("name"),
                "error_type": error_type,
                "failed_check": failed_check_name,
                "expected": check_detail.get("expected"),
                "actual": check_detail.get("actual"),
                "candidate_user_message": last_turn.get("user_message"),
                "model_intent": last_turn.get("policy_intent"),
                "model_action": last_turn.get("policy_action"),
                "model_slots": last_turn.get("policy_slots"),
                "state_after_turn": last_turn.get("state_after_turn"),
            })

    return candidates


def main():
    report = load_report()

    summary = report.get("summary", {})

    failed_cases = extract_failed_cases(report)
    training_candidates = build_training_candidates(failed_cases)

    output = {
        "source_report": str(REPORT_PATH),
        "summary": {
            "total_cases": summary.get("total_cases"),
            "passed_cases": summary.get("passed_cases"),
            "failed_cases": summary.get("failed_cases"),
            "pass_rate": summary.get("pass_rate"),
        },
        "failed_cases": failed_cases,
        "training_candidates": training_candidates,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("========== E2E FAILURE ANALYSIS ==========")
    print(f"Total cases : {summary.get('total_cases')}")
    print(f"Passed      : {summary.get('passed_cases')}")
    print(f"Failed      : {summary.get('failed_cases')}")
    print(f"Pass rate   : {summary.get('pass_rate')}")
    print(f"Failed cases extracted: {len(failed_cases)}")
    print(f"Training candidates   : {len(training_candidates)}")
    print(f"Output path: {OUTPUT_PATH}")

    if failed_cases:
        print("\nFailed case list:")
        for case in failed_cases:
            print(f"- {case['case_id']} | {case['name']}")
            for failed_check in case.get("failed_checks", {}).keys():
                print(f"  + {failed_check} -> {classify_error_type(failed_check)}")


if __name__ == "__main__":
    main()