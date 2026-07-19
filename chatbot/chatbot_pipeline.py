from chatbot.conversation_state import ConversationState
from chatbot.dialog_manager import DialogManager
from chatbot.response_generator import ResponseGenerator

from dialogue.dialogue_policy import DialoguePolicy
from inventory.inventory_service import InventoryService
from orders.order_service import OrderService


class ChatbotPipeline:
    def __init__(self, recommender_func=None, dialogue_policy_func=None):
        self.state = ConversationState()

        self.dialog_manager = DialogManager()
        self.response_generator = ResponseGenerator()

        self.recommender_func = recommender_func
        self.dialogue_policy_func = dialogue_policy_func

        self.rule_policy = DialoguePolicy()

        self.inventory_service = InventoryService()
        self.order_service = OrderService()

        self.last_bot_message = ""
        self.last_recommendation = None

    # =====================================================
    # MAIN CHAT
    # =====================================================

    def chat(self, user_message: str):
        current_state = self.state.get_state()

        policy_output = self._predict_policy(
            user_message=user_message,
            state=current_state,
            last_bot_message=self.last_bot_message,
        )

        policy_slots = policy_output.get("slots", {})

        if policy_slots:
            self.state.update(policy_slots)

        updated_state = self.state.get_state()

        action = policy_output.get("action", "clarify_user_intent")

        # =================================================
        # SECURITY GUARDRAIL
        # Customer chatbot không được xác nhận thanh toán
        # =================================================

        if action == "confirm_payment" or self._is_payment_confirmation_request(user_message):
            response = (
                "Dạ chức năng xác nhận thanh toán chỉ dành cho admin. "
                "Anh/chị vui lòng chờ shop kiểm tra giao dịch và xác nhận đơn hàng ạ."
            )

            return self._build_result(
                message=response,
                result_type="security_block",
                policy_output=policy_output,
                state=updated_state,
            )

        # =================================================
        # ROUTE ACTIONS
        # =================================================

        if action == "check_inventory":
            response = self._handle_inventory_check(updated_state)

            return self._build_result(
                message=response,
                result_type="inventory",
                policy_output=policy_output,
                state=updated_state,
            )

        if action == "answer_flower_colors":
            response = self._answer_flower_colors(updated_state)

            return self._build_result(
                message=response,
                result_type="flower_colors",
                policy_output=policy_output,
                state=updated_state,
            )

        if action == "answer_price_info":
            response = self._answer_price_info()

            return self._build_result(
                message=response,
                result_type="price_info",
                policy_output=policy_output,
                state=updated_state,
            )

        if action == "answer_premium_option":
            response = self._answer_premium_option()

            return self._build_result(
                message=response,
                result_type="premium_option",
                policy_output=policy_output,
                state=updated_state,
            )

        if action == "answer_budget_suggestion":
            response = self._answer_budget_suggestion()

            return self._build_result(
                message=response,
                result_type="budget_suggestion",
                policy_output=policy_output,
                state=updated_state,
            )

        if action == "answer_flower_pairing":
            response = self._answer_flower_pairing(updated_state)

            return self._build_result(
                message=response,
                result_type="flower_pairing",
                policy_output=policy_output,
                state=updated_state,
            )

        if action == "answer_flower_meaning":
            response = self._answer_flower_meaning(updated_state)

            return self._build_result(
                message=response,
                result_type="flower_meaning",
                policy_output=policy_output,
                state=updated_state,
            )

        if action == "collect_customer_info":
            response = (
                "Dạ anh/chị cho em xin thông tin nhận hàng theo mẫu:\n\n"
                "**Họ tên - Số điện thoại - Địa chỉ giao hàng**"
            )

            return self._build_result(
                message=response,
                result_type="collect_customer_info",
                policy_output=policy_output,
                state=updated_state,
            )

        if action == "create_order":
            response = self._handle_create_order(updated_state)

            return self._build_result(
                message=response,
                result_type="order",
                policy_output=policy_output,
                state=updated_state,
            )

        if action == "answer_general":
            response = (
                "Dạ em có thể hỗ trợ tư vấn bó hoa theo dịp tặng, ngân sách, "
                "loại hoa, màu sắc, kiểm tra tồn kho hoặc tạo đơn hàng cho anh/chị ạ."
            )

            return self._build_result(
                message=response,
                result_type="general",
                policy_output=policy_output,
                state=updated_state,
            )

        if action == "recommend_bouquet" or policy_output.get("should_recommend", False):
            response = self._handle_recommendation(updated_state)

            return self._build_result(
                message=response,
                result_type="recommendation",
                policy_output=policy_output,
                state=updated_state,
            )

        response = self._handle_missing_info(updated_state)

        return self._build_result(
            message=response,
            result_type="ask_missing_info",
            policy_output=policy_output,
            state=updated_state,
        )

    # =====================================================
    # POLICY
    # =====================================================

    def _predict_policy(self, user_message: str, state: dict, last_bot_message: str):
        if self.dialogue_policy_func is not None:
            try:
                return self.dialogue_policy_func(
                    user_message=user_message,
                    state=state,
                    last_bot_message=last_bot_message,
                )
            except TypeError:
                try:
                    return self.dialogue_policy_func(
                        user_message,
                        state,
                        last_bot_message,
                    )
                except Exception:
                    pass
            except Exception:
                pass

        try:
            return self.rule_policy.predict(
                user_message=user_message,
                state=state,
                last_bot_message=last_bot_message,
            )
        except TypeError:
            return self.rule_policy.predict(
                user_message,
                state,
                last_bot_message,
            )

    # =====================================================
    # HANDLERS
    # =====================================================

    def _handle_missing_info(self, state: dict):
        if not state.get("occasion"):
            return (
                "Dạ anh/chị muốn tặng bó hoa này vào dịp gì ạ? "
                "Ví dụ sinh nhật, kỷ niệm, tốt nghiệp hoặc chúc mừng."
            )

        if not state.get("recipient"):
            return (
                "Dạ anh/chị muốn tặng bó hoa này cho ai ạ? "
                "Ví dụ người yêu, mẹ, bạn bè, thầy cô hoặc đồng nghiệp."
            )

        if not state.get("budget"):
            return (
                "Dạ anh/chị muốn bó hoa trong khoảng ngân sách bao nhiêu ạ? "
                "Ví dụ 500k, 800k hoặc khoảng từ 500k đến 1 triệu."
            )

        return self._handle_recommendation(state)

    def _handle_recommendation(self, state: dict):
        if self.recommender_func is None:
            return (
                "Dạ hiện tại chức năng gợi ý bó hoa chưa được kết nối. "
                "Anh/chị vui lòng thử lại sau ạ."
            )

        try:
            recommendation = self.recommender_func(state)

            self.last_recommendation = recommendation

            return self._format_recommendation_response(recommendation)

        except Exception as e:
            return (
                "Dạ hệ thống đang gặp lỗi khi gợi ý bó hoa. "
                f"Chi tiết lỗi: {str(e)}"
            )

    def _handle_inventory_check(self, state: dict):
        flower_names = state.get("flower_preference", [])

        if not flower_names:
            return (
                "Dạ anh/chị muốn kiểm tra tồn kho loại hoa nào ạ? "
                "Ví dụ: cẩm tú cầu, hoa hồng, tulip, cát tường."
            )

        responses = []

        for flower_name in flower_names:
            flower = self.inventory_service.get_flower(flower_name)

            if not flower:
                alternatives = self.inventory_service.suggest_alternatives(flower_name)

                if alternatives:
                    alt_names = [
                        item.get("flower_name", "hoa khác")
                        for item in alternatives[:3]
                    ]
                    responses.append(
                        f"Dạ hiện em chưa tìm thấy **{flower_name}** trong kho. "
                        f"Anh/chị có thể tham khảo: {', '.join(alt_names)}."
                    )
                else:
                    responses.append(
                        f"Dạ hiện em chưa tìm thấy **{flower_name}** trong kho ạ."
                    )

                continue

            stock = flower.get("stock", 0)
            status = flower.get("status", "unknown")
            unit_price = flower.get("unit_price", 0)

            if status == "out_of_stock" or stock <= 0:
                alternatives = self.inventory_service.suggest_alternatives(flower_name)

                if alternatives:
                    alt_names = [
                        item.get("flower_name", "hoa khác")
                        for item in alternatives[:3]
                    ]
                    responses.append(
                        f"Dạ **{flower_name}** hiện đang hết hàng. "
                        f"Anh/chị có thể đổi sang: {', '.join(alt_names)}."
                    )
                else:
                    responses.append(
                        f"Dạ **{flower_name}** hiện đang hết hàng ạ."
                    )
            else:
                responses.append(
                    f"Dạ **{flower_name}** hiện còn **{stock} cành**, "
                    f"giá khoảng **{unit_price:,}đ/cành** ạ."
                )

        return "\n\n".join(responses)

    def _handle_create_order(self, state: dict):
        customer_name = state.get("customer_name")
        customer_phone = state.get("customer_phone")
        customer_address = state.get("customer_address")

        if not customer_name or not customer_phone or not customer_address:
            return (
                "Dạ anh/chị cho em xin thông tin nhận hàng theo mẫu:\n\n"
                "**Họ tên - Số điện thoại - Địa chỉ giao hàng**"
            )

        if not self.last_recommendation:
            return (
                "Dạ em chưa có bó hoa nào để tạo đơn. "
                "Anh/chị vui lòng để em gợi ý bó hoa trước ạ."
            )

        try:
            # OrderService của bạn nhận:
            # create_order(self, state: dict, recommendation: dict = None)
            result = self.order_service.create_order(
                state=state,
                recommendation=self.last_recommendation
            )

            if not result:
                return (
                    "Dạ hệ thống chưa tạo được đơn hàng. "
                    "Anh/chị thử lại giúp em ạ."
                )

            if result.get("success") is False:
                error_message = result.get("message") or result.get("error") or "Không rõ lỗi."
                return (
                    "Dạ hệ thống chưa tạo được đơn hàng.\n\n"
                    f"**Lý do:** {error_message}"
                )

            # create_order trả về {"success": True, "order": order}
            order = result.get("order", result)

            order_id = order.get("order_id", "Không rõ")

            payment = order.get("payment", {})

            payment_code = (
                payment.get("payment_code")
                or payment.get("code")
                or "Chưa có"
            )

            transfer_content = (
                payment.get("transfer_content")
                or payment.get("content")
                or payment.get("description")
                or payment_code
            )

            bouquet = order.get("bouquet", {})

            total_price = (
                payment.get("amount")
                or bouquet.get("estimated_price")
                or order.get("total_price")
                or order.get("estimated_price")
                or self._extract_total_price_from_recommendation(self.last_recommendation)
                or 0
            )

            try:
                total_price_text = f"{int(total_price):,}đ"
            except Exception:
                total_price_text = str(total_price)

            response = (
                "Dạ em đã tạo đơn hàng cho anh/chị ạ.\n\n"
                f"**Mã đơn hàng:** {order_id}\n\n"
                f"**Tổng tiền:** {total_price_text}\n\n"
                f"**Mã thanh toán:** {payment_code}\n\n"
                f"**Nội dung chuyển khoản:** `{transfer_content}`\n\n"
                "Sau khi anh/chị chuyển khoản, shop sẽ kiểm tra và xác nhận thanh toán ạ."
            )

            return response

        except Exception as e:
            return (
                "Dạ hệ thống đang gặp lỗi khi tạo đơn hàng. "
                f"Chi tiết lỗi: {str(e)}"
            )

    # =====================================================
    # ANSWER HELPERS
    # =====================================================

    def _answer_price_info(self):
        return (
            "Dạ giá bó hoa thường phụ thuộc vào loại hoa, số lượng cành, "
            "phụ kiện trang trí và phong cách bó. "
            "Anh/chị có thể cho em biết ngân sách dự kiến, ví dụ 500k, 800k "
            "hoặc khoảng từ 500k đến 1 triệu để em tư vấn phù hợp hơn ạ."
        )

    def _answer_premium_option(self):
        return (
            "Dạ với ngân sách cao hơn, em có thể gợi ý bó hoa dùng hoa chính đẹp hơn, "
            "nhiều lớp hoa phụ hơn và phối màu sang hơn. "
            "Anh/chị cho em biết mức ngân sách mong muốn để em gợi ý cụ thể ạ."
        )

    def _answer_budget_suggestion(self):
        return (
            "Dạ nếu anh/chị chưa rõ ngân sách, có thể tham khảo nhanh:\n\n"
            "- Khoảng **300k - 500k**: bó nhỏ, đơn giản.\n"
            "- Khoảng **500k - 800k**: bó vừa, đẹp và cân đối.\n"
            "- Trên **800k**: bó lớn hơn, phối nhiều hoa và phụ kiện hơn."
        )

    def _answer_flower_pairing(self, state: dict):
        flowers = state.get("flower_preference", [])

        if flowers:
            flower_text = ", ".join(flowers)
            return (
                f"Dạ với **{flower_text}**, em có thể phối thêm baby trắng, "
                "hoa hồng kem hoặc lá bạc để bó hoa mềm mại và sang hơn ạ."
            )

        return (
            "Dạ anh/chị muốn phối hoa nào ạ? "
            "Ví dụ cẩm tú cầu, hoa hồng, tulip hoặc cát tường."
        )

    def _answer_flower_meaning(self, state: dict):
        flowers = state.get("flower_preference", [])

        if not flowers:
            return (
                "Dạ anh/chị muốn hỏi ý nghĩa loài hoa nào ạ? "
                "Ví dụ hoa hồng, cẩm tú cầu, tulip hoặc cát tường."
            )

        meanings = {
            "hoa hồng": "tình yêu, sự lãng mạn và sự trân trọng",
            "cẩm tú cầu": "sự chân thành, biết ơn và cảm xúc tinh tế",
            "tulip": "tình cảm nhẹ nhàng, thanh lịch và sự may mắn",
            "cát tường": "may mắn, tốt lành và lời chúc bình an",
            "hướng dương": "sự tích cực, niềm tin và năng lượng vui vẻ",
            "baby": "sự tinh khiết, nhẹ nhàng và tình cảm trong sáng",
        }

        responses = []

        for flower in flowers:
            meaning = meanings.get(flower)
            if meaning:
                responses.append(f"**{flower}** thường tượng trưng cho {meaning}.")
            else:
                responses.append(
                    f"Dạ **{flower}** là loài hoa đẹp và có thể phối theo nhiều dịp tặng khác nhau ạ."
                )

        return "\n\n".join(responses)

    def _answer_flower_colors(self, state: dict):
        flower_names = state.get("flower_preference", [])

        # Nếu user hỏi "những hoa trên" nhưng không nói tên hoa,
        # lấy danh sách hoa từ bó hoa đã recommend gần nhất.
        if not flower_names:
            flower_names = self._extract_flowers_from_last_recommendation()

        if not flower_names:
            return (
                "Dạ anh/chị muốn hỏi màu của loại hoa nào ạ? "
                "Ví dụ: cẩm tú cầu, hoa hồng kem, baby trắng hoặc cát tường."
            )

        responses = []

        for flower_name in flower_names:
            flower = self.inventory_service.get_flower(flower_name)

            if not flower:
                responses.append(
                    f"Dạ hiện em chưa có dữ liệu màu cho **{flower_name}** trong kho ạ."
                )
                continue

            colors = (
                flower.get("colors")
                or flower.get("color")
                or flower.get("color_tone")
                or flower.get("available_colors")
                or []
            )

            if isinstance(colors, str):
                colors = [colors]

            if colors:
                color_text = ", ".join(colors)
                responses.append(
                    f"**{flower_name}** hiện có các màu/tone: **{color_text}**."
                )
            else:
                responses.append(
                    f"Dạ **{flower_name}** hiện chưa có thông tin màu chi tiết trong kho ạ."
                )

        return "\n\n".join(responses)

    # =====================================================
    # FORMATTERS
    # =====================================================

    def _format_recommendation_response(self, recommendation):
        if not recommendation:
            return (
                "Dạ em chưa tìm được bó hoa phù hợp. "
                "Anh/chị có thể đổi ngân sách hoặc loại hoa mong muốn giúp em ạ."
            )

        if not isinstance(recommendation, dict):
            return str(recommendation)

        recommended_flowers = recommendation.get("recommended_flowers", [])
        rag_recommended_flowers = recommendation.get("rag_recommended_flowers", [])
        bouquet_proposal = recommendation.get("bouquet_proposal", {})
        budget_note = recommendation.get("budget_note")
        final_advice = recommendation.get("final_advice")

        lines = []
        lines.append("Dạ em gợi ý cho anh/chị bó hoa như sau:\n")

        bouquet_items = []
        estimated_price = None
        proposal_advice = None

        if isinstance(bouquet_proposal, dict) and bouquet_proposal:
            bouquet_items = (
                bouquet_proposal.get("bouquet_items")
                or bouquet_proposal.get("items")
                or bouquet_proposal.get("flowers")
                or bouquet_proposal.get("components")
                or []
            )

            estimated_price = (
                bouquet_proposal.get("estimated_price")
                or bouquet_proposal.get("total_price")
                or bouquet_proposal.get("price")
                or bouquet_proposal.get("final_price")
            )

            proposal_advice = (
                bouquet_proposal.get("advice")
                or bouquet_proposal.get("message")
                or bouquet_proposal.get("note")
            )

        if bouquet_items:
            lines.append("**Thành phần bó hoa:**")

            for item in bouquet_items:
                lines.append(self._format_flower_item(item))

        elif recommended_flowers:
            lines.append("**Các hoa phù hợp:**")

            for item in recommended_flowers:
                lines.append(self._format_recommended_flower(item))

        else:
            lines.append(
                "Hiện tại hệ thống đã gọi chức năng gợi ý, "
                "nhưng chưa lấy được danh sách hoa chi tiết."
            )

            keys = ", ".join(recommendation.keys())
            lines.append(f"\n**Debug keys recommendation:** `{keys}`")

        if rag_recommended_flowers:
            lines.append("\n**Gợi ý thêm từ RAG:**")

            for item in rag_recommended_flowers[:3]:
                if isinstance(item, dict):
                    flower_name = (
                        item.get("flower_name")
                        or item.get("name")
                        or item.get("english_name")
                        or "Hoa"
                    )
                    lines.append(f"- {flower_name}")
                else:
                    lines.append(f"- {item}")

        if estimated_price is not None:
            try:
                lines.append(f"\n**Giá dự kiến:** {int(estimated_price):,}đ")
            except Exception:
                lines.append(f"\n**Giá dự kiến:** {estimated_price}")

        if budget_note:
            lines.append(f"\n**Ghi chú ngân sách:** {budget_note}")

        if proposal_advice:
            lines.append(f"\n**Tư vấn bó hoa:** {proposal_advice}")

        if final_advice:
            lines.append(f"\n**Tư vấn:** {final_advice}")

        lines.append(
            "\nNếu anh/chị thích bó này, có thể nhắn **ok lấy bó này** để em tạo đơn ạ."
        )

        return "\n".join(lines)

    def _format_flower_item(self, item):
        if isinstance(item, str):
            return f"- {item}"

        if not isinstance(item, dict):
            return f"- {str(item)}"

        flower_name = (
            item.get("flower_name")
            or item.get("name")
            or item.get("flower")
            or item.get("item_name")
            or item.get("title")
            or "Hoa"
        )

        quantity = (
            item.get("quantity")
            or item.get("qty")
            or item.get("amount")
            or item.get("count")
            or 1
        )

        unit_price = (
            item.get("unit_price")
            or item.get("price")
            or item.get("unitPrice")
            or item.get("unit_cost")
            or 0
        )

        subtotal = (
            item.get("subtotal")
            or item.get("total")
            or item.get("total_price")
            or item.get("cost")
            or None
        )

        if subtotal is None:
            try:
                subtotal = int(quantity) * int(unit_price)
            except Exception:
                subtotal = 0

        try:
            subtotal_text = f"{int(subtotal):,}đ"
        except Exception:
            subtotal_text = str(subtotal)

        if unit_price:
            return (
                f"- **{flower_name}**: {quantity} cành "
                f"({subtotal_text})"
            )

        return f"- **{flower_name}**: {quantity} cành"

    def _format_recommended_flower(self, item):
        if isinstance(item, str):
            return f"- {item}"

        if not isinstance(item, dict):
            return f"- {str(item)}"

        flower_name = (
            item.get("flower_name")
            or item.get("name")
            or item.get("english_name")
            or "Hoa"
        )

        reason = (
            item.get("reason")
            or item.get("description")
            or item.get("explanation")
            or item.get("meaning")
            or ""
        )

        score = (
            item.get("score")
            or item.get("hybrid_score")
            or item.get("semantic_score")
            or item.get("final_score")
        )

        line = f"- **{flower_name}**"

        if score is not None:
            try:
                line += f" — điểm phù hợp: {float(score):.2f}"
            except Exception:
                pass

        if reason:
            line += f"\n  {reason}"

        return line

    def _extract_flowers_from_last_recommendation(self):
        if not isinstance(self.last_recommendation, dict):
            return []

        flower_names = []

        bouquet_proposal = self.last_recommendation.get("bouquet_proposal", {})

        if isinstance(bouquet_proposal, dict):
            bouquet_items = (
                bouquet_proposal.get("bouquet_items")
                or bouquet_proposal.get("items")
                or bouquet_proposal.get("flowers")
                or bouquet_proposal.get("components")
                or []
            )

            for item in bouquet_items:
                if isinstance(item, dict):
                    flower_name = (
                        item.get("flower_name")
                        or item.get("name")
                        or item.get("flower")
                        or item.get("item_name")
                    )

                    if flower_name and flower_name not in flower_names:
                        flower_names.append(flower_name)

        if not flower_names:
            recommended_flowers = self.last_recommendation.get("recommended_flowers", [])

            for item in recommended_flowers:
                if isinstance(item, dict):
                    flower_name = (
                        item.get("flower_name")
                        or item.get("name")
                        or item.get("english_name")
                    )

                    if flower_name and flower_name not in flower_names:
                        flower_names.append(flower_name)

        return flower_names

    def _extract_total_price_from_recommendation(self, recommendation):
        if not isinstance(recommendation, dict):
            return 0

        bouquet_proposal = recommendation.get("bouquet_proposal", {})

        if isinstance(bouquet_proposal, dict):
            price = (
                bouquet_proposal.get("estimated_price")
                or bouquet_proposal.get("total_price")
                or bouquet_proposal.get("price")
                or bouquet_proposal.get("final_price")
            )

            if price:
                return price

        price = (
            recommendation.get("estimated_price")
            or recommendation.get("total_price")
            or recommendation.get("price")
            or recommendation.get("final_price")
        )

        if price:
            return price

        return 0

    def _build_result(self, message, result_type, policy_output, state):
        self.last_bot_message = message

        return {
            "type": result_type,
            "message": message,
            "policy_output": policy_output,
            "state": state,
            "last_recommendation": self.last_recommendation,
        }

    # =====================================================
    # UTILS
    # =====================================================

    def _is_payment_confirmation_request(self, user_message: str):
        user_lower = user_message.lower()

        keywords = [
            "xác nhận thanh toán",
            "confirm payment",
            "đã thanh toán",
            "duyệt thanh toán",
            "xác nhận đơn đã trả tiền",
        ]

        return any(keyword in user_lower for keyword in keywords)

    def reset(self):
        self.state.reset()
        self.last_bot_message = ""
        self.last_recommendation = None