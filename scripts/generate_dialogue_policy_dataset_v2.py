import json
import random
from pathlib import Path


OUTPUT_DIR = Path("data/processed")
TRAIN_PATH = OUTPUT_DIR / "dialogue_policy_train_v2.jsonl"
VAL_PATH = OUTPUT_DIR / "dialogue_policy_val_v2.jsonl"

RANDOM_SEED = 42
random.seed(RANDOM_SEED)


SYSTEM_PROMPT = (
    "Bạn là Dialogue Policy Model cho hệ thống tư vấn và quản lý cửa hàng hoa. "
    "Nhiệm vụ của bạn là đọc trạng thái hội thoại hiện tại, tin nhắn gần nhất của bot "
    "và tin nhắn mới của khách hàng, sau đó trả về JSON action hợp lệ. "
    "Chỉ trả về JSON, không giải thích."
)


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


OCCASION_ALIASES = {
    "Valentine": [
        "valentine",
        "lễ tình nhân",
        "ngày lễ tình nhân",
        "ngày tình yêu",
        "14/2",
        "14 tháng 2"
    ],
    "Quốc tế Phụ nữ": [
        "8/3",
        "8 tháng 3",
        "quốc tế phụ nữ",
        "ngày phụ nữ"
    ],
    "Phụ nữ Việt Nam": [
        "20/10",
        "20 tháng 10",
        "phụ nữ việt nam",
        "ngày phụ nữ việt nam"
    ],
    "Nhà giáo Việt Nam": [
        "20/11",
        "20 tháng 11",
        "ngày nhà giáo",
        "nhà giáo việt nam"
    ],
    "Giáng sinh": [
        "giáng sinh",
        "noel",
        "christmas"
    ],
    "Tết": [
        "tết",
        "tết nguyên đán",
        "năm mới"
    ],
    "Ngày của mẹ": [
        "ngày của mẹ",
        "mother's day",
        "tặng mẹ ngày của mẹ"
    ],
    "Sinh nhật": [
        "sinh nhật",
        "birthday",
        "mừng tuổi mới"
    ],
    "Kỷ niệm": [
        "kỷ niệm",
        "kỉ niệm",
        "anniversary",
        "kỷ niệm yêu nhau",
        "kỷ niệm ngày cưới"
    ],
    "Tốt nghiệp": [
        "tốt nghiệp",
        "ra trường",
        "graduation"
    ],
    "Khai trương": [
        "khai trương",
        "mở cửa hàng",
        "mừng khai trương"
    ],
    "Cầu hôn": [
        "cầu hôn",
        "proposal",
        "ngỏ lời cầu hôn"
    ],
    "Tỏ tình": [
        "tỏ tình",
        "thổ lộ tình cảm",
        "confess"
    ],
    "Xin lỗi": [
        "xin lỗi",
        "làm hòa",
        "muốn xin lỗi"
    ],
    "Cảm ơn": [
        "cảm ơn",
        "tri ân",
        "biết ơn"
    ],
    "Chia buồn": [
        "chia buồn",
        "viếng",
        "đám tang"
    ],
    "Thăm bệnh": [
        "thăm bệnh",
        "đi viện",
        "người ốm"
    ]
}


RECIPIENT_ALIASES = {
    "người yêu": [
        "người yêu",
        "bạn gái",
        "bạn trai",
        "crush",
        "vợ",
        "chồng"
    ],
    "mẹ": [
        "mẹ",
        "má",
        "mẹ mình",
        "mẹ tôi"
    ],
    "thầy cô": [
        "thầy cô",
        "cô giáo",
        "thầy giáo",
        "giảng viên"
    ],
    "bạn bè": [
        "bạn",
        "bạn thân",
        "bạn bè",
        "một người bạn"
    ],
    "đồng nghiệp": [
        "đồng nghiệp",
        "sếp",
        "chị cùng công ty",
        "anh cùng công ty"
    ],
    "khách hàng": [
        "khách hàng",
        "đối tác",
        "client"
    ]
}


