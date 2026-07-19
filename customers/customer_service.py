import json
from pathlib import Path
from datetime import datetime


class CustomerService:
    def __init__(self, customer_path=None):
        if customer_path is None:
            self.customer_path = Path(__file__).resolve().parent / "customers.json"
        else:
            self.customer_path = Path(customer_path)

        self.customers = self._load_customers()

    def _load_customers(self):
        if not self.customer_path.exists():
            return []

        with open(self.customer_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def save_customers(self):
        with open(self.customer_path, "w", encoding="utf-8") as f:
            json.dump(self.customers, f, ensure_ascii=False, indent=2)

    def find_by_phone(self, phone: str):
        if not phone:
            return None

        for customer in self.customers:
            if customer.get("phone") == phone:
                return customer

        return None

    def create_or_update_customer(self, name: str, phone: str, address: str):
        existing_customer = self.find_by_phone(phone)

        if existing_customer:
            existing_customer["name"] = name or existing_customer.get("name")
            existing_customer["address"] = address or existing_customer.get("address")
            existing_customer["updated_at"] = self._now()
            self.save_customers()
            return existing_customer

        customer_id = self._generate_customer_id()

        customer = {
            "customer_id": customer_id,
            "name": name,
            "phone": phone,
            "address": address,
            "orders": [],
            "created_at": self._now(),
            "updated_at": self._now()
        }

        self.customers.append(customer)
        self.save_customers()

        return customer

    def add_order_to_customer(self, phone: str, order_id: str):
        customer = self.find_by_phone(phone)

        if customer is None:
            return None

        if order_id not in customer["orders"]:
            customer["orders"].append(order_id)

        customer["updated_at"] = self._now()
        self.save_customers()

        return customer

    def _generate_customer_id(self):
        next_number = len(self.customers) + 1
        return f"CUS-{next_number:04d}"

    def _now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")