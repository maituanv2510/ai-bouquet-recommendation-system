"""
Sinh synthetic dataset dạng chat-style JSONL để fine-tune LLM cho tác vụ
"trích xuất yêu cầu đặt hoa có cấu trúc" (structured bouquet requirement
extraction) từ tin nhắn khách hàng tiếng Việt.

Output:
    data/synthetic/customer_request_extraction_2000.jsonl

Số lượng: 2000 dòng (samples), mỗi dòng là 1 JSON object dạng:
{
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "<tin nhắn khách hàng tiếng Việt>"},
    {"role": "assistant", "content": "<JSON string đã trích xuất>"}
  ]
}

assistant.content là một JSON STRING hợp lệ (json.dumps) theo schema:
{
  "product_type": "bouquet",
  "occasion": null hoặc string,
  "recipient": null hoặc string,
  "budget": null hoặc number,
  "budget_type": null hoặc "maximum" | "around" | "minimum",
  "color_tone": list[string],
  "style": list[string],
  "meaning_intent": list[string],
  "flower_preference": list[string],
  "flower_avoidance": list[string],
  "delivery_time": null hoặc string,
  "missing_fields": list[string]
}

Dataset được tạo từ 8 nhóm request khác nhau để đảm bảo đa dạng:
    1. full_request       : request đầy đủ thông tin
    2. budget_max         : có ngân sách tối đa rõ ràng
    3. required_flower    : có loại hoa bắt buộc phải có
    4. avoided_flower     : có loại hoa khách không muốn
    5. vague_request       : request mơ hồ, thiếu nhiều thông tin
    6. delivery_time       : nhấn mạnh thời gian giao hoa
    7. special_occasion    : dịp đặc biệt (khai trương, tốt nghiệp, xin lỗi, cảm ơn)
    8. edge_case           : các trường hợp biên (không dấu, viết tắt, mâu thuẫn...)

random seed = 42 để đảm bảo tái lập được kết quả.
"""

import os
import json
import random
import unicodedata

RANDOM_SEED = 42
# Danh sách giá trị mẫu
OCCASIONS = [
    "tặng mẹ", "tặng bạn", "tặng người yêu", "sinh nhật", "khai trương",
    "tốt nghiệp", "xin lỗi", "cảm ơn", "thăm bệnh", "kỷ niệm",
]
SPECIAL_OCCASIONS = ["khai trương", "tốt nghiệp", "xin lỗi", "cảm ơn"]
OCCASION_TO_RECIPIENT = {
    "tặng mẹ": "mẹ", "tặng bạn": "bạn", "tặng người yêu": "người yêu",
}
SPECIAL_OCCASION_RECIPIENTS = {
    "khai trương": ["khách hàng", "sếp", "đồng nghiệp"],
    "tốt nghiệp": ["bạn", "cô giáo", "bạn nữ"],
    "xin lỗi": ["người yêu", "bạn"],
    "cảm ơn": ["cô giáo", "đồng nghiệp", "khách hàng", "sếp"],
}

RECIPIENTS = ["mẹ", "bạn", "bạn nữ", "người yêu", "sếp", "đồng nghiệp", "cô giáo", "khách hàng"]
FLOWERS = ["cẩm tú cầu", "hoa hồng", "baby's breath", "cát tường", "hướng dương", "tulip", "cẩm chướng", "đồng tiền"]
COLORS = ["hồng", "trắng", "xanh", "đỏ", "vàng", "tím"]
STYLES = ["nhẹ nhàng", "sang trọng", "tối giản", "rực rỡ", "lãng mạn", "thanh lịch"]
BUDGETS = [300000, 400000, 500000, 600000, 800000, 1000000]
MEANINGS = [
    "thể hiện tình yêu", "lời cảm ơn chân thành", "lời xin lỗi chân thành",
    "chúc mừng thành công", "động viên tinh thần", "chúc sức khỏe mau bình phục",
    "kỷ niệm đáng nhớ", "sự trân trọng",
]
# (cụm câu chèn vào tin nhắn, giá trị chuẩn hóa lưu vào delivery_time)
DELIVERY_PHRASES = [
    ("giao trong hôm nay", "hôm nay"),
    ("giao sáng mai", "sáng mai"),
    ("giao trước 18h", "trước 18h"),
    ("giao vào cuối tuần", "cuối tuần"),
    ("giao đúng 8h sáng mai", "8h sáng mai"),
    ("giao trong 2 giờ tới", "trong 2 giờ tới"),
    ("giao vào ngày mai", "ngày mai"),
    ("giao trước 12h trưa nay", "trước 12h trưa nay"),
]

