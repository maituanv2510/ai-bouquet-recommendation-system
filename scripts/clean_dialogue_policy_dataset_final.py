import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

TRAIN_PATH = ROOT_DIR / "data" / "processed" / "dialogue_policy_train_final.jsonl"
VAL_PATH = ROOT_DIR / "data" / "processed" / "dialogue_policy_val_final.jsonl"


def is_valid_record(item):
    if not isinstance(item, dict):
        return False

    text = item.get("text")

    if not isinstance(text, str):
        return False

    if not text.strip():
        return False

    required_markers = [
        "<|im_start|>system",
        "<|im_start|>user",
        "<|im_start|>assistant",
        "<|im_end|>",
    ]

    for marker in required_markers:
        if marker not in text:
            return False

    return True


def load_jsonl(path):
    rows = []

    with open(path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                print(f"[DROP] {path.name} line {line_number}: JSON decode error")
                continue

            rows.append((line_number, item))

    return rows


def save_jsonl(path, rows):
    backup_path = path.with_suffix(path.suffix + ".bak")

    # Backup file cũ
    path.replace(backup_path)

    with open(path, "w", encoding="utf-8") as f:
        for item in rows:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Backup saved: {backup_path}")
    print(f"Cleaned file saved: {path}")


def clean_file(path):
    rows = load_jsonl(path)

    valid_rows = []
    invalid_rows = []

    for line_number, item in rows:
        if is_valid_record(item):
            valid_rows.append(item)
        else:
            invalid_rows.append((line_number, item))

    print("=" * 70)
    print(f"File: {path}")
    print(f"Original rows: {len(rows)}")
    print(f"Valid rows   : {len(valid_rows)}")
    print(f"Invalid rows : {len(invalid_rows)}")

    if invalid_rows:
        print("Invalid line numbers:")
        for line_number, _ in invalid_rows:
            print(f"- line {line_number}")

    save_jsonl(path, valid_rows)


def main():
    clean_file(TRAIN_PATH)
    clean_file(VAL_PATH)

    print("=" * 70)
    print("Done cleaning final dataset.")


if __name__ == "__main__":
    main()