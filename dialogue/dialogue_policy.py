import re

from dialogue.action_schema import get_empty_policy_output, validate_policy_output, DEFAULT_SLOTS


class DialoguePolicy:
    def __init__(self, model_func=None):
        self.model_func = model_func

    def predict(self, user_message: str, state: dict = None, last_bot_message: str = ""):
        state = state or {}

        if self.model_func:
            output = self.model_func(
                user_message=user_message,
                state=state,
                last_bot_message=last_bot_message
            )

            ok, message = validate_policy_output(output)

            if ok:
                return output

            print(f"[DialoguePolicy] Invalid model output: {message}")

        output = self._rule_based_policy(
            user_message=user_message,
            state=state,
            last_bot_message=last_bot_message
        )

        ok, message = validate_policy_output(output)

        if not ok:
            print(f"[DialoguePolicy] Invalid fallback output: {message}")
            return get_empty_policy_output()

        return output

    def _rule_based_policy(self, user_message: str, state: dict, last_bot_message: str):
        text = user_message.lower().strip()

        slots = self._extract_slots(text)

        # 1. Payment confirmation is admin-only.
        # Customer chatbot must never route this to confirm_payment.
        if self._looks_like_payment_confirmation_request(text):
            return self._make_output(
                intent="general_question",
                action="answer_general",
                slots=DEFAULT_SLOTS.copy(),
                should_update_state=False,
                should_recommend=False,
                should_check_inventory=False,
                should_create_order=False,
                should_collect_customer_info=False,
                response_goal="Từ chối xác nhận thanh toán vì đây là chức năng admin."
            )

        # 2. Customer info
        if self._looks_like_customer_info(text, last_bot_message):
            customer_slots = self._extract_customer_info(user_message)

            return self._make_output(
                intent="provide_customer_info",
                action="create_order",
                slots=customer_slots,
                should_update_state=True,
                should_recommend=False,
                should_check_inventory=True,
                should_create_order=True,
                should_collect_customer_info=False,
                response_goal="Lưu thông tin khách hàng và tạo đơn hàng."
            )

        # 3. Confirm order
        if self._contains_any(text, [
            "chốt", "lấy bó này", "đặt bó này", "tạo đơn", "mình lấy",
            "tôi lấy", "ok lấy", "okela", "oke lấy", "đồng ý", "chốt đơn",
            "lấy bó đó", "lấy bó này đi", "lấy phương án này", "lấy mẫu này"
        ]):
            return self._make_output(
                intent="confirm_order",
                action="collect_customer_info",
                slots=DEFAULT_SLOTS.copy(),
                should_update_state=False,
                should_recommend=False,
                should_check_inventory=True,
                should_create_order=False,
                should_collect_customer_info=True,
                response_goal="Khách đã chốt phương án, cần xin tên, số điện thoại và địa chỉ giao hàng."
            )

        # 4. Ask premium / highest price
        if self._contains_any(text, [
            "đắt nhất", "cao cấp nhất", "premium", "xịn nhất",
            "bó lớn nhất", "bó sang nhất"
        ]):
            return self._make_output(
                intent="ask_premium_option",
                action="answer_premium_option",
                slots=DEFAULT_SLOTS.copy(),
                should_update_state=False,
                should_recommend=False,
                should_check_inventory=False,
                should_create_order=False,
                should_collect_customer_info=False,
                response_goal="Giải thích các mức giá bó hoa cao cấp/premium của shop, chưa tạo đơn."
            )

        # 5. Ask general price
        if self._contains_any(text, [
            "giá bao nhiêu", "tầm bao nhiêu", "khoảng bao nhiêu",
            "bó rẻ nhất", "tầm tiền", "mức giá", "bao nhiêu tiền"
        ]):
            return self._make_output(
                intent="ask_price_range",
                action="answer_price_info",
                slots=slots,
                should_update_state=False,
                should_recommend=False,
                should_check_inventory=False,
                should_create_order=False,
                should_collect_customer_info=False,
                response_goal="Giải thích các mức giá bó hoa phổ biến của shop."
            )

        # 6. Ask flower combination
        if self._contains_any(text, [
            "phối với hoa nào", "kết hợp với hoa nào", "nên phối",
            "nên kết hợp", "đi với hoa nào", "hợp với hoa nào"
        ]):
            return self._make_output(
                intent="ask_flower_combination",
                action="answer_flower_pairing",
                slots=slots,
                should_update_state=True,
                should_recommend=False,
                should_check_inventory=True,
                should_create_order=False,
                should_collect_customer_info=False,
                response_goal="Tư vấn loại hoa nên phối, hợp dịp nào và người nhận nào."
            )

        # 7. Ask inventory
        if self._contains_any(text, [
            "còn hàng không", "còn không", "có không", "shop còn",
            "bên mình có", "bên bạn có"
        ]) and slots.get("flower_preference"):
            return self._make_output(
                intent="ask_inventory",
                action="check_inventory",
                slots=slots,
                should_update_state=True,
                should_recommend=False,
                should_check_inventory=True,
                should_create_order=False,
                should_collect_customer_info=False,
                response_goal="Kiểm tra tồn kho loại hoa khách hỏi."
            )

        # 8. Modify existing bouquet
        if self._contains_any(text, [
            "đổi", "thay", "bỏ", "không thích", "tránh", "không lấy", "thêm",
            "cho thêm", "tăng ngân sách", "giảm ngân sách", "chuyển sang"
        ]):
            intent = self._detect_modify_intent(text)

            return self._make_output(
                intent=intent,
                action="update_bouquet",
                slots=slots,
                should_update_state=True,
                should_recommend=True,
                should_check_inventory=True,
                should_create_order=False,
                should_collect_customer_info=False,
                response_goal="Cập nhật yêu cầu mới của khách và đề xuất lại bó hoa."
            )

        # 9. New bouquet request / provide missing info
        has_bouquet_signal = self._contains_any(text, [
            "đặt bó hoa", "mua bó hoa", "cần bó hoa", "tư vấn bó hoa",
            "cho tôi bó", "cho mình bó", "muốn bó hoa", "tặng"
        ])

        has_useful_slots = self._has_useful_slots(slots)

        if has_bouquet_signal or has_useful_slots:
            current_has_required = self._state_has_required_after_update(state, slots)

            if current_has_required:
                return self._make_output(
                    intent="new_bouquet_request",
                    action="recommend_bouquet",
                    slots=slots,
                    should_update_state=True,
                    should_recommend=True,
                    should_check_inventory=True,
                    should_create_order=False,
                    should_collect_customer_info=False,
                    response_goal="Đề xuất bó hoa phù hợp với yêu cầu, ngân sách và tồn kho."
                )

            return self._make_output(
                intent="provide_missing_info",
                action="ask_missing_info",
                slots=slots,
                should_update_state=True,
                should_recommend=False,
                should_check_inventory=False,
                should_create_order=False,
                should_collect_customer_info=False,
                response_goal="Cập nhật thông tin khách vừa cung cấp và hỏi tiếp thông tin còn thiếu."
            )

        return self._make_output(
            intent="unclear",
            action="clarify_user_intent",
            slots=DEFAULT_SLOTS.copy(),
            should_update_state=False,
            should_recommend=False,
            should_check_inventory=False,
            should_create_order=False,
            should_collect_customer_info=False,
            response_goal="Hỏi lại khách muốn tư vấn theo hướng nào: ngân sách, loại hoa, dịp tặng, kiểm tra kho hoặc tạo đơn."
        )

    def _make_output(
        self,
        intent,
        action,
        slots,
        should_update_state,
        should_recommend,
        should_check_inventory,
        should_create_order,
        should_collect_customer_info,
        response_goal
    ):
        merged_slots = DEFAULT_SLOTS.copy()
        merged_slots.update(slots or {})

        return {
            "intent": intent,
            "action": action,
            "slots": merged_slots,
            "should_update_state": should_update_state,
            "should_recommend": should_recommend,
            "should_check_inventory": should_check_inventory,
            "should_create_order": should_create_order,
            "should_collect_customer_info": should_collect_customer_info,
            "response_goal": response_goal
        }

    def _extract_slots(self, text: str):
        slots = DEFAULT_SLOTS.copy()

        # Occasion
        if "sinh nhật" in text:
            slots["occasion"] = "sinh nhật"
        elif "kỷ niệm" in text or "kỉ niệm" in text:
            slots["occasion"] = "kỷ niệm"
        elif "tốt nghiệp" in text:
            slots["occasion"] = "tốt nghiệp"
        elif "khai trương" in text:
            slots["occasion"] = "khai trương"
        elif "chúc mừng" in text:
            slots["occasion"] = "chúc mừng"
        elif "cầu hôn" in text:
            slots["occasion"] = "cầu hôn"
        elif "tỏ tình" in text:
            slots["occasion"] = "tỏ tình"

        # Recipient
        if "bạn nữ" in text:
            slots["recipient"] = "bạn nữ"
        elif "cho mẹ" in text or "tặng mẹ" in text or "mẹ" in text:
            slots["recipient"] = "mẹ"
        elif "người yêu" in text:
            slots["recipient"] = "người yêu"
        elif "đồng nghiệp" in text:
            slots["recipient"] = "đồng nghiệp"
        elif "thầy cô" in text or "cô giáo" in text or "thầy giáo" in text:
            slots["recipient"] = "thầy cô"
        elif "bạn bè" in text:
            slots["recipient"] = "bạn bè"

        # Budget
        budget_info = self._extract_budget(text)
        slots.update(budget_info)

        # Flower preference / avoidance
        flower_keywords = [
            "cẩm tú cầu",
            "hoa hồng kem",
            "hoa hồng",
            "baby trắng",
            "baby",
            "tulip",
            "hướng dương",
            "hoa ly",
            "ly",
            "lan",
            "cát tường",
            "mẫu đơn",
            "đồng tiền",
            "lá bạc"
        ]

        avoid_signal = self._contains_any(text, [
            "không thích", "tránh", "không lấy", "đừng dùng", "bỏ"
        ])

        for flower in flower_keywords:
            if flower in text:
                if avoid_signal:
                    if flower not in slots["flower_avoidance"]:
                        slots["flower_avoidance"].append(flower)
                else:
                    if flower not in slots["flower_preference"]:
                        slots["flower_preference"].append(flower)

        # Color
        for color in ["hồng", "trắng", "xanh", "đỏ", "vàng", "tím", "pastel", "kem", "cam"]:
            if color in text and color not in slots["color_tone"]:
                slots["color_tone"].append(color)

        # Style
        style_map = {
            "nhẹ nhàng": "nhẹ nhàng",
            "sang trọng": "sang trọng",
            "tối giản": "tối giản",
            "rực rỡ": "rực rỡ",
            "dễ thương": "dễ thương",
            "trang nhã": "trang nhã",
            "tinh tế": "tinh tế",
            "bó giấy hàn quốc": "bó giấy Hàn Quốc",
            "giấy hàn quốc": "bó giấy Hàn Quốc",
            "bó tròn": "bó tròn",
            "bó dài": "bó dài"
        }

        for key, value in style_map.items():
            if key in text and value not in slots["style"]:
                slots["style"].append(value)

        return slots

    def _extract_budget(self, text: str):
        result = {
            "budget": None,
            "budget_min": None,
            "budget_max": None,
            "budget_type": None,
        }

        amounts = self._find_money_amounts(text)

        if not amounts:
            return result

        if (
            ("từ" in text and ("đến" in text or "tới" in text))
            or ("đến" in text and len(amounts) >= 2)
            or ("tới" in text and len(amounts) >= 2)
        ):
            if len(amounts) >= 2:
                budget_min = min(amounts[0], amounts[1])
                budget_max = max(amounts[0], amounts[1])

                result["budget_min"] = budget_min
                result["budget_max"] = budget_max
                result["budget"] = int((budget_min + budget_max) / 2)
                result["budget_type"] = "range"
                return result

        if self._contains_any(text, [
            "dưới", "không quá", "tối đa", "đổ lại", "trở xuống", "ít hơn"
        ]):
            result["budget_max"] = amounts[0]
            result["budget"] = amounts[0]
            result["budget_type"] = "maximum"
            return result

        if self._contains_any(text, [
            "trên", "hơn", "tối thiểu", "trở lên"
        ]):
            result["budget_min"] = amounts[0]
            result["budget"] = amounts[0]
            result["budget_type"] = "minimum"
            return result

        if self._contains_any(text, [
            "khoảng", "tầm", "cỡ"
        ]):
            result["budget"] = amounts[0]
            result["budget_min"] = int(amounts[0] * 0.85)
            result["budget_max"] = int(amounts[0] * 1.15)
            result["budget_type"] = "approximate"
            return result

        result["budget"] = amounts[0]
        result["budget_max"] = amounts[0]
        result["budget_type"] = "maximum"

        return result

    def _find_money_amounts(self, text: str):
        amounts = []

        pattern_k_tr = r"(\d+(?:[.,]\d+)?)\s*(k|tr|triệu)"
        matches = re.findall(pattern_k_tr, text)

        for number, unit in matches:
            number = number.replace(",", ".")
            value = float(number)

            if unit == "k":
                amounts.append(int(value * 1000))
            elif unit in ["tr", "triệu"]:
                amounts.append(int(value * 1000000))

        pattern_nghin = r"(\d+(?:[.,]\d+)?)\s*(nghìn|ngàn)"
        matches_nghin = re.findall(pattern_nghin, text)

        for number, unit in matches_nghin:
            number = number.replace(",", ".")
            value = float(number)
            amounts.append(int(value * 1000))

        return amounts

    def _looks_like_payment_confirmation_request(self, text: str):
        has_payment_signal = self._contains_any(text, [
            "xác nhận thanh toán",
            "đã thanh toán",
            "đã chuyển khoản",
            "confirm payment",
            "khách đã trả tiền",
            "đã trả tiền"
        ])

        has_order_id = re.search(
            r"ORD-\d{8}-\d{4}",
            text,
            flags=re.IGNORECASE
        ) is not None

        return has_payment_signal and has_order_id

    def _contains_any(self, text: str, keywords: list):
        return any(keyword in text for keyword in keywords)

    def _has_useful_slots(self, slots: dict):
        return any([
            slots.get("occasion"),
            slots.get("recipient"),
            slots.get("budget"),
            slots.get("flower_preference"),
            slots.get("flower_avoidance"),
            slots.get("color_tone"),
            slots.get("style")
        ])

    def _state_has_required_after_update(self, state: dict, slots: dict):
        occasion = slots.get("occasion") or state.get("occasion")
        recipient = slots.get("recipient") or state.get("recipient")
        budget = slots.get("budget") or state.get("budget")

        return bool(occasion and recipient and budget)

    def _detect_modify_intent(self, text: str):
        if self._contains_any(text, ["ngân sách", "tăng", "giảm", "đắt hơn", "rẻ hơn"]):
            return "modify_budget"

        if self._contains_any(text, ["tone", "màu"]):
            return "modify_color"

        if self._contains_any(text, ["kiểu", "phong cách", "sang trọng", "nhẹ nhàng", "hàn quốc"]):
            return "modify_style"

        return "modify_flower"

    def _looks_like_customer_info(self, text: str, last_bot_message: str = ""):
        has_phone = re.search(r"(0|\+84)\d{8,10}", text) is not None

        has_address_signal = self._contains_any(text, [
            "địa chỉ", "giao ở", "giao đến", "ở "
        ])

        has_name_signal = self._contains_any(text, [
            "tên tôi", "mình tên", "em tên", "anh tên", "chị tên", "tôi là"
        ])

        last_bot_asked_customer_info = self._contains_any(
            last_bot_message.lower(),
            [
                "cho em xin tên",
                "số điện thoại",
                "địa chỉ giao hàng",
                "tên người đặt"
            ]
        )

        has_dash_format = "-" in text and has_phone

        return has_phone and (
            has_address_signal
            or has_name_signal
            or last_bot_asked_customer_info
            or has_dash_format
        )

    def _extract_customer_info(self, user_message: str):
        slots = DEFAULT_SLOTS.copy()

        text = user_message.strip()

        phone_match = re.search(r"(0|\+84)\d{8,10}", text)

        if phone_match:
            slots["customer_phone"] = phone_match.group(0)

        # Case 1: "Tên - SĐT - Địa chỉ"
        if "-" in text and slots["customer_phone"]:
            parts = [part.strip() for part in text.split("-") if part.strip()]

            if len(parts) >= 3:
                slots["customer_name"] = parts[0]
                slots["customer_address"] = " - ".join(parts[2:])
                return slots

        # Case 2: "Tên, SĐT, Địa chỉ"
        if "," in text and slots["customer_phone"]:
            parts = [part.strip() for part in text.split(",") if part.strip()]

            if len(parts) >= 3:
                non_phone_parts = [
                    part for part in parts
                    if slots["customer_phone"] not in part
                ]

                if len(non_phone_parts) >= 2:
                    slots["customer_name"] = non_phone_parts[0]
                    slots["customer_address"] = non_phone_parts[-1]
                    return slots

        # Case 3: natural language
        name_patterns = [
            r"tên tôi là ([^,\.]+)",
            r"mình tên ([^,\.]+)",
            r"em tên ([^,\.]+)",
            r"anh tên ([^,\.]+)",
            r"chị tên ([^,\.]+)",
            r"tôi là ([^,\.]+)"
        ]

        for pattern in name_patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                slots["customer_name"] = match.group(1).strip()
                break

        address_patterns = [
            r"địa chỉ(?: là)? ([^,\.]+)",
            r"giao ở ([^,\.]+)",
            r"giao đến ([^,\.]+)",
            r"ở ([^,\.]+)"
        ]

        for pattern in address_patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                slots["customer_address"] = match.group(1).strip()
                break

        # Case 4: fallback
        if slots["customer_phone"] and not slots["customer_name"]:
            text_without_phone = text.replace(slots["customer_phone"], "").strip()
            text_without_phone = text_without_phone.replace("-", " ").replace(",", " ").strip()

            words = text_without_phone.split()

            if len(words) >= 2:
                slots["customer_name"] = " ".join(words[:3])

            if len(words) > 3:
                slots["customer_address"] = " ".join(words[3:])

        return slots