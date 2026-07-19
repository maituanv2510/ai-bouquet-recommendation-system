from dialogue.dialogue_policy import DialoguePolicy


def main():
    policy = DialoguePolicy()

    test_messages = [
        "bó hoa đắt nhất bên bạn tầm bao nhiêu",
        "tôi muốn đặt bó hoa tặng mẹ sinh nhật khoảng từ 500k đến 1 triệu",
        "cẩm tú cầu phối với hoa nào đẹp hơn",
        "shop còn tulip không",
        "ok lấy bó này",
        "tên tôi là Nguyễn Văn An, số điện thoại 0912345678, giao ở Cầu Giấy",
        "đổi sang tone hồng được không"
    ]

    state = {}

    for msg in test_messages:
        print("=" * 80)
        print("USER:", msg)

        result = policy.predict(
            user_message=msg,
            state=state,
            last_bot_message=""
        )

        print(result)


if __name__ == "__main__":
    main()