STARTERS = [
    "Chào shop, ", "Shop ơi, ", "Mình muốn ", "Cho mình đặt ", "Cho mình hỏi ",
    "Mình cần ", "Shop tư vấn giúp mình, ", "Alo shop, ", "Em chào shop, ", "",
]
CLOSERS = [
    "", " được không shop?", " shop tư vấn giúp mình nhé.", " cảm ơn shop!",
    " nha shop.", " ạ.", " nhé!", " giúp mình với.",
]

IMPORTANT_FIELDS = ["occasion", "recipient", "budget", "color_tone", "style", "delivery_time"]

SYSTEM_PROMPT = (
    "You extract structured bouquet requirements from Vietnamese customer "
    "messages. Return only valid JSON."
)


# Hàm tiện ích

def cap(text: str) -> str:
    """Viết hoa chữ cái đầu câu."""
    text = text.strip()
    return text[0].upper() + text[1:] if text else text


def strip_diacritics(text: str) -> str:
    """Bỏ dấu tiếng Việt (mô phỏng khách hàng gõ không dấu)."""
    normalized = unicodedata.normalize("NFD", text)
    no_marks = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    no_marks = no_marks.replace("đ", "d").replace("Đ", "D")
    return unicodedata.normalize("NFC", no_marks)


def pick_colors(rng, k=None):
    if k is None:
        k = rng.randint(1, 3)
    k = max(0, min(k, len(COLORS)))
    return rng.sample(COLORS, k) if k > 0 else []


def pick_styles(rng, k=None):
    if k is None:
        k = rng.randint(1, 2)
    k = max(0, min(k, len(STYLES)))
    return rng.sample(STYLES, k) if k > 0 else []


def pick_flowers(rng, k=None):
    if k is None:
        k = rng.randint(1, 2)
    k = max(0, min(k, len(FLOWERS)))
    return rng.sample(FLOWERS, k) if k > 0 else []


def format_money_text(n: int, rng) -> str:
    """Sinh nhiều cách viết số tiền khác nhau trong văn nói."""
    forms = [f"{n:,}".replace(",", ".") + "đ", f"{n:,}".replace(",", ".") + " đồng"]
    if n % 1000 == 0:
        forms.append(f"{n // 1000}k")
    if n % 1_000_000 == 0:
        forms.append(f"{n // 1_000_000} triệu")
        forms.append(f"{n // 1_000_000}tr")
    return rng.choice(forms)


def budget_clause(n: int, budget_type: str, rng) -> str:
    money = format_money_text(n, rng)
    if budget_type == "maximum":
        template = rng.choice([
            "tối đa {m}", "trong khoảng {m} đổ lại", "không quá {m}",
            "dưới {m}", "chỉ tầm {m} thôi", "ngân sách tối đa {m}",
        ])
    elif budget_type == "minimum":
        template = rng.choice([
            "tối thiểu {m}", "từ {m} trở lên", "trên {m}", "ít nhất {m}",
        ])
    else:  # around
        template = rng.choice([
            "khoảng {m}", "tầm {m}", "ngân sách khoảng {m}", "trong khoảng {m}",
        ])
    return template.format(m=money)


def compute_missing(data: dict) -> list:
    missing = []
    for field in IMPORTANT_FIELDS:
        value = data.get(field)
        if value is None:
            missing.append(field)
        elif isinstance(value, list) and len(value) == 0:
            missing.append(field)
    return missing


def base_data(**kwargs) -> dict:
    """Tạo dict theo schema chuẩn, các field không truyền sẽ mang giá trị mặc định."""
    data = {
        "product_type": "bouquet",
        "occasion": None,
        "recipient": None,
        "budget": None,
        "budget_type": None,
        "color_tone": [],
        "style": [],
        "meaning_intent": [],
        "flower_preference": [],
        "flower_avoidance": [],
        "delivery_time": None,
    }
    data.update(kwargs)
    data["missing_fields"] = compute_missing(data)
    return data


