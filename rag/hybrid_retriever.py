import os
import pandas as pd

from qdrant_client import QdrantClient

from rag.embedding_service import EmbeddingService


FLOWER_KB_PATH = "data/processed/flower_knowledge_base.csv"
COLLECTION_NAME = "flower_knowledge_base"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333


def split_semicolon(value):
    if pd.isna(value) or value == "":
        return []

    return [
        item.strip().lower()
        for item in str(value).split(";")
        if item.strip()
    ]


class HybridRetriever:
    def __init__(self):
        self.embedder = EmbeddingService("BAAI/bge-m3")

        self.client = QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT
        )

        if not os.path.exists(FLOWER_KB_PATH):
            raise FileNotFoundError(f"Cannot find {FLOWER_KB_PATH}")

        self.flower_df = pd.read_csv(FLOWER_KB_PATH)

    def build_query_text(self, requirements):
        parts = []

        occasion = requirements.get("occasion")
        recipient = requirements.get("recipient")
        color_tone = requirements.get("color_tone", [])
        style = requirements.get("style", [])
        flower_preference = requirements.get("flower_preference", [])
        flower_avoidance = requirements.get("flower_avoidance", [])
        meaning_intent = requirements.get("meaning_intent", [])

        if occasion:
            parts.append(f"Dịp: {occasion}")

        if recipient:
            parts.append(f"Người nhận: {recipient}")

        if color_tone:
            parts.append(f"Màu sắc mong muốn: {', '.join(color_tone)}")

        if style:
            parts.append(f"Phong cách: {', '.join(style)}")

        if flower_preference:
            parts.append(f"Hoa yêu thích: {', '.join(flower_preference)}")

        if flower_avoidance:
            parts.append(f"Hoa cần tránh: {', '.join(fower for fower in flower_avoidance)}")

        if meaning_intent:
            parts.append(f"Ý nghĩa mong muốn: {', '.join(meaning_intent)}")

        return ". ".join(parts)

    def semantic_search(self, query, top_k=5):
        query_vector = self.embedder.encode_one(query)

        results = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
            with_payload=True
        ).points

        semantic_results = []

        for result in results:
            payload = result.payload or {}

            semantic_results.append({
                "flower_id": payload.get("flower_id", ""),
                "flower_name": payload.get("flower_name", ""),
                "english_name": payload.get("english_name", ""),
                "available_colors": payload.get("available_colors", []),
                "meanings": payload.get("meanings", []),
                "suitable_occasions": payload.get("suitable_occasions", []),
                "style_tags": payload.get("style_tags", []),
                "bouquet_role": payload.get("bouquet_role", []),
                "price_level": payload.get("price_level", ""),
                "compatible_flowers": payload.get("compatible_flowers", []),
                "description": payload.get("description", ""),
                "document_text": payload.get("document_text", ""),
                "semantic_score": float(result.score),
                "keyword_score": 0,
                "hybrid_score": float(result.score)
            })

        return semantic_results

    def keyword_score_row(self, row, requirements):
        score = 0

        occasion = requirements.get("occasion")
        recipient = requirements.get("recipient")
        color_tone = requirements.get("color_tone", [])
        style = requirements.get("style", [])
        flower_preference = requirements.get("flower_preference", [])
        flower_avoidance = requirements.get("flower_avoidance", [])
        meaning_intent = requirements.get("meaning_intent", [])

        flower_name = str(row.get("flower_name", "")).lower()
        english_name = str(row.get("english_name", "")).lower()

        available_colors = split_semicolon(row.get("available_colors", ""))
        meanings = split_semicolon(row.get("meanings", ""))
        suitable_occasions = split_semicolon(row.get("suitable_occasions", ""))
        style_tags = split_semicolon(row.get("style_tags", ""))
        bouquet_role = split_semicolon(row.get("bouquet_role", ""))
        description = str(row.get("description", "")).lower()

        for flower in flower_preference:
            flower = str(flower).lower().strip()

            if flower and (flower in flower_name or flower in english_name):
                score += 5

        for flower in flower_avoidance:
            flower = str(flower).lower().strip()

            if flower and (flower in flower_name or flower in english_name):
                score -= 10

        if occasion:
            occasion = str(occasion).lower().strip()

            if occasion in suitable_occasions or occasion in description:
                score += 3

        if recipient:
            recipient = str(recipient).lower().strip()

            if recipient in description:
                score += 1

        for color in color_tone:
            color = str(color).lower().strip()

            if color in available_colors or color in description:
                score += 2

        for item in style:
            item = str(item).lower().strip()

            if item in style_tags or item in bouquet_role or item in description:
                score += 2

        for intent in meaning_intent:
            intent = str(intent).lower().strip()

            if intent in meanings or intent in description:
                score += 2

        return score

    def keyword_search(self, requirements, top_k=5):
        scored_rows = []

        for _, row in self.flower_df.iterrows():
            score = self.keyword_score_row(row, requirements)

            if score > 0:
                scored_rows.append({
                    "flower_id": row.get("flower_id", ""),
                    "flower_name": row.get("flower_name", ""),
                    "english_name": row.get("english_name", ""),
                    "available_colors": split_semicolon(row.get("available_colors", "")),
                    "meanings": split_semicolon(row.get("meanings", "")),
                    "suitable_occasions": split_semicolon(row.get("suitable_occasions", "")),
                    "style_tags": split_semicolon(row.get("style_tags", "")),
                    "bouquet_role": split_semicolon(row.get("bouquet_role", "")),
                    "price_level": row.get("price_level", ""),
                    "compatible_flowers": split_semicolon(row.get("compatible_flowers", "")),
                    "description": row.get("description", ""),
                    "document_text": row.get("description", ""),
                    "semantic_score": 0,
                    "keyword_score": score,
                    "hybrid_score": score
                })

        scored_rows = sorted(
            scored_rows,
            key=lambda x: x["keyword_score"],
            reverse=True
        )

        return scored_rows[:top_k]

    def merge_results(self, semantic_results, keyword_results, top_k=5):
        merged = {}

        for item in semantic_results:
            flower_name = item.get("flower_name", "")

            if flower_name not in merged:
                merged[flower_name] = item

            merged[flower_name]["semantic_score"] = item.get("semantic_score", 0)

        for item in keyword_results:
            flower_name = item.get("flower_name", "")

            if flower_name not in merged:
                merged[flower_name] = item

            merged[flower_name]["keyword_score"] = item.get("keyword_score", 0)

        final_results = []

        for flower_name, item in merged.items():
            semantic_score = item.get("semantic_score", 0)
            keyword_score = item.get("keyword_score", 0)

            hybrid_score = semantic_score + keyword_score

            item["hybrid_score"] = hybrid_score

            final_results.append(item)

        final_results = sorted(
            final_results,
            key=lambda x: x["hybrid_score"],
            reverse=True
        )

        return final_results[:top_k]

    def retrieve(self, requirements, top_k=5):
        query = self.build_query_text(requirements)

        semantic_results = self.semantic_search(
            query=query,
            top_k=top_k
        )

        keyword_results = self.keyword_search(
            requirements=requirements,
            top_k=top_k
        )

        final_results = self.merge_results(
            semantic_results=semantic_results,
            keyword_results=keyword_results,
            top_k=top_k
        )

        return final_results


if __name__ == "__main__":
    requirements = {
        "occasion": "sinh nhật",
        "recipient": "bạn gái",
        "budget": 500000,
        "budget_type": "maximum",
        "flower_preference": ["hoa hồng"],
        "flower_avoidance": [],
        "color_tone": ["đỏ", "hồng"],
        "style": ["lãng mạn"],
        "meaning_intent": ["tình yêu", "ngọt ngào"]
    }

    retriever = HybridRetriever()

    results = retriever.retrieve(
        requirements=requirements,
        top_k=5
    )

    print("\n=== RETRIEVAL RESULTS ===")

    for idx, item in enumerate(results, start=1):
        print(f"\nResult {idx}")
        print("Flower:", item.get("flower_name"))
        print("English name:", item.get("english_name"))
        print("Semantic score:", item.get("semantic_score"))
        print("Keyword score:", item.get("keyword_score"))
        print("Hybrid score:", item.get("hybrid_score"))
        print("Meanings:", item.get("meanings"))
        print("Occasions:", item.get("suitable_occasions"))
        print("Colors:", item.get("available_colors"))
        print("Description:", item.get("description"))