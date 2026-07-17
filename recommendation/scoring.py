from typing import List, Dict, Any, Optional


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).lower().strip()


def normalize_list(values: Optional[List[str]]) -> List[str]:
    if not values:
        return []
    return [normalize_text(v) for v in values]


class RecommendationScorer:
    def __init__(self):
        pass

    def required_flower_score(
        self,
        candidate: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> float:
        preferences = normalize_list(requirements.get("flower_preference", []))

        if not preferences:
            return 0.5

        base_name = normalize_text(candidate.get("base_flower_name"))
        variant_name = normalize_text(candidate.get("variant_name"))

        for pref in preferences:
            if pref in base_name or pref in variant_name:
                return 1.0

        return 0.0

    def color_score(
        self,
        candidate: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> float:
        color_tone = normalize_list(requirements.get("color_tone", []))

        # If user does not specify color, do not punish candidate too much
        if not color_tone:
            return 0.7

        candidate_color = normalize_text(candidate.get("color"))

        if candidate_color in color_tone:
            return 1.0

        return 0.2

    def stock_score(self, candidate: Dict[str, Any]) -> float:
        stock = int(candidate.get("stock_quantity", 0))

        if stock >= 20:
            return 1.0
        if stock >= 10:
            return 0.85
        if stock >= 4:
            return 0.7
        if stock >= 1:
            return 0.45

        return 0.0

    def freshness_score(self, candidate: Dict[str, Any]) -> float:
        freshness = normalize_text(candidate.get("freshness_status"))
        status = normalize_text(candidate.get("status"))
        days = int(candidate.get("days_since_import", 0))

        if freshness == "expired" or status == "expired":
            return 0.0

        if freshness == "fresh" and days <= 2:
            return 1.0

        if freshness == "fresh" and days <= 4:
            return 0.85

        if freshness == "near_expiry" or days >= 5:
            return 0.45

        return 0.7

    def price_score(
        self,
        candidate: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> float:
        budget = requirements.get("budget")
        price = float(candidate.get("selling_price", 0))

        if budget is None:
            return 0.7

        try:
            budget = float(budget)
        except Exception:
            return 0.7

        if budget <= 0:
            return 0.7

        ratio = price / budget

        if ratio <= 0.05:
            return 1.0
        if ratio <= 0.10:
            return 0.9
        if ratio <= 0.20:
            return 0.75
        if ratio <= 0.35:
            return 0.5

        return 0.2

    def normalize_rag_score(self, rag_score: float) -> float:
        """
        RAG scores may be around 0.3 - 1.5 depending on boosting.
        Clip to 0-1 range for scoring.
        """
        if rag_score is None:
            return 0.0

        rag_score = float(rag_score)

        if rag_score >= 1.0:
            return 1.0

        if rag_score <= 0:
            return 0.0

        return rag_score

    def score_candidate(
        self,
        candidate: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        required_score = self.required_flower_score(candidate, requirements)
        rag_score = self.normalize_rag_score(candidate.get("rag_score", 0.0))
        color_score = self.color_score(candidate, requirements)
        stock_score = self.stock_score(candidate)
        freshness_score = self.freshness_score(candidate)
        price_score = self.price_score(candidate, requirements)

        final_score = (
            0.35 * required_score
            + 0.25 * rag_score
            + 0.15 * color_score
            + 0.10 * stock_score
            + 0.10 * freshness_score
            + 0.05 * price_score
        )

        scored = dict(candidate)
        scored["score_breakdown"] = {
            "required_flower_score": required_score,
            "rag_score": rag_score,
            "color_score": color_score,
            "stock_score": stock_score,
            "freshness_score": freshness_score,
            "price_score": price_score,
        }
        scored["final_score"] = round(final_score, 4)

        return scored

    def score_candidates(
        self,
        candidates: List[Dict[str, Any]],
        requirements: Dict[str, Any],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        scored = [
            self.score_candidate(candidate, requirements)
            for candidate in candidates
        ]

        scored = sorted(
            scored,
            key=lambda x: x["final_score"],
            reverse=True,
        )

        return scored[:top_k]


if __name__ == "__main__":
    sample_candidates = [
        {
            "variant_name": "Cẩm tú cầu xanh",
            "base_flower_name": "Cẩm tú cầu",
            "color": "xanh",
            "stock_quantity": 8,
            "selling_price": 60000,
            "freshness_status": "fresh",
            "days_since_import": 1,
            "status": "available",
            "rag_score": 1.32,
        },
        {
            "variant_name": "Cát tường trắng",
            "base_flower_name": "Cát tường",
            "color": "trắng",
            "stock_quantity": 25,
            "selling_price": 18000,
            "freshness_status": "fresh",
            "days_since_import": 1,
            "status": "available",
            "rag_score": 0.86,
        },
    ]

    sample_requirements = {
        "budget": 500000,
        "flower_preference": ["cẩm tú cầu"],
        "color_tone": [],
    }

    scorer = RecommendationScorer()
    results = scorer.score_candidates(sample_candidates, sample_requirements)

    for item in results:
        print(item["variant_name"], item["final_score"], item["score_breakdown"])