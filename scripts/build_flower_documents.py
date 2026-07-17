import os
import json
import pandas as pd
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "processed",
    "flower_knowledge_base.csv"
)
OUTPUT_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "processed",
    "flower_documents.jsonl"
)
def safe_get(row, column):
    if column in row and pd.notna(row[column]):
        return str(row[column]).strip()
    return ""
def build_document(row, idx):
    flower_name = safe_get(row, "flower_name")
    meaning = safe_get(row, "meaning")
    suitable_occasions = safe_get(row, "suitable_occasions")
    suitable_recipients = safe_get(row, "suitable_recipients")
    colors = safe_get(row, "colors")
    style = safe_get(row, "style")
    avoid_context = safe_get(row, "avoid_context")
    notes = safe_get(row, "notes")
    text = f"""
Tên hoa: {flower_name}
Ý nghĩa: {meaning}
Dịp phù hợp: {suitable_occasions}
Người nhận phù hợp: {suitable_recipients}
Màu sắc phổ biến: {colors}
Phong cách phù hợp: {style}
Trường hợp nên tránh: {avoid_context}
Ghi chú: {notes}
""".strip()
    return {
        "id": f"flower_knowledge_{idx}",
        "text": text,
        "metadata": {
            "source": "flower_knowledge_base",
            "row_id": idx,
            "flower_name": flower_name,
            "type": "flower_knowledge"
        }
    }

def main():
    df = pd.read_csv(INPUT_PATH)
    documents = []
    for idx, row in df.iterrows():
        document = build_document(row, idx)
        documents.append(document)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for document in documents:
            f.write(json.dumps(document, ensure_ascii=False) + "\n")
    print(f"Created {len(documents)} documents")
    print(f"Saved to: {OUTPUT_PATH}")
if __name__ == "__main__":
    main()