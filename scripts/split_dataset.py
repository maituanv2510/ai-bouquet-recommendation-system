"""
Chia file synthetic dataset (JSONL) thành 3 tập train/val/test theo tỉ lệ 80/10/10.

Input:
    data/synthetic/customer_request_extraction_2000.jsonl

Output:
    data/processed/customer_request_train.jsonl   (1600 samples)
    data/processed/customer_request_val.jsonl      (200 samples)
    data/processed/customer_request_test.jsonl     (200 samples)

Logic:
    - Đọc toàn bộ các dòng JSONL từ file input (giữ nguyên nội dung từng dòng,
      không parse lại / không chỉnh sửa).
    - Shuffle với random seed = 42 để đảm bảo tái lập được.
    - Chia theo tỉ lệ 80/10/10: train = 1600, val = 200, test = 200.
    - Ghi ra 3 file JSONL tương ứng.
    - In ra số lượng dòng của từng file sau khi split.
"""

import os
import random

RANDOM_SEED = 42

INPUT_PATH = os.path.join("data", "synthetic", "customer_request_extraction_2000.jsonl")
OUTPUT_DIR = os.path.join("data", "processed")

TRAIN_PATH = os.path.join(OUTPUT_DIR, "customer_request_train.jsonl")
VAL_PATH = os.path.join(OUTPUT_DIR, "customer_request_val.jsonl")
TEST_PATH = os.path.join(OUTPUT_DIR, "customer_request_test.jsonl")

TRAIN_RATIO = 0.8
VAL_RATIO = 0.1
TEST_RATIO = 0.1


def read_lines(path: str) -> list:
    """Đọc toàn bộ các dòng JSONL, giữ nguyên nội dung (chỉ bỏ ký tự xuống dòng cuối)."""
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]
    return lines


def write_lines(path: str, lines: list) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def split_dataset(lines: list, rng: random.Random):
    total = len(lines)

    shuffled = lines[:]
    rng.shuffle(shuffled)

    n_train = int(round(total * TRAIN_RATIO))
    n_val = int(round(total * VAL_RATIO))
    n_test = total - n_train - n_val  # phần còn lại, tránh lệch do làm tròn

    train_lines = shuffled[:n_train]
    val_lines = shuffled[n_train:n_train + n_val]
    test_lines = shuffled[n_train + n_val:]

    return train_lines, val_lines, test_lines


def main():
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(
            f"Không tìm thấy file input: {INPUT_PATH}. "
            "Hãy chạy generate_customer_requests.py trước để tạo dataset."
        )

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    lines = read_lines(INPUT_PATH)
    rng = random.Random(RANDOM_SEED)

    train_lines, val_lines, test_lines = split_dataset(lines, rng)

    write_lines(TRAIN_PATH, train_lines)
    write_lines(VAL_PATH, val_lines)
    write_lines(TEST_PATH, test_lines)

    print(f"Tổng số samples đầu vào: {len(lines)}")
    print(f"Train: {len(train_lines)} samples -> {TRAIN_PATH}")
    print(f"Val:   {len(val_lines)} samples -> {VAL_PATH}")
    print(f"Test:  {len(test_lines)} samples -> {TEST_PATH}")


if __name__ == "__main__":
    main()