BUDGET_CASES = [
    {
        "text": "khoảng 500k",
        "budget": 500000,
        "budget_min": 425000,
        "budget_max": 575000,
        "budget_type": "approximate"
    },
    {
        "text": "tầm 700k",
        "budget": 700000,
        "budget_min": 595000,
        "budget_max": 805000,
        "budget_type": "approximate"
    },
    {
        "text": "khoảng 1 triệu",
        "budget": 1000000,
        "budget_min": 850000,
        "budget_max": 1150000,
        "budget_type": "approximate"
    },
    {
        "text": "dưới 500k",
        "budget": 500000,
        "budget_min": None,
        "budget_max": 500000,
        "budget_type": "maximum"
    },
    {
        "text": "không quá 800k",
        "budget": 800000,
        "budget_min": None,
        "budget_max": 800000,
        "budget_type": "maximum"
    },
    {
        "text": "trên 1 triệu",
        "budget": 1000000,
        "budget_min": 1000000,
        "budget_max": None,
        "budget_type": "minimum"
    },
    {
        "text": "từ 500k đến 1 triệu",
        "budget": 750000,
        "budget_min": 500000,
        "budget_max": 1000000,
        "budget_type": "range"
    },
    {
        "text": "từ 700k tới 1tr2",
        "budget": 950000,
        "budget_min": 700000,
        "budget_max": 1200000,
        "budget_type": "range"
    }
]


FLOWER_ALIASES = {
    "cẩm tú cầu": ["cẩm tú cầu", "hydrangea"],
    "hoa hồng kem": ["hoa hồng kem", "hồng kem"],
    "hoa hồng": ["hoa hồng", "rose"],
    "baby trắng": ["baby trắng", "hoa baby", "baby"],
    "tulip": ["tulip", "hoa tulip"],
    "hướng dương": ["hướng dương", "hoa hướng dương"],
    "cát tường": ["cát tường", "hoa cát tường"],
    "lá bạc": ["lá bạc", "silver dollar"]
}


COLOR_TONES = [
    "hồng",
    "trắng",
    "đỏ",
    "vàng",
    "tím",
    "pastel",
    "kem",
    "xanh"
]


STYLES = [
    "nhẹ nhàng",
    "sang trọng",
    "tối giản",
    "rực rỡ",
    "dễ thương",
    "trang nhã",
    "bó giấy Hàn Quốc",
    "bó tròn",
    "bó dài"
]


def make_slots(**kwargs):
    slots = DEFAULT_SLOTS.copy()

    for key, value in kwargs.items():
        slots[key] = value

    return slots


def make_output(
    intent,
    action,
    slots=None,
    should_update_state=False,
    should_recommend=False,
    should_check_inventory=False,
    should_create_order=False,
    should_collect_customer_info=False,
    response_goal=""
):
    return {
        "intent": intent,
        "action": action,
        "slots": slots or DEFAULT_SLOTS.copy(),
        "should_update_state": should_update_state,
        "should_recommend": should_recommend,
        "should_check_inventory": should_check_inventory,
        "should_create_order": should_create_order,
        "should_collect_customer_info": should_collect_customer_info,
        "response_goal": response_goal
    }


def make_chat_case(state, last_bot, user_message, output):
    user_content = (
        f"STATE:\n{json.dumps(state, ensure_ascii=False)}\n\n"
        f"LAST_BOT:\n{last_bot}\n\n"
        f"USER:\n{user_message}"
    )

    return {
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_content
            },
            {
                "role": "assistant",
                "content": json.dumps(output, ensure_ascii=False)
            }
        ]
    }


def empty_state():
    return DEFAULT_SLOTS.copy()


def random_occasion():
    occasion = random.choice(list(OCCASION_ALIASES.keys()))
    alias = random.choice(OCCASION_ALIASES[occasion])
    return occasion, alias


def random_recipient():
    recipient = random.choice(list(RECIPIENT_ALIASES.keys()))
    alias = random.choice(RECIPIENT_ALIASES[recipient])
    return recipient, alias


def random_flower():
    flower = random.choice(list(FLOWER_ALIASES.keys()))
    alias = random.choice(FLOWER_ALIASES[flower])
    return flower, alias


