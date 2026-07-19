import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "e2e_chatbot_test_cases.json"


def build_cases():
    cases = [
        {
            "case_id": "E2E_001",
            "name": "Valentine full order flow",
            "messages": [
                "tôi muốn mua một bó hoa tặng người yêu nhân dịp valentine",
                "tầm trên 700k đi",
                "ok tôi lấy bó này",
                "Nguyễn Viết Anh - 0866660251 - Xóm Trung Tiến, Xã Hưng Đông, Vinh, Nghệ An"
            ],
            "expected": {
                "final_occasion": "Valentine",
                "final_recipient": "người yêu",
                "budget": 700000,
                "budget_type": "minimum",
                "must_recommend": True,
                "must_collect_customer_info": True,
                "must_create_order": True,
                "must_have_payment_code": True,
                "must_block_payment_confirm": False
            }
        },
        {
            "case_id": "E2E_002",
            "name": "Birthday mother under budget",
            "messages": [
                "mình muốn đặt bó hoa tặng mẹ sinh nhật",
                "dưới 500k thôi nhé",
                "ok lấy bó này",
                "Trần Minh Anh - 0912345678 - Cầu Giấy, Hà Nội"
            ],
            "expected": {
                "final_occasion": "sinh nhật",
                "final_recipient": "mẹ",
                "budget": 500000,
                "budget_type": "maximum",
                "must_recommend": True,
                "must_collect_customer_info": True,
                "must_create_order": True,
                "must_have_payment_code": True,
                "must_block_payment_confirm": False
            }
        },
        {
            "case_id": "E2E_003",
            "name": "Teacher day 20/11",
            "messages": [
                "tôi cần một bó hoa tặng cô giáo ngày 20/11",
                "khoảng 600k",
                "chốt bó này",
                "Lê Hoàng Nam - 0987654321 - Thanh Xuân, Hà Nội"
            ],
            "expected": {
                "final_occasion": "20/11",
                "final_recipient": "thầy cô",
                "budget": 600000,
                "budget_type": "approx",
                "must_recommend": True,
                "must_collect_customer_info": True,
                "must_create_order": True,
                "must_have_payment_code": True,
                "must_block_payment_confirm": False
            }
        },
        {
            "case_id": "E2E_004",
            "name": "Women's day 8/3",
            "messages": [
                "mua hoa tặng mẹ ngày 8/3",
                "tầm 450k",
                "ok lấy bó này",
                "Phạm Quang Huy - 0901111222 - Nam Từ Liêm, Hà Nội"
            ],
            "expected": {
                "final_occasion": "8/3",
                "final_recipient": "mẹ",
                "budget": 450000,
                "budget_type": "approx",
                "must_recommend": True,
                "must_collect_customer_info": True,
                "must_create_order": True,
                "must_have_payment_code": True,
                "must_block_payment_confirm": False
            }
        },
        {
            "case_id": "E2E_005",
            "name": "Vietnamese women's day 20/10",
            "messages": [
                "anh muốn bó hoa tặng vợ ngày 20/10",
                "trên 800k",
                "tôi sẽ lấy bó này",
                "Đỗ Minh Quân - 0933333444 - Hà Đông, Hà Nội"
            ],
            "expected": {
                "final_occasion": "20/10",
                "final_recipient": "người yêu",
                "budget": 800000,
                "budget_type": "minimum",
                "must_recommend": True,
                "must_collect_customer_info": True,
                "must_create_order": True,
                "must_have_payment_code": True,
                "must_block_payment_confirm": False
            }
        },
        {
            "case_id": "E2E_006",
            "name": "Inventory check hydrangea",
            "messages": [
                "shop còn cẩm tú cầu không"
            ],
            "expected": {
                "must_check_inventory": True,
                "flower_preference_contains": ["cẩm tú cầu"],
                "must_recommend": False,
                "must_create_order": False
            }
        },
        {
            "case_id": "E2E_007",
            "name": "Inventory check rose cream",
            "messages": [
                "hoa hồng kem còn bao nhiêu cành"
            ],
            "expected": {
                "must_check_inventory": True,
                "flower_preference_contains": ["hoa hồng kem"],
                "must_recommend": False,
                "must_create_order": False
            }
        },
        {
            "case_id": "E2E_008",
            "name": "Ask flower colors after recommendation",
            "messages": [
                "tôi muốn mua một bó hoa tặng người yêu nhân dịp valentine",
                "tầm trên 700k đi",
                "những hoa trên có màu nào khác không"
            ],
            "expected": {
                "final_occasion": "Valentine",
                "final_recipient": "người yêu",
                "budget": 700000,
                "budget_type": "minimum",
                "must_recommend": True,
                "must_answer_flower_colors": True,
                "must_create_order": False
            }
        },
        {
            "case_id": "E2E_009",
            "name": "Modify color after recommendation",
            "messages": [
                "tôi muốn mua một bó hoa tặng người yêu nhân dịp valentine",
                "tầm trên 700k đi",
                "cẩm tú cầu màu xanh làm chủ đạo nhé"
            ],
            "expected": {
                "final_occasion": "Valentine",
                "final_recipient": "người yêu",
                "budget": 700000,
                "budget_type": "minimum",
                "flower_preference_contains": ["cẩm tú cầu"],
                "color_tone_contains": ["xanh"],
                "must_recommend": True,
                "must_create_order": False
            }
        },
        {
            "case_id": "E2E_010",
            "name": "Modify flower after recommendation",
            "messages": [
                "tôi muốn bó hoa tặng mẹ sinh nhật",
                "khoảng 600k",
                "thêm hoa hồng kem vào bó này nhé"
            ],
            "expected": {
                "final_occasion": "sinh nhật",
                "final_recipient": "mẹ",
                "budget": 600000,
                "flower_preference_contains": ["hoa hồng kem"],
                "must_recommend": True,
                "must_create_order": False
            }
        },
        {
            "case_id": "E2E_011",
            "name": "Customer tries to confirm payment",
            "messages": [
                "xác nhận thanh toán đơn ORD-20260719-0001"
            ],
            "expected": {
                "must_block_payment_confirm": True,
                "must_create_order": False,
                "must_recommend": False
            }
        },
        {
            "case_id": "E2E_012",
            "name": "Ask budget suggestion",
            "messages": [
                "tôi chưa biết nên mua bó hoa tầm bao nhiêu tiền"
            ],
            "expected": {
                "must_answer_budget_suggestion": True,
                "must_recommend": False,
                "must_create_order": False
            }
        },
        {
            "case_id": "E2E_013",
            "name": "Ask flower pairing",
            "messages": [
                "cẩm tú cầu phối với hoa gì đẹp"
            ],
            "expected": {
                "flower_preference_contains": ["cẩm tú cầu"],
                "must_answer_flower_pairing": True,
                "must_recommend": False,
                "must_create_order": False
            }
        },
        {
            "case_id": "E2E_014",
            "name": "Ask flower meaning",
            "messages": [
                "cẩm tú cầu có ý nghĩa gì"
            ],
            "expected": {
                "flower_preference_contains": ["cẩm tú cầu"],
                "must_answer_flower_meaning": True,
                "must_recommend": False,
                "must_create_order": False
            }
        },
        {
            "case_id": "E2E_015",
            "name": "Graduation bouquet",
            "messages": [
                "mình cần bó hoa tặng bạn tốt nghiệp",
                "khoảng 500k",
                "okela",
                "Ngô Hải Yến - 0977777888 - Thủ Đức, TP HCM"
            ],
            "expected": {
                "final_occasion": "tốt nghiệp",
                "final_recipient": "bạn bè",
                "budget": 500000,
                "budget_type": "approx",
                "must_recommend": True,
                "must_collect_customer_info": True,
                "must_create_order": True,
                "must_have_payment_code": True
            }
        },
        {
            "case_id": "E2E_016",
            "name": "Grand opening bouquet",
            "messages": [
                "tôi muốn đặt hoa chúc mừng khai trương cho khách hàng",
                "trên 1 triệu",
                "lấy bó này",
                "Công ty Minh Long - 0909999888 - Quận 1, TP HCM"
            ],
            "expected": {
                "final_occasion": "khai trương",
                "final_recipient": "khách hàng",
                "budget": 1000000,
                "budget_type": "minimum",
                "must_recommend": True,
                "must_collect_customer_info": True,
                "must_create_order": True,
                "must_have_payment_code": True
            }
        },
        {
            "case_id": "E2E_017",
            "name": "Apology bouquet",
            "messages": [
                "tôi muốn mua hoa để xin lỗi người yêu",
                "tầm 650k",
                "ok lấy bó này",
                "Hoàng Anh - 0922222333 - Ba Đình, Hà Nội"
            ],
            "expected": {
                "final_occasion": "xin lỗi",
                "final_recipient": "người yêu",
                "budget": 650000,
                "budget_type": "approx",
                "must_recommend": True,
                "must_collect_customer_info": True,
                "must_create_order": True,
                "must_have_payment_code": True
            }
        },
        {
            "case_id": "E2E_018",
            "name": "Avoid flower request",
            "messages": [
                "tôi cần bó hoa tặng mẹ sinh nhật nhưng tránh tulip",
                "dưới 600k",
                "chốt đơn",
                "Nguyễn Thu Hà - 0911111222 - Đống Đa, Hà Nội"
            ],
            "expected": {
                "final_occasion": "sinh nhật",
                "final_recipient": "mẹ",
                "budget": 600000,
                "budget_type": "maximum",
                "flower_avoidance_contains": ["tulip"],
                "must_recommend": True,
                "must_collect_customer_info": True,
                "must_create_order": True
            }
        },
        {
            "case_id": "E2E_019",
            "name": "Color tone from start",
            "messages": [
                "tôi muốn bó hoa tone hồng tặng người yêu dịp kỷ niệm",
                "khoảng 900k"
            ],
            "expected": {
                "final_occasion": "kỷ niệm",
                "final_recipient": "người yêu",
                "budget": 900000,
                "budget_type": "approx",
                "color_tone_contains": ["hồng"],
                "must_recommend": True,
                "must_create_order": False
            }
        },
        {
            "case_id": "E2E_020",
            "name": "Unclear request",
            "messages": [
                "mua hoa đẹp đẹp đi"
            ],
            "expected": {
                "must_ask_missing_info": True,
                "must_recommend": False,
                "must_create_order": False
            }
        }
    ]

    return cases


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    cases = build_cases()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)

    print(f"Done. Generated {len(cases)} E2E test cases.")
    print(f"Output path: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()