def assemble_message(rng, clauses, shuffle=True) -> str:
    clauses = [c for c in clauses if c]
    if shuffle:
        rng.shuffle(clauses)
    starter = rng.choice(STARTERS)
    closer = rng.choice(CLOSERS)
    body = ", ".join(clauses)
    text = f"{starter}{body}{closer}"
    return cap(text)

# 1. Full request - đầy đủ thông tin

def gen_full_request(rng):
    occasion = rng.choice(OCCASIONS)
    recipient = OCCASION_TO_RECIPIENT.get(occasion) or rng.choice(RECIPIENTS)
    budget = rng.choice(BUDGETS)
    budget_type = rng.choice(["maximum", "around", "minimum"])
    colors = pick_colors(rng, rng.randint(1, 3))
    styles = pick_styles(rng, rng.randint(1, 2))
    meaning = [rng.choice(MEANINGS)] if rng.random() < 0.7 else []
    flower_pref = pick_flowers(rng, 1) if rng.random() < 0.6 else []
    flower_avoid = pick_flowers(rng, 1) if rng.random() < 0.2 else []
    flower_avoid = [f for f in flower_avoid if f not in flower_pref]
    if rng.random() < 0.6:
        delivery_phrase, delivery_val = rng.choice(DELIVERY_PHRASES)
    else:
        delivery_phrase, delivery_val = None, None

    clauses = [f"đặt hoa {occasion}", budget_clause(budget, budget_type, rng)]
    if occasion not in OCCASION_TO_RECIPIENT and rng.random() < 0.7:
        clauses.append(f"tặng cho {recipient}")
    if colors:
        clauses.append(f"tông màu {', '.join(colors)}")
    if styles:
        clauses.append(f"phong cách {', '.join(styles)}")
    if flower_pref:
        clauses.append(f"nhất định phải có {', '.join(flower_pref)}")
    if flower_avoid:
        clauses.append(f"không muốn có {', '.join(flower_avoid)}")
    if meaning:
        clauses.append(f"muốn thể hiện {meaning[0]}")
    if delivery_phrase:
        clauses.append(delivery_phrase)

    text = assemble_message(rng, clauses)
    data = base_data(
        occasion=occasion, recipient=recipient, budget=budget, budget_type=budget_type,
        color_tone=colors, style=styles, meaning_intent=meaning,
        flower_preference=flower_pref, flower_avoidance=flower_avoid,
        delivery_time=delivery_val,
    )
    return text, data


# 2. Budget max - có ngân sách tối đa rõ ràng

def gen_budget_max(rng):
    has_occasion = rng.random() < 0.7
    occasion = rng.choice(OCCASIONS) if has_occasion else None
    recipient = None
    if occasion in OCCASION_TO_RECIPIENT:
        recipient = OCCASION_TO_RECIPIENT[occasion]
    elif rng.random() < 0.5:
        recipient = rng.choice(RECIPIENTS)

    budget = rng.choice(BUDGETS)
    colors = pick_colors(rng, rng.randint(0, 2))
    styles = pick_styles(rng, rng.randint(0, 1))

    clauses = []
    clauses.append(f"hoa {occasion}" if occasion else "một bó hoa")
    if recipient and occasion not in OCCASION_TO_RECIPIENT:
        clauses.append(f"tặng {recipient}")
    clauses.append(budget_clause(budget, "maximum", rng))
    if colors:
        clauses.append(f"màu {', '.join(colors)}")
    if styles:
        clauses.append(f"phong cách {', '.join(styles)}")

    text = assemble_message(rng, clauses)
    data = base_data(
        occasion=occasion, recipient=recipient, budget=budget, budget_type="maximum",
        color_tone=colors, style=styles,
    )
    return text, data


# 3. Required flower - có hoa bắt buộc phải có

