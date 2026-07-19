from datetime import datetime


class PaymentService:
    def __init__(self):
        pass

    def generate_payment_code(self, order_number: int):
        date_part = datetime.now().strftime("%Y%m%d")
        return f"BQ{date_part}{order_number:04d}"

    def build_payment_info(self, order_id: str, payment_code: str, amount: int, customer_name: str = None):
        transfer_content = payment_code

        if customer_name:
            transfer_content += f" {customer_name}"

        return {
            "payment_code": payment_code,
            "amount": amount,
            "transfer_content": transfer_content,
            "payment_status": "pending",
            "note": (
                "Khách hàng vui lòng chuyển khoản đúng nội dung để shop xác nhận đơn nhanh hơn."
            )
        }