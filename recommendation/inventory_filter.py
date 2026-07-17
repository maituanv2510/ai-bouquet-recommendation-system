import os
import sys
from typing import List, Dict, Any, Optional

import pandas as pd


INVENTORY_PATH = "data/processed/inventory_sample.csv"


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).lower().strip()


def normalize_list(values: Optional[List[str]]) -> List[str]:
    if not values:
        return []
    return [normalize_text(v) for v in values]


class InventoryFilter:
    def __init__(self, inventory_path: str = INVENTORY_PATH):
        if not os.path.exists(inventory_path):
            raise FileNotFoundError(f"Cannot find inventory file: {inventory_path}")

        self.inventory_path = inventory_path
        self.inventory_df = pd.read_csv(inventory_path)

        required_cols = [
            "inventory_id",
            "flower_id",
            "variant_name",
            "base_flower_name",
            "color",
            "stock_quantity",
            "unit",
            "selling_price",
            "freshness_status",
            "days_since_import",
            "status",
        ]

        missing_cols = [
            col for col in required_cols
            if col not in self.inventory_df.columns
        ]

        if missing_cols:
            raise ValueError(f"Missing columns in inventory file: {missing_cols}")

    def is_available_row(self, row: pd.Series) -> bool:
        status = normalize_text(row.get("status"))
        freshness_status = normalize_text(row.get("freshness_status"))
        stock_quantity = int(row.get("stock_quantity", 0))

        if stock_quantity <= 0:
            return False

        if status in ["out_of_stock", "expired"]:
            return False

        if freshness_status == "expired":
            return False

        return True

    def filter_candidates(
        self,
        retrieved_flowers: List[Dict[str, Any]],
        requirements: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        flower_avoidance = normalize_list(requirements.get("flower_avoidance", []))
        color_tone = normalize_list(requirements.get("color_tone", []))

        candidates = []

        for retrieved in retrieved_flowers:
            retrieved_flower_id = retrieved.get("flower_id")
            retrieved_flower_name = normalize_text(retrieved.get("flower_name"))

            if not retrieved_flower_id and not retrieved_flower_name:
                continue

            matched_rows = self.inventory_df.copy()

            if retrieved_flower_id:
                matched_rows = matched_rows[
                    matched_rows["flower_id"].astype(str) == str(retrieved_flower_id)
                ]
            else:
                matched_rows = matched_rows[
                    matched_rows["base_flower_name"].apply(normalize_text)
                    == retrieved_flower_name
                ]

            for _, row in matched_rows.iterrows():
                base_flower_name = normalize_text(row.get("base_flower_name"))
                variant_name = normalize_text(row.get("variant_name"))

                # Avoidance rule
                should_avoid = False
                for avoid in flower_avoidance:
                    if avoid in base_flower_name or avoid in variant_name:
                        should_avoid = True
                        break

                if should_avoid:
                    continue

                # Availability rule
                if not self.is_available_row(row):
                    continue

                color = normalize_text(row.get("color"))

                color_match = False
                if color_tone:
                    color_match = color in color_tone

                candidate = {
                    "inventory_id": row.get("inventory_id"),
                    "flower_id": row.get("flower_id"),
                    "variant_name": row.get("variant_name"),
                    "base_flower_name": row.get("base_flower_name"),
                    "color": row.get("color"),
                    "stock_quantity": int(row.get("stock_quantity")),
                    "unit": row.get("unit"),
                    "selling_price": float(row.get("selling_price")),
                    "freshness_status": row.get("freshness_status"),
                    "days_since_import": int(row.get("days_since_import")),
                    "status": row.get("status"),

                    # From RAG
                    "rag_score": float(retrieved.get("score", 0.0)),
                    "retrieval_source": retrieved.get("retrieval_source", []),
                    "payload": retrieved.get("payload", {}),

                    # Helper fields
                    "color_match": color_match,
                }

                candidates.append(candidate)

        return candidates


if __name__ == "__main__":
    sample_retrieved = [
        {
            "flower_id": "F001",
            "flower_name": "Cẩm tú cầu",
            "score": 1.32,
            "retrieval_source": ["semantic", "keyword", "required_flower_boost"],
            "payload": {},
        },
        {
            "flower_id": "F004",
            "flower_name": "Cát tường",
            "score": 0.86,
            "retrieval_source": ["semantic"],
            "payload": {},
        },
    ]

    sample_requirements = {
        "flower_avoidance": [],
        "color_tone": [],
    }

    inventory_filter = InventoryFilter()
    results = inventory_filter.filter_candidates(
        retrieved_flowers=sample_retrieved,
        requirements=sample_requirements,
    )

    for item in results:
        print(item)