"""
Output:
    data/processed/recommendation_eval.jsonl

Each line is one JSON object with:
    - customer_request
    - requirements
    - expected_constraints
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

OUTPUT_PATH = Path("data/processed/recommendation_eval.jsonl")
TOTAL_CASES = 150
SEED = 42

# Simulated flower inventory for evaluation case design.
# The generated dataset does not include selected products; it only defines constraints.
FLOWER_IN_STOCK = {
    "rose": True,
    "baby breath": True,
    "sunflower": True,
    "tulip": True,
    "carnation": True,
    "orchid": True,
    "lily": True,
    "hydrangea": True,
    "daisy": True,
    "peony": False,
    "lavender": False,
    "blue rose": False,
    "camellia": False,
}

FLOWERS = list(FLOWER_IN_STOCK.keys())
IN_STOCK_FLOWERS = [name for name, available in FLOWER_IN_STOCK.items() if available]
OUT_OF_STOCK_FLOWERS = [name for name, available in FLOWER_IN_STOCK.items() if not available]

OCCASIONS = [
    "birthday",
    "anniversary",
    "graduation",
    "apology",
    "wedding",
    "grand opening",
    "valentine",
    "mother day",
    "teacher day",
    "condolence",
    "congratulation",
    "get well soon",
    "proposal",
    "farewell",
    "thank you",
]

RECIPIENTS = [
    "girlfriend",
    "boyfriend",
    "mother",
    "father",
    "wife",
    "husband",
    "teacher",
    "boss",
    "coworker",
    "friend",
    "client",
    "grandmother",
    "younger sister",
    "older brother",
    "business partner",
]

COLOR_TONES = [
    ["red"],
    ["pink"],
    ["white"],
    ["yellow"],
    ["purple"],
    ["blue"],
    ["orange"],
    ["pastel"],
    ["warm"],
    ["elegant", "white"],
    ["romantic", "red", "pink"],
]

STYLES = [
    ["romantic"],
    ["minimal"],
    ["luxury"],
    ["modern"],
    ["cute"],
    ["elegant"],
    ["natural"],
    ["fresh"],
    ["Korean style"],
    ["large bouquet"],
    ["small bouquet"],
]

BUDGETS = [150000, 200000, 250000, 300000, 350000, 400000, 500000, 700000, 900000, 1200000]
LOW_BUDGETS = [100000, 120000, 150000, 180000, 200000]


def make_request_text(
    occasion: str,
    recipient: str,
    budget: Optional[int],
    flower_preference: List[str],
    flower_avoidance: List[str],
    color_tone: List[str],
    style: List[str],
    vague: bool = False,
) -> str:
    """Create a natural Vietnamese customer request."""

    if vague:
        vague_templates = [
            f"Tư vấn giúp tôi một bó hoa tặng {recipient}, nhìn ổn và dễ tặng là được.",
            f"Tôi cần hoa cho dịp {occasion}, không biết chọn loại nào, shop gợi ý giúp.",
            f"Muốn mua hoa tặng {recipient}, kiểu đẹp đẹp một chút, không cần quá cầu kỳ.",
            f"Có mẫu nào phù hợp để tặng {recipient} không? Tôi chưa có ý tưởng cụ thể.",
        ]
        return random.choice(vague_templates)

    parts = [f"Tôi muốn đặt một bó hoa cho dịp {occasion} tặng {recipient}"]

    if flower_preference:
        parts.append("ưu tiên có " + ", ".join(flower_preference))

    if flower_avoidance:
        parts.append("tránh dùng " + ", ".join(flower_avoidance))

    if color_tone:
        parts.append("tông màu " + ", ".join(color_tone))

    if style:
        parts.append("phong cách " + ", ".join(style))

    if budget is not None:
        parts.append(f"ngân sách tối đa {budget:,} VND".replace(",", "."))
    else:
        parts.append("chưa giới hạn ngân sách")

    return ", ".join(parts) + "."


def build_case(
    occasion: str,
    recipient: str,
    budget: Optional[int],
    budget_type: str,
    flower_preference: List[str],
    flower_avoidance: List[str],
    color_tone: List[str],
    style: List[str],
    vague: bool = False,
) -> Dict[str, Any]:
    """Build one evaluation case and derive expected constraints."""

    required_flower_available = all(FLOWER_IN_STOCK.get(flower, False) for flower in flower_preference)

    # If a required flower is out of stock, the recommender should NOT select it.
    # Therefore must_include_required_flower is false in that conflict case.
    must_include_required_flower = bool(flower_preference) and required_flower_available

    return {
        "customer_request": make_request_text(
            occasion=occasion,
            recipient=recipient,
            budget=budget,
            flower_preference=flower_preference,
            flower_avoidance=flower_avoidance,
            color_tone=color_tone,
            style=style,
            vague=vague,
        ),
        "requirements": {
            "occasion": occasion,
            "recipient": recipient,
            "budget": budget,
            "budget_type": budget_type,
            "flower_preference": flower_preference,
            "flower_avoidance": flower_avoidance,
            "color_tone": color_tone,
            "style": style,
        },
        "expected_constraints": {
            "must_include_required_flower": must_include_required_flower,
            "must_not_select_out_of_stock": True,
            "must_be_within_budget": budget is not None,
            "must_avoid_flowers": flower_avoidance,
        },
    }


def generate_cases() -> List[Dict[str, Any]]:
    random.seed(SEED)
    cases: List[Dict[str, Any]] = []

    scenario_plan = [
        ("required_flower", 30),
        ("avoid_flower", 25),
        ("low_budget", 25),
        ("no_budget", 20),
        ("specific_color", 20),
        ("missing_color", 10),
        ("vague_request", 10),
        ("required_out_of_stock", 10),
    ]

    for scenario, count in scenario_plan:
        for _ in range(count):
            occasion = random.choice(OCCASIONS)
            recipient = random.choice(RECIPIENTS)
            budget: Optional[int] = random.choice(BUDGETS)
            budget_type = "maximum"
            flower_preference: List[str] = []
            flower_avoidance: List[str] = []
            color_tone: List[str] = random.choice(COLOR_TONES)
            style: List[str] = random.choice(STYLES)
            vague = False

            if scenario == "required_flower":
                flower_preference = random.sample(IN_STOCK_FLOWERS, k=random.choice([1, 1, 2]))

            elif scenario == "avoid_flower":
                flower_avoidance = random.sample(FLOWERS, k=random.choice([1, 1, 2]))
                flower_preference = random.sample(
                    [f for f in IN_STOCK_FLOWERS if f not in flower_avoidance],
                    k=random.choice([0, 1]),
                )

            elif scenario == "low_budget":
                budget = random.choice(LOW_BUDGETS)
                flower_preference = random.sample(IN_STOCK_FLOWERS, k=random.choice([0, 1]))
                style = random.choice([["simple"], ["small bouquet"], ["minimal"]])

            elif scenario == "no_budget":
                budget = None
                budget_type = "none"
                flower_preference = random.sample(IN_STOCK_FLOWERS, k=random.choice([0, 1, 2]))
                style = random.choice([["luxury"], ["premium"], ["elegant"], ["large bouquet"]])

            elif scenario == "specific_color":
                color_tone = random.choice(COLOR_TONES)
                flower_preference = random.sample(IN_STOCK_FLOWERS, k=random.choice([0, 1]))

            elif scenario == "missing_color":
                color_tone = []
                flower_preference = random.sample(IN_STOCK_FLOWERS, k=random.choice([0, 1]))

            elif scenario == "vague_request":
                color_tone = []
                style = []
                flower_preference = []
                flower_avoidance = []
                budget = random.choice([None, 250000, 400000, 600000])
                budget_type = "none" if budget is None else "maximum"
                vague = True

            elif scenario == "required_out_of_stock":
                flower_preference = random.sample(OUT_OF_STOCK_FLOWERS, k=random.choice([1, 1, 2]))
                flower_avoidance = random.sample(
                    [f for f in FLOWERS if f not in flower_preference],
                    k=random.choice([0, 1]),
                )

            cases.append(
                build_case(
                    occasion=occasion,
                    recipient=recipient,
                    budget=budget,
                    budget_type=budget_type,
                    flower_preference=flower_preference,
                    flower_avoidance=flower_avoidance,
                    color_tone=color_tone,
                    style=style,
                    vague=vague,
                )
            )

    random.shuffle(cases)
    return cases


def validate_cases(cases: List[Dict[str, Any]]) -> None:
    if len(cases) != TOTAL_CASES:
        raise ValueError(f"Expected {TOTAL_CASES} cases, got {len(cases)}")

    required_top_fields = {"customer_request", "requirements", "expected_constraints"}
    required_requirement_fields = {
        "occasion",
        "recipient",
        "budget",
        "budget_type",
        "flower_preference",
        "flower_avoidance",
        "color_tone",
        "style",
    }
    required_constraint_fields = {
        "must_include_required_flower",
        "must_not_select_out_of_stock",
        "must_be_within_budget",
        "must_avoid_flowers",
    }

    for index, case in enumerate(cases, start=1):
        if set(case.keys()) != required_top_fields:
            raise ValueError(f"Case {index} has invalid top-level fields")

        if set(case["requirements"].keys()) != required_requirement_fields:
            raise ValueError(f"Case {index} has invalid requirements fields")

        if set(case["expected_constraints"].keys()) != required_constraint_fields:
            raise ValueError(f"Case {index} has invalid expected_constraints fields")

        budget = case["requirements"]["budget"]
        budget_type = case["requirements"]["budget_type"]

        if budget is None and budget_type != "none":
            raise ValueError(f"Case {index} has no budget but budget_type is not 'none'")

        if budget is not None and budget_type != "maximum":
            raise ValueError(f"Case {index} has budget but budget_type is not 'maximum'")


def save_jsonl(cases: List[Dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for case in cases:
            file.write(json.dumps(case, ensure_ascii=False) + "\n")


def main() -> None:
    cases = generate_cases()
    validate_cases(cases)
    save_jsonl(cases, OUTPUT_PATH)
    print(f"Generated {len(cases)} cases -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

