import json
import random
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

TRAIN_OUTPUT = ROOT_DIR / "data" / "processed" / "dialogue_policy_train_v3.jsonl"
VAL_OUTPUT = ROOT_DIR / "data" / "processed" / "dialogue_policy_val_v3.jsonl"


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
    "customer_address": None,
    "order_id": None,
}


FULL_RECOMMENDED_STATE = {
    "occasion": "Valentine",
    "recipient": "người yêu",
    "budget": 700000,
    "budget_min": 700000,
    "budget_max": None,
    "budget_type": "minimum",
    "flower_preference": [],
    "flower_avoidance": [],
    "color_tone": [],
    "style": [],
    "delivery_time": None,
    "customer_name": None,
    "customer_phone": None,
    "customer_address": None,
    "order_id": None,
}


def make_output(
    intent,
    action,
    slots=None,
    should_update_state=False,
    should_recommend=False,
):
    base_slots = DEFAULT_STATE.copy()

    if slots:
        for key, value in slots.items():
            base_slots[key] = value

    return {
        "intent": intent,
        "action": action,
        "slots": base_slots,
        "should_update_state": should_update_state,
        "should_recommend": should_recommend,
    }


def make_record(user_message, state, last_bot_message, output):
    system_prompt = (
        "Bạn là Dialogue Policy Model cho hệ thống tư vấn và quản lý cửa hàng hoa. "
        "Nhiệm vụ của bạn là đọc trạng thái hội thoại hiện tại, tin nhắn gần nhất của bot "
        "và tin nhắn mới của khách hàng, sau đó trả về JSON action hợp lệ. "
        "Chỉ trả về JSON, không giải thích."
    )

    user_content = (
        f"STATE:\n{json.dumps(state, ensure_ascii=False)}\n\n"
        f"LAST_BOT:\n{last_bot_message}\n\n"
        f"USER:\n{user_message}"
    )

    assistant_content = json.dumps(output, ensure_ascii=False)

    text = (
        "<|im_start|>system\n"
        f"{system_prompt}"
        "<|im_end|>\n"
        "<|im_start|>user\n"
        f"{user_content}"
        "<|im_end|>\n"
        "<|im_start|>assistant\n"
        f"{assistant_content}"
        "<|im_end|>"
    )

    return {
        "text": text,
        "user_message": user_message,
        "state": state,
        "last_bot_message": last_bot_message,
        "expected_output": output,
    }


def build_color_question_cases():
    cases = []

    messages = [
        "những hoa trên có màu nào khác không",
        "các hoa trên có màu gì",
        "bó này có màu nào khác không",
        "hoa trong bó này có tone nào",
        "cẩm tú cầu có màu gì",
        "hoa hồng kem có màu nào khác không",
        "baby trắng có màu nào không",
        "cát tường có những màu nào",
        "shop cho em xem màu của các hoa trên",
        "mấy hoa vừa gợi ý có màu nào khác không",
    ]

    for msg in messages:
        slots = {}

        if "cẩm tú cầu" in msg:
            slots["flower_preference"] = ["cẩm tú cầu"]
        elif "hoa hồng kem" in msg:
            slots["flower_preference"] = ["hoa hồng kem"]
        elif "baby" in msg:
            slots["flower_preference"] = ["baby trắng"]
        elif "cát tường" in msg:
            slots["flower_preference"] = ["cát tường"]

        output = make_output(
            intent="ask_flower_colors",
            action="answer_flower_colors",
            slots=slots,
            should_update_state=False,
            should_recommend=False,
        )

        cases.append(
            make_record(
                user_message=msg,
                state=FULL_RECOMMENDED_STATE,
                last_bot_message="Dạ em gợi ý cho anh/chị bó hoa như sau...",
                output=output,
            )
        )

    return cases


def build_modify_color_cases():
    cases = []

    examples = [
        ("cẩm tú cầu màu xanh làm chủ đạo nhé", ["cẩm tú cầu"], ["xanh"]),
        ("đổi sang tone hồng nhé", [], ["hồng"]),
        ("cho bó này màu trắng chủ đạo", [], ["trắng"]),
        ("em muốn thêm màu tím vào bó này", [], ["tím"]),
        ("thêm hoa hồng kem vào bó này nhé", ["hoa hồng kem"], []),
        ("đổi hoa chính sang cẩm tú cầu", ["cẩm tú cầu"], []),
        ("ưu tiên hoa hồng kem và tone pastel", ["hoa hồng kem"], ["pastel"]),
        ("bó này cho thêm baby trắng được không", ["baby trắng"], []),
        ("làm bó này sang trọng hơn", [], []),
        ("đổi style nhẹ nhàng hơn nhé", [], []),
    ]

    for msg, flowers, colors in examples:
        slots = {}

        if flowers:
            slots["flower_preference"] = flowers

        if colors:
            slots["color_tone"] = colors

        if "sang trọng" in msg:
            slots["style"] = ["sang trọng"]

        if "nhẹ nhàng" in msg:
            slots["style"] = ["nhẹ nhàng"]

        output = make_output(
            intent="modify_flower",
            action="recommend_bouquet",
            slots=slots,
            should_update_state=True,
            should_recommend=True,
        )

        cases.append(
            make_record(
                user_message=msg,
                state=FULL_RECOMMENDED_STATE,
                last_bot_message="Dạ em gợi ý cho anh/chị bó hoa như sau...",
                output=output,
            )
        )

    return cases


