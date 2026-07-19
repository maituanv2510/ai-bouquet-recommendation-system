from inventory.inventory_service import InventoryService


def main():
    inventory = InventoryService()

    print("=== ALL FLOWERS ===")
    for flower in inventory.get_all_flowers():
        print(
            flower["flower_name"],
            "| stock:",
            flower["stock"],
            "| price:",
            flower["unit_price"],
            "| status:",
            flower["status"]
        )

    print("\n=== CHECK AVAILABLE ===")
    print("cẩm tú cầu:", inventory.is_available("cẩm tú cầu"))
    print("tulip:", inventory.is_available("tulip"))

    print("\n=== FILTER FLOWERS ===")
    result = inventory.filter_available_flowers([
        "cẩm tú cầu",
        "tulip",
        "hoa hồng kem",
        "baby trắng"
    ])
    print(result)

    print("\n=== SUGGEST ALTERNATIVES FOR TULIP ===")
    state = {
        "occasion": "sinh nhật",
        "recipient": "mẹ",
        "color_tone": ["trắng", "xanh"],
        "style": ["nhẹ nhàng"]
    }

    alternatives = inventory.suggest_alternatives("tulip", state=state)

    for item in alternatives:
        print(item)


if __name__ == "__main__":
    main()