from inventory.inventory_service import InventoryService


class BouquetBuilder:
    def __init__(self):
        self.inventory = InventoryService()

    def build_bouquet(self, state: dict):
        budget = state.get("budget")
        budget_min = state.get("budget_min")
        budget_max = state.get("budget_max")
        budget_type = state.get("budget_type")

        flower_preference = state.get("flower_preference", [])
        flower_avoidance = state.get("flower_avoidance", [])
        occasion = state.get("occasion")
        recipient = state.get("recipient")
        color_tone = state.get("color_tone", [])
        style = state.get("style", [])

        budget_plan = self._get_budget_plan(
            budget=budget,
            budget_min=budget_min,
            budget_max=budget_max,
            budget_type=budget_type
        )

        bouquet_items = self._build_base_items(
            flower_preference=flower_preference,
            flower_avoidance=flower_avoidance,
            state=state,
            budget_plan=budget_plan
        )

        bouquet_items = self._remove_duplicate_items(bouquet_items)

        # Tận dụng ngân sách bằng cách tăng số lượng hoa phù hợp
        bouquet_items = self._utilize_budget(
            bouquet_items=bouquet_items,
            budget_plan=budget_plan,
            flower_avoidance=flower_avoidance
        )

        estimated_price = self._calculate_estimated_price(bouquet_items)

        proposal = {
            "budget": budget,
            "budget_min": budget_min,
            "budget_max": budget_max,
            "budget_type": budget_type,
            "target_budget": budget_plan.get("target_budget"),
            "budget_plan": budget_plan,
            "occasion": occasion,
            "recipient": recipient,
            "color_tone": color_tone,
            "style": style,
            "bouquet_items": bouquet_items,
            "estimated_price": estimated_price,
            "price_status": self._get_price_status(
                estimated_price=estimated_price,
                budget=budget,
                budget_min=budget_min,
                budget_max=budget_max,
                budget_type=budget_type
            ),
            "advice": self._build_advice(
                state=state,
                bouquet_items=bouquet_items,
                estimated_price=estimated_price,
                budget_plan=budget_plan
            )
        }

        return proposal

    # =========================
    # Budget plan
    # =========================

    def _get_budget_plan(self, budget=None, budget_min=None, budget_max=None, budget_type=None):
        if budget_type == "range" and budget_min and budget_max:
            target_budget = int(budget_min + (budget_max - budget_min) * 0.75)

            return {
                "budget_level": self._classify_budget_level(target_budget),
                "bouquet_size": self._classify_bouquet_size(target_budget),
                "target_budget": target_budget,
                "budget_min": budget_min,
                "budget_max": budget_max,
                "budget_type": "range",
                "description": (
                    f"Khách đưa ngân sách từ {self._format_money(budget_min)} đến {self._format_money(budget_max)}. "
                    f"Hệ thống chọn mức thiết kế khoảng {self._format_money(target_budget)} để bó hoa đẹp, đầy đặn nhưng vẫn không sát trần ngân sách."
                )
            }

        if budget_type == "maximum" and budget_max:
            target_budget = int(budget_max * 0.85)

            return {
                "budget_level": self._classify_budget_level(target_budget),
                "bouquet_size": self._classify_bouquet_size(target_budget),
                "target_budget": target_budget,
                "budget_min": None,
                "budget_max": budget_max,
                "budget_type": "maximum",
                "description": (
                    f"Khách muốn bó hoa dưới {self._format_money(budget_max)}. "
                    f"Hệ thống chọn mức khoảng {self._format_money(target_budget)} để bó đẹp nhưng vẫn an toàn ngân sách."
                )
            }

        if budget_type == "minimum" and budget_min:
            target_budget = int(budget_min * 1.25)

            return {
                "budget_level": self._classify_budget_level(target_budget),
                "bouquet_size": self._classify_bouquet_size(target_budget),
                "target_budget": target_budget,
                "budget_min": budget_min,
                "budget_max": None,
                "budget_type": "minimum",
                "description": (
                    f"Khách muốn bó hoa trên {self._format_money(budget_min)}. "
                    f"Hệ thống đề xuất mức khoảng {self._format_money(target_budget)} để bó hoa đầy đặn và xứng với ngân sách hơn."
                )
            }

        if budget_type == "approximate" and budget:
            target_budget = budget

            return {
                "budget_level": self._classify_budget_level(target_budget),
                "bouquet_size": self._classify_bouquet_size(target_budget),
                "target_budget": target_budget,
                "budget_min": budget_min,
                "budget_max": budget_max,
                "budget_type": "approximate",
                "description": (
                    f"Khách đưa ngân sách khoảng {self._format_money(budget)}. "
                    "Hệ thống thiết kế bó hoa xoay quanh mức này."
                )
            }

        target_budget = budget or 500000

        return {
            "budget_level": self._classify_budget_level(target_budget),
            "bouquet_size": self._classify_bouquet_size(target_budget),
            "target_budget": target_budget,
            "budget_min": budget_min,
            "budget_max": budget_max,
            "budget_type": budget_type or "unknown",
            "description": "Chưa có ngân sách rõ ràng, hệ thống tạm đề xuất bó size vừa."
        }

    def _classify_budget_level(self, target_budget):
        if target_budget < 300000:
            return "low"
        if target_budget < 500000:
            return "standard"
        if target_budget < 800000:
            return "good"
        if target_budget < 1200000:
            return "high"
        return "premium"

    def _classify_bouquet_size(self, target_budget):
        if target_budget < 300000:
            return "small"
        if target_budget < 500000:
            return "small-medium"
        if target_budget < 800000:
            return "medium"
        if target_budget < 1200000:
            return "large"
        return "premium"

    # =========================
    # Build bouquet
    # =========================

    def _build_base_items(self, flower_preference, flower_avoidance, state, budget_plan):
        items = []

        main_flower = self._choose_main_flower(
            flower_preference=flower_preference,
            flower_avoidance=flower_avoidance,
            state=state
        )

        if main_flower:
            items.append({
                "flower_name": main_flower["flower_name"],
                "role": "main",
                "quantity": 1,
                "unit_price": main_flower["unit_price"],
                "reason": main_flower["reason"]
            })

        support_flowers = self._choose_support_flowers(
            main_flower_name=main_flower["flower_name"] if main_flower else None,
            flower_avoidance=flower_avoidance,
            state=state
        )

        for flower in support_flowers:
            items.append({
                "flower_name": flower["flower_name"],
                "role": "support",
                "quantity": 1,
                "unit_price": flower["unit_price"],
                "reason": flower["reason"]
            })

        decoration = self._choose_decoration_flower(flower_avoidance)

        if decoration:
            items.append({
                "flower_name": decoration["flower_name"],
                "role": "decoration",
                "quantity": 1,
                "unit_price": decoration["unit_price"],
                "reason": decoration["reason"]
            })

        return items

    def _choose_main_flower(self, flower_preference, flower_avoidance, state):
        for flower_name in flower_preference:
            if flower_name in flower_avoidance:
                continue

            if self.inventory.is_available(flower_name):
                return {
                    "flower_name": flower_name,
                    "unit_price": self.inventory.get_unit_price(flower_name),
                    "reason": self._build_main_reason(flower_name, state)
                }

        candidates = self._rank_available_flowers(state)

        for candidate in candidates:
            flower_name = candidate["flower_name"]

            if flower_name in flower_avoidance:
                continue

            if self._is_decoration_flower(flower_name):
                continue

            return candidate

        return None

    def _choose_support_flowers(self, main_flower_name, flower_avoidance, state):
        support_order = [
            "hoa hồng kem",
            "baby trắng",
            "cát tường",
            "hướng dương"
        ]

        selected = []

        for flower_name in support_order:
            if flower_name == main_flower_name:
                continue

            if flower_name in flower_avoidance:
                continue

            if not self.inventory.is_available(flower_name):
                continue

            selected.append({
                "flower_name": flower_name,
                "unit_price": self.inventory.get_unit_price(flower_name),
                "reason": self._build_support_reason(flower_name, state)
            })

            if len(selected) >= 3:
                break

        return selected

    def _choose_decoration_flower(self, flower_avoidance):
        if "lá bạc" in flower_avoidance:
            return None

        if not self.inventory.is_available("lá bạc"):
            return None

        return {
            "flower_name": "lá bạc",
            "unit_price": self.inventory.get_unit_price("lá bạc"),
            "reason": "Dùng để trang trí, giúp bó hoa đầy đặn và hài hòa hơn."
        }

    # =========================
    # Budget utilization
    # =========================

    def _utilize_budget(self, bouquet_items, budget_plan, flower_avoidance):
        target_budget = budget_plan.get("target_budget") or 500000

        if not bouquet_items:
            return bouquet_items

        safety_min = int(target_budget * 0.75)
        safety_max = int(target_budget * 0.95)

        # Set số lượng ban đầu theo size
        self._set_initial_quantities(bouquet_items, target_budget)

        estimated_price = self._calculate_estimated_price(bouquet_items)

        # Nếu vẫn quá thấp, tăng dần số lượng hoa
        loop_guard = 0

        while estimated_price < safety_min and loop_guard < 100:
            added = self._increase_one_step(
                bouquet_items=bouquet_items,
                safety_max=safety_max
            )

            if not added:
                break

            estimated_price = self._calculate_estimated_price(bouquet_items)
            loop_guard += 1

        # Nếu vượt quá max, giảm nhẹ
        loop_guard = 0

        while estimated_price > safety_max and loop_guard < 100:
            reduced = self._decrease_one_step(bouquet_items)

            if not reduced:
                break

            estimated_price = self._calculate_estimated_price(bouquet_items)
            loop_guard += 1

        return bouquet_items

    def _set_initial_quantities(self, bouquet_items, target_budget):
        for item in bouquet_items:
            role = item.get("role")

            if target_budget < 300000:
                quantity_map = {"main": 1, "support": 2, "decoration": 2}
            elif target_budget < 500000:
                quantity_map = {"main": 2, "support": 3, "decoration": 3}
            elif target_budget < 800000:
                quantity_map = {"main": 3, "support": 5, "decoration": 4}
            elif target_budget < 1200000:
                quantity_map = {"main": 4, "support": 7, "decoration": 6}
            else:
                quantity_map = {"main": 6, "support": 10, "decoration": 8}

            item["quantity"] = quantity_map.get(role, 1)

    def _increase_one_step(self, bouquet_items, safety_max):
        # Ưu tiên tăng hoa phụ trước để bó đầy hơn, rồi mới tăng hoa chính
        priority_roles = ["support", "main", "decoration"]

        for role in priority_roles:
            for item in bouquet_items:
                if item.get("role") != role:
                    continue

                unit_price = item.get("unit_price", 0)
                current_total = self._calculate_estimated_price(bouquet_items)

                if current_total + unit_price <= safety_max:
                    item["quantity"] += 1
                    return True

        return False

    def _decrease_one_step(self, bouquet_items):
        # Giảm decoration trước, rồi support, rồi main
        priority_roles = ["decoration", "support", "main"]

        for role in priority_roles:
            for item in bouquet_items:
                if item.get("role") != role:
                    continue

                min_quantity = 1

                if item.get("quantity", 0) > min_quantity:
                    item["quantity"] -= 1
                    return True

        return False

    # =========================
    # Ranking / reason
    # =========================

    def _rank_available_flowers(self, state):
        candidates = []

        occasion = state.get("occasion")
        recipient = state.get("recipient")
        color_tone = state.get("color_tone", [])
        style = state.get("style", [])

        for flower in self.inventory.get_all_flowers():
            if flower.get("status") != "available":
                continue

            if flower.get("stock", 0) <= 0:
                continue

            score = 0

            if occasion and occasion in flower.get("suitable_occasions", []):
                score += 3

            if recipient and recipient in flower.get("suitable_recipients", []):
                score += 3

            for color in color_tone:
                if color in flower.get("color", []):
                    score += 1

            for style_tag in style:
                if style_tag in flower.get("style_tags", []):
                    score += 1

            candidates.append({
                "flower_name": flower["flower_name"],
                "unit_price": flower["unit_price"],
                "score": score,
                "reason": self._build_context_reason(flower, occasion, recipient)
            })

        return sorted(candidates, key=lambda x: x["score"], reverse=True)

    def _build_main_reason(self, flower_name, state):
        occasion = state.get("occasion")
        recipient = state.get("recipient")

        if flower_name == "cẩm tú cầu":
            reason = "Cẩm tú cầu có form tròn, mềm và nổi bật nên rất hợp làm hoa chính"

            if occasion:
                reason += f", phù hợp dịp {occasion}"

            if recipient:
                reason += f", hợp để tặng {recipient}"

            return reason + "."

        return "Hoa chính theo yêu cầu của khách hàng."

    def _build_context_reason(self, flower, occasion=None, recipient=None):
        flower_name = flower.get("flower_name")

        reasons = []

        if occasion and occasion in flower.get("suitable_occasions", []):
            reasons.append(f"phù hợp dịp {occasion}")

        if recipient and recipient in flower.get("suitable_recipients", []):
            reasons.append(f"hợp để tặng {recipient}")

        if not reasons:
            reasons.append("phù hợp để phối trong bó hoa quà tặng")

        return f"{flower_name} " + ", ".join(reasons) + "."

    def _build_support_reason(self, flower_name, state):
        if flower_name == "hoa hồng kem":
            return (
                "Hoa hồng kem giúp bó hoa sáng, mềm và sang hơn, "
                "phù hợp khi muốn tạo cảm giác tinh tế."
            )

        if flower_name == "baby trắng":
            return (
                "Baby trắng giúp bó hoa nhẹ nhàng, thoáng và mềm hơn, "
                "rất hợp để phối với hoa chính."
            )

        if flower_name == "cát tường":
            return (
                "Cát tường tạo cảm giác thanh lịch, trang nhã, "
                "phù hợp với các dịp tặng người thân hoặc chúc mừng."
            )

        if flower_name == "hướng dương":
            return (
                "Hướng dương tạo cảm giác tươi sáng, tích cực, "
                "phù hợp với dịp chúc mừng hoặc tốt nghiệp."
            )

        return "Dùng để phối phụ, giúp bó hoa hài hòa hơn."

    # =========================
    # Price
    # =========================

    def _calculate_estimated_price(self, bouquet_items):
        flower_total = 0

        for item in bouquet_items:
            quantity = item.get("quantity", 0)
            unit_price = item.get("unit_price", 0)
            flower_total += quantity * unit_price

        wrapping_fee = self._calculate_wrapping_fee(flower_total)

        return flower_total + wrapping_fee

    def _calculate_wrapping_fee(self, flower_total):
        if flower_total < 250000:
            return 50000
        if flower_total < 500000:
            return 80000
        if flower_total < 900000:
            return 120000
        return 180000

    def _get_price_status(self, estimated_price, budget=None, budget_min=None, budget_max=None, budget_type=None):
        if budget_type == "range" and budget_min and budget_max:
            if budget_min <= estimated_price <= budget_max:
                return "within_budget"
            if estimated_price < budget_min:
                return "below_budget_range"
            return "over_budget"

        if budget_type == "minimum" and budget_min:
            if estimated_price >= budget_min:
                return "within_budget"
            return "below_budget_minimum"

        if budget_type == "maximum" and budget_max:
            if estimated_price <= budget_max:
                return "within_budget"
            if estimated_price <= budget_max * 1.15:
                return "slightly_over_budget"
            return "over_budget"

        if budget is None:
            return "unknown_budget"

        if estimated_price <= budget:
            return "within_budget"

        if estimated_price <= budget * 1.15:
            return "slightly_over_budget"

        return "over_budget"

    # =========================
    # Advice
    # =========================

    def _build_advice(self, state, bouquet_items, estimated_price, budget_plan):
        occasion = state.get("occasion")
        recipient = state.get("recipient")
        style = state.get("style", [])
        color_tone = state.get("color_tone", [])

        flower_names = [item["flower_name"] for item in bouquet_items]

        advice = "Dạ em đề xuất bó hoa này theo hướng "

        if style:
            advice += f"{', '.join(style)}, "
        else:
            advice += "nhẹ nhàng và dễ tặng, "

        if color_tone:
            advice += f"tone {', '.join(color_tone)}, "

        if occasion or recipient:
            advice += "phù hợp "

            if occasion:
                advice += f"dịp {occasion} "

            if recipient:
                advice += f"cho {recipient}"

            advice += ". "
        else:
            advice += "phù hợp làm quà tặng. "

        advice += (
            f"Với ngân sách này, hệ thống chọn size {budget_plan['bouquet_size']} "
            f"và target khoảng {self._format_money(budget_plan.get('target_budget'))}. "
            f"Các hoa chính/phụ gồm {', '.join(flower_names)}. "
        )

        if "cẩm tú cầu" in flower_names:
            advice += (
                "Cẩm tú cầu có form tròn, mềm và nổi bật nên rất hợp làm hoa chính. "
                "Khi phối với baby trắng, cát tường hoặc hoa hồng kem, bó hoa sẽ nhẹ nhàng, đầy đặn và tinh tế hơn. "
            )

        advice += f"Giá ước lượng hiện tại khoảng {self._format_money(estimated_price)}."

        return advice

    # =========================
    # Utils
    # =========================

    def _remove_duplicate_items(self, bouquet_items):
        seen = set()
        result = []

        for item in bouquet_items:
            flower_name = item["flower_name"]

            if flower_name in seen:
                continue

            seen.add(flower_name)
            result.append(item)

        return result

    def _is_decoration_flower(self, flower_name):
        return flower_name in ["lá bạc"]

    def _format_money(self, amount):
        if amount is None:
            return "chưa xác định"

        return f"{amount:,}đ".replace(",", ".")