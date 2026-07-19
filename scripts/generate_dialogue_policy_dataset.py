import json
import random
from pathlib import Path


OUTPUT_PATH = Path("data/processed/dialogue_policy_train.jsonl")


DEFAULT_STATE = {
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
    "customer_address": None
}


def make_slots(
    occasion=None,
    recipient=None,
    budget=None,
    budget_min=None,
    budget_max=None,
    budget_type=None,
    flower_preference=None,
    flower_avoidance=None,
    color_tone=None,
    style=None,
    delivery_time=None,
    customer_name=None,
    customer_phone=None,
    customer_address=None
):
    return {
        "occasion": occasion,
        "recipient": recipient,
        "budget": budget,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "budget_type": budget_type,
        "flower_preference": flower_preference or [],
        "flower_avoidance": flower_avoidance or [],
        "color_tone": color_tone or [],
        "style": style or [],
        "delivery_time": delivery_time,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "customer_address": customer_address
    }


def make_case(
    state,
    last_bot_message,
    user_message,
    intent,
    action,
    slots,
    should_update_state,
    should_recommend,
    should_check_inventory,
    should_create_order,
    should_collect_customer_info,
    response_goal
):
    return {
        "conversation_context": {
            "state": state,
            "last_bot_message": last_bot_message
        },
        "user_message": user_message,
        "expected_output": {
            "intent": intent,
            "action": action,
            "slots": slots,
            "should_update_state": should_update_state,
            "should_recommend": should_recommend,
            "should_check_inventory": should_check_inventory,
            "should_create_order": should_create_order,
            "should_collect_customer_info": should_collect_customer_info,
            "response_goal": response_goal
        }
    }


def generate_new_bouquet_request_cases():
    cases = []

    messages = [
        (
            "tôi muốn đặt bó hoa tặng mẹ dịp sinh nhật khoảng từ 500k đến 1 triệu",
            "sinh nhật",
            "mẹ",
            750000,
            500000,
            1000000,
            "range"
        ),
        (
            "mình cần bó hoa sinh nhật cho bạn nữ dưới 700k",
            "sinh nhật",
            "bạn nữ",
            700000,
            None,
            700000,
            "maximum"
        ),
        (
            "cho tôi bó hoa tặng người yêu trên 500k",
            None,
            "người yêu",
            500000,
            500000,
            None,
            "minimum"
        ),
        (
            "em muốn bó hoa tốt nghiệp tone vàng tầm 400k",
            "tốt nghiệp",
            None,
            400000,
            340000,
            460000,
            "approximate"
        ),
        (
            "tôi muốn đặt bó hoa khai trương khoảng 1 triệu",
            "khai trương",
            None,
            1000000,
            850000,
            1150000,
            "approximate"
        )
    ]

    for text, occasion, recipient, budget, bmin, bmax, btype in messages:
        cases.append(
            make_case(
                state=DEFAULT_STATE.copy(),
                last_bot_message="Dạ anh/chị cần tư vấn bó hoa như thế nào ạ?",
                user_message=text,
                intent="new_bouquet_request",
                action="recommend_bouquet",
                slots=make_slots(
                    occasion=occasion,
                    recipient=recipient,
                    budget=budget,
                    budget_min=bmin,
                    budget_max=bmax,
                    budget_type=btype,
                    color_tone=["vàng"] if "tone vàng" in text else []
                ),
                should_update_state=True,
                should_recommend=True,
                should_check_inventory=True,
                should_create_order=False,
                should_collect_customer_info=False,
                response_goal="Tạo đề xuất bó hoa phù hợp với yêu cầu, ngân sách và tồn kho."
            )
        )

    return cases


def generate_price_question_cases():
    cases = []

    states = [
        {
            **DEFAULT_STATE,
            "occasion": "sinh nhật",
            "recipient": "mẹ",
            "budget": 500000,
            "budget_type": "maximum"
        },
        DEFAULT_STATE.copy()
    ]

    messages = [
        "bó hoa đắt nhất bên bạn tầm bao nhiêu",
        "shop có bó cao cấp nhất giá khoảng bao nhiêu",
        "bó premium bên mình giá thế nào",
        "bó rẻ nhất khoảng bao nhiêu",
        "tầm tiền nào thì bó hoa nhìn đẹp"
    ]

    for state in states:
        for msg in messages:
            if "đắt nhất" in msg or "cao cấp" in msg or "premium" in msg:
                intent = "ask_premium_option"
                action = "answer_premium_option"
                goal = "Giải thích các mức giá bó hoa cao cấp/premium của shop, chưa tạo đơn."
            elif "rẻ nhất" in msg:
                intent = "ask_price_range"
                action = "answer_price_info"
                goal = "Giải thích mức giá bó hoa cơ bản/rẻ nhất của shop."
            else:
                intent = "ask_budget_suggestion"
                action = "answer_budget_suggestion"
                goal = "Tư vấn khách nên chọn ngân sách nào để bó hoa đẹp."

            cases.append(
                make_case(
                    state=state,
                    last_bot_message="Anh/chị muốn em giữ phương án này hay điều chỉnh gì thêm ạ?",
                    user_message=msg,
                    intent=intent,
                    action=action,
                    slots=make_slots(),
                    should_update_state=False,
                    should_recommend=False,
                    should_check_inventory=False,
                    should_create_order=False,
                    should_collect_customer_info=False,
                    response_goal=goal
                )
            )

    return cases