def gen_required_flower(rng):
    occasion = rng.choice(OCCASIONS) if rng.random() < 0.6 else None
    recipient = OCCASION_TO_RECIPIENT.get(occasion) if occasion else None
    if recipient is None and rng.random() < 0.4:
        recipient = rng.choice(RECIPIENTS)

    flower_pref = pick_flowers(rng, rng.randint(1, 2))
    budget = rng.choice(BUDGETS) if rng.random() < 0.4 else None
    budget_type = rng.choice(["maximum", "around"]) if budget else None
    colors = pick_colors(rng, rng.randint(0, 2))

    required_phrase = rng.choice([
        "nhất định phải có {f}", "bắt buộc phải có {f}", "phải có {f} trong bó nha",
        "mình chỉ muốn {f} thôi", "làm bó hoa có {f}",
    ]).format(f=", ".join(flower_pref))

    clauses = [required_phrase]
    if occasion:
        clauses.append(f"để {occasion}" if occasion not in OCCASION_TO_RECIPIENT else f"đặt hoa {occasion}")
    if recipient and occasion not in OCCASION_TO_RECIPIENT and recipient:
        clauses.append(f"tặng {recipient}")
    if budget:
        clauses.append(budget_clause(budget, budget_type, rng))
    if colors:
        clauses.append(f"tông màu {', '.join(colors)}")

    text = assemble_message(rng, clauses)
    data = base_data(
        occasion=occasion, recipient=recipient, budget=budget, budget_type=budget_type,
        color_tone=colors, flower_preference=flower_pref,
    )
    return text, data


# 4. Avoided flower - có hoa không muốn


def gen_avoided_flower(rng):
    occasion = rng.choice(OCCASIONS) if rng.random() < 0.6 else None
    recipient = OCCASION_TO_RECIPIENT.get(occasion) if occasion else None
    if recipient is None and rng.random() < 0.4:
        recipient = rng.choice(RECIPIENTS)

    flower_avoid = pick_flowers(rng, rng.randint(1, 2))
    flower_pref = pick_flowers(rng, 1) if rng.random() < 0.3 else []
    flower_pref = [f for f in flower_pref if f not in flower_avoid]
    colors = pick_colors(rng, rng.randint(0, 2))
    styles = pick_styles(rng, rng.randint(0, 1))

    avoid_phrase = rng.choice([
        "không thích {f}", "tránh giúp mình hoa {f}", "đừng cho {f} vào nha",
        "mình bị dị ứng {f} nên đừng cho vào", "không muốn có {f}",
    ]).format(f=", ".join(flower_avoid))

    clauses = [avoid_phrase]
    if occasion:
        clauses.append(f"đặt hoa {occasion}")
    if recipient and occasion not in OCCASION_TO_RECIPIENT and recipient:
        clauses.append(f"tặng {recipient}")
    if flower_pref:
        clauses.append(f"thay vào đó cho mình {', '.join(flower_pref)}")
    if colors:
        clauses.append(f"tông màu {', '.join(colors)}")
    if styles:
        clauses.append(f"phong cách {', '.join(styles)}")

    text = assemble_message(rng, clauses)
    data = base_data(
        occasion=occasion, recipient=recipient, color_tone=colors, style=styles,
        flower_preference=flower_pref, flower_avoidance=flower_avoid,
    )
    return text, data


# 5. Vague request - request mơ hồ


VAGUE_TEMPLATES = [
    "Shop ơi cho mình xem hoa đẹp đẹp nha.",
    "Mình muốn mua hoa nhưng chưa biết chọn loại nào.",
    "Tư vấn giúp mình bó hoa nào cũng được ạ.",
    "Cho mình một bó hoa được không shop?",
    "Mình cần mua hoa, shop gợi ý giúp mình với.",
    "Có hoa nào đẹp không shop, mình chưa nghĩ ra mua gì.",
    "Mình muốn đặt hoa, chưa biết dịp gì cả, cứ đẹp là được.",
    "Shop có bó hoa nào bán chạy không, giới thiệu mình xem.",
    "Mình phân vân quá, shop tư vấn giúp mình loại hoa nào hợp nha.",
    "Cho mình hỏi bên shop có hoa không ạ?",
]