def generate_new_request_cases(n=400):
    cases = []

    templates = [
        "tôi muốn đặt một bó hoa tặng {recipient_alias} nhân dịp {occasion_alias}",
        "mình cần bó hoa cho {recipient_alias} vào {occasion_alias}",
        "cho tôi một bó hoa để tặng {recipient_alias} ngày {occasion_alias}",
        "{occasion_alias} này tôi muốn mua hoa cho {recipient_alias}",
        "tư vấn giúp tôi bó hoa tặng {recipient_alias} dịp {occasion_alias}",
        "mua hoa cho {recipient_alias} {occasion_alias}",
        "cần bó hoa {style} tặng {recipient_alias} dịp {occasion_alias}",
        "tôi muốn bó hoa tone {color} cho {recipient_alias} ngày {occasion_alias}",
        "cho mình bó hoa có {flower_alias} tặng {recipient_alias} dịp {occasion_alias}",
        "đặt bó hoa {budget_text} tặng {recipient_alias} dịp {occasion_alias}"
    ]

    for _ in range(n):
        occasion, occasion_alias = random_occasion()
        recipient, recipient_alias = random_recipient()
        budget_case = random.choice(BUDGET_CASES)
        flower, flower_alias = random_flower()
        color = random.choice(COLOR_TONES)
        style = random.choice(STYLES)

        template = random.choice(templates)
        user_message = template.format(
            recipient_alias=recipient_alias,
            occasion_alias=occasion_alias,
            budget_text=budget_case["text"],
            flower_alias=flower_alias,
            color=color,
            style=style
        )

        has_budget = "{budget_text}" in template
        has_flower = "{flower_alias}" in template
        has_color = "{color}" in template
        has_style = "{style}" in template

        slots = make_slots(
            occasion=occasion,
            recipient=recipient,
            budget=budget_case["budget"] if has_budget else None,
            budget_min=budget_case["budget_min"] if has_budget else None,
            budget_max=budget_case["budget_max"] if has_budget else None,
            budget_type=budget_case["budget_type"] if has_budget else None,
            flower_preference=[flower] if has_flower else [],
            color_tone=[color] if has_color else [],
            style=[style] if has_style else []
        )

        should_recommend = has_budget

        output = make_output(
            intent="new_bouquet_request" if should_recommend else "provide_missing_info",
            action="recommend_bouquet" if should_recommend else "ask_missing_info",
            slots=slots,
            should_update_state=True,
            should_recommend=should_recommend,
            should_check_inventory=should_recommend,
            response_goal=(
                "Đề xuất bó hoa phù hợp với yêu cầu, ngân sách và tồn kho."
                if should_recommend
                else "Hỏi thêm ngân sách của khách."
            )
        )

        cases.append(make_chat_case(empty_state(), "", user_message, output))

    return cases


def generate_provide_missing_budget_cases(n=250):
    cases = []

    last_bot = "Dạ anh/chị muốn bó hoa khoảng bao nhiêu tiền ạ?"

    for _ in range(n):
        occasion, occasion_alias = random_occasion()
        recipient, recipient_alias = random_recipient()
        budget_case = random.choice(BUDGET_CASES)

        state = make_slots(
            occasion=occasion,
            recipient=recipient
        )

        user_message = budget_case["text"]

        slots = make_slots(
            budget=budget_case["budget"],
            budget_min=budget_case["budget_min"],
            budget_max=budget_case["budget_max"],
            budget_type=budget_case["budget_type"]
        )

        output = make_output(
            intent="provide_missing_info",
            action="recommend_bouquet",
            slots=slots,
            should_update_state=True,
            should_recommend=True,
            should_check_inventory=True,
            response_goal="Cập nhật ngân sách và đề xuất bó hoa phù hợp."
        )

        cases.append(make_chat_case(state, last_bot, user_message, output))

    return cases


def generate_price_question_cases(n=120):
    cases = []

    messages = [
        "bó hoa bên bạn giá bao nhiêu",
        "shop có những mức giá nào",
        "bó rẻ nhất tầm bao nhiêu",
        "bó đẹp tầm bao nhiêu tiền",
        "mức giá phổ biến là bao nhiêu",
        "tôi chưa biết nên chọn tầm tiền nào",
        "bao nhiêu tiền thì có bó hoa đẹp",
        "bó cao cấp nhất giá bao nhiêu",
        "bó premium bên mình khoảng bao nhiêu",
        "đắt nhất là bao nhiêu"
    ]

    for _ in range(n):
        msg = random.choice(messages)

        if "cao cấp" in msg or "premium" in msg or "đắt nhất" in msg:
            intent = "ask_premium_option"
            action = "answer_premium_option"
            goal = "Giải thích các mức giá bó hoa cao cấp/premium."
        else:
            intent = "ask_price_range"
            action = "answer_price_info"
            goal = "Giải thích các mức giá bó hoa phổ biến."

        output = make_output(
            intent=intent,
            action=action,
            slots=DEFAULT_SLOTS.copy(),
            should_update_state=False,
            should_recommend=False,
            should_check_inventory=False,
            response_goal=goal
        )

        cases.append(make_chat_case(empty_state(), "", msg, output))

    return cases


