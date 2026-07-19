import json
import random
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

TRAIN_V2_PATH = ROOT_DIR / "data" / "processed" / "dialogue_policy_train_v2.jsonl"
VAL_V2_PATH = ROOT_DIR / "data" / "processed" / "dialogue_policy_val_v2.jsonl"

TRAIN_V3_PATH = ROOT_DIR / "data" / "processed" / "dialogue_policy_train_v3.jsonl"
VAL_V3_PATH = ROOT_DIR / "data" / "processed" / "dialogue_policy_val_v3.jsonl"

TRAIN_FINAL_PATH = ROOT_DIR / "data" / "processed" / "dialogue_policy_train_final.jsonl"
VAL_FINAL_PATH = ROOT_DIR / "data" / "processed" / "dialogue_policy_val_final.jsonl"


def load_jsonl(path):
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {path}")

    rows = []

    with open(path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Lỗi JSON ở file {path}, line {line_number}: {str(e)}"
                )

    return rows


def save_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        for item in rows:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def remove_duplicates(rows):
    seen = set()
    unique_rows = []

    for item in rows:
        text = item.get("text", "")

        if text in seen:
            continue

        seen.add(text)
        unique_rows.append(item)

    return unique_rows


def main():
    print("Loading datasets...")

    train_v2 = load_jsonl(TRAIN_V2_PATH)
    val_v2 = load_jsonl(VAL_V2_PATH)

    train_v3 = load_jsonl(TRAIN_V3_PATH)
    val_v3 = load_jsonl(VAL_V3_PATH)

    print(f"Train v2: {len(train_v2)}")
    print(f"Val v2  : {len(val_v2)}")
    print(f"Train v3: {len(train_v3)}")
    print(f"Val v3  : {len(val_v3)}")

    train_final = train_v2 + train_v3
    val_final = val_v2 + val_v3

    train_final = remove_duplicates(train_final)
    val_final = remove_duplicates(val_final)

    random.seed(42)
    random.shuffle(train_final)
    random.shuffle(val_final)

    save_jsonl(TRAIN_FINAL_PATH, train_final)
    save_jsonl(VAL_FINAL_PATH, val_final)

    print("\nDone merging datasets.")
    print(f"Train final: {len(train_final)}")
    print(f"Val final  : {len(val_final)}")
    print(f"Train output: {TRAIN_FINAL_PATH}")
    print(f"Val output  : {VAL_FINAL_PATH}")


if __name__ == "__main__":
    main()