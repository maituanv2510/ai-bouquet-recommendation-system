# Demo Checklist

This checklist is used to demonstrate the AI Bouquet Recommendation & Flower Shop Management System.

---

## 1. Start Customer Chatbot

Run:

```powershell
python -m streamlit run frontend\streamlit_customer.py
```

Expected:

- Customer chatbot UI opens.
- Sidebar shows conversation state.
- Debug panel shows policy output and last recommendation.

---

## 2. Start Admin Dashboard

Run:

```powershell
python -m streamlit run frontend\streamlit_admin.py
```

Default MVP password:

```text
123456
```

Expected:

- Admin dashboard opens.
- Admin can view the order list.
- Admin can confirm payment.
- Order status and inventory are updated after confirmation.

---

## 3. Customer Bouquet Request

Input:

```text
tôi muốn mua một bó hoa tặng người yêu nhân dịp valentine
```

Expected:

- Bot extracts occasion: `Valentine`
- Bot extracts recipient: `người yêu`
- Bot asks for budget if budget is missing.

---

## 4. Provide Budget

Input:

```text
tầm trên 700k đi
```

Expected:

- Bot extracts budget: `700000`
- Bot extracts budget type: `minimum`
- Bot recommends a bouquet.

---

## 5. Ask Flower Colors

Input:

```text
những hoa trên có màu nào khác không
```

Expected:

- Bot does not create a new order.
- Bot does not reset the conversation.
- Bot returns available colors of flowers in the recommended bouquet.

---

## 6. Modify Bouquet Color or Main Flower

Input:

```text
cẩm tú cầu màu xanh làm chủ đạo nhé
```

Expected:

- Bot updates `flower_preference`.
- Bot updates `color_tone`.
- Bot recommends again using the new flower/color preference.

---

## 7. Confirm Order

Input:

```text
ok tôi lấy bó này
```

Expected:

- Bot does not confirm payment.
- Bot asks for customer information.

Expected bot response should ask for:

```text
Họ tên - Số điện thoại - Địa chỉ giao hàng
```

---

## 8. Provide Customer Information

Input:

```text
Nguyễn Viết Anh - 0866660251 - Xóm Trung Tiến, Xã Hưng Đông, Vinh, Nghệ An
```

Expected:

- Bot creates an order.
- Bot returns order ID.
- Bot returns payment code.
- Bot returns transfer content.

---

## 9. Check Order JSON

Open:

```text
orders/orders.json
```

Expected:

- New order is saved.
- Order status is `pending_payment`.
- Payment status is `pending`.

---

## 10. Admin Confirm Payment

In Admin Dashboard:

- Find pending order.
- Click confirm payment.

Expected:

- Payment status changes to `paid`.
- Order status changes to `preparing`.
- Inventory stock is decreased.

---

## 11. Check Inventory JSON

Open:

```text
inventory/inventory_data.json
```

Expected:

- Stock of bouquet items decreases according to bouquet quantities.

---

## 12. Security Test

Input in customer chatbot:

```text
xác nhận thanh toán đơn ORD-20260719-0001
```

Expected:

- Bot blocks the request.
- Customer chatbot must not confirm payment.
- Payment confirmation is only available in Admin Dashboard.

---

## 13. Run E2E Test

Run:

```powershell
python scripts\test_e2e_chatbot.py
```

Expected:

- Test cases are executed.
- Report is saved to:

```text
outputs/e2e_chatbot_test_report.json
```

---

## 14. Analyze Failed Cases

Run:

```powershell
python scripts\analyze_e2e_failures.py
```

Expected:

- Failed cases are extracted.
- Output is saved to:

```text
outputs/e2e_failed_cases.json
```