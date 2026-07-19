from rag.hybrid_retriever import HybridRetriever
from rag.rag_prompt_builder import RAGPromptBuilder


class RAGPipeline:
    def __init__(self):
        self.retriever = HybridRetriever()
        self.prompt_builder = RAGPromptBuilder()

    def run(self, requirements, top_k=5):
        retrieved_flowers = self.retriever.retrieve(
            requirements=requirements,
            top_k=top_k
        )

        prompt = self.prompt_builder.build_prompt(
            requirements=requirements,
            retrieved_flowers=retrieved_flowers
        )

        return {
            "requirements": requirements,
            "retrieved_flowers": retrieved_flowers,
            "prompt": prompt
        }


if __name__ == "__main__":
    requirements = {
        "occasion": "sinh nhật",
        "recipient": "bạn gái",
        "budget": 500000,
        "budget_type": "maximum",
        "flower_preference": ["hoa hồng"],
        "flower_avoidance": [],
        "color_tone": ["đỏ", "hồng"],
        "style": ["lãng mạn"],
        "meaning_intent": ["tình yêu", "ngọt ngào"]
    }

    pipeline = RAGPipeline()

    result = pipeline.run(
        requirements=requirements,
        top_k=5
    )

    print("\n=== RETRIEVED FLOWERS ===")
    for idx, flower in enumerate(result["retrieved_flowers"], start=1):
        print(f"{idx}. {flower.get('flower_name')} | score={flower.get('hybrid_score')}")

    print("\n=== FINAL RAG PROMPT ===")
    print(result["prompt"])