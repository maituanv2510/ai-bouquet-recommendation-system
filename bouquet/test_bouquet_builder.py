from bouquet.bouquet_builder import BouquetBuilder


def main():
    builder = BouquetBuilder()

    state = {
        "occasion": "sinh nhật",
        "recipient": "mẹ",
        "budget": 500000,
        "budget_type": "maximum",
        "flower_preference": ["cẩm tú cầu"],
        "flower_avoidance": [],
        "color_tone": ["xanh"],
        "style": ["bó giấy Hàn Quốc"],
        "delivery_time": None
    }

    proposal = builder.build_bouquet(state)

    print("=== BOUQUET PROPOSAL ===")
    print("Budget:", proposal["budget"])
    print("Budget plan:", proposal["budget_plan"])
    print("Estimated price:", proposal["estimated_price"])
    print("Price status:", proposal["price_status"])

    print("\n=== BOUQUET ITEMS ===")
    for item in proposal["bouquet_items"]:
        print(
            item["role"],
            "|",
            item["flower_name"],
            "| quantity:",
            item["quantity"],
            "| unit price:",
            item["unit_price"],
            "| reason:",
            item["reason"]
        )

    print("\n=== ADVICE ===")
    print(proposal["advice"])


if __name__ == "__main__":
    main()