import json


class RAGPromptBuilder:
    def build_context(self, retrieved_flowers):
        context_blocks = []

        for idx, flower in enumerate(retrieved_flowers, start=1):
            block = f"""
[{idx}]
Tên hoa: {flower.get("flower_name", "")}
Tên tiếng Anh: {flower.get("english_name", "")}
Ý nghĩa: {flower.get("meanings", [])}
Dịp phù hợp: {flower.get("suitable_occasions", [])}
Màu sắc: {flower.get("available_colors", [])}
Phong cách: {flower.get("style_tags", [])}
Vai trò trong bó hoa: {flower.get("bouquet_role", [])}
Mức giá: {flower.get("price_level", "")}
Hoa kết hợp tốt: {flower.get("compatible_flowers", [])}
Mô tả: {flower.get("description", "")}
Hybrid score: {flower.get("hybrid_score", 0)}
""".strip()

            context_blocks.append(block)

        return "\n\n".join(context_blocks)

    def build_prompt(self, requirements, retrieved_flowers):
        context = self.build_context(retrieved_flowers)

        prompt = f"""
Bạn là trợ lý tư vấn bó hoa cho một cửa hàng hoa.

Nhiệm vụ:
- Đọc yêu cầu khách hàng.
- Dựa trên dữ liệu hoa được truy xuất từ knowledge base.
- Đề xuất các loại hoa phù hợp.
- Không bịa thông tin ngoài context.
- Nếu thiếu thông tin quan trọng, hãy nêu rõ cần hỏi thêm.

Yêu cầu khách hàng đã được trích xuất JSON:
{json.dumps(requirements, ensure_ascii=False, indent=2)}

Dữ liệu hoa truy xuất được:
{context}

Hãy trả lời bằng JSON hợp lệ theo format:
{{
  "recommended_flowers": [
    {{
      "flower_name": "...",
      "reason": "...",
      "matched_requirements": ["..."]
    }}
  ],
  "avoid_flowers": [
    {{
      "flower_name": "...",
      "reason": "..."
    }}
  ],
  "suggested_bouquet_style": "...",
  "missing_information_to_ask": ["..."],
  "final_advice": "..."
}}
""".strip()

        return prompt


if __name__ == "__main__":
    sample_requirements = {
        "occasion": "sinh nhật",
        "recipient": "bạn gái",
        "budget": 500000,
        "flower_preference": ["hoa hồng"],
        "color_tone": ["đỏ", "hồng"],
        "style": ["lãng mạn"]
    }

    sample_flowers = [
        {
            "flower_name": "Hoa hồng",
            "english_name": "Rose",
            "meanings": ["tình yêu", "lãng mạn"],
            "suitable_occasions": ["sinh nhật", "kỷ niệm"],
            "available_colors": ["đỏ", "hồng"],
            "style_tags": ["lãng mạn"],
            "bouquet_role": ["main"],
            "price_level": "medium",
            "compatible_flowers": ["baby", "cẩm tú cầu"],
            "description": "Hoa hồng phù hợp để thể hiện tình yêu."
        }
    ]

    builder = RAGPromptBuilder()
    prompt = builder.build_prompt(sample_requirements, sample_flowers)

    print(prompt)