"""
Đánh giá model đã fine-tune (LoRA adapter trên nền Qwen2.5-3B-Instruct, load
4-bit) cho tác vụ trích xuất yêu cầu đặt hoa có cấu trúc từ tin nhắn khách
hàng tiếng Việt.

Input:
    - data/processed/customer_request_test.jsonl
    - Base model: Qwen/Qwen2.5-3B-Instruct (load 4-bit qua bitsandbytes)
    - LoRA adapter: outputs/qwen2.5-3b-bouquet-extractor

Output:
    - outputs/extraction_metrics.json      (các chỉ số đánh giá tổng hợp)
    - outputs/sample_predictions.jsonl     (20 sample dự đoán đầu tiên, để soi lỗi)

Quy trình:
    1. Load base model 4-bit + tokenizer.
    2. Load LoRA adapter lên trên base model bằng PEFT.
    3. Với mỗi sample trong test set:
        - Lấy user message (câu hỏi khách hàng).
        - Lấy gold JSON từ assistant.content (nhãn đúng).
        - Gọi model sinh JSON dự đoán (dùng chat template + generate).
        - Cố gắng parse JSON dự đoán; nếu lỗi, KHÔNG crash, chỉ ghi nhận là
          dự đoán không hợp lệ và tiếp tục sample kế tiếp.
    4. Tính các chỉ số:
        - json_validity_rate            : tỉ lệ output parse được thành JSON hợp lệ
        - budget_accuracy                : tỉ lệ budget dự đoán khớp gold
        - occasion_accuracy              : tỉ lệ occasion dự đoán khớp gold
        - recipient_accuracy             : tỉ lệ recipient dự đoán khớp gold
        - flower_preference_exact_match  : tỉ lệ list flower_preference khớp gold
        - color_tone_exact_match         : tỉ lệ list color_tone khớp gold
      (Các mẫu có JSON không hợp lệ được tính là SAI cho mọi field, không bị bỏ qua
      khỏi mẫu số, để phản ánh đúng hiệu năng thực tế của model.)
    5. Lưu kết quả.
"""

import os
import re
import json
import traceback

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

# Cấu hình
BASE_MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"
ADAPTER_PATH = os.path.join("outputs", "qwen2.5-3b-bouquet-extractor")
TEST_PATH = os.path.join("data", "processed", "customer_request_test.jsonl")

OUTPUT_DIR = "outputs"
METRICS_PATH = os.path.join(OUTPUT_DIR, "extraction_metrics.json")
SAMPLE_PRED_PATH = os.path.join(OUTPUT_DIR, "sample_predictions.jsonl")

NUM_SAMPLE_PREDICTIONS_TO_SAVE = 20
MAX_NEW_TOKENS = 256

SYSTEM_PROMPT = (
    "You extract structured bouquet requirements from Vietnamese customer "
    "messages. Return only valid JSON."
)

FIELDS_TO_COMPARE_SCALAR = ["occasion", "recipient", "budget"]
FIELDS_TO_COMPARE_LIST = ["flower_preference", "color_tone"]

# Load model
def load_model_and_tokenizer():
    print(f"Đang load base model 4-bit: {BASE_MODEL_NAME} ...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
    )

    print(f"Đang load LoRA adapter từ: {ADAPTER_PATH} ...")
    model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
    model.eval()

    return model, tokenizer

# Sinh dự đoán từ model