def generate_flower_combination_cases():
    cases = []

    messages = [
        (
            "cẩm tú cầu phối với hoa nào đẹp hơn",
            ["cẩm tú cầu"],
            "Tư vấn cẩm tú cầu nên phối với hoa nào, hợp dịp nào và người nhận nào."
        ),
        (
            "hoa hồng kem kết hợp với hoa gì thì hợp tặng mẹ",
            ["hoa hồng kem"],
            "Tư vấn hoa hồng kem nên phối với hoa nào để tặng mẹ."
        ),
        (
            "baby trắng dùng để phối với hoa nào",
            ["baby trắng"],
            "Giải thích baby trắng phù hợp làm hoa phụ với những loại hoa nào."
        ),
        (
            "tulip phối với hoa gì cho sang",
            ["tulip"],
            "Tư vấn tulip nên phối với hoa nào để tạo phong cách sang trọng."
        )
    ]

    for msg, flowers, goal in messages:
        cases.append(
            make_case(
                state=DEFAULT_STATE.copy(),
                last_bot_message="Anh/chị muốn tìm hiểu loại hoa nào ạ?",
                user_message=msg,
                intent="ask_flower_combination",
                action="answer_flower_pairing",
                slots=make_slots(flower_preference=flowers),
                should_update_state=True,
                should_recommend=False,
                should_check_inventory=True,
                should_create_order=False,
                should_collect_customer_info=False,
                response_goal=goal
            )
        )

    return cases


def generate_modify_cases():
    cases = []

    base_state = {
        **DEFAULT_STATE,
        "occasion": "sinh nhật",
        "recipient": "mẹ",
        "budget": 700000,
        "budget_type": "maximum",
        "flower_preference": ["cẩm tú cầu"],
        "color_tone": ["xanh"],
        "style": ["bó giấy Hàn Quốc"]
    }

    messages = [
        (
            "đổi sang tone hồng được không",
            "modify_color",
            "update_bouquet",
            make_slots(color_tone=["hồng"]),
            "Cập nhật tone màu sang hồng và đề xuất điều chỉnh bó hoa."
        ),
        (
            "thêm hoa hồng kem vào được không",
            "modify_flower",
            "update_bouquet",
            make_slots(flower_preference=["hoa hồng kem"]),
            "Thêm hoa hồng kem vào yêu cầu và cập nhật bó hoa."
        ),
        (
            "bỏ cẩm tú cầu đi",
            "modify_flower",
            "update_bouquet",
            make_slots(flower_avoidance=["cẩm tú cầu"]),
            "Loại bỏ cẩm tú cầu khỏi bó hoa và gợi ý hoa thay thế."
        ),
        (
            "tăng ngân sách lên 1 triệu",
            "modify_budget",
            "update_bouquet",
            make_slots(
                budget=1000000,
                budget_min=None,
                budget_max=1000000,
                budget_type="maximum"
            ),
            "Cập nhật ngân sách lên 1 triệu và đề xuất bó hoa đầy đặn hơn."
        ),
        (
            "chuyển sang kiểu sang trọng hơn",
            "modify_style",
            "update_bouquet",
            make_slots(style=["sang trọng"]),
            "Cập nhật phong cách sang trọng hơn cho bó hoa."
        )
    ]

    for msg, intent, action, slots, goal in messages:
        cases.append(
            make_case(
                state=base_state,
                last_bot_message="Anh/chị muốn giữ phương án này hay điều chỉnh gì thêm ạ?",
                user_message=msg,
                intent=intent,
                action=action,
                slots=slots,
                should_update_state=True,
                should_recommend=True,
                should_check_inventory=True,
                should_create_order=False,
                should_collect_customer_info=False,
                response_goal=goal
            )
        )

    return cases


def generate_inventory_cases():
    cases = []

    messages = [
        (
            "shop còn cẩm tú cầu không",
            ["cẩm tú cầu"],
            "Kiểm tra tồn kho cẩm tú cầu và trả lời khách."
        ),
        (
            "tulip còn hàng không",
            ["tulip"],
            "Kiểm tra tồn kho tulip, nếu hết thì gợi ý hoa thay thế."
        ),
        (
            "bên mình có hoa hồng kem không",
            ["hoa hồng kem"],
            "Kiểm tra shop có hoa hồng kem không."
        )
    ]

    for msg, flowers, goal in messages:
        cases.append(
            make_case(
                state=DEFAULT_STATE.copy(),
                last_bot_message="Anh/chị muốn hỏi loại hoa nào ạ?",
                user_message=msg,
                intent="ask_inventory",
                action="check_inventory",
                slots=make_slots(flower_preference=flowers),
                should_update_state=True,
                should_recommend=False,
                should_check_inventory=True,
                should_create_order=False,
                should_collect_customer_info=False,
                response_goal=goal
            )
        )

    return cases


