import json
from pathlib import Path
from datetime import datetime

from customers.customer_service import CustomerService
from payment.payment_service import PaymentService
from inventory.inventory_service import InventoryService


class OrderService:
    def __init__(self, order_path=None):
        if order_path is None:
            self.order_path = Path(__file__).resolve().parent / "orders.json"
        else:
            self.order_path = Path(order_path)

        self.orders = self._load_orders()
        self.customer_service = CustomerService()
        self.payment_service = PaymentService()
        self.inventory_service = InventoryService()

    def _load_orders(self):
        if not self.order_path.exists():
            return []

        with open(self.order_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def save_orders(self):
        with open(self.order_path, "w", encoding="utf-8") as f:
            json.dump(self.orders, f, ensure_ascii=False, indent=2)

    # =========================
    # Create order
    # =========================

    def create_order(self, state: dict, recommendation: dict = None):
        customer_name = state.get("customer_name")
        customer_phone = state.get("customer_phone")
        customer_address = state.get("customer_address")

        if not customer_name or not customer_phone or not customer_address:
            return {
                "success": False,
                "error": "missing_customer_info",
                "message": "Thiếu tên, số điện thoại hoặc địa chỉ giao hàng."
            }

        customer = self.customer_service.create_or_update_customer(
            name=customer_name,
            phone=customer_phone,
            address=customer_address
        )

        order_number = len(self.orders) + 1
        order_id = self._generate_order_id(order_number)

        bouquet_info = self._build_bouquet_info(
            state=state,
            recommendation=recommendation
        )

        estimated_price = bouquet_info.get("estimated_price") or state.get("budget") or 0

        payment_code = self.payment_service.generate_payment_code(order_number)

        payment_info = self.payment_service.build_payment_info(
            order_id=order_id,
            payment_code=payment_code,
            amount=estimated_price,
            customer_name=customer_name
        )

        order = {
            "order_id": order_id,
            "customer_id": customer["customer_id"],
            "customer": {
                "name": customer_name,
                "phone": customer_phone,
                "address": customer_address
            },
            "bouquet": bouquet_info,
            "payment": payment_info,
            "status": "pending_payment",
            "created_at": self._now(),
            "updated_at": self._now()
        }

        self.orders.append(order)
        self.save_orders()

        self.customer_service.add_order_to_customer(
            phone=customer_phone,
            order_id=order_id
        )

        return {
            "success": True,
            "order": order
        }

    # =========================
    # Find order
    # =========================

    def find_order_by_id(self, order_id: str):
        if not order_id:
            return None

        for order in self.orders:
            if order.get("order_id") == order_id:
                return order

        return None

    # =========================
    # Confirm payment
    # =========================

    def confirm_payment(self, order_id: str):
        order = self.find_order_by_id(order_id)

        if order is None:
            return {
                "success": False,
                "error": "order_not_found",
                "message": f"Không tìm thấy đơn hàng {order_id}."
            }

        payment = order.get("payment", {})
        payment_status = payment.get("payment_status")

        if payment_status == "paid":
            return {
                "success": False,
                "error": "already_paid",
                "message": f"Đơn hàng {order_id} đã được xác nhận thanh toán trước đó.",
                "order": order
            }

        inventory_result = self._update_inventory_after_payment(order)

        order["payment"]["payment_status"] = "paid"
        order["status"] = "preparing"
        order["updated_at"] = self._now()

        self.save_orders()

        return {
            "success": True,
            "order": order,
            "inventory_result": inventory_result,
            "message": f"Đã xác nhận thanh toán cho đơn {order_id}."
        }

    def _update_inventory_after_payment(self, order: dict):
        bouquet = order.get("bouquet", {})
        bouquet_items = bouquet.get("bouquet_items", [])

        updated_items = []
        failed_items = []

        for item in bouquet_items:
            flower_name = item.get("flower_name")
            quantity = item.get("quantity", 0)

            if not flower_name or not quantity:
                continue

            try:
                # Gọi positional arguments để tránh lỗi:
                # TypeError: unexpected keyword argument 'flower_name'
                success = self.inventory_service.decrease_stock(
                    flower_name,
                    quantity
                )
            except TypeError:
                success = False
            except Exception:
                success = False

            if success:
                updated_items.append({
                    "flower_name": flower_name,
                    "quantity_decreased": quantity
                })
            else:
                failed_items.append({
                    "flower_name": flower_name,
                    "quantity": quantity,
                    "reason": "Không đủ tồn kho hoặc không tìm thấy hoa."
                })

        return {
            "updated_items": updated_items,
            "failed_items": failed_items
        }

    # =========================
    # Build bouquet info
    # =========================

    def _build_bouquet_info(self, state: dict, recommendation: dict = None):
        bouquet_items = []
        estimated_price = None
        bouquet_size = None

        if recommendation:
            bouquet_proposal = recommendation.get("bouquet_proposal")

            if bouquet_proposal:
                bouquet_items = bouquet_proposal.get("bouquet_items", [])
                estimated_price = bouquet_proposal.get("estimated_price")
                bouquet_size = bouquet_proposal.get("budget_plan", {}).get("bouquet_size")

        return {
            "occasion": state.get("occasion"),
            "recipient": state.get("recipient"),
            "budget": state.get("budget"),
            "budget_min": state.get("budget_min"),
            "budget_max": state.get("budget_max"),
            "budget_type": state.get("budget_type"),
            "flower_preference": state.get("flower_preference", []),
            "flower_avoidance": state.get("flower_avoidance", []),
            "color_tone": state.get("color_tone", []),
            "style": state.get("style", []),
            "delivery_time": state.get("delivery_time"),
            "bouquet_size": bouquet_size,
            "bouquet_items": bouquet_items,
            "estimated_price": estimated_price
        }

    # =========================
    # Utils
    # =========================

    def _generate_order_id(self, order_number: int):
        date_part = datetime.now().strftime("%Y%m%d")
        return f"ORD-{date_part}-{order_number:04d}"

    def _now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")