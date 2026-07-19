import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from dialogue.action_schema import validate_policy_output


DATA_PATH = Path("data/processed/dialogue_policy_train.jsonl")


def main():
    if not DATA_PATH.exists():
        print(f"File not found: {DATA_PATH}")
        return

    total = 0
    valid = 0
    invalid = 0

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f, start=1):
            total += 1

            try:
                item = json.loads(line)
            except Exception as e:
                invalid += 1
                print(f"[Line {line_idx}] JSON error: {e}")
                continue

            expected_output = item.get("expected_output")
            ok, message = validate_policy_output(expected_output)

            if ok:
                valid += 1
            else:
                invalid += 1
                print(f"[Line {line_idx}] Invalid: {message}")

    print("=== Dialogue Policy Dataset Validation ===")
    print("Total:", total)
    print("Valid:", valid)
    print("Invalid:", invalid)


if __name__ == "__main__":
    main()