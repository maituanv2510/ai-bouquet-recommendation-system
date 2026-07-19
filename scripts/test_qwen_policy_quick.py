import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from dialogue.qwen_dialogue_policy import QwenDialoguePolicy


def main():
    policy = QwenDialoguePolicy(
        adapter_path="outputs/qwen2.5-3b-dialogue-policy",
        max_new_tokens=96
    )

    state = {
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
        "order_id": None,
    }

    test_messages = [
        "tôi muốn mua một bó hoa tặng người yêu nhân dịp valentine",
        "tôi muốn tặng nhân ngày lễ tình nhân",
        "nhân dịp tết",
        "tầm trên 800k",
        "shop còn cẩm tú cầu không",
    ]

    for msg in test_messages:
        print("=" * 80)
        print("USER:", msg)
        output = policy.predict(
            user_message=msg,
            state=state,
            last_bot_message=""
        )
        print(output)


if __name__ == "__main__":
    main()