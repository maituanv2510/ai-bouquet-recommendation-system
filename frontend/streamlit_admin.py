import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from orders.order_service import OrderService


ADMIN_PASSWORD = "123456"


st.set_page_config(
    page_title="AI Bouquet Admin Panel",
    page_icon="🛠️",
    layout="wide"
)

st.title("🛠️ AI Bouquet Admin Panel")
st.caption("Trang quản trị đơn hàng, thanh toán và tồn kho.")

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    st.subheader("Đăng nhập admin")

    password = st.text_input(
        "Nhập mật khẩu admin",
        type="password"
    )

    if st.button("Đăng nhập"):
        if password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.success("Đăng nhập thành công.")
            st.rerun()
        else:
            st.error("Sai mật khẩu admin.")

    st.stop()


with st.sidebar:
    st.header("Admin Mode")

    if st.button("Đăng xuất"):
        st.session_state.admin_logged_in = False
        st.rerun()

    if st.button("Reload dữ liệu"):
        st.rerun()


order_service = OrderService()
orders = order_service.orders

st.subheader("Danh sách đơn hàng")

if not orders:
    st.info("Hiện chưa có đơn hàng nào.")
    st.stop()


status_filter = st.selectbox(
    "Lọc theo trạng thái đơn",
    options=[
        "all",
        "pending_payment",
        "preparing",
        "delivering",
        "completed",
        "cancelled"
    ]
)

filtered_orders = orders

if status_filter != "all":
    filtered_orders = [
        order for order in orders
        if order.get("status") == status_filter
    ]

if not filtered_orders:
    st.warning("Không có đơn hàng nào theo bộ lọc này.")
    st.stop()


for order in reversed(filtered_orders):
    order_id = order.get("order_id")
    customer = order.get("customer", {})
    bouquet = order.get("bouquet", {})
    payment = order.get("payment", {})

    customer_name = customer.get("name")
    customer_phone = customer.get("phone")
    customer_address = customer.get("address")

    order_status = order.get("status")
    payment_status = payment.get("payment_status")
    amount = payment.get("amount")
    payment_code = payment.get("payment_code")
    transfer_content = payment.get("transfer_content")

    bouquet_items = bouquet.get("bouquet_items", [])

    with st.expander(f"{order_id} | {customer_name} | {order_status} | {payment_status}"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Thông tin khách hàng")
            st.write(f"**Tên:** {customer_name}")
            st.write(f"**SĐT:** {customer_phone}")
            st.write(f"**Địa chỉ:** {customer_address}")

            st.markdown("### Thanh toán")
            st.write(f"**Mã thanh toán:** {payment_code}")
            st.write(f"**Nội dung CK:** {transfer_content}")
            st.write(f"**Số tiền:** {amount:,}đ" if amount else "**Số tiền:** chưa xác định")
            st.write(f"**Trạng thái thanh toán:** {payment_status}")
            st.write(f"**Trạng thái đơn:** {order_status}")

        with col2:
            st.markdown("### Thành phần bó hoa")

            if bouquet_items:
                for item in bouquet_items:
                    flower_name = item.get("flower_name")
                    quantity = item.get("quantity")
                    role = item.get("role")
                    unit_price = item.get("unit_price")

                    st.write(
                        f"- **{flower_name}**: {quantity} cành "
                        f"({role}) - {unit_price:,}đ/cành"
                        if unit_price
                        else f"- **{flower_name}**: {quantity} cành ({role})"
                    )
            else:
                st.write("Chưa có thành phần bó hoa.")

        st.divider()

        if payment_status != "paid":
            if st.button(
                f"Xác nhận đã thanh toán và trừ kho",
                key=f"confirm_payment_{order_id}"
            ):
                result = order_service.confirm_payment(order_id=order_id)

                if result.get("success"):
                    st.success(f"Đã xác nhận thanh toán cho đơn {order_id}.")
                    st.json(result)
                    st.rerun()
                else:
                    st.error(result.get("message", "Không xác nhận được thanh toán."))
                    st.json(result)
        else:
            st.success("Đơn này đã được xác nhận thanh toán.")

        st.write("Raw order data:")
        st.json(order)