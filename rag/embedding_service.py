from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self, model_name="BAAI/bge-m3"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def encode_one(self, text: str):
        vector = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return vector.tolist()

    def encode_many(self, texts: list[str]):
        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True
        )
        return vectors.tolist()