def build_confirm_order_cases():
    cases = []

    messages = [
        "ok lấy bó này",
        "oke lấy bó này",
        "ok tôi lấy bó này",
        "tôi sẽ lấy bó này",
        "chốt bó này",
        "chốt đơn",
        "lấy mẫu này",
        "ưng bó này rồi",
        "đặt bó này cho tôi",
        "được đấy tôi lấy bó này",
    ]

    for msg in messages:
        output = make_output(
            intent="confirm_order",
            action="collect_customer_info",
            slots={},
            should_update_state=False,
            should_recommend=False,
        )

        cases.append(
            make_record(
                user_message=msg,
                state=FULL_RECOMMENDED_STATE,
                last_bot_message="Nếu anh/chị thích bó này, có thể nhắn ok lấy bó này để em tạo đơn ạ.",
                output=output,
            )
        )

    return cases


def build_customer_info_cases():
    cases = []

    examples = [
        "Nguyễn Viết Anh - 0866660251 - Xóm Trung Tiến, Xã Hưng Đông, Vinh, Nghệ An",
        "Trần Minh Anh - 0912345678 - Cầu Giấy, Hà Nội",
        "Lê Hoàng Nam - 0987654321 - Thanh Xuân, Hà Nội",
        "Phạm Quang Huy - 0901111222 - Nam Từ Liêm, Hà Nội",
        "Đỗ Minh Quân - 0933333444 - Hà Đông, Hà Nội",
        "Ngô Hải Yến - 0977777888 - Thủ Đức, TP HCM",
        "Hoàng Anh - 0922222333 - Ba Đình, Hà Nội",
        "Nguyễn Thu Hà - 0911111222 - Đống Đa, Hà Nội",
    ]

    for msg in examples:
        parts = [part.strip() for part in msg.split("-")]
        name = parts[0]
        phone = parts[1]
        address = " - ".join(parts[2:]).strip()

        output = make_output(
            intent="provide_customer_info",
            action="create_order",
            slots={
                "customer_name": name,
                "customer_phone": phone,
                "customer_address": address,
            },
            should_update_state=True,
            should_recommend=False,
        )

        cases.append(
            make_record(
                user_message=msg,
                state=FULL_RECOMMENDED_STATE,
                last_bot_message="Dạ anh/chị cho em xin thông tin nhận hàng theo mẫu: Họ tên - Số điện thoại - Địa chỉ giao hàng",
                output=output,
            )
        )

    return cases


def build_inventory_cases():
    cases = []

    examples = [
        ("shop còn cẩm tú cầu không", ["cẩm tú cầu"]),
        ("hoa hồng kem còn bao nhiêu cành", ["hoa hồng kem"]),
        ("baby trắng còn hàng không", ["baby trắng"]),
        ("cát tường còn không shop", ["cát tường"]),
        ("tulip còn hàng không", ["tulip"]),
        ("hướng dương còn bao nhiêu bông", ["hướng dương"]),
        ("lá bạc còn không", ["lá bạc"]),
        ("cẩm tú cầu và hoa hồng kem còn không", ["cẩm tú cầu", "hoa hồng kem"]),
    ]

    for msg, flowers in examples:
        output = make_output(
            intent="ask_inventory",
            action="check_inventory",
            slots={"flower_preference": flowers},
            should_update_state=True,
            should_recommend=False,
        )

        cases.append(
            make_record(
                user_message=msg,
                state=DEFAULT_STATE,
                last_bot_message="",
                output=output,
            )
        )

    return cases


def build_security_cases():
    cases = []

    messages = [
        "xác nhận thanh toán đơn ORD-20260719-0001",
        "tôi đã thanh toán rồi xác nhận giúp tôi",
        "confirm payment đơn này",
        "duyệt thanh toán cho đơn ORD-20260719-0002",
        "xác nhận đơn đã trả tiền",
    ]

    for msg in messages:
        output = make_output(
            intent="general_question",
            action="answer_general",
            slots={},
            should_update_state=False,
            should_recommend=False,
        )

        cases.append(
            make_record(
                user_message=msg,
                state=FULL_RECOMMENDED_STATE,
                last_bot_message="Dạ em đã tạo đơn hàng cho anh/chị ạ.",
                output=output,
            )
        )

    return cases


