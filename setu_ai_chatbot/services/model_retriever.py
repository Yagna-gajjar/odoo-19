import hashlib
import json
import re

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class OdooModelRetriever:

    SCHEMA_CHUNK_SIZE = 500
    SCHEMA_CHUNK_OVERLAP = 100
    QUESTION_CHUNK_SIZE = 180
    QUESTION_CHUNK_OVERLAP = 40

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        self._schema_key = None
        self._chunk_models = []
        self._chunk_texts = []
        self._chunk_embeddings = None

    def _window_chunks(self, text, size, overlap):

        text = " ".join((text or "").split())

        if not text:
            return []

        if len(text) <= size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = min(start + size, len(text))
            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= len(text):
                break

            start = end - overlap

        return chunks

    def _chunk_question(self, question):

        text = " ".join((question or "").split())

        if not text:
            return []

        clauses = [
            part.strip()
            for part in re.split(
                r"\s*(?:,|;|\?|\band\b|\bor\b|\balso\b)\s*",
                text,
                flags=re.IGNORECASE,
            )
            if part and part.strip()
        ]

        chunks = []

        for clause in clauses or [text]:
            chunks.extend(
                self._window_chunks(
                    clause,
                    self.QUESTION_CHUNK_SIZE,
                    self.QUESTION_CHUNK_OVERLAP,
                )
            )

        if text not in chunks:
            chunks.insert(0, text)

        unique = []
        seen = set()

        for chunk in chunks:
            if chunk not in seen:
                seen.add(chunk)
                unique.append(chunk)

        return unique

    def _model_document(self, model_name, model_schema):

        lines = [
            f"Model: {model_name}",
            f"Description: {model_schema.get('description') or ''}",
            "Fields:",
        ]

        for field_name, field in (model_schema.get("fields") or {}).items():
            relation = field.get("relation")
            relation_text = f" -> {relation}" if relation else ""
            lines.append(
                f"{field_name} ({field.get('type', '')}{relation_text}): "
                f"{field.get('string') or ''}"
            )

        return "\n".join(lines)

    def _schema_chunks(self, schema):

        chunk_models = []
        chunk_texts = []

        for model_name, model_schema in schema.items():
            document = self._model_document(model_name, model_schema)
            header = (
                f"Model: {model_name}. "
                f"Description: {model_schema.get('description') or ''}. "
            )

            for piece in self._window_chunks(
                document,
                self.SCHEMA_CHUNK_SIZE,
                self.SCHEMA_CHUNK_OVERLAP,
            ):
                if not piece.startswith("Model:"):
                    piece = header + piece

                chunk_models.append(model_name)
                chunk_texts.append(piece)

        return chunk_models, chunk_texts

    def _build_index(self, schema):

        schema_key = hashlib.sha256(
            json.dumps(
                schema,
                sort_keys=True,
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()

        if schema_key == self._schema_key:
            return

        chunk_models, chunk_texts = self._schema_chunks(schema)

        self._chunk_models = chunk_models
        self._chunk_texts = chunk_texts

        if chunk_texts:
            self._chunk_embeddings = self.model.encode(
                chunk_texts,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        else:
            self._chunk_embeddings = None

        self._schema_key = schema_key

        print(
            f"Indexed {len(chunk_texts)} schema chunks "
            f"across {len(set(chunk_models))} Odoo models."
        )

    def find_relevant_models(self, question, schema, top_k=5):

        self._build_index(schema)

        question_chunks = self._chunk_question(question)

        if not question_chunks or self._chunk_embeddings is None:
            return []

        question_embeddings = self.model.encode(
            question_chunks,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        similarities = cosine_similarity(
            question_embeddings,
            self._chunk_embeddings,
        )

        chunk_scores = similarities.max(axis=0)

        best_by_model = {}

        for index, score in enumerate(chunk_scores):
            model_name = self._chunk_models[index]
            score = float(score)
            current = best_by_model.get(model_name)

            if current is None or score > current["score"]:
                best_by_model[model_name] = {
                    "model": model_name,
                    "description": (
                        schema.get(model_name) or {}
                    ).get("description", ""),
                    "score": score,
                    "schema_chunk": self._chunk_texts[index],
                    "question_chunks": question_chunks,
                }

        ranked = sorted(
            best_by_model.values(),
            key=lambda item: item["score"],
            reverse=True,
        )

        return ranked[:top_k]