def generate_confirm_order_cases():
    cases = []

    base_state = {
        **DEFAULT_STATE,
        "occasion": "sinh nhật",
        "recipient": "mẹ",
        "budget": 700000,
        "budget_type": "maximum",
        "flower_preference": ["cẩm tú cầu", "hoa hồng kem"],
        "color_tone": ["xanh"],
        "style": ["bó giấy Hàn Quốc"]
    }

    messages = [
        "ok lấy bó này",
        "chốt đơn này giúp tôi",
        "mình đặt bó này nhé",
        "được rồi tạo đơn đi",
        "tôi lấy phương án này"
    ]

    for msg in messages:
        cases.append(
            make_case(
                state=base_state,
                last_bot_message="Anh/chị muốn em giữ phương án này, đổi tone màu hay tạo đơn không ạ?",
                user_message=msg,
                intent="confirm_order",
                action="collect_customer_info",
                slots=make_slots(),
                should_update_state=False,
                should_recommend=False,
                should_check_inventory=True,
                should_create_order=False,
                should_collect_customer_info=True,
                response_goal="Khách đã chốt phương án, cần xin thông tin tên, số điện thoại và địa chỉ trước khi tạo đơn."
            )
        )

    return cases


def generate_customer_info_cases():
    cases = []

    base_state = {
        **DEFAULT_STATE,
        "occasion": "sinh nhật",
        "recipient": "mẹ",
        "budget": 700000,
        "budget_type": "maximum",
        "flower_preference": ["cẩm tú cầu"]
    }

    messages = [
        (
            "tên tôi là Nguyễn Văn An, số điện thoại 0912345678, giao ở Cầu Giấy",
            "Nguyễn Văn An",
            "0912345678",
            "Cầu Giấy"
        ),
        (
            "mình tên Mai, sđt 0987654321, địa chỉ ở Hà Đông",
            "Mai",
            "0987654321",
            "Hà Đông"
        )
    ]

    for msg, name, phone, address in messages:
        cases.append(
            make_case(
                state=base_state,
                last_bot_message="Anh/chị cho em xin tên, số điện thoại và địa chỉ giao hàng ạ.",
                user_message=msg,
                intent="provide_customer_info",
                action="create_order",
                slots=make_slots(
                    customer_name=name,
                    customer_phone=phone,
                    customer_address=address
                ),
                should_update_state=True,
                should_recommend=False,
                should_check_inventory=True,
                should_create_order=True,
                should_collect_customer_info=False,
                response_goal="Lưu thông tin khách hàng và tạo đơn hàng."
            )
        )

    return cases


def generate_unclear_cases():
    cases = []

    messages = [
        "ừm sao nhỉ",
        "cũng được",
        "không biết nữa",
        "bạn thấy sao",
        "còn gì không"
    ]

    for msg in messages:
        cases.append(
            make_case(
                state=DEFAULT_STATE.copy(),
                last_bot_message="Anh/chị muốn đặt hoa cho dịp gì ạ?",
                user_message=msg,
                intent="unclear",
                action="clarify_user_intent",
                slots=make_slots(),
                should_update_state=False,
                should_recommend=False,
                should_check_inventory=False,
                should_create_order=False,
                should_collect_customer_info=False,
                response_goal="Hỏi lại khách hàng muốn tư vấn theo hướng nào: dịp tặng, ngân sách, loại hoa, hay tạo đơn."
            )
        )

    return cases


def augment_cases(cases, target_size=600):
    """
    Nhân bản nhẹ dataset bằng cách shuffle và thay last_bot_message một chút.
    Không tạo dữ liệu quá phức tạp, tránh nhiễu.
    """

    if len(cases) >= target_size:
        return cases[:target_size]

    bot_messages = [
        "Anh/chị muốn em tư vấn thêm gì ạ?",
        "Anh/chị muốn giữ phương án này hay điều chỉnh gì thêm ạ?",
        "Dạ em có thể hỗ trợ thêm về ngân sách, loại hoa, kiểu bó hoặc tạo đơn ạ.",
        "Anh/chị cần em kiểm tra kho, gợi ý hoa hay tạo đơn ạ?"
    ]

    augmented = list(cases)

    while len(augmented) < target_size:
        case = random.choice(cases)
        new_case = json.loads(json.dumps(case, ensure_ascii=False))
        new_case["conversation_context"]["last_bot_message"] = random.choice(bot_messages)
        augmented.append(new_case)

    return augmented


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    cases = []
    cases.extend(generate_new_bouquet_request_cases())
    cases.extend(generate_price_question_cases())
    cases.extend(generate_flower_combination_cases())
    cases.extend(generate_modify_cases())
    cases.extend(generate_inventory_cases())
    cases.extend(generate_confirm_order_cases())
    cases.extend(generate_customer_info_cases())
    cases.extend(generate_unclear_cases())

    cases = augment_cases(cases, target_size=600)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    print(f"Saved {len(cases)} dialogue policy cases to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()