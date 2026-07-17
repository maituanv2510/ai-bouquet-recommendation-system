import os
import sys
import json
from pprint import pprint


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
RAG_DIR = os.path.join(PROJECT_ROOT, "rag")

sys.path.append(PROJECT_ROOT)
sys.path.append(RAG_DIR)

from hybrid_retriever import HybridRetriever


def build_simple_recommendation(requirements, retrieved_flowers, top_k=3):
    flower_preference = [
        str(item).lower().strip()
        for item in requirements.get("flower_preference", [])
    ]

    flower_avoidance = [
        str(item).lower().strip()
        for item in requirements.get("flower_avoidance", [])
    ]

    budget = requirements.get("budget")
    budget_type = requirements.get("budget_type")

    recommended_flowers = []
    avoid_flowers = []

    for flower in retrieved_flowers:
        flower_name = str(flower.get("flower_name", "")).lower().strip()

        is_avoided = False
        for avoid in flower_avoidance:
            if avoid and avoid in flower_name:
                is_avoided = True
                break

        if is_avoided:
            avoid_flowers.append({
                "flower_name": flower.get("flower_name", ""),
                "reason": "Hoa này nằm trong danh sách khách hàng muốn tránh."
            })
            continue

        matched_requirements = []

        for preferred in flower_preference:
            if preferred and preferred in flower_name:
                matched_requirements.append("matched_flower_preference")

        if requirements.get("occasion"):
            matched_requirements.append("matched_occasion_or_context")

        if requirements.get("meaning_intent"):
            matched_requirements.append("matched_meaning_intent")

        if requirements.get("color_tone"):
            matched_requirements.append("matched_color_tone")

        recommended_flowers.append({
            "flower_name": flower.get("flower_name", ""),
            "english_name": flower.get("english_name", ""),
            "reason": flower.get("description", ""),
            "matched_requirements": matched_requirements,
            "semantic_score": flower.get("semantic_score", 0),
            "keyword_score": flower.get("keyword_score", 0),
            "hybrid_score": flower.get("hybrid_score", 0),
            "retrieval_source": flower.get("retrieval_source", "hybrid")
        })

    recommended_flowers = sorted(
        recommended_flowers,
        key=lambda x: x.get("hybrid_score", 0),
        reverse=True
    )

    final_result = {
        "requirements": requirements,
        "recommended_flowers": recommended_flowers[:top_k],
        "avoid_flowers": avoid_flowers,
        "budget_note": {
            "budget": budget,
            "budget_type": budget_type,
            "note": "Budget sẽ được dùng để lọc/tối ưu combo bó hoa ở bước inventory hoặc pricing."
        },
        "final_advice": build_final_advice(requirements, recommended_flowers[:top_k])
    }

    return final_result


def build_final_advice(requirements, recommended_flowers):
    recipient = requirements.get("recipient", "người nhận")
    occasion = requirements.get("occasion", "dịp này")
    budget = requirements.get("budget")

    flower_names = [
        flower.get("flower_name", "")
        for flower in recommended_flowers
        if flower.get("flower_name")
    ]

    if flower_names:
        flower_text = ", ".join(flower_names)
    else:
        flower_text = "các loại hoa phù hợp từ dữ liệu hiện có"

    if budget:
        return (
            f"Với ngân sách khoảng {budget:,} VND, hệ thống gợi ý sử dụng "
            f"{flower_text} để tặng {recipient} nhân dịp {occasion}. "
            f"Các lựa chọn này được chọn dựa trên sở thích hoa, ý nghĩa và mức độ phù hợp với yêu cầu khách hàng."
        )

    return (
        f"Hệ thống gợi ý sử dụng {flower_text} để tặng {recipient} nhân dịp {occasion}. "
        f"Các lựa chọn này được chọn dựa trên sở thích hoa, ý nghĩa và mức độ phù hợp với yêu cầu khách hàng."
    )


def print_retrieved_flowers(retrieved_flowers):
    for idx, item in enumerate(retrieved_flowers, start=1):
        print(
            idx,
            "| Flower:",
            item.get("flower_name", ""),
            "| Hybrid score:",
            round(item.get("hybrid_score", 0), 4),
            "| Semantic score:",
            round(item.get("semantic_score", 0), 4),
            "| Keyword score:",
            round(item.get("keyword_score", 0), 4),
            "| Source:",
            item.get("retrieval_source", "hybrid")
        )


def main():
    print("=" * 80)
    print("STEP 1 — Requirement JSON")

    requirements = {
        "occasion": "tặng bạn",
        "recipient": "bạn",
        "budget": 500000,
        "budget_type": "maximum",
        "flower_preference": ["cẩm tú cầu"],
        "flower_avoidance": [],
        "color_tone": [],
        "style": [],
        "meaning_intent": ["tình bạn", "chân thành"]
    }

    pprint(requirements)

    print("=" * 80)
    print("STEP 2 — Retrieved flowers from RAG")

    retriever = HybridRetriever()

    retrieved_flowers = retriever.retrieve(
        requirements=requirements,
        top_k=8
    )

    print_retrieved_flowers(retrieved_flowers)

    print("=" * 80)
    print("STEP 3 — Final Recommendation")

    final_result = build_simple_recommendation(
        requirements=requirements,
        retrieved_flowers=retrieved_flowers,
        top_k=3
    )

    pprint(final_result)

    print("=" * 80)
    print("STEP 4 — Save output")

    os.makedirs("outputs/recommendation_test", exist_ok=True)

    output_path = "outputs/recommendation_test/sample_recommendation_result.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)

    print(f"Saved result to: {output_path}")


if __name__ == "__main__":
    main()