def generate_inventory_cases(n=120):
    cases = []

    templates = [
        "shop còn {flower_alias} không",
        "bên mình có {flower_alias} không",
        "{flower_alias} còn hàng không",
        "kiểm tra giúp tôi {flower_alias} còn không",
        "hoa {flower_alias} còn bao nhiêu cành"
    ]

    for _ in range(n):
        flower, flower_alias = random_flower()
        msg = random.choice(templates).format(flower_alias=flower_alias)

        slots = make_slots(
            flower_preference=[flower]
        )

        output = make_output(
            intent="ask_inventory",
            action="check_inventory",
            slots=slots,
            should_update_state=True,
            should_recommend=False,
            should_check_inventory=True,
            response_goal="Kiểm tra tồn kho loại hoa khách hỏi."
        )

        cases.append(make_chat_case(empty_state(), "", msg, output))

    return cases


def generate_pairing_cases(n=120):
    cases = []

    templates = [
        "{flower_alias} phối với hoa nào đẹp",
        "{flower_alias} nên kết hợp với hoa nào",
        "{flower_alias} hợp với hoa nào",
        "nên phối {flower_alias} với gì",
        "hoa {flower_alias} đi với hoa nào thì đẹp"
    ]

    for _ in range(n):
        flower, flower_alias = random_flower()
        msg = random.choice(templates).format(flower_alias=flower_alias)

        slots = make_slots(
            flower_preference=[flower]
        )

        output = make_output(
            intent="ask_flower_combination",
            action="answer_flower_pairing",
            slots=slots,
            should_update_state=True,
            should_recommend=False,
            should_check_inventory=True,
            response_goal="Tư vấn loại hoa nên phối và cách phối phù hợp."
        )

        cases.append(make_chat_case(empty_state(), "", msg, output))

    return cases


def generate_modify_cases(n=160):
    cases = []

    state = make_slots(
        occasion="Sinh nhật",
        recipient="mẹ",
        budget=700000,
        budget_min=595000,
        budget_max=805000,
        budget_type="approximate",
        flower_preference=["cẩm tú cầu"]
    )

    messages = [
        ("đổi sang tone hồng được không", "modify_color", make_slots(color_tone=["hồng"])),
        ("đổi sang tone trắng đi", "modify_color", make_slots(color_tone=["trắng"])),
        ("thêm hoa hồng kem vào bó", "modify_flower", make_slots(flower_preference=["hoa hồng kem"])),
        ("bỏ tulip ra giúp tôi", "modify_flower", make_slots(flower_avoidance=["tulip"])),
        ("tăng ngân sách lên khoảng 1 triệu", "modify_budget", make_slots(
            budget=1000000,
            budget_min=850000,
            budget_max=1150000,
            budget_type="approximate"
        )),
        ("giảm xuống dưới 500k", "modify_budget", make_slots(
            budget=500000,
            budget_max=500000,
            budget_type="maximum"
        )),
        ("đổi sang phong cách sang trọng", "modify_style", make_slots(style=["sang trọng"])),
        ("cho kiểu bó giấy Hàn Quốc", "modify_style", make_slots(style=["bó giấy Hàn Quốc"]))
    ]

    for _ in range(n):
        msg, intent, slots = random.choice(messages)

        output = make_output(
            intent=intent,
            action="update_bouquet",
            slots=slots,
            should_update_state=True,
            should_recommend=True,
            should_check_inventory=True,
            response_goal="Cập nhật yêu cầu mới của khách và đề xuất lại bó hoa."
        )

        cases.append(make_chat_case(state, "Anh/chị muốn em điều chỉnh gì thêm không ạ?", msg, output))

    return cases


def generate_confirm_order_cases(n=80):
    cases = []

    state = make_slots(
        occasion="Valentine",
        recipient="người yêu",
        budget=800000,
        budget_min=680000,
        budget_max=920000,
        budget_type="approximate"
    )

    messages = [
        "ok lấy bó này",
        "chốt bó này đi",
        "mình lấy mẫu này",
        "oke đặt bó này",
        "đồng ý lấy bó này",
        "okela lấy phương án này",
        "tạo đơn giúp tôi",
        "chốt đơn"
    ]

    for _ in range(n):
        msg = random.choice(messages)

        output = make_output(
            intent="confirm_order",
            action="collect_customer_info",
            slots=DEFAULT_SLOTS.copy(),
            should_update_state=False,
            should_recommend=False,
            should_check_inventory=True,
            should_create_order=False,
            should_collect_customer_info=True,
            response_goal="Khách đã chốt phương án, cần xin tên, số điện thoại và địa chỉ giao hàng."
        )

        cases.append(make_chat_case(state, "Anh/chị muốn em giữ phương án này không ạ?", msg, output))

    return cases


