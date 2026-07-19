class ResponseGenerator:
    def __init__(self):
        pass

    # =========================
    # Helper functions
    # =========================

    def _format_list(self, items):
        if not items:
            return ""

        if isinstance(items, str):
            return items

        if len(items) == 1:
            return items[0]

        return ", ".join(items)

    def _format_money(self, amount):
        if amount is None:
            return ""

        return f"{amount:,}đ".replace(",", ".")

    def _convert_role_to_vietnamese(self, role: str):
        mapping = {
            "main": "hoa chính",
            "support": "hoa phụ",
            "decoration": "trang trí"
        }

        return mapping.get(role, role)

    # =========================
    # Follow-up / missing info
    # =========================

    def generate_follow_up_response(self, question: str, state: dict):
        return question

    # =========================
    # Recommendation response
    # =========================

    def generate_recommendation_response(self, recommendation: dict, state: dict):
        bouquet_proposal = recommendation.get("bouquet_proposal")

        if bouquet_proposal:
            return self._generate_bouquet_proposal_response(
                bouquet_proposal=bouquet_proposal,
                state=state
            )

        return self._generate_basic_recommendation_response(
            recommendation=recommendation,
            state=state
        )

    def _generate_bouquet_proposal_response(self, bouquet_proposal: dict, state: dict):
        budget_plan = bouquet_proposal.get("budget_plan", {})
        bouquet_items = bouquet_proposal.get("bouquet_items", [])
        estimated_price = bouquet_proposal.get("estimated_price")
        price_status = bouquet_proposal.get("price_status")
        advice = bouquet_proposal.get("advice")

        occasion = state.get("occasion")
        recipient = state.get("recipient")
        budget = state.get("budget")
        budget_min = state.get("budget_min")
        budget_max = state.get("budget_max")
        budget_type = state.get("budget_type")
        color_tone = state.get("color_tone", [])
        style = state.get("style", [])
        flower_preference = state.get("flower_preference", [])

        response = "Dạ em đề xuất một phương án bó hoa cụ thể như sau ạ.\n\n"

        summary_parts = []

        if occasion:
            summary_parts.append(f"dịp {occasion}")

        if recipient:
            summary_parts.append(f"tặng {recipient}")

        if budget_type == "range" and budget_min and budget_max:
            summary_parts.append(
                f"ngân sách từ {self._format_money(budget_min)} đến {self._format_money(budget_max)}"
            )
        elif budget_type == "minimum" and budget_min:
            summary_parts.append(
                f"ngân sách trên {self._format_money(budget_min)}"
            )
        elif budget_type == "maximum" and budget_max:
            summary_parts.append(
                f"ngân sách dưới {self._format_money(budget_max)}"
            )
        elif budget:
            summary_parts.append(f"ngân sách khoảng {self._format_money(budget)}")

        if flower_preference:
            summary_parts.append(f"ưu tiên {self._format_list(flower_preference)}")

        if color_tone:
            summary_parts.append(f"tone {self._format_list(color_tone)}")

        if style:
            summary_parts.append(f"phong cách {self._format_list(style)}")

        if summary_parts:
            response += "Với yêu cầu: "
            response += ", ".join(summary_parts)
            response += ".\n\n"

        bouquet_size = budget_plan.get("bouquet_size", "medium")
        budget_description = budget_plan.get("description", "")

        response += f"- Size bó đề xuất: {bouquet_size}\n"

        if estimated_price:
            response += f"- Giá ước lượng: {self._format_money(estimated_price)}\n"

        if price_status == "within_budget":
            response += "- Trạng thái ngân sách: nằm trong ngân sách khách đưa ra\n"
        elif price_status == "below_budget_range":
            response += "- Trạng thái ngân sách: đang thấp hơn khoảng ngân sách khách muốn, có thể tăng thêm hoa chính hoặc hoa phụ\n"
        elif price_status == "below_budget_minimum":
            response += "- Trạng thái ngân sách: đang thấp hơn mức tối thiểu khách muốn, nên tăng size bó hoặc thêm hoa cao cấp hơn\n"
        elif price_status == "slightly_over_budget":
            response += "- Trạng thái ngân sách: hơi vượt nhẹ, có thể giảm bớt hoa phụ hoặc lá trang trí\n"
        elif price_status == "over_budget":
            response += "- Trạng thái ngân sách: đang vượt ngân sách, nên giảm số lượng hoa chính hoặc chọn hoa thay thế mềm hơn\n"
        elif price_status == "unknown_budget":
            response += "- Trạng thái ngân sách: chưa có ngân sách cụ thể nên đây là phương án tham khảo\n"

        if budget_description:
            response += f"- Ghi chú: {budget_description}\n"

        response += "\nThành phần bó hoa em đề xuất:\n"

        if bouquet_items:
            for item in bouquet_items:
                role = item.get("role", "")
                flower_name = item.get("flower_name", "")
                quantity = item.get("quantity", 0)
                unit_price = item.get("unit_price", 0)
                reason = item.get("reason", "")

                role_vi = self._convert_role_to_vietnamese(role)

                line = f"- {flower_name}: {quantity} cành"

                if role_vi:
                    line += f" ({role_vi})"

                if unit_price:
                    line += f" - {self._format_money(unit_price)}/cành"

                if reason:
                    line += f". {reason}"

                response += line + "\n"
        else:
            response += "- Hiện tại chưa có thành phần bó hoa cụ thể.\n"

        response += "\nTư vấn phối hoa:\n"

        if advice:
            response += advice
        else:
            response += (
                "Bó hoa này có thể thiết kế theo hướng hài hòa giữa hoa chính, "
                "hoa phụ và lá trang trí để phù hợp với nhu cầu của khách hàng."
            )

        response += (
            "\n\nAnh/chị muốn em giữ phương án này, thêm hoa khác, đổi tone màu, "
            "đổi kiểu bó hay điều chỉnh ngân sách không ạ?"
        )

        return response

    def _generate_basic_recommendation_response(self, recommendation: dict, state: dict):
        occasion = state.get("occasion")
        recipient = state.get("recipient")
        budget = state.get("budget")
        flower_preference = state.get("flower_preference", [])
        color_tone = state.get("color_tone", [])
        style = state.get("style", [])

        recommended_flowers = recommendation.get("recommended_flowers", [])
        avoid_flowers = recommendation.get("avoid_flowers", [])
        budget_note = recommendation.get("budget_note", "")
        final_advice = recommendation.get("final_advice", "")

        flower_names = []

        for item in recommended_flowers:
            if isinstance(item, dict):
                name = (
                    item.get("flower_name")
                    or item.get("name")
                    or item.get("vietnamese_name")
                )
                if name and name not in flower_names:
                    flower_names.append(name)

        if not flower_names:
            flower_names = flower_preference

        flower_text = self._format_list(flower_names)
        preference_text = self._format_list(flower_preference)
        color_text = self._format_list(color_tone)
        style_text = self._format_list(style)

        response = "Dạ em gợi ý cho anh/chị một phương án như sau ạ.\n\n"

        details = []

        if budget:
            details.append(f"ngân sách khoảng {self._format_money(budget)}")

        if occasion:
            details.append(f"tặng dịp {occasion}")

        if recipient:
            details.append(f"cho {recipient}")

        if preference_text:
            details.append(f"ưu tiên {preference_text}")

        if color_text:
            details.append(f"tone {color_text}")

        if style_text:
            details.append(f"phong cách {style_text}")

        if details:
            response += "Với yêu cầu "
            response += ", ".join(details)
            response += ", em đề xuất:\n\n"
        else:
            response += "Với yêu cầu hiện tại, em đề xuất:\n\n"

        if flower_text:
            response += f"- Thành phần hoa gợi ý: {flower_text}\n"

        if budget_note:
            response += f"- Ghi chú ngân sách: {budget_note}\n"

        if avoid_flowers:
            avoid_text = self._format_list(avoid_flowers)
            response += f"- Nên tránh: {avoid_text}\n"

        response += "\n"

        if final_advice:
            response += final_advice
        else:
            response += (
                "Bó hoa này có thể thiết kế theo hướng hài hòa, dễ tặng "
                "và phù hợp với nhu cầu hiện tại ạ."
            )

        response += "\n\nAnh/chị có muốn em điều chỉnh thêm về màu sắc, kiểu bó hoặc loại hoa không ạ?"

        return response

    # =========================
    # DialoguePolicy action responses
    # =========================

    def generate_shop_price_info_response(self, state: dict):
        return (
            "Dạ giá bó hoa bên em thường chia theo các mức như sau ạ:\n\n"
            "- Bó nhỏ/basic: khoảng 250.000đ - 400.000đ, phù hợp tặng nhẹ nhàng hoặc các dịp đơn giản.\n"
            "- Bó vừa: khoảng 400.000đ - 700.000đ, phù hợp sinh nhật, tốt nghiệp, tặng bạn bè hoặc đồng nghiệp.\n"
            "- Bó đẹp/đầy đặn: khoảng 700.000đ - 1.200.000đ, phù hợp tặng mẹ, người yêu hoặc các dịp kỷ niệm.\n"
            "- Bó premium/lớn: từ 1.200.000đ trở lên, phù hợp dịp đặc biệt, cầu hôn, sự kiện hoặc khi muốn bó thật nổi bật.\n\n"
            "Nếu anh/chị cho em biết dịp tặng, người nhận và ngân sách dự kiến, em có thể đề xuất bó phù hợp hơn ạ."
        )

    def generate_premium_option_response(self, state: dict):
        occasion = state.get("occasion")
        recipient = state.get("recipient")

        response = (
            "Dạ với dòng bó cao cấp, shop có thể thiết kế nhiều mức tùy size và loại hoa ạ.\n\n"
            "Thông thường có thể chia như sau:\n\n"
            "- Bó cao cấp vừa: khoảng 800.000đ - 1.200.000đ\n"
            "- Bó lớn/premium: khoảng 1.200.000đ - 1.800.000đ\n"
            "- Bó sự kiện hoặc bó rất lớn: từ 2.000.000đ trở lên\n\n"
        )

        if occasion or recipient:
            details = []

            if occasion:
                details.append(f"dịp {occasion}")

            if recipient:
                details.append(f"tặng {recipient}")

            response += (
                f"Với {', '.join(details)}, em nghĩ mức đẹp và hợp lý là khoảng "
                "1.200.000đ - 1.500.000đ. "
            )

        response += (
            "Ở mức này có thể dùng nhiều hoa chính hơn như cẩm tú cầu, hoa hồng kem, "
            "cát tường, baby trắng và lá trang trí cao cấp để bó nhìn đầy, sang và có điểm nhấn hơn ạ.\n\n"
            "Anh/chị muốn em dựng thử một phương án bó premium khoảng 1.500.000đ không ạ?"
        )

        return response

    def generate_budget_suggestion_response(self, state: dict):
        return (
            "Dạ nếu anh/chị chưa rõ nên chọn ngân sách nào, em gợi ý như sau ạ:\n\n"
            "- Dưới 400.000đ: phù hợp bó nhỏ, đơn giản, dễ tặng.\n"
            "- 400.000đ - 700.000đ: phù hợp bó size vừa, nhìn đẹp và vẫn tiết kiệm.\n"
            "- 700.000đ - 1.200.000đ: bó sẽ đầy đặn hơn, có nhiều hoa chính và phối phụ đẹp hơn.\n"
            "- Trên 1.200.000đ: phù hợp bó premium, sang trọng, nhiều hoa chính hoặc hoa cao cấp.\n\n"
            "Với đa số nhu cầu sinh nhật hoặc tặng mẹ/người yêu, khoảng 600.000đ - 900.000đ là mức khá đẹp ạ."
        )

    def generate_flower_pairing_response(self, state: dict, slots: dict):
        flowers = slots.get("flower_preference") or state.get("flower_preference", [])

        if "cẩm tú cầu" in flowers:
            return (
                "Dạ cẩm tú cầu rất hợp để làm hoa chính vì form hoa tròn, mềm và nổi bật ạ.\n\n"
                "Một số cách phối đẹp:\n"
                "- Cẩm tú cầu + hoa hồng kem + baby trắng: nhẹ nhàng, sang, hợp sinh nhật, kỷ niệm, tặng mẹ hoặc người yêu.\n"
                "- Cẩm tú cầu + cát tường + lá bạc: trang nhã, tinh tế, hợp tặng mẹ, thầy cô hoặc đồng nghiệp nữ.\n"
                "- Cẩm tú cầu + hoa hồng pastel + baby trắng: hợp kiểu bó giấy Hàn Quốc, nhìn nữ tính và hiện đại.\n\n"
                "Nếu ngân sách từ 500.000đ - 1.000.000đ, em khuyên dùng cẩm tú cầu làm điểm nhấn chính rồi phối hoa hồng kem và baby trắng để bó đầy hơn mà vẫn mềm mại ạ."
            )

        if "hoa hồng kem" in flowers:
            return (
                "Dạ hoa hồng kem dễ phối và tạo cảm giác tinh tế, sang nhẹ ạ.\n\n"
                "Có thể phối với baby trắng, cẩm tú cầu, cát tường hoặc lá bạc. "
                "Kiểu này hợp tặng mẹ, người yêu, bạn nữ hoặc dịp sinh nhật/kỷ niệm."
            )

        if "baby trắng" in flowers:
            return (
                "Dạ baby trắng thường dùng làm hoa phụ để bó hoa mềm, thoáng và nhẹ nhàng hơn ạ.\n\n"
                "Baby trắng hợp phối với cẩm tú cầu, hoa hồng kem, tulip hoặc cát tường. "
                "Nếu khách thích phong cách Hàn Quốc hoặc tone pastel thì baby trắng là lựa chọn rất an toàn."
            )

        if "tulip" in flowers:
            return (
                "Dạ tulip hợp với phong cách hiện đại, sang và hơi premium ạ.\n\n"
                "Tulip có thể phối với baby trắng, hoa hồng kem hoặc lá bạc. "
                "Kiểu này hợp tặng người yêu, bạn nữ, sinh nhật hoặc kỷ niệm. "
                "Tuy nhiên nên kiểm tra tồn kho trước vì tulip thường dễ hết hàng hơn các loại phổ biến."
            )

        return (
            "Dạ loại hoa này có thể phối cùng hoa hồng kem, baby trắng, cát tường hoặc lá bạc để bó hoa hài hòa hơn ạ. "
            "Nếu anh/chị cho em biết dịp tặng và người nhận, em sẽ gợi ý cách phối cụ thể hơn."
        )

    def generate_inventory_check_response(self, state: dict, slots: dict, inventory_result: dict = None):
        flowers = slots.get("flower_preference") or state.get("flower_preference", [])

        if not flowers:
            return "Dạ anh/chị muốn em kiểm tra tồn kho loại hoa nào ạ?"

        if inventory_result is None:
            flower_text = self._format_list(flowers)
            return f"Dạ em sẽ kiểm tra tồn kho cho {flower_text} ạ."

        available = inventory_result.get("available", [])
        unavailable = inventory_result.get("unavailable", [])
        alternatives = inventory_result.get("alternatives", {})

        response = ""

        if available:
            response += "Dạ hiện tại shop còn các loại hoa sau ạ:\n\n"

            for item in available:
                flower_name = item.get("flower_name")
                stock = item.get("stock")
                unit_price = item.get("unit_price")

                response += f"- {flower_name}: còn {stock} cành"

                if unit_price:
                    response += f", giá khoảng {self._format_money(unit_price)}/cành"

                response += "\n"

            response += "\n"

        if unavailable:
            response += "Một số loại hoa hiện tại đang hết hàng hoặc chưa có trong kho:\n\n"

            for item in unavailable:
                flower_name = item.get("flower_name")
                response += f"- {flower_name}\n"

                alt_items = alternatives.get(flower_name, [])

                if alt_items:
                    response += "  Gợi ý thay thế:\n"

                    for alt in alt_items:
                        alt_name = alt.get("flower_name")
                        alt_price = alt.get("unit_price")
                        reason = alt.get("reason")

                        response += f"  + {alt_name}"

                        if alt_price:
                            response += f" ({self._format_money(alt_price)}/cành)"

                        if reason:
                            response += f": {reason}"

                        response += "\n"

            response += "\n"

        if available and not unavailable:
            response += (
                "Anh/chị muốn em dùng loại hoa này để dựng một phương án bó hoa theo ngân sách hiện tại không ạ?"
            )
        elif unavailable and not available:
            response += (
                "Nếu anh/chị muốn, em có thể dùng các hoa thay thế trên để đề xuất lại một bó phù hợp hơn ạ."
            )
        else:
            response += (
                "Em có thể giữ các hoa còn hàng và thay các hoa hết hàng bằng phương án tương tự để bó hoa vẫn đẹp ạ."
            )

        return response

    # =========================
    # Post-recommendation / update responses
    # =========================

    def generate_add_more_response(self, user_message: str, state: dict):
        flower_preference = state.get("flower_preference", [])
        color_tone = state.get("color_tone", [])
        style = state.get("style", [])

        flower_text = self._format_list(flower_preference)
        color_text = self._format_list(color_tone)
        style_text = self._format_list(style)

        response = "Dạ được ạ. "

        if flower_text:
            response += f"Em đã ghi nhận thêm yêu cầu ưu tiên {flower_text}. "
        else:
            response += "Anh/chị muốn thêm loại hoa nào vào bó hoa ạ? "

        if color_text:
            response += f"Tone màu hiện tại đang là {color_text}. "

        if style_text:
            response += f"Phong cách hiện tại là {style_text}. "

        response += (
            "Với bó hoa hiện tại, mình có thể dùng hoa chính làm điểm nhấn, "
            "sau đó phối thêm hoa phụ như baby trắng, cát tường, hoa hồng kem hoặc lá bạc "
            "để bó hoa nhìn đầy đặn và hài hòa hơn ạ."
        )

        return response

    def generate_alternative_response(self, state: dict):
        occasion = state.get("occasion")
        recipient = state.get("recipient")
        budget = state.get("budget")
        flower_preference = state.get("flower_preference", [])

        response = "Dạ có ạ. Nếu anh/chị chưa chắc nên phối hoa nào, em gợi ý thêm một vài hướng như sau:\n\n"

        if "cẩm tú cầu" in flower_preference:
            response += (
                "- Cẩm tú cầu + hoa hồng kem + baby trắng: hợp với sinh nhật, kỷ niệm, tặng mẹ hoặc người yêu. "
                "Cẩm tú cầu làm hoa chính mềm và nổi bật, hoa hồng kem làm bó sáng hơn, baby trắng giúp tổng thể nhẹ nhàng.\n"
            )
            response += (
                "- Cẩm tú cầu + cát tường + lá bạc: hợp với phong cách trang nhã, tinh tế, phù hợp tặng mẹ, thầy cô hoặc đồng nghiệp nữ.\n"
            )
            response += (
                "- Cẩm tú cầu + hoa hồng pastel + baby trắng: hợp với bó giấy Hàn Quốc, tạo cảm giác nữ tính và hiện đại.\n"
            )
        else:
            response += (
                "- Hoa hồng kem + baby trắng + lá bạc: nhẹ nhàng, dễ tặng, phù hợp sinh nhật hoặc kỷ niệm.\n"
            )
            response += (
                "- Cẩm tú cầu + cát tường + baby trắng: mềm mại, trang nhã, hợp tặng mẹ hoặc bạn nữ.\n"
            )
            response += (
                "- Hướng dương + cát tường + lá phụ: tươi sáng, hợp chúc mừng, tốt nghiệp hoặc khai trương.\n"
            )

        if budget:
            response += f"\nVới ngân sách khoảng {self._format_money(budget)}, em sẽ ưu tiên phương án không quá nhiều hoa chính để bó vẫn đẹp mà không bị vượt ngân sách."

        if occasion or recipient:
            details = []

            if occasion:
                details.append(f"dịp {occasion}")

            if recipient:
                details.append(f"tặng {recipient}")

            response += f"\nVới {', '.join(details)}, em khuyên nên chọn tone nhẹ nhàng, không quá rực để bó hoa dễ tạo thiện cảm hơn ạ."

        return response

    def generate_price_response(self, state: dict):
        budget = state.get("budget")
        budget_min = state.get("budget_min")
        budget_max = state.get("budget_max")
        budget_type = state.get("budget_type")

        if budget_type == "range" and budget_min and budget_max:
            return (
                f"Dạ với ngân sách từ {self._format_money(budget_min)} đến {self._format_money(budget_max)}, "
                "em có thể thiết kế bó size vừa đến lớn, nhìn đầy đặn và có nhiều hoa chính hơn. "
                "Mức đẹp thường nằm khoảng 70-85% ngân sách tối đa để bó vẫn đẹp mà không bị sát trần ạ."
            )

        if budget_type == "minimum" and budget_min:
            return (
                f"Dạ với ngân sách trên {self._format_money(budget_min)}, "
                "mình có thể làm bó đầy đặn hơn, tăng số lượng hoa chính hoặc chọn phong cách premium hơn ạ."
            )

        if budget_type == "maximum" and budget_max:
            return (
                f"Dạ với ngân sách dưới {self._format_money(budget_max)}, "
                "em sẽ ưu tiên phương án không vượt quá mức này, cân bằng giữa hoa chính và hoa phụ ạ."
            )

        if budget:
            return (
                f"Dạ với ngân sách khoảng {self._format_money(budget)}, "
                "em sẽ thiết kế bó hoa sao cho phù hợp nhất với mức này. "
                "Nếu muốn bó trông đầy đặn hơn, mình có thể tăng thêm ngân sách hoặc giảm bớt các loại hoa giá cao ạ."
            )

        return (
            "Dạ hiện tại mình chưa có ngân sách cụ thể, nên em chưa thể ước lượng chính xác. "
            "Anh/chị muốn bó hoa khoảng bao nhiêu tiền ạ?"
        )

    def generate_confirm_response(self, state: dict):
        occasion = state.get("occasion")
        recipient = state.get("recipient")
        budget = state.get("budget")
        budget_min = state.get("budget_min")
        budget_max = state.get("budget_max")
        budget_type = state.get("budget_type")
        flower_preference = state.get("flower_preference", [])
        color_tone = state.get("color_tone", [])
        style = state.get("style", [])

        response = "Dạ em chốt lại yêu cầu hiện tại của anh/chị như sau:\n\n"

        if occasion:
            response += f"- Dịp tặng: {occasion}\n"

        if recipient:
            response += f"- Người nhận: {recipient}\n"

        if budget_type == "range" and budget_min and budget_max:
            response += f"- Ngân sách: từ {self._format_money(budget_min)} đến {self._format_money(budget_max)}\n"
        elif budget_type == "minimum" and budget_min:
            response += f"- Ngân sách: trên {self._format_money(budget_min)}\n"
        elif budget_type == "maximum" and budget_max:
            response += f"- Ngân sách: dưới {self._format_money(budget_max)}\n"
        elif budget:
            response += f"- Ngân sách: khoảng {self._format_money(budget)}\n"

        if flower_preference:
            response += f"- Hoa ưu tiên: {self._format_list(flower_preference)}\n"

        if color_tone:
            response += f"- Tone màu: {self._format_list(color_tone)}\n"

        if style:
            response += f"- Kiểu bó/phong cách: {self._format_list(style)}\n"

        response += (
            "\nNếu triển khai thực tế, bước tiếp theo em sẽ xin thông tin người đặt, "
            "số điện thoại, địa chỉ giao hàng và tạo mã đơn/mã chuyển khoản ạ."
        )

        return response

    # =========================
    # Order response
    # =========================

    def generate_order_created_response(self, order_result: dict):
        if not order_result.get("success"):
            return (
                "Dạ em chưa tạo được đơn vì còn thiếu thông tin khách hàng. "
                "Anh/chị vui lòng gửi giúp em tên người đặt, số điện thoại và địa chỉ giao hàng ạ."
            )

        order = order_result.get("order", {})

        order_id = order.get("order_id")
        customer = order.get("customer", {})
        bouquet = order.get("bouquet", {})
        payment = order.get("payment", {})

        customer_name = customer.get("name")
        customer_phone = customer.get("phone")
        customer_address = customer.get("address")

        estimated_price = bouquet.get("estimated_price")
        bouquet_items = bouquet.get("bouquet_items", [])

        payment_code = payment.get("payment_code")
        transfer_content = payment.get("transfer_content")
        amount = payment.get("amount")

        response = "Dạ em đã tạo đơn hàng cho anh/chị thành công ạ.\n\n"

        response += f"- Mã đơn hàng: {order_id}\n"
        response += f"- Tên khách hàng: {customer_name}\n"
        response += f"- Số điện thoại: {customer_phone}\n"
        response += f"- Địa chỉ giao hàng: {customer_address}\n"

        if estimated_price:
            response += f"- Tổng tiền dự kiến: {self._format_money(estimated_price)}\n"

        if bouquet_items:
            response += "\nThành phần bó hoa:\n"

            for item in bouquet_items:
                flower_name = item.get("flower_name")
                quantity = item.get("quantity")
                role = item.get("role")

                role_vi = self._convert_role_to_vietnamese(role)

                response += f"- {flower_name}: {quantity} cành"

                if role_vi:
                    response += f" ({role_vi})"

                response += "\n"

        response += "\nThông tin chuyển khoản:\n"
        response += f"- Mã chuyển khoản: {payment_code}\n"
        response += f"- Nội dung chuyển khoản: {transfer_content}\n"

        if amount:
            response += f"- Số tiền: {self._format_money(amount)}\n"

        response += (
            "\nSau khi anh/chị chuyển khoản, shop sẽ xác nhận đơn và chuẩn bị bó hoa ạ."
        )

        return response

    # =========================
    # Payment response
    # =========================

    def generate_payment_confirmed_response(self, payment_result: dict):
        if not payment_result.get("success"):
            error = payment_result.get("error")
            message = payment_result.get("message", "")

            if error == "order_not_found":
                return (
                    "Dạ em không tìm thấy đơn hàng này trong hệ thống ạ. "
                    "Anh/chị kiểm tra lại mã đơn giúp em nhé."
                )

            if error == "already_paid":
                return (
                    "Dạ đơn hàng này đã được xác nhận thanh toán trước đó rồi ạ.\n\n"
                    f"{message}"
                )

            return (
                "Dạ em chưa xác nhận được thanh toán cho đơn này ạ.\n"
                f"Lý do: {message}"
            )

        order = payment_result.get("order", {})
        inventory_result = payment_result.get("inventory_result", {})

        order_id = order.get("order_id")
        status = order.get("status")
        payment = order.get("payment", {})
        payment_status = payment.get("payment_status")

        updated_items = inventory_result.get("updated_items", [])
        failed_items = inventory_result.get("failed_items", [])

        response = "Dạ đã xác nhận thanh toán thành công ạ.\n\n"

        response += f"- Mã đơn hàng: {order_id}\n"
        response += f"- Trạng thái thanh toán: {payment_status}\n"
        response += f"- Trạng thái đơn hàng: {status}\n"

        if updated_items:
            response += "\nTồn kho đã được cập nhật:\n"

            for item in updated_items:
                flower_name = item.get("flower_name")
                quantity = item.get("quantity_decreased")

                response += f"- {flower_name}: đã trừ {quantity} cành\n"

        if failed_items:
            response += "\nMột số hoa chưa trừ được tồn kho:\n"

            for item in failed_items:
                flower_name = item.get("flower_name")
                quantity = item.get("quantity")
                reason = item.get("reason")

                response += f"- {flower_name}: {quantity} cành. Lý do: {reason}\n"

        response += (
            "\nĐơn hàng đã chuyển sang trạng thái đang chuẩn bị. "
            "Shop có thể tiến hành bó hoa và giao cho khách ạ."
        )

        return response