def generate_prediction(model, tokenizer, user_message: str) -> str:
    """Gọi model sinh chuỗi output (raw text) cho 1 tin nhắn khách hàng."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            temperature=None,
            top_p=None,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
        )

    generated_ids = output_ids[0][inputs["input_ids"].shape[1]:]
    raw_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
    return raw_text.strip()


def extract_json_from_text(text: str):
    """
    Cố gắng parse JSON từ output của model. Model có thể sinh thêm text thừa
    xung quanh JSON, nên thử parse trực tiếp trước, nếu lỗi thì tìm đoạn
    JSON object đầu tiên bằng regex rồi thử lại.
    Trả về (parsed_json hoặc None, is_valid: bool).
    """
    try:
        return json.loads(text), True
    except (json.JSONDecodeError, TypeError):
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0)), True
        except json.JSONDecodeError:
            pass

    return None, False


# So sánh giá trị

def normalize_scalar(value):
    if isinstance(value, str):
        return value.strip().lower()
    return value


def normalize_list(value):
    if not isinstance(value, list):
        return None
    return set(str(v).strip().lower() for v in value)


def compare_scalar(pred_value, gold_value) -> bool:
    return normalize_scalar(pred_value) == normalize_scalar(gold_value)


def compare_list(pred_value, gold_value) -> bool:
    pred_set = normalize_list(pred_value)
    gold_set = normalize_list(gold_value)
    if pred_set is None or gold_set is None:
        return False
    return pred_set == gold_set


# Đọc test set

def load_test_samples(path: str) -> list:
    samples = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            messages = record["messages"]
            user_msg = next(m["content"] for m in messages if m["role"] == "user")
            assistant_msg = next(m["content"] for m in messages if m["role"] == "assistant")
            gold_json = json.loads(assistant_msg)
            samples.append({"user_message": user_msg, "gold": gold_json})
    return samples


# Đánh giá chính

def evaluate(model, tokenizer, samples: list):
    total = len(samples)
    num_valid_json = 0

    scalar_correct = {field: 0 for field in FIELDS_TO_COMPARE_SCALAR}
    list_correct = {field: 0 for field in FIELDS_TO_COMPARE_LIST}

    sample_predictions = []

    for i, sample in enumerate(samples):
        user_message = sample["user_message"]
        gold = sample["gold"]

        raw_output = ""
        predicted_json = None
        is_valid_json = False

        # KHÔNG được để lỗi sinh/parse JSON làm crash toàn bộ vòng lặp đánh giá
        try:
            raw_output = generate_prediction(model, tokenizer, user_message)
            predicted_json, is_valid_json = extract_json_from_text(raw_output)
        except Exception as e:
            print(f"[!] Lỗi khi xử lý sample {i}: {e}")
            traceback.print_exc()
            raw_output = raw_output or ""
            predicted_json = None
            is_valid_json = False

        if is_valid_json:
            num_valid_json += 1

        # Tính từng field: nếu JSON không hợp lệ hoặc thiếu field -> coi là sai
        for field in FIELDS_TO_COMPARE_SCALAR:
            gold_value = gold.get(field)
            pred_value = predicted_json.get(field) if isinstance(predicted_json, dict) else None
            if is_valid_json and compare_scalar(pred_value, gold_value):
                scalar_correct[field] += 1

        for field in FIELDS_TO_COMPARE_LIST:
            gold_value = gold.get(field)
            pred_value = predicted_json.get(field) if isinstance(predicted_json, dict) else None
            if is_valid_json and compare_list(pred_value, gold_value):
                list_correct[field] += 1

        if i < NUM_SAMPLE_PREDICTIONS_TO_SAVE:
            sample_predictions.append({
                "user_message": user_message,
                "gold": gold,
                "raw_model_output": raw_output,
                "predicted_json": predicted_json,
                "is_valid_json": is_valid_json,
            })

        if (i + 1) % 10 == 0 or (i + 1) == total:
            print(f"Đã xử lý {i + 1}/{total} samples...")

    metrics = {
        "total_samples": total,
        "json_validity_rate": num_valid_json / total if total else 0.0,
        "budget_accuracy": scalar_correct["budget"] / total if total else 0.0,
        "occasion_accuracy": scalar_correct["occasion"] / total if total else 0.0,
        "recipient_accuracy": scalar_correct["recipient"] / total if total else 0.0,
        "flower_preference_exact_match": list_correct["flower_preference"] / total if total else 0.0,
        "color_tone_exact_match": list_correct["color_tone"] / total if total else 0.0,
    }

    return metrics, sample_predictions


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(TEST_PATH):
        raise FileNotFoundError(f"Không tìm thấy file test: {TEST_PATH}")

    samples = load_test_samples(TEST_PATH)
    print(f"Đã load {len(samples)} test samples từ {TEST_PATH}")

    model, tokenizer = load_model_and_tokenizer()

    metrics, sample_predictions = evaluate(model, tokenizer, samples)

    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    with open(SAMPLE_PRED_PATH, "w", encoding="utf-8") as f:
        for record in sample_predictions:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("\n=== KẾT QUẢ ĐÁNH GIÁ ===")
    for key, value in metrics.items():
        print(f"{key}: {value}")

    print(f"\nĐã lưu metrics tại: {METRICS_PATH}")
    print(f"Đã lưu {len(sample_predictions)} sample predictions tại: {SAMPLE_PRED_PATH}")


if __name__ == "__main__":
    main()