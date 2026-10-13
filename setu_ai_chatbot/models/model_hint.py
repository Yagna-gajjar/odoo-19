import json
import math
import re
from collections import Counter

from odoo import api, models

from .model_hint_examples import EXAMPLES

_TOKEN_RE = re.compile(r'[a-z0-9]+')
_STOP_WORDS = frozenset({
    'a', 'an', 'the', 'of', 'for', 'to', 'in', 'on', 'and', 'or', 'is', 'are',
    'was', 'were', 'what', 'which', 'who', 'how', 'me', 'my', 'our', 'show',
    'list', 'get', 'with', 'from', 'by', 'all', 'please', 'do', 'does', 'did',
    'can', 'i', 'we', 'their', 'have', 'has', 'had', 'this', 'that', 'these',
    'those', 'many', 'much', 'most', 'be', 'been', 'it', 'its', 'at', 'into',
    'there', 'any', 'some', 'only', 'also', 'per', 'not', 'you', 'your',
})
_CACHE = {'signature': None, 'classifier': None}


def tokenize(text):
    tokens = []
    for token in _TOKEN_RE.findall((text or '').lower()):
        token = _stem(token)
        if len(token) < 2 or token in _STOP_WORDS:
            continue
        tokens.append(token)
    return tokens


def _stem(token):
    if len(token) > 5 and token.endswith('ies'):
        return token[:-3] + 'y'
    if len(token) > 4 and token.endswith('s') and not token.endswith('ss'):
        return token[:-1]
    return token


class TfidfBinaryRelevance:
    """One-vs-rest model-name classifier over TF-IDF class centroids.

    Each training label gets the average TF-IDF vector of its questions.
    A question scores a label by cosine similarity. Labels below the
    confidence threshold are omitted.
    """

    def __init__(self, min_score=0.22, min_relative=0.4):
        self.min_score = min_score
        self.min_relative = min_relative
        self.index = {}
        self.idf = []
        self.centroids = {}

    def fit(self, examples):
        documents = []
        labels = []
        for example in examples:
            documents.append(tokenize(example.get('question')))
            labels.append([name for name in example.get('models') or [] if isinstance(name, str)])
        document_frequency = Counter()
        for document in documents:
            document_frequency.update(set(document))
        vocabulary = sorted(document_frequency)
        self.index = {term: position for position, term in enumerate(vocabulary)}
        total = len(documents) or 1
        self.idf = [
            math.log((total + 1) / (document_frequency[term] + 1)) + 1.0
            for term in vocabulary
        ]
        vectors = [self._tfidf(document) for document in documents]
        grouped = {}
        for vector, names in zip(vectors, labels):
            for name in names:
                grouped.setdefault(name, []).append(vector)
        self.centroids = {
            name: self._centroid(vectors_for_label)
            for name, vectors_for_label in grouped.items()
        }
        return self

    def predict(self, question, limit=3):
        tokens = tokenize(question)
        if not tokens or not any(token in self.index for token in tokens):
            return []
        vector = self._tfidf(tokens)
        if not vector:
            return []
        scored = []
        for name, centroid in self.centroids.items():
            score = _dot(vector, centroid)
            if score >= self.min_score:
                scored.append({'model': name, 'score': round(score, 4)})
        scored.sort(key=lambda item: (-item['score'], item['model']))
        if not scored:
            return []
        top = scored[0]['score']
        floor = top * self.min_relative
        kept = [item for item in scored if item['score'] >= floor]
        return kept[: max(limit, 0)]

    def _tfidf(self, tokens):
        counts = Counter(token for token in tokens if token in self.index)
        if not counts:
            return {}
        total = float(sum(counts.values()))
        vector = {
            self.index[term]: (count / total) * self.idf[self.index[term]]
            for term, count in counts.items()
        }
        return _normalize(vector)

    @staticmethod
    def _centroid(vectors):
        totals = {}
        for vector in vectors:
            for position, value in vector.items():
                totals[position] = totals.get(position, 0.0) + value
        count = float(len(vectors) or 1)
        return _normalize({position: value / count for position, value in totals.items()})


def _normalize(vector):
    norm = math.sqrt(sum(value * value for value in vector.values()))
    if not norm:
        return {}
    return {position: value / norm for position, value in vector.items()}


def _dot(left, right):
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(position, 0.0) for position, value in left.items())


def trained_classifier():
    """Fit the bundled examples once, then reuse that classifier."""
    signature = json.dumps(EXAMPLES, sort_keys=True)
    if _CACHE['signature'] != signature or _CACHE['classifier'] is None:
        _CACHE['classifier'] = TfidfBinaryRelevance().fit(EXAMPLES)
        _CACHE['signature'] = signature
    return _CACHE['classifier']


class SetuAiModelHint(models.AbstractModel):
    _name = 'setu.ai.model.hint'
    _description = 'Model Hint Predictor'

    _DEFAULT_LIMIT = 3
    _QUERYABLE_KINDS = ('model', 'manual', 'query')

    @api.model
    def predict_models(self, question, limit=None):
        """Return ranked registry models for a business question.

        Each item is ``{'model': technical_name, 'score': confidence}``.
        Scores below the classifier threshold are dropped. Names that are
        missing, stale, or not a queryable registry model are dropped too.
        """
        if not isinstance(question, str) or not question.strip():
            return []
        limit = self._DEFAULT_LIMIT if limit is None else limit
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = self._DEFAULT_LIMIT
        if limit <= 0:
            return []
        ranked = trained_classifier().predict(question, limit=limit)
        if not ranked:
            return []
        available = set(self.env['setu.ai.schema.model'].search([
            ('name', 'in', [item['model'] for item in ranked]),
            ('is_stale', '=', False),
            ('model_kind', 'in', list(self._QUERYABLE_KINDS)),
        ]).mapped('name'))
        return [item for item in ranked if item['model'] in available]
