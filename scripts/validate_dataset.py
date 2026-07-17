"""
Kiểm tra tính hợp lệ của các file dataset JSONL dùng để fine-tune LLM
(tác vụ trích xuất yêu cầu đặt hoa có cấu trúc từ tin nhắn khách hàng).

Input:
    data/processed/customer_request_train.jsonl
    data/processed/customer_request_val.jsonl
    data/processed/customer_request_test.jsonl

Các kiểm tra thực hiện trên mỗi dòng:
    1. Dòng parse được thành JSON.
    2. JSON có key "messages".
    3. "messages" có đúng 3 phần tử với role lần lượt là: system, user, assistant.
    4. assistant.content parse được thành JSON (JSON string hợp lệ).
    5. JSON trong assistant.content có đủ các field bắt buộc:
       product_type, occasion, recipient, budget, budget_type, color_tone,
       style, meaning_intent, flower_preference, flower_avoidance,
       delivery_time, missing_fields
    6. budget phải là int/float hoặc null.
    7. color_tone, style, meaning_intent, flower_preference, flower_avoidance,
       missing_fields phải là list.
    8. budget_type chỉ được là null, "maximum", "around", hoặc "minimum".

Output: in ra console
    - Với mỗi file: tổng số sample, số sample lỗi.
    - 10 lỗi đầu tiên (nếu có) trên toàn bộ các file.
    - Tổng kết chung (tổng số sample, tổng số lỗi) trên tất cả các file.
"""

import os
import json

INPUT_FILES = [
    os.path.join("data", "processed", "customer_request_train.jsonl"),
    os.path.join("data", "processed", "customer_request_val.jsonl"),
    os.path.join("data", "processed", "customer_request_test.jsonl"),
]

REQUIRED_ASSISTANT_FIELDS = [
    "product_type", "occasion", "recipient", "budget", "budget_type",
    "color_tone", "style", "meaning_intent", "flower_preference",
    "flower_avoidance", "delivery_time", "missing_fields",
]

LIST_FIELDS = [
    "color_tone", "style", "meaning_intent", "flower_preference",
    "flower_avoidance", "missing_fields",
]

VALID_BUDGET_TYPES = {None, "maximum", "around", "minimum"}
REQUIRED_ROLES = ["system", "user", "assistant"]


def validate_line(raw_line: str):
    """
    Kiểm tra 1 dòng JSONL theo các yêu cầu 1-8.
    Trả về (is_valid: bool, errors: list[str]).
    Dừng sớm nếu các bước nền tảng (parse JSON, cấu trúc messages) thất bại,
    vì các bước sau phụ thuộc vào chúng.
    """
    errors = []

    # 1. Dòng parse được thành JSON
    try:
        record = json.loads(raw_line)
    except json.JSONDecodeError as e:
        return False, [f"Dòng không parse được JSON: {e}"]

    # 2. Có key "messages"
    if "messages" not in record:
        return False, ["Thiếu key 'messages'"]

    messages = record["messages"]

    # 3. messages có 3 phần tử với role: system, user, assistant
    if not isinstance(messages, list) or len(messages) != 3:
        return False, [f"'messages' phải có đúng 3 phần tử (hiện có: {len(messages) if isinstance(messages, list) else 'không phải list'})"]

    roles = [m.get("role") for m in messages if isinstance(m, dict)]
    if roles != REQUIRED_ROLES:
        errors.append(f"Thứ tự/role của messages không đúng: {roles} (yêu cầu: {REQUIRED_ROLES})")

    assistant_msg = next((m for m in messages if isinstance(m, dict) and m.get("role") == "assistant"), None)
    if assistant_msg is None:
        errors.append("Không tìm thấy message có role 'assistant'")
        return False, errors

    assistant_content = assistant_msg.get("content")
    if not isinstance(assistant_content, str):
        errors.append("assistant.content không phải là string")
        return False, errors

    # 4. assistant.content parse được thành JSON
    try:
        data = json.loads(assistant_content)
    except json.JSONDecodeError as e:
        errors.append(f"assistant.content không parse được JSON: {e}")
        return False, errors

    if not isinstance(data, dict):
        errors.append("assistant.content parse ra không phải JSON object")
        return False, errors

    # 5. Đủ các field bắt buộc
    missing_keys = [f for f in REQUIRED_ASSISTANT_FIELDS if f not in data]
    if missing_keys:
        errors.append(f"assistant.content thiếu field: {missing_keys}")

    # 6. budget phải là int/float hoặc null
    if "budget" in data:
        budget = data["budget"]
        if budget is not None and not isinstance(budget, (int, float)):
            errors.append(f"'budget' phải là int/float hoặc null, hiện là: {type(budget).__name__} ({budget!r})")
        elif isinstance(budget, bool):  # bool là subclass của int, cần loại trừ
            errors.append(f"'budget' không được là boolean, hiện là: {budget!r}")

    # 7. Các field list phải là list
    for field in LIST_FIELDS:
        if field in data and not isinstance(data[field], list):
            errors.append(f"'{field}' phải là list, hiện là: {type(data[field]).__name__} ({data[field]!r})")

    # 8. budget_type chỉ được null/maximum/around/minimum
    if "budget_type" in data and data["budget_type"] not in VALID_BUDGET_TYPES:
        errors.append(f"'budget_type' không hợp lệ: {data['budget_type']!r} (chỉ chấp nhận null/maximum/around/minimum)")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_file(path: str):
    """
    Kiểm tra toàn bộ 1 file JSONL.
    Trả về dict thống kê: total, num_errors, error_details (list các lỗi kèm số dòng).
    """
    total = 0
    num_errors = 0
    error_details = []

    if not os.path.exists(path):
        return {"total": 0, "num_errors": 0, "error_details": [], "file_missing": True}

    with open(path, "r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            raw_line = raw_line.rstrip("\n")
            if not raw_line.strip():
                continue
            total += 1
            is_valid, errors = validate_line(raw_line)
            if not is_valid:
                num_errors += 1
                for err in errors:
                    error_details.append({
                        "file": path,
                        "line": line_number,
                        "error": err,
                    })

    return {"total": total, "num_errors": num_errors, "error_details": error_details, "file_missing": False}


def main():
    all_error_details = []
    grand_total = 0
    grand_num_errors = 0

    print("=" * 70)
    print("KIỂM TRA DATASET JSONL")
    print("=" * 70)

    for path in INPUT_FILES:
        result = validate_file(path)

        if result["file_missing"]:
            print(f"\n[!] Không tìm thấy file: {path}")
            continue

        print(f"\nFile: {path}")
        print(f"  Tổng số sample : {result['total']}")
        print(f"  Số sample lỗi  : {result['num_errors']}")

        grand_total += result["total"]
        grand_num_errors += result["num_errors"]
        all_error_details.extend(result["error_details"])

    print("\n" + "=" * 70)
    print("TỔNG KẾT")
    print("=" * 70)
    print(f"Tổng số sample (tất cả các file) : {grand_total}")
    print(f"Tổng số sample lỗi                : {grand_num_errors}")

    if all_error_details:
        print(f"\n10 lỗi đầu tiên (trong tổng số {len(all_error_details)} lỗi):")
        for i, err in enumerate(all_error_details[:10], start=1):
            print(f"  {i}. [{err['file']}:{err['line']}] {err['error']}")
    else:
        print("\nKhông phát hiện lỗi nào. Dataset hợp lệ 100%.")


if __name__ == "__main__":
    main()