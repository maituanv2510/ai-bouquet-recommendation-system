import json
from pathlib import Path


class InventoryService:
    def __init__(self, inventory_path=None):
        if inventory_path is None:
            self.inventory_path = Path(__file__).resolve().parent / "inventory_data.json"
        else:
            self.inventory_path = Path(inventory_path)

        self.inventory = self._load_inventory()

    def _load_inventory(self):
        if not self.inventory_path.exists():
            raise FileNotFoundError(f"Inventory file not found: {self.inventory_path}")

        with open(self.inventory_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_inventory(self):
        with open(self.inventory_path, "w", encoding="utf-8") as f:
            json.dump(self.inventory, f, ensure_ascii=False, indent=2)

    def get_all_flowers(self):
        return list(self.inventory.values())

    def get_flower(self, flower_name: str):
        if not flower_name:
            return None

        flower_name = flower_name.lower().strip()

        for name, info in self.inventory.items():
            if name.lower() == flower_name:
                return info

        return None

    def is_available(self, flower_name: str, required_quantity: int = 1):
        flower = self.get_flower(flower_name)

        if flower is None:
            return False

        if flower.get("status") != "available":
            return False

        if flower.get("stock", 0) < required_quantity:
            return False

        return True

    def get_unit_price(self, flower_name: str):
        flower = self.get_flower(flower_name)

        if flower is None:
            return None

        return flower.get("unit_price")

    def filter_available_flowers(self, flower_names: list):
        available = []
        unavailable = []

        for flower_name in flower_names:
            if self.is_available(flower_name):
                available.append(flower_name)
            else:
                unavailable.append(flower_name)

        return {
            "available": available,
            "unavailable": unavailable
        }

    def suggest_alternatives(self, unavailable_flower: str, state: dict = None, limit: int = 3):
        state = state or {}

        occasion = state.get("occasion")
        recipient = state.get("recipient")
        color_tone = state.get("color_tone", [])
        style = state.get("style", [])

        candidates = []

        for flower_name, info in self.inventory.items():
            if info.get("status") != "available":
                continue

            if info.get("stock", 0) <= 0:
                continue

            score = 0

            if occasion and occasion in info.get("suitable_occasions", []):
                score += 2

            if recipient and recipient in info.get("suitable_recipients", []):
                score += 2

            for color in color_tone:
                if color in info.get("color", []):
                    score += 1

            for style_tag in style:
                if style_tag in info.get("style_tags", []):
                    score += 1

            candidates.append({
                "flower_name": flower_name,
                "unit_price": info.get("unit_price"),
                "stock": info.get("stock"),
                "score": score,
                "reason": self._build_alternative_reason(info, occasion, recipient)
            })

        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

        return candidates[:limit]

    def _build_alternative_reason(self, flower_info: dict, occasion=None, recipient=None):
        name = flower_info.get("flower_name")

        reason_parts = []

        if occasion and occasion in flower_info.get("suitable_occasions", []):
            reason_parts.append(f"phù hợp dịp {occasion}")

        if recipient and recipient in flower_info.get("suitable_recipients", []):
            reason_parts.append(f"hợp để tặng {recipient}")

        if not reason_parts:
            reason_parts.append("có thể phối phụ để bó hoa hài hòa hơn")

        return f"{name} " + ", ".join(reason_parts)

    def decrease_stock(self, flower_items: list):
        """
        flower_items format:
        [
            {"flower_name": "cẩm tú cầu", "quantity": 2},
            {"flower_name": "baby trắng", "quantity": 3}
        ]
        """

        for item in flower_items:
            flower_name = item.get("flower_name")
            quantity = item.get("quantity", 1)

            flower = self.get_flower(flower_name)

            if flower is None:
                raise ValueError(f"Flower not found in inventory: {flower_name}")

            if flower.get("stock", 0) < quantity:
                raise ValueError(f"Not enough stock for flower: {flower_name}")

        for item in flower_items:
            flower_name = item.get("flower_name")
            quantity = item.get("quantity", 1)

            flower = self.get_flower(flower_name)
            flower["stock"] -= quantity

            if flower["stock"] <= 0:
                flower["status"] = "out_of_stock"

        self.save_inventory()

    def increase_stock(self, flower_name: str, quantity: int):
        flower = self.get_flower(flower_name)

        if flower is None:
            raise ValueError(f"Flower not found in inventory: {flower_name}")

        flower["stock"] += quantity

        if flower["stock"] > 0:
            flower["status"] = "available"

        self.save_inventory()