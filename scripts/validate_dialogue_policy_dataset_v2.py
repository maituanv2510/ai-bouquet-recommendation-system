import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from dialogue.action_schema import validate_policy_output


DATA_PATHS = [
    Path("data/processed/dialogue_policy_train_v2.jsonl"),
    Path("data/processed/dialogue_policy_val_v2.jsonl")
]


def validate_file(path: Path):
    if not path.exists():
        print(f"File not found: {path}")
        return False

    total = 0
    valid = 0
    invalid = 0

    with open(path, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f, start=1):
            total += 1

            try:
                item = json.loads(line)
            except Exception as e:
                invalid += 1
                print(f"[{path} - Line {line_idx}] JSON line error: {e}")
                continue

            messages = item.get("messages")

            if not isinstance(messages, list) or len(messages) != 3:
                invalid += 1
                print(f"[{path} - Line {line_idx}] messages must be list with 3 items")
                continue

            assistant_msg = messages[2]

            if assistant_msg.get("role") != "assistant":
                invalid += 1
                print(f"[{path} - Line {line_idx}] third message must be assistant")
                continue

            try:
                output = json.loads(assistant_msg.get("content", ""))
            except Exception as e:
                invalid += 1
                print(f"[{path} - Line {line_idx}] assistant content is not valid JSON: {e}")
                continue

            ok, message = validate_policy_output(output)

            if ok:
                valid += 1
            else:
                invalid += 1
                print(f"[{path} - Line {line_idx}] invalid policy output: {message}")

    print(f"\n=== Validate {path} ===")
    print("Total:", total)
    print("Valid:", valid)
    print("Invalid:", invalid)

    return invalid == 0


def main():
    all_ok = True

    for path in DATA_PATHS:
        ok = validate_file(path)

        if not ok:
            all_ok = False

    if all_ok:
        print("\nAll dataset files are valid.")
    else:
        print("\nSome dataset files have errors.")


if __name__ == "__main__":
    main()