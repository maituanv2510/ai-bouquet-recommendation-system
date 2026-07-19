import json
import sys
from pathlib import Path
from datetime import datetime


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

TEST_CASE_PATH = ROOT_DIR / "data" / "processed" / "e2e_chatbot_test_cases.json"
OUTPUT_PATH = ROOT_DIR / "outputs" / "e2e_chatbot_test_report.json"


# =========================================================
# Import project modules
# =========================================================

from chatbot.chatbot_pipeline import ChatbotPipeline
from recommendation.recommendation_service import run_recommendation_from_state


try:
    from dialogue.qwen_dialogue_policy import QwenDialoguePolicy
except Exception:
    QwenDialoguePolicy = None


# =========================================================
# Load test cases
# =========================================================

def load_test_cases():
    if not TEST_CASE_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy file test case: {TEST_CASE_PATH}")

    with open(TEST_CASE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# Build chatbot
# =========================================================

def build_chatbot(use_qwen=True):
    dialogue_policy_func = None

    if use_qwen and QwenDialoguePolicy is not None:
        print("[INFO] Loading Qwen Dialogue Policy...")
        qwen_policy = QwenDialoguePolicy(
            adapter_path="outputs/qwen2.5-3b-dialogue-policy",
            max_new_tokens=96,
        )
        dialogue_policy_func = qwen_policy.predict
    else:
        print("[INFO] Qwen not used. Fallback to rule policy.")

    chatbot = ChatbotPipeline(
        recommender_func=run_recommendation_from_state,
        dialogue_policy_func=dialogue_policy_func,
    )

    return chatbot


# =========================================================
# Helpers
# =========================================================

def contains_all(actual_list, expected_list):
    if not expected_list:
        return True

    if not isinstance(actual_list, list):
        return False

    actual_lower = [str(x).lower() for x in actual_list]

    for expected in expected_list:
        if str(expected).lower() not in actual_lower:
            return False

    return True


def normalize_text(text):
    if text is None:
        return ""

    return str(text).lower()


def get_nested(data, path, default=None):
    current = data

    for key in path:
        if not isinstance(current, dict):
            return default

        current = current.get(key)

        if current is None:
            return default

    return current


def detect_has_payment_code(result):
    message = normalize_text(result.get("message", ""))

    if "mã thanh toán" in message:
        if "chưa có" not in message:
            return True

    last_recommendation = result.get("last_recommendation")

    # last_recommendation thường không chứa payment.
    # Payment chủ yếu nằm trong message sau create_order.
    return False


def detect_created_order(result):
    message = normalize_text(result.get("message", ""))

    if "đã tạo đơn hàng" in message:
        return True

    if "mã đơn hàng" in message and "không rõ" not in message:
        return True

    return False


def detect_collect_customer_info(result):
    message = normalize_text(result.get("message", ""))

    return (
        "họ tên" in message
        and "số điện thoại" in message
        and "địa chỉ" in message
    )


def detect_recommendation(result):
    result_type = result.get("type")
    message = normalize_text(result.get("message", ""))

    if result_type == "recommendation":
        return True

    if "gợi ý" in message and "bó hoa" in message:
        return True

    if "thành phần bó hoa" in message:
        return True

    return False


def detect_inventory_check(result):
    result_type = result.get("type")
    message = normalize_text(result.get("message", ""))

    if result_type == "inventory":
        return True

    if "hiện còn" in message or "hết hàng" in message or "tồn kho" in message:
        return True

    return False


def detect_flower_colors(result):
    result_type = result.get("type")
    message = normalize_text(result.get("message", ""))

    if result_type == "flower_colors":
        return True

    if "màu/tone" in message or "các màu" in message or "tone" in message:
        return True

    return False


def detect_security_block(result):
    result_type = result.get("type")
    message = normalize_text(result.get("message", ""))

    if result_type == "security_block":
        return True

    if "chỉ dành cho admin" in message:
        return True

    return False


def detect_budget_suggestion(result):
    result_type = result.get("type")
    message = normalize_text(result.get("message", ""))

    if result_type == "budget_suggestion":
        return True

    if "300k" in message and "500k" in message:
        return True

    return False


def detect_flower_pairing(result):
    result_type = result.get("type")
    message = normalize_text(result.get("message", ""))

    if result_type == "flower_pairing":
        return True

    if "phối" in message:
        return True

    return False


def detect_flower_meaning(result):
    result_type = result.get("type")
    message = normalize_text(result.get("message", ""))

    if result_type == "flower_meaning":
        return True

    if "tượng trưng" in message or "ý nghĩa" in message:
        return True

    return False


def detect_ask_missing_info(result):
    result_type = result.get("type")
    message = normalize_text(result.get("message", ""))

    if result_type == "ask_missing_info":
        return True

    missing_keywords = [
        "dịp gì",
        "tặng cho ai",
        "ngân sách",
        "bao nhiêu",
    ]

    return any(keyword in message for keyword in missing_keywords)


# =========================================================
# Evaluation
# =========================================================

def evaluate_case(case, chatbot):
    case_id = case.get("case_id")
    name = case.get("name")
    messages = case.get("messages", [])
    expected = case.get("expected", {})

    print(f"\n========== Running {case_id}: {name} ==========")

    chatbot.reset()

    conversation_results = []

    for idx, message in enumerate(messages):
        print(f"[USER {idx + 1}] {message}")

        result = chatbot.chat(message)

        bot_message = result.get("message", "")
        print(f"[BOT  {idx + 1}] {bot_message[:300]}...")

        conversation_results.append({
            "user_message": message,
            "bot_message": bot_message,
            "result_type": result.get("type"),
            "policy_output": result.get("policy_output"),
            "state": result.get("state"),
        })

    final_result = result
    final_state = final_result.get("state", {})

    checks = {}

    # =====================================================
    # State checks
    # =====================================================

    if "final_occasion" in expected:
        checks["final_occasion"] = {
            "expected": expected["final_occasion"],
            "actual": final_state.get("occasion"),
            "passed": final_state.get("occasion") == expected["final_occasion"],
        }

    if "final_recipient" in expected:
        checks["final_recipient"] = {
            "expected": expected["final_recipient"],
            "actual": final_state.get("recipient"),
            "passed": final_state.get("recipient") == expected["final_recipient"],
        }

    if "budget" in expected:
        checks["budget"] = {
            "expected": expected["budget"],
            "actual": final_state.get("budget"),
            "passed": final_state.get("budget") == expected["budget"],
        }

    if "budget_type" in expected:
        checks["budget_type"] = {
            "expected": expected["budget_type"],
            "actual": final_state.get("budget_type"),
            "passed": final_state.get("budget_type") == expected["budget_type"],
        }

    if "flower_preference_contains" in expected:
        checks["flower_preference_contains"] = {
            "expected": expected["flower_preference_contains"],
            "actual": final_state.get("flower_preference", []),
            "passed": contains_all(
                final_state.get("flower_preference", []),
                expected["flower_preference_contains"],
            ),
        }

    if "flower_avoidance_contains" in expected:
        checks["flower_avoidance_contains"] = {
            "expected": expected["flower_avoidance_contains"],
            "actual": final_state.get("flower_avoidance", []),
            "passed": contains_all(
                final_state.get("flower_avoidance", []),
                expected["flower_avoidance_contains"],
            ),
        }

    if "color_tone_contains" in expected:
        checks["color_tone_contains"] = {
            "expected": expected["color_tone_contains"],
            "actual": final_state.get("color_tone", []),
            "passed": contains_all(
                final_state.get("color_tone", []),
                expected["color_tone_contains"],
            ),
        }

    # =====================================================
    # Flow/action checks over all turns
    # =====================================================

    all_turns = conversation_results

    has_recommend = any(
        turn.get("result_type") == "recommendation"
        or "thành phần bó hoa" in normalize_text(turn.get("bot_message"))
        for turn in all_turns
    )

    has_collect_customer_info = any(
        detect_collect_customer_info({
            "type": turn.get("result_type"),
            "message": turn.get("bot_message"),
        })
        for turn in all_turns
    )

    has_create_order = any(
        detect_created_order({
            "type": turn.get("result_type"),
            "message": turn.get("bot_message"),
        })
        for turn in all_turns
    )

    has_payment_code = any(
        detect_has_payment_code({
            "type": turn.get("result_type"),
            "message": turn.get("bot_message"),
        })
        for turn in all_turns
    )

    has_inventory_check = any(
        detect_inventory_check({
            "type": turn.get("result_type"),
            "message": turn.get("bot_message"),
        })
        for turn in all_turns
    )

    has_flower_colors = any(
        detect_flower_colors({
            "type": turn.get("result_type"),
            "message": turn.get("bot_message"),
        })
        for turn in all_turns
    )

    has_security_block = any(
        detect_security_block({
            "type": turn.get("result_type"),
            "message": turn.get("bot_message"),
        })
        for turn in all_turns
    )

    has_budget_suggestion = any(
        detect_budget_suggestion({
            "type": turn.get("result_type"),
            "message": turn.get("bot_message"),
        })
        for turn in all_turns
    )

    has_flower_pairing = any(
        detect_flower_pairing({
            "type": turn.get("result_type"),
            "message": turn.get("bot_message"),
        })
        for turn in all_turns
    )

    has_flower_meaning = any(
        detect_flower_meaning({
            "type": turn.get("result_type"),
            "message": turn.get("bot_message"),
        })
        for turn in all_turns
    )

    has_ask_missing_info = any(
        detect_ask_missing_info({
            "type": turn.get("result_type"),
            "message": turn.get("bot_message"),
        })
        for turn in all_turns
    )

    flow_checks = {
        "must_recommend": has_recommend,
        "must_collect_customer_info": has_collect_customer_info,
        "must_create_order": has_create_order,
        "must_have_payment_code": has_payment_code,
        "must_check_inventory": has_inventory_check,
        "must_answer_flower_colors": has_flower_colors,
        "must_block_payment_confirm": has_security_block,
        "must_answer_budget_suggestion": has_budget_suggestion,
        "must_answer_flower_pairing": has_flower_pairing,
        "must_answer_flower_meaning": has_flower_meaning,
        "must_ask_missing_info": has_ask_missing_info,
    }

    for key, actual_value in flow_checks.items():
        if key in expected:
            expected_value = expected[key]
            checks[key] = {
                "expected": expected_value,
                "actual": actual_value,
                "passed": actual_value == expected_value,
            }

    passed = all(item["passed"] for item in checks.values())

    return {
        "case_id": case_id,
        "name": name,
        "passed": passed,
        "checks": checks,
        "final_state": final_state,
        "conversation_results": conversation_results,
    }


def summarize_report(results):
    total = len(results)
    passed = sum(1 for item in results if item.get("passed"))
    failed = total - passed

    failed_cases = [
        {
            "case_id": item["case_id"],
            "name": item["name"],
            "failed_checks": [
                key for key, value in item.get("checks", {}).items()
                if not value.get("passed")
            ],
        }
        for item in results
        if not item.get("passed")
    ]

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_cases": total,
        "passed_cases": passed,
        "failed_cases": failed,
        "pass_rate": round(passed / total, 4) if total else 0,
        "failed_case_details": failed_cases,
    }


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    cases = load_test_cases()

    chatbot = build_chatbot(use_qwen=True)

    results = []

    for case in cases:
        result = evaluate_case(case, chatbot)
        results.append(result)

    summary = summarize_report(results)

    report = {
        "summary": summary,
        "results": results,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n========== E2E TEST SUMMARY ==========")
    print(f"Total cases : {summary['total_cases']}")
    print(f"Passed      : {summary['passed_cases']}")
    print(f"Failed      : {summary['failed_cases']}")
    print(f"Pass rate   : {summary['pass_rate']}")
    print(f"Report path : {OUTPUT_PATH}")

    if summary["failed_cases"] > 0:
        print("\nFailed cases:")
        for item in summary["failed_case_details"]:
            print(f"- {item['case_id']} | {item['name']} | failed: {item['failed_checks']}")


if __name__ == "__main__":
    main()