def gen_vague_request(rng):
    if rng.random() < 0.5:
        text = rng.choice(VAGUE_TEMPLATES)
        data = base_data()
        return text, data

    # Mơ hồ nhưng có 1 mẩu thông tin rất nhỏ, không rõ ràng
    hint_type = rng.choice(["occasion_only", "color_only", "style_only", "budget_vague"])
    if hint_type == "occasion_only":
        occasion = rng.choice(OCCASIONS)
        text = assemble_message(rng, [f"mua hoa {occasion}", "nhưng chưa biết chọn loại nào"])
        data = base_data(occasion=occasion)
    elif hint_type == "color_only":
        color = rng.choice(COLORS)
        text = assemble_message(rng, [f"thích màu {color}", "còn lại shop tư vấn giúp mình"])
        data = base_data(color_tone=[color])
    elif hint_type == "style_only":
        style = rng.choice(STYLES)
        text = assemble_message(rng, [f"muốn phong cách {style} thôi", "chưa nghĩ ra gì thêm"])
        data = base_data(style=[style])
    else:  # budget_vague
        text = assemble_message(rng, ["mình có ít tiền thôi", "shop tư vấn bó nào rẻ rẻ giúp mình"])
        data = base_data()
    return text, data


# 6. Delivery time - nhấn mạnh thời gian giao


def gen_delivery_time(rng):
    delivery_phrase, delivery_val = rng.choice(DELIVERY_PHRASES)
    occasion = rng.choice(OCCASIONS) if rng.random() < 0.5 else None
    recipient = OCCASION_TO_RECIPIENT.get(occasion) if occasion else None
    if recipient is None and rng.random() < 0.3:
        recipient = rng.choice(RECIPIENTS)
    budget = rng.choice(BUDGETS) if rng.random() < 0.3 else None
    budget_type = rng.choice(["maximum", "around"]) if budget else None

    clauses = [delivery_phrase]
    if occasion:
        clauses.append(f"đặt hoa {occasion}")
    if recipient and occasion not in OCCASION_TO_RECIPIENT and recipient:
        clauses.append(f"tặng {recipient}")
    if budget:
        clauses.append(budget_clause(budget, budget_type, rng))

    text = assemble_message(rng, clauses)
    data = base_data(
        occasion=occasion, recipient=recipient, budget=budget, budget_type=budget_type,
        delivery_time=delivery_val,
    )
    return text, data

# 7. Special occasion - khai trương, tốt nghiệp, xin lỗi, cảm ơn


def gen_special_occasion(rng):
    occasion = rng.choice(SPECIAL_OCCASIONS)
    recipient = rng.choice(SPECIAL_OCCASION_RECIPIENTS[occasion]) if rng.random() < 0.7 else None
    budget = rng.choice(BUDGETS) if rng.random() < 0.6 else None
    budget_type = rng.choice(["maximum", "around", "minimum"]) if budget else None
    colors = pick_colors(rng, rng.randint(0, 2))
    styles = pick_styles(rng, rng.randint(0, 2))
    meaning = [rng.choice(MEANINGS)] if rng.random() < 0.5 else []
    if rng.random() < 0.4:
        delivery_phrase, delivery_val = rng.choice(DELIVERY_PHRASES)
    else:
        delivery_phrase, delivery_val = None, None

    clauses = [f"đặt hoa {occasion}"]
    if recipient:
        clauses.append(f"tặng {recipient}")
    if budget:
        clauses.append(budget_clause(budget, budget_type, rng))
    if colors:
        clauses.append(f"tông màu {', '.join(colors)}")
    if styles:
        clauses.append(f"phong cách {', '.join(styles)}")
    if meaning:
        clauses.append(f"để {meaning[0]}")
    if delivery_phrase:
        clauses.append(delivery_phrase)

    text = assemble_message(rng, clauses)
    data = base_data(
        occasion=occasion, recipient=recipient, budget=budget, budget_type=budget_type,
        color_tone=colors, style=styles, meaning_intent=meaning, delivery_time=delivery_val,
    )
    return text, data


# 8. Edge cases


