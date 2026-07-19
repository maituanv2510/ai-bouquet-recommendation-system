from bouquet.bouquet_builder import BouquetBuilder


class RecommendationService:
    def __init__(self, use_rag=False):
        """
        use_rag=False:
        - Ưu tiên chạy ổn chatbot + inventory + pricing trước
        - RAG chỉ bật sau khi chắc chắn Qdrant/RAGPipeline ổn

        Khi muốn bật RAG lại:
        _service = RecommendationService(use_rag=True)
        """

        self.use_rag = use_rag
        self.bouquet_builder = BouquetBuilder()
        self.rag_pipeline = None

        if self.use_rag:
            self.rag_pipeline = self._init_rag_safely()

    def run_recommendation_from_state(self, state: dict):
        """
        Nhận state từ chatbot:
        - Tạo requirements chuẩn
        - Dùng BouquetBuilder để tạo bó hoa theo budget + tồn kho
        - Nếu RAG bật và chạy được thì lấy thêm kiến thức hoa
        - Trả về response cho chatbot
        """

        requirements = {
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
        }

        # Core chính: build bó hoa theo kho + ngân sách
        bouquet_proposal = self.bouquet_builder.build_bouquet(requirements)

        # RAG chỉ là optional
        query = self._build_rag_query(requirements)
        retrieved_flowers = []

        if self.use_rag and self.rag_pipeline is not None:
            retrieved_flowers = self._run_rag_safely(query)

        recommended_flowers = self._build_recommended_flowers_from_bouquet(
            bouquet_proposal=bouquet_proposal
        )

        # Nếu RAG có kết quả thì bổ sung thêm lý do, nhưng không phụ thuộc vào RAG
        rag_flowers = self._format_retrieved_flowers(
            retrieved_flowers=retrieved_flowers,
            requirements=requirements
        )

        return {
            "recommended_flowers": recommended_flowers,
            "rag_recommended_flowers": rag_flowers,
            "bouquet_proposal": bouquet_proposal,
            "avoid_flowers": requirements["flower_avoidance"],
            "budget_note": self._build_budget_note(requirements, bouquet_proposal),
            "final_advice": bouquet_proposal.get("advice"),
            "requirements": requirements,
            "rag_query": query,
            "rag_enabled": self.use_rag,
            "rag_used": bool(retrieved_flowers),
        }

    def _init_rag_safely(self):
        """
        Lazy import RAGPipeline để tránh app chết nếu RAG đang lỗi.
        """

        try:
            from rag.rag_pipeline import RAGPipeline
            return RAGPipeline()
        except Exception as e:
            print(f"[RecommendationService] RAG disabled. Reason: {e}")
            return None

    def _run_rag_safely(self, query: str):
        """
        Gọi RAG nếu đã bật.
        Nếu lỗi thì trả list rỗng, không phá chatbot.
        """

        try:
            rag_result = self.rag_pipeline.run(query)
        except Exception as e:
            print(f"[RecommendationService] RAG call skipped. Reason: {e}")
            return []

        if isinstance(rag_result, dict):
            return (
                rag_result.get("retrieved_flowers")
                or rag_result.get("flowers")
                or rag_result.get("contexts")
                or rag_result.get("results")
                or []
            )

        if isinstance(rag_result, list):
            return rag_result

        return []

    def _build_rag_query(self, requirements: dict):
        query_parts = []

        occasion = requirements.get("occasion")
        recipient = requirements.get("recipient")
        budget = requirements.get("budget")
        budget_min = requirements.get("budget_min")
        budget_max = requirements.get("budget_max")
        budget_type = requirements.get("budget_type")
        flower_preference = requirements.get("flower_preference", [])
        flower_avoidance = requirements.get("flower_avoidance", [])
        color_tone = requirements.get("color_tone", [])
        style = requirements.get("style", [])

        if occasion:
            query_parts.append(f"dịp {occasion}")

        if recipient:
            query_parts.append(f"tặng {recipient}")

        if budget_type == "range" and budget_min and budget_max:
            query_parts.append(f"ngân sách từ {budget_min} đến {budget_max}")
        elif budget_type == "minimum" and budget_min:
            query_parts.append(f"ngân sách trên {budget_min}")
        elif budget_type == "maximum" and budget_max:
            query_parts.append(f"ngân sách dưới {budget_max}")
        elif budget:
            query_parts.append(f"ngân sách khoảng {budget}")

        if flower_preference:
            query_parts.append("ưu tiên " + ", ".join(flower_preference))

        if flower_avoidance:
            query_parts.append("tránh " + ", ".join(flower_avoidance))

        if color_tone:
            query_parts.append("tone màu " + ", ".join(color_tone))

        if style:
            query_parts.append("phong cách " + ", ".join(style))

        if not query_parts:
            return "tư vấn bó hoa phù hợp cho khách hàng"

        return " ".join(query_parts)

    def _build_recommended_flowers_from_bouquet(self, bouquet_proposal: dict):
        bouquet_items = bouquet_proposal.get("bouquet_items", [])

        recommended_flowers = []

        for item in bouquet_items:
            recommended_flowers.append({
                "flower_name": item.get("flower_name"),
                "reason": item.get("reason"),
                "role": item.get("role"),
                "quantity": item.get("quantity"),
                "unit_price": item.get("unit_price"),
                "source": "bouquet_builder"
            })

        return recommended_flowers

    def _format_retrieved_flowers(self, retrieved_flowers, requirements: dict):
        recommended_flowers = []

        if not isinstance(retrieved_flowers, list):
            return recommended_flowers

        for item in retrieved_flowers:
            if not isinstance(item, dict):
                continue

            flower_name = (
                item.get("flower_name")
                or item.get("name")
                or item.get("vietnamese_name")
                or item.get("title")
            )

            if not flower_name:
                continue

            if flower_name in requirements.get("flower_avoidance", []):
                continue

            recommended_flowers.append({
                "flower_name": flower_name,
                "reason": item.get(
                    "description",
                    "Phù hợp với yêu cầu khách hàng."
                ),
                "hybrid_score": item.get("hybrid_score", 0),
                "semantic_score": item.get("semantic_score", 0),
                "keyword_score": item.get("keyword_score", 0),
                "source": item.get("retrieval_source", "rag")
            })

        return recommended_flowers

    def _build_budget_note(self, requirements: dict, bouquet_proposal: dict):
        budget = requirements.get("budget")
        budget_min = requirements.get("budget_min")
        budget_max = requirements.get("budget_max")
        budget_type = requirements.get("budget_type")

        estimated_price = bouquet_proposal.get("estimated_price")
        price_status = bouquet_proposal.get("price_status")

        estimated_text = self._format_money(estimated_price)

        if budget_type == "range" and budget_min and budget_max:
            return (
                f"Khách đưa ngân sách từ {self._format_money(budget_min)} đến {self._format_money(budget_max)}. "
                f"Phương án hiện tại ước lượng khoảng {estimated_text}."
            )

        if budget_type == "minimum" and budget_min:
            return (
                f"Khách muốn bó hoa trên khoảng {self._format_money(budget_min)}. "
                f"Phương án hiện tại ước lượng khoảng {estimated_text}."
            )

        if budget_type == "maximum" and budget_max:
            return (
                f"Khách muốn bó hoa không vượt quá khoảng {self._format_money(budget_max)}. "
                f"Phương án hiện tại ước lượng khoảng {estimated_text}."
            )

        if budget_type == "approximate" and budget:
            return (
                f"Khách đưa ngân sách khoảng {self._format_money(budget)}. "
                f"Phương án hiện tại ước lượng khoảng {estimated_text}."
            )

        if price_status == "unknown_budget":
            return "Khách hàng chưa cung cấp ngân sách cụ thể."

        return f"Phương án hiện tại ước lượng khoảng {estimated_text}."

    def _format_money(self, amount):
        if amount is None:
            return "chưa xác định"

        return f"{amount:,}đ".replace(",", ".")


_service = None


def run_recommendation_from_state(state: dict):
    global _service

    if _service is None:
        # Tạm thời để False cho ổn định chatbot + inventory + pricing trước
        _service = RecommendationService(use_rag=False)

    return _service.run_recommendation_from_state(state)