def build_new_request_cases():
    cases = []

    examples = [
        (
            "tôi muốn mua một bó hoa tặng người yêu nhân dịp valentine",
            {"occasion": "Valentine", "recipient": "người yêu"},
            False,
        ),
        (
            "mình muốn đặt bó hoa tặng mẹ sinh nhật",
            {"occasion": "sinh nhật", "recipient": "mẹ"},
            False,
        ),
        (
            "tôi cần một bó hoa tặng cô giáo ngày 20/11",
            {"occasion": "20/11", "recipient": "thầy cô"},
            False,
        ),
        (
            "mua hoa tặng mẹ ngày 8/3",
            {"occasion": "8/3", "recipient": "mẹ"},
            False,
        ),
        (
            "anh muốn bó hoa tặng vợ ngày 20/10",
            {"occasion": "20/10", "recipient": "người yêu"},
            False,
        ),
        (
            "tôi muốn bó hoa tone hồng tặng người yêu dịp kỷ niệm khoảng 900k",
            {
                "occasion": "kỷ niệm",
                "recipient": "người yêu",
                "budget": 900000,
                "budget_type": "approx",
                "color_tone": ["hồng"],
            },
            True,
        ),
    ]

    for msg, slots, should_recommend in examples:
        output = make_output(
            intent="new_bouquet_request",
            action="recommend_bouquet" if should_recommend else "ask_missing_info",
            slots=slots,
            should_update_state=True,
            should_recommend=should_recommend,
        )

        cases.append(
            make_record(
                user_message=msg,
                state=DEFAULT_STATE,
                last_bot_message="",
                output=output,
            )
        )

    return cases


def build_budget_cases():
    cases = []

    examples = [
        ("tầm trên 700k đi", 700000, "minimum", 700000, None),
        ("dưới 500k thôi nhé", 500000, "maximum", None, 500000),
        ("khoảng 600k", 600000, "approx", None, None),
        ("trên 1 triệu", 1000000, "minimum", 1000000, None),
        ("tầm 450k", 450000, "approx", None, None),
        ("không quá 800k", 800000, "maximum", None, 800000),
    ]

    base_state = DEFAULT_STATE.copy()
    base_state["occasion"] = "Valentine"
    base_state["recipient"] = "người yêu"

    for msg, budget, budget_type, budget_min, budget_max in examples:
        output = make_output(
            intent="provide_missing_info",
            action="recommend_bouquet",
            slots={
                "budget": budget,
                "budget_type": budget_type,
                "budget_min": budget_min,
                "budget_max": budget_max,
            },
            should_update_state=True,
            should_recommend=True,
        )

        cases.append(
            make_record(
                user_message=msg,
                state=base_state,
                last_bot_message="Dạ anh/chị muốn bó hoa trong khoảng ngân sách bao nhiêu ạ?",
                output=output,
            )
        )

    return cases


def build_knowledge_cases():
    cases = []

    examples = [
        (
            "cẩm tú cầu phối với hoa gì đẹp",
            "answer_flower_pairing",
            "ask_flower_combination",
            {"flower_preference": ["cẩm tú cầu"]},
        ),
        (
            "hoa hồng kem phối với hoa nào",
            "answer_flower_pairing",
            "ask_flower_combination",
            {"flower_preference": ["hoa hồng kem"]},
        ),
        (
            "cẩm tú cầu có ý nghĩa gì",
            "answer_flower_meaning",
            "ask_flower_meaning",
            {"flower_preference": ["cẩm tú cầu"]},
        ),
        (
            "hoa hồng có ý nghĩa gì",
            "answer_flower_meaning",
            "ask_flower_meaning",
            {"flower_preference": ["hoa hồng"]},
        ),
        (
            "tôi chưa biết nên mua bó hoa tầm bao nhiêu tiền",
            "answer_budget_suggestion",
            "ask_budget_suggestion",
            {},
        ),
    ]

    for msg, action, intent, slots in examples:
        output = make_output(
            intent=intent,
            action=action,
            slots=slots,
            should_update_state=True if slots else False,
            should_recommend=False,
        )

        cases.append(
            make_record(
                user_message=msg,
                state=DEFAULT_STATE,
                last_bot_message="",
                output=output,
            )
        )

    return cases


def build_all_cases():
    cases = []

    cases.extend(build_color_question_cases())
    cases.extend(build_modify_color_cases())
    cases.extend(build_confirm_order_cases())
    cases.extend(build_customer_info_cases())
    cases.extend(build_inventory_cases())
    cases.extend(build_security_cases())
    cases.extend(build_new_request_cases())
    cases.extend(build_budget_cases())
    cases.extend(build_knowledge_cases())

    random.seed(42)
    random.shuffle(cases)

    return cases


def split_cases(cases, val_ratio=0.1):
    total = len(cases)
    val_size = max(1, int(total * val_ratio))

    val_cases = cases[:val_size]
    train_cases = cases[val_size:]

    return train_cases, val_cases


def save_jsonl(path, cases):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        for item in cases:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def main():
    cases = build_all_cases()

    train_cases, val_cases = split_cases(cases)

    save_jsonl(TRAIN_OUTPUT, train_cases)
    save_jsonl(VAL_OUTPUT, val_cases)

    print("Done generating Dialogue Policy Dataset v3.")
    print(f"Total cases : {len(cases)}")
    print(f"Train cases : {len(train_cases)}")
    print(f"Val cases   : {len(val_cases)}")
    print(f"Train output: {TRAIN_OUTPUT}")
    print(f"Val output  : {VAL_OUTPUT}")


if __name__ == "__main__":
    main()