def gen_edge_case(rng):
    sub_type = rng.choice([
        "empty_short", "no_diacritics", "slang_budget", "no_color_preference",
        "all_caps_urgent", "long_rambling", "budget_range", "only_delivery_no_context",
    ])

    if sub_type == "empty_short":
        text = rng.choice(["Cho mình đặt hoa.", "Mua hoa.", "Đặt hoa giúp mình.", "Có hoa không shop?"])
        data = base_data()

    elif sub_type == "no_diacritics":
        occasion = rng.choice(OCCASIONS)
        recipient = OCCASION_TO_RECIPIENT.get(occasion) or rng.choice(RECIPIENTS)
        raw = assemble_message(rng, [
            f"dat hoa {occasion}" if occasion in OCCASION_TO_RECIPIENT else f"dat hoa {occasion} tang {recipient}",
        ])
        text = strip_diacritics(raw)
        data = base_data(occasion=occasion, recipient=recipient)

    elif sub_type == "slang_budget":
        budget = rng.choice(BUDGETS)
        btype = rng.choice(["maximum", "around"])
        slang = f"{budget // 1000}k đổ lại" if btype == "maximum" else f"tầm {budget // 1000}k"
        text = assemble_message(rng, [f"mình có {slang} thôi", "shop tư vấn giúp mình"])
        data = base_data(budget=budget, budget_type=btype)

    elif sub_type == "no_color_preference":
        occasion = rng.choice(OCCASIONS)
        text = assemble_message(rng, [f"đặt hoa {occasion}", "màu gì cũng được, shop tự chọn giúp mình"])
        data = base_data(occasion=occasion, recipient=OCCASION_TO_RECIPIENT.get(occasion))

    elif sub_type == "all_caps_urgent":
        occasion = rng.choice(OCCASIONS)
        delivery_phrase, delivery_val = rng.choice(DELIVERY_PHRASES)
        text = f"SHOP ƠI MÌNH CẦN GẤP HOA {occasion.upper()}, {delivery_phrase.upper()} NHÉ!!!"
        data = base_data(occasion=occasion, recipient=OCCASION_TO_RECIPIENT.get(occasion), delivery_time=delivery_val)

    elif sub_type == "long_rambling":
        occasion1 = rng.choice(OCCASIONS)
        occasion2 = rng.choice([o for o in OCCASIONS if o != occasion1])
        colors = pick_colors(rng, 2)
        text = (
            f"Chào shop, mình đang phân vân không biết nên đặt hoa {occasion1} hay hoa {occasion2} nữa, "
            f"chắc thôi lấy hoa {occasion1} cho chắc, mình thích màu {', '.join(colors)}, "
            "mà thôi để shop tư vấn thêm giúp mình cũng được."
        )
        data = base_data(occasion=occasion1, color_tone=colors)

    elif sub_type == "budget_range":
        lo, hi = sorted(rng.sample(BUDGETS, 2))
        text = assemble_message(rng, [
            f"ngân sách khoảng {lo // 1000}k đến {hi // 1000}k", "shop chọn giúp mình bó phù hợp",
        ])
        # Diễn giải khoảng ngân sách -> lấy giá trị trung bình, kiểu "around"
        avg_budget = (lo + hi) // 2
        data = base_data(budget=avg_budget, budget_type="around")

    else:  # only_delivery_no_context
        delivery_phrase, delivery_val = rng.choice(DELIVERY_PHRASES)
        text = cap(f"{delivery_phrase} được không shop?")
        data = base_data(delivery_time=delivery_val)

    return text, data


# Bộ sinh dataset chính


CATEGORY_GENERATORS = [
    (gen_full_request, 300),
    (gen_budget_max, 250),
    (gen_required_flower, 250),
    (gen_avoided_flower, 200),
    (gen_vague_request, 250),
    (gen_delivery_time, 250),
    (gen_special_occasion, 300),
    (gen_edge_case, 200),
]


def build_dataset(rng) -> list:
    samples = []
    for generator_fn, count in CATEGORY_GENERATORS:
        for _ in range(count):
            user_text, data = generator_fn(rng)
            assistant_content = json.dumps(data, ensure_ascii=False)
            record = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": assistant_content},
                ]
            }
            samples.append(record)

    rng.shuffle(samples)  # trộn thứ tự các nhóm để dataset không bị phân khối
    return samples


def main():
    output_dir = os.path.join("data", "synthetic")
    output_path = os.path.join(output_dir, "customer_request_extraction_2000.jsonl")
    os.makedirs(output_dir, exist_ok=True)

    rng = random.Random(RANDOM_SEED)
    samples = build_dataset(rng)

    with open(output_path, "w", encoding="utf-8") as f:
        for record in samples:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Đã sinh {len(samples)} samples.")
    print(f"File được lưu tại: {output_path}")


if __name__ == "__main__":
    main()