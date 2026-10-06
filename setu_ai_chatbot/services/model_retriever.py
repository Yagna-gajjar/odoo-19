import hashlib
import json

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class OdooModelRetriever:

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        self._catalog_key = None
        self._model_names = []
        self._model_embeddings = None

    def _build_index(self, catalog):

        catalog_key = hashlib.sha256(
            json.dumps(
                catalog,
                sort_keys=True,
                ensure_ascii=False
            ).encode("utf-8")
        ).hexdigest()

        if catalog_key == self._catalog_key:
            return

        self._model_names = list(catalog.keys())

        model_descriptions = [
            f"{model_name}: {description}"
            for model_name, description in catalog.items()
        ]

        self._model_embeddings = self.model.encode(
            model_descriptions,
            normalize_embeddings=True,
        )

        self._catalog_key = catalog_key

        print(
            f"Indexed {len(self._model_names)} Odoo models."
        )

    def find_relevant_models(self, question, catalog, top_k=5):

        self._build_index(catalog)

        question_embedding = self.model.encode(
            [question],
            normalize_embeddings=True,
        )

        similarities = cosine_similarity(
            question_embedding,
            self._model_embeddings
        )[0]

        ranked_indexes = similarities.argsort()[::-1][:top_k]

        results = []

        for index in ranked_indexes:
            model_name = self._model_names[index]

            results.append({
                "model": model_name,
                "description": catalog[model_name],
                "score": float(similarities[index]),
            })

        return results