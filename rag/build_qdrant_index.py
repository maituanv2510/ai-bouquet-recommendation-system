import os
import uuid
import pandas as pd
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from rag.embedding_service import EmbeddingService


FLOWER_KB_PATH = "data/processed/flower_knowledge_base.csv"
COLLECTION_NAME = "flower_knowledge_base"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333


def split_semicolon(value):
    if pd.isna(value) or value == "":
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()]


def build_document_text(row):
    flower_name = row.get("flower_name", "")
    english_name = row.get("english_name", "")
    colors = row.get("available_colors", "")
    meanings = row.get("meanings", "")
    occasions = row.get("suitable_occasions", "")
    styles = row.get("style_tags", "")
    role = row.get("bouquet_role", "")
    price_level = row.get("price_level", "")
    description = row.get("description", "")

    text = f"""
{flower_name} / {english_name}.
Ý nghĩa: {meanings}.
Phù hợp dịp: {occasions}.
Phong cách: {styles}.
Vai trò trong bó hoa: {role}.
Màu phổ biến: {colors}.
Mức giá: {price_level}.
Mô tả: {description}
""".strip()

    return text


def main():
    if not os.path.exists(FLOWER_KB_PATH):
        raise FileNotFoundError(f"Cannot find {FLOWER_KB_PATH}")

    df = pd.read_csv(FLOWER_KB_PATH)
    print(f"Loaded {len(df)} flower records")

    embedder = EmbeddingService("BAAI/bge-m3")

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    vector_size = len(embedder.encode_one("test"))
    print("Vector size:", vector_size)

    existing_collections = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME in existing_collections:
        print(f"Deleting existing collection: {COLLECTION_NAME}")
        client.delete_collection(collection_name=COLLECTION_NAME)

    print(f"Creating collection: {COLLECTION_NAME}")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        )
    )

    points = []

    for idx, row in tqdm(df.iterrows(), total=len(df)):
        document_text = build_document_text(row)
        vector = embedder.encode_one(document_text)

        payload = {
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
            "document_text": document_text
        }

        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload=payload
        )

        points.append(point)

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    print(f"Inserted {len(points)} points into Qdrant collection '{COLLECTION_NAME}'")


if __name__ == "__main__":
    main()