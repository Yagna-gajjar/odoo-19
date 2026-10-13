import re

from odoo import api, models
from odoo.exceptions import AccessError

_TOKEN_RE = re.compile(r'[a-z0-9_.]+')
_RELATIONAL_TYPES = frozenset({
    'many2one',
    'one2many',
    'many2many',
    'many2one_reference',
    'reference',
})
_STOP_WORDS = frozenset({
    'a', 'an', 'the', 'of', 'for', 'to', 'in', 'on', 'and', 'or', 'is', 'are',
    'what', 'which', 'who', 'how', 'me', 'my', 'show', 'list', 'get', 'with',
    'from', 'by', 'all', 'please', 'do', 'does', 'did', 'can', 'i', 'we',
})
_SCORE_HINT_EXACT = 100
_SCORE_HINT_PARTIAL = 60
_SCORE_NAME_EXACT = 80
_SCORE_NAME_PARTIAL = 50
_SCORE_DESCRIPTION = 40
_FIELD_SCORE_CAP = 70


class SetuAiSchemaRetrieval(models.AbstractModel):
    _name = 'setu.ai.schema.retrieval'
    _description = 'AI Schema Retrieval'

    _DEFAULT_MODEL_LIMIT = 8
    _DEFAULT_FIELD_LIMIT = 25
    _DEFAULT_RELATIONSHIP_DEPTH = 1
    _PARAM_MODEL_LIMIT = 'setu_ai_chatbot.schema_retrieval_model_limit'
    _PARAM_FIELD_LIMIT = 'setu_ai_chatbot.schema_retrieval_field_limit'
    _PARAM_RELATIONSHIP_DEPTH = 'setu_ai_chatbot.schema_retrieval_relationship_depth'

    @api.model
    def lookup_models(self, term, limit_models=None, limit_fields=None, relationship_depth=None):
        """Find registry models by technical name, partial name, description, or field."""
        return self.retrieve(
            question=term,
            limit_models=limit_models,
            limit_fields=limit_fields,
            relationship_depth=relationship_depth,
        )

    @api.model
    def retrieve(self, question=None, model_hints=None, limit_models=None,
                 limit_fields=None, relationship_depth=None):
        """Return schema context for a question from stored registry metadata.

        Matching is keyword and hint based. Confident local model predictions
        are added after explicit hints. The stored schema models are the
        source of truth; stale rows are ignored. ``sudo()`` is not used.
        """
        self._check_administrator()
        limits = self._resolve_limits(limit_models, limit_fields, relationship_depth)
        hints = self._with_predicted_hints(
            question,
            self._normalize_hints(model_hints),
            limits['models'],
        )
        keywords = self._keywords(question)
        result = {
            'question': (question or '').strip(),
            'keywords': keywords,
            'model_hints': hints,
            'unknown_hints': [],
            'limits': limits,
            'models': [],
        }
        if not keywords and not hints:
            return result

        ranked, unknown_hints = self._rank_models(keywords, hints)
        result['unknown_hints'] = unknown_hints
        selected, roles = self._select_models(ranked, limits)
        included_names = {schema_model.name for schema_model in selected}
        ranked_by_id = {item['record'].id: item for item in ranked}
        result['models'] = [
            self._serialize_model(
                schema_model,
                ranked_by_id.get(schema_model.id),
                roles.get(schema_model.id, 'related'),
                keywords,
                limits['fields'],
                included_names,
            )
            for schema_model in selected
        ]
        return result

    @api.model
    def _check_administrator(self):
        if self.env.su or self.env.user.has_group('base.group_system'):
            return
        raise AccessError(self.env._(
            'Only administrators can retrieve schema metadata.'
        ))

    @api.model
    def _resolve_limits(self, limit_models, limit_fields, relationship_depth):
        return {
            'models': self._bounded_int(
                limit_models, self._PARAM_MODEL_LIMIT, self._DEFAULT_MODEL_LIMIT,
            ),
            'fields': self._bounded_int(
                limit_fields, self._PARAM_FIELD_LIMIT, self._DEFAULT_FIELD_LIMIT,
            ),
            'relationship_depth': self._bounded_int(
                relationship_depth,
                self._PARAM_RELATIONSHIP_DEPTH,
                self._DEFAULT_RELATIONSHIP_DEPTH,
            ),
        }

    @api.model
    def _bounded_int(self, value, parameter, default):
        if value is None:
            value = self.env['ir.config_parameter'].get_param(parameter, default=str(default))
        try:
            number = int(value)
        except (TypeError, ValueError):
            number = default
        return max(number, 0)

    @api.model
    def _normalize_hints(self, model_hints):
        if not model_hints:
            return []
        if isinstance(model_hints, str):
            model_hints = [model_hints]
        hints = []
        seen = set()
        for hint in model_hints:
            text = str(hint or '').strip()
            key = text.lower()
            if not text or key in seen:
                continue
            seen.add(key)
            hints.append(text)
        return hints

    @api.model
    def _with_predicted_hints(self, question, hints, limit_models):
        """Keep explicit hints first, then add confident predicted model names."""
        if not isinstance(question, str) or not question.strip() or limit_models <= 0:
            return hints
        predictions = self.env['setu.ai.model.hint'].predict_models(
            question,
            limit=min(limit_models, 3),
        )
        merged = list(hints)
        seen = {hint.lower() for hint in hints}
        for prediction in predictions:
            name = prediction['model']
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(name)
        return merged

    @api.model
    def _keywords(self, question):
        text = (question or '').strip().lower().replace('%', ' ')
        if not text:
            return []
        keywords = []
        seen = set()
        for token in _TOKEN_RE.findall(text):
            parts = [token]
            if '.' in token or '_' in token:
                parts.extend(part for part in re.split(r'[._]+', token) if part)
            if token.endswith('s') and not token.endswith('ss') and len(token) > 4:
                parts.append(token[:-1])
            for part in parts:
                if len(part) < 2 or part in _STOP_WORDS or part in seen:
                    continue
                seen.add(part)
                keywords.append(part)
        return keywords

    @api.model
    def _rank_models(self, keywords, hints):
        ranked = {}
        unknown_hints = []
        schema_model_obj = self.env['setu.ai.schema.model']
        for hint in hints:
            matches = self._models_for_hint(hint)
            if not matches:
                unknown_hints.append(hint)
                continue
            for schema_model in matches:
                exact = schema_model.name.lower() == hint.lower()
                self._add_score(
                    ranked,
                    schema_model,
                    _SCORE_HINT_EXACT if exact else _SCORE_HINT_PARTIAL,
                    'hint',
                )
        if keywords:
            name_domain = [('is_stale', '=', False)] + self._or_domain([
                clause
                for keyword in keywords
                for clause in (
                    ('name', 'ilike', self._like_term(keyword)),
                    ('description', 'ilike', self._like_term(keyword)),
                )
            ])
            for schema_model in schema_model_obj.search(name_domain):
                self._score_model_text(ranked, schema_model, keywords)
            field_domain = [
                ('is_stale', '=', False),
                ('schema_model_id.is_stale', '=', False),
            ] + self._or_domain([
                clause
                for keyword in keywords
                for clause in (
                    ('name', 'ilike', self._like_term(keyword)),
                    ('field_label', 'ilike', self._like_term(keyword)),
                    ('help', 'ilike', self._like_term(keyword)),
                )
            ])
            fields_by_model = {}
            for schema_field in self.env['setu.ai.schema.field'].search(field_domain):
                fields_by_model.setdefault(schema_field.schema_model_id, self.env['setu.ai.schema.field'])
                fields_by_model[schema_field.schema_model_id] |= schema_field
            for schema_model, schema_fields in fields_by_model.items():
                self._score_model_fields(ranked, schema_model, schema_fields, keywords)
        ordered = sorted(
            ranked.values(),
            key=lambda item: (-item['score'], item['record'].name),
        )
        return ordered, unknown_hints

    @api.model
    def _models_for_hint(self, hint):
        schema_model_obj = self.env['setu.ai.schema.model']
        like_hint = self._like_term(hint)
        exact = schema_model_obj.search([
            ('is_stale', '=', False),
            ('name', '=ilike', like_hint),
        ], limit=1)
        if exact:
            return exact
        return schema_model_obj.search([
            ('is_stale', '=', False),
            '|',
            ('name', 'ilike', like_hint),
            ('description', 'ilike', like_hint),
        ])

    @api.model
    def _score_model_text(self, ranked, schema_model, keywords):
        name = (schema_model.name or '').lower()
        description = (schema_model.description or '').lower()
        for keyword in keywords:
            if name == keyword:
                self._add_score(ranked, schema_model, _SCORE_NAME_EXACT, 'technical_name')
            elif keyword in name:
                self._add_score(ranked, schema_model, _SCORE_NAME_PARTIAL, 'partial_name')
            if keyword in description:
                self._add_score(ranked, schema_model, _SCORE_DESCRIPTION, 'description')

    @api.model
    def _score_model_fields(self, ranked, schema_model, schema_fields, keywords):
        points = 0
        for schema_field in schema_fields:
            field_points, reason = self._field_keyword_score(schema_field, keywords)
            if not field_points:
                continue
            points += field_points
            self._add_score(ranked, schema_model, 0, reason)
        if points:
            self._add_score(ranked, schema_model, min(points, _FIELD_SCORE_CAP), 'field')

    @api.model
    def _field_keyword_score(self, schema_field, keywords):
        name = (schema_field.name or '').lower()
        label = (schema_field.field_label or '').lower()
        help_text = (schema_field.help or '').lower()
        points = 0
        for keyword in keywords:
            if name == keyword:
                points += 35
            elif keyword in name:
                points += 20
            if keyword in label:
                points += 25
            if help_text and keyword in help_text:
                points += 10
        if not points:
            return 0, None
        return points, 'field:%s' % schema_field.name

    @api.model
    def _add_score(self, ranked, schema_model, points, reason):
        item = ranked.get(schema_model.id)
        if not item:
            item = {'record': schema_model, 'score': 0, 'reasons': []}
            ranked[schema_model.id] = item
        item['score'] += points
        if reason and reason not in item['reasons']:
            item['reasons'].append(reason)

    @api.model
    def _select_models(self, ranked, limits):
        selected = []
        roles = {}
        seen = set()
        for item in ranked:
            if len(selected) >= limits['models']:
                break
            schema_model = item['record']
            selected.append(schema_model)
            roles[schema_model.id] = 'matched'
            seen.add(schema_model.id)
        if not limits['relationship_depth']:
            return selected, roles
        frontier = list(selected)
        for _depth in range(limits['relationship_depth']):
            if len(selected) >= limits['models']:
                break
            next_frontier = []
            related_by_name = self._models_by_names(self._relation_names(frontier))
            for schema_model in frontier:
                for schema_field in schema_model.field_ids.sorted('name'):
                    if len(selected) >= limits['models']:
                        break
                    related = related_by_name.get(schema_field.relation)
                    if not related or related.id in seen or not self._is_relationship(schema_field):
                        continue
                    selected.append(related)
                    roles[related.id] = 'related'
                    seen.add(related.id)
                    next_frontier.append(related)
            frontier = next_frontier
        return selected, roles

    @api.model
    def _relation_names(self, schema_models):
        names = set()
        for schema_model in schema_models:
            for schema_field in schema_model.field_ids:
                if self._is_relationship(schema_field) and schema_field.relation:
                    names.add(schema_field.relation)
        return names

    @api.model
    def _models_by_names(self, names):
        if not names:
            return {}
        records = self.env['setu.ai.schema.model'].search([
            ('name', 'in', list(names)),
            ('is_stale', '=', False),
        ])
        return {record.name: record for record in records}

    @api.model
    def _is_relationship(self, schema_field):
        return (
            not schema_field.is_stale
            and schema_field.field_type in _RELATIONAL_TYPES
            and bool(schema_field.relation)
        )

    @api.model
    def _serialize_model(self, schema_model, ranked_item, role, keywords, field_limit, included_names):
        reasons = list(ranked_item['reasons']) if ranked_item else []
        if role == 'related' and 'related' not in reasons:
            reasons.append('related')
        available_names = set(included_names)
        related_targets = {
            schema_field.relation
            for schema_field in schema_model.field_ids
            if self._is_relationship(schema_field)
        }
        if related_targets:
            available_names.update(self._models_by_names(related_targets))
        fields_payload = self._select_fields(schema_model, keywords, field_limit)
        field_names = {field_payload['name'] for field_payload in fields_payload}
        relationships = []
        for schema_field in schema_model.field_ids.sorted('name'):
            if schema_field.name not in field_names or not self._is_relationship(schema_field):
                continue
            related_name = schema_field.relation or None
            relationships.append({
                'field': schema_field.name,
                'label': schema_field.field_label,
                'type': schema_field.field_type,
                'related_model': related_name,
                'included': bool(related_name and related_name in included_names),
                'missing': bool(related_name) and related_name not in available_names,
            })
        return {
            'name': schema_model.name,
            'description': schema_model.description or '',
            'module': schema_model.module or None,
            'model_kind': schema_model.model_kind,
            'table_name': schema_model.table_name or None,
            'match': {
                'role': role,
                'score': ranked_item['score'] if ranked_item else 0,
                'reasons': reasons,
            },
            'fields': fields_payload,
            'relationships': relationships,
        }

    @api.model
    def _select_fields(self, schema_model, keywords, field_limit):
        ranked_fields = []
        for schema_field in schema_model.field_ids:
            if schema_field.is_stale:
                continue
            ranked_fields.append((
                self._field_priority(schema_field, keywords),
                schema_field.name,
                schema_field,
            ))
        ranked_fields.sort(key=lambda item: (-item[0], item[1]))
        return [
            self._serialize_field(schema_field)
            for _priority, _name, schema_field in ranked_fields[:field_limit]
        ]

    @api.model
    def _field_priority(self, schema_field, keywords):
        points, _reason = self._field_keyword_score(schema_field, keywords)
        if schema_field.field_type in _RELATIONAL_TYPES:
            points += 10
        if schema_field.store and not schema_field.is_computed:
            points += 1
        return points

    @api.model
    def _serialize_field(self, schema_field):
        return {
            'name': schema_field.name,
            'label': schema_field.field_label or schema_field.name,
            'type': schema_field.field_type,
            'description': schema_field.help or '',
            'relation': schema_field.relation or None,
            'store': bool(schema_field.store),
            'is_computed': bool(schema_field.is_computed),
            'is_related': bool(schema_field.is_related),
            'related_path': schema_field.related_path or None,
        }

    @api.model
    def _like_term(self, value):
        """Escape LIKE wildcards so underscores in field names stay literal."""
        return (
            value.replace('\\', '\\\\')
            .replace('%', r'\%')
            .replace('_', r'\_')
        )

    @api.model
    def _or_domain(self, clauses):
        if not clauses:
            return []
        return (['|'] * (len(clauses) - 1)) + clauses