def generate_customer_info_cases(n=120):
    cases = []

    state = make_slots(
        occasion="Valentine",
        recipient="người yêu",
        budget=800000,
        budget_min=680000,
        budget_max=920000,
        budget_type="approximate"
    )

    last_bot = "Dạ để tạo đơn, anh/chị cho em xin tên người đặt, số điện thoại và địa chỉ giao hàng ạ."

    samples = [
        ("Nguyễn Văn An - 0912345678 - Cầu Giấy Hà Nội", "Nguyễn Văn An", "0912345678", "Cầu Giấy Hà Nội"),
        ("Trần Mai Anh - 0987654321 - Mỹ Đình Hà Nội", "Trần Mai Anh", "0987654321", "Mỹ Đình Hà Nội"),
        ("tên tôi là Lê Minh, số điện thoại 0901111222, giao ở Hà Đông", "Lê Minh", "0901111222", "Hà Đông"),
        ("mình tên Phạm Hương, sđt 0933333444, địa chỉ là Ba Đình", "Phạm Hương", "0933333444", "Ba Đình"),
        ("Hoàng Đức - 0829092076 - Thạch Hòa Thạch Thất Hòa Lạc", "Hoàng Đức", "0829092076", "Thạch Hòa Thạch Thất Hòa Lạc")
    ]

    for _ in range(n):
        msg, name, phone, address = random.choice(samples)

        slots = make_slots(
            customer_name=name,
            customer_phone=phone,
            customer_address=address
        )

        output = make_output(
            intent="provide_customer_info",
            action="create_order",
            slots=slots,
            should_update_state=True,
            should_recommend=False,
            should_check_inventory=True,
            should_create_order=True,
            should_collect_customer_info=False,
            response_goal="Lưu thông tin khách hàng và tạo đơn hàng."
        )

        cases.append(make_chat_case(state, last_bot, msg, output))

    return cases


def generate_admin_block_cases(n=80):
    cases = []

    messages = [
        "xác nhận thanh toán đơn ORD-20260718-0001",
        "đã thanh toán đơn ORD-20260718-0002",
        "khách đã trả tiền đơn ORD-20260718-0003",
        "đã chuyển khoản đơn ORD-20260718-0004",
        "confirm payment ORD-20260718-0005"
    ]

    for _ in range(n):
        msg = random.choice(messages)

        output = make_output(
            intent="general_question",
            action="answer_general",
            slots=DEFAULT_SLOTS.copy(),
            should_update_state=False,
            should_recommend=False,
            should_check_inventory=False,
            should_create_order=False,
            should_collect_customer_info=False,
            response_goal="Từ chối xác nhận thanh toán vì đây là chức năng admin."
        )

        cases.append(make_chat_case(empty_state(), "", msg, output))

    return cases


def generate_unclear_cases(n=80):
    cases = []

    messages = [
        "alo",
        "shop ơi",
        "bên mình tư vấn sao",
        "hoa đẹp không",
        "mình chưa biết chọn gì",
        "tư vấn đi",
        "hôm nay có gì đẹp",
        "mình muốn xem thêm"
    ]

    for _ in range(n):
        msg = random.choice(messages)

        output = make_output(
            intent="unclear",
            action="clarify_user_intent",
            slots=DEFAULT_SLOTS.copy(),
            should_update_state=False,
            should_recommend=False,
            should_check_inventory=False,
            should_create_order=False,
            should_collect_customer_info=False,
            response_goal="Hỏi lại khách muốn tư vấn theo ngân sách, dịp tặng, người nhận, loại hoa hay kiểm tra kho."
        )

        cases.append(make_chat_case(empty_state(), "", msg, output))

    return cases


def generate_all_cases():
    cases = []

    cases.extend(generate_new_request_cases(400))
    cases.extend(generate_provide_missing_budget_cases(250))
    cases.extend(generate_price_question_cases(120))
    cases.extend(generate_inventory_cases(120))
    cases.extend(generate_pairing_cases(120))
    cases.extend(generate_modify_cases(160))
    cases.extend(generate_confirm_order_cases(80))
    cases.extend(generate_customer_info_cases(120))
    cases.extend(generate_admin_block_cases(80))
    cases.extend(generate_unclear_cases(80))

    random.shuffle(cases)

    return cases


def save_jsonl(path, items):
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cases = generate_all_cases()

    split_idx = int(len(cases) * 0.9)

    train_cases = cases[:split_idx]
    val_cases = cases[split_idx:]

    save_jsonl(TRAIN_PATH, train_cases)
    save_jsonl(VAL_PATH, val_cases)

    print("=== Dialogue Policy Dataset V2 Generated ===")
    print("Total:", len(cases))
    print("Train:", len(train_cases), "->", TRAIN_PATH)
    print("Val:", len(val_cases), "->", VAL_PATH)


if __name__ == "__main__":
    main()