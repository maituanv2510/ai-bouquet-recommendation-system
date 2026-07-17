import os

from rag_pipeline import RAGPipeline


def main():
    requirements = {
        "product_type": "bouquet",
        "occasion": None,
        "recipient": "người bạn",
        "budget": 500000,
        "budget_type": "maximum",
        "color_tone": [],
        "style": [],
        "meaning_intent": [],
        "flower_preference": ["cẩm tú cầu"],
        "flower_avoidance": [],
        "delivery_time": None,
        "missing_fields": ["occasion", "color_tone", "style", "delivery_time"]
    }

    pipeline = RAGPipeline()

    result = pipeline.run(
        requirements=requirements,
        top_k=5
    )

    print("\n=== REQUIREMENTS ===")
    print(result["requirements"])

    print("\n=== RETRIEVED FLOWERS ===")
    for idx, flower in enumerate(result["retrieved_flowers"], start=1):
        print(f"\n{idx}. {flower.get('flower_name')}")
        print("Score:", flower.get("hybrid_score"))
        print("Meanings:", flower.get("meanings"))
        print("Colors:", flower.get("available_colors"))
        print("Description:", flower.get("description"))

    print("\n=== PROMPT ===")
    print(result["prompt"])

    os.makedirs("outputs/rag_test", exist_ok=True)

    with open("outputs/rag_test/sample_rag_prompt.txt", "w", encoding="utf-8") as f:
        f.write(result["prompt"])

    print("\nSaved prompt to: outputs/rag_test/sample_rag_prompt.txt")


if __name__ == "__main__":
    main()