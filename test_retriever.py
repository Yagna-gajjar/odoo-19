from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class OdooModelRetriever:

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def find_relevant_models(self, question, catalog, top_k=3):

        model_names = list(catalog.keys())

        model_descriptions = [
            f"{model_name}: {description}"
            for model_name, description in catalog.items()
        ]

        question_embedding = self.model.encode([question])

        model_embeddings = self.model.encode(model_descriptions)

        similarities = cosine_similarity(
            question_embedding,
            model_embeddings
        )[0]

        ranked_indexes = similarities.argsort()[::-1][:top_k]

        results = []

        for index in ranked_indexes:
            results.append({
                "model": model_names[index],
                "description": catalog[model_names[index]],
                "score": float(similarities[index]),
            })

        return results


catalog = {
    "res.partner": "Contact",
    "sale.order": "Sales Order",
    "sale.order.line": "Sales Order Line",
    "product.product": "Product",
    "account.move": "Journal Entry",
}

retriever = OdooModelRetriever()

question = "How many customers do we have?"

results = retriever.find_relevant_models(
    question,
    catalog,
    top_k=3,
)

for result in results:
    print(result)