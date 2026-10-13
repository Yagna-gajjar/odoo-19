import json
import re

from odoo import api, models
from odoo.exceptions import AccessError

from .conversation import ConversationUnavailable
from .gemini_client import GeminiError

_OPERATIONS = ('count', 'search', 'aggregate', 'group_aggregate')
_NUMBER = re.compile(r'(?<![\w.])\d+(?:\.\d+)?(?![\w.])')
_SENSITIVE_FIELDS = frozenset({
    'name', 'display_name', 'complete_name', 'email', 'email_normalized',
    'phone', 'mobile', 'street', 'street2', 'vat', 'city', 'zip',
    'contact_address', 'function', 'title', 'comment', 'ref',
})

_PLAN_SCHEMA = {
    'type': 'object',
    'properties': {
        'operation': {'type': 'string', 'enum': list(_OPERATIONS)},
        'model': {'type': 'string'},
        'fields': {'type': 'array', 'items': {'type': 'string'}},
        'filters': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'field': {'type': 'string'},
                    'operator': {'type': 'string'},
                    'value': {'type': 'string'},
                },
                'required': ['field', 'operator', 'value'],
            },
        },
        'order': {'type': 'string'},
        'limit': {'type': 'integer'},
        'offset': {'type': 'integer'},
        'groupby': {'type': 'array', 'items': {'type': 'string'}},
        'aggregations': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'field': {'type': 'string'},
                    'function': {'type': 'string', 'enum': ['count', 'sum', 'avg', 'min', 'max']},
                    'alias': {'type': 'string'},
                },
                'required': ['field', 'function'],
            },
        },
    },
    'required': ['operation', 'model'],
}
_EXPLANATION_SCHEMA = {
    'type': 'object',
    'properties': {
        'explanation': {'type': 'string'},
    },
    'required': ['explanation'],
}


class SetuAiAnalytics(models.AbstractModel):
    _name = 'setu.ai.analytics'
    _description = 'AI Analytics'

    _SCHEMA_MODEL_LIMIT = 5
    _SCHEMA_FIELD_LIMIT = 12

    @api.model
    def answer(self, question, model_hints=None, conversation_id=None):
        """Answer a question from schema context, a validated query, and Gemini.

        A conversation id supplies prior questions and summaries. Gemini must
        return a new plan, which the read-only query engine validates and runs.
        """
        question = (question or '').strip()
        if not question:
            return self._response(question, model_hints, error={
                'type': 'validation',
                'message': 'Enter a question.',
            })
        try:
            conversation = self.env['setu.ai.conversation'].prepare_session(conversation_id)
        except ConversationUnavailable as error:
            return self._response(question, model_hints, error={
                'type': 'conversation',
                'message': str(error),
            })
        history = conversation.context_payload()
        hints = self._merge_hints(model_hints, conversation.hint_models())
        try:
            schema = self.env['setu.ai.schema.retrieval'].retrieve(
                question=question,
                model_hints=hints,
                limit_models=self._SCHEMA_MODEL_LIMIT,
                limit_fields=self._SCHEMA_FIELD_LIMIT,
                relationship_depth=1,
            )
        except AccessError as error:
            return self._response(question, model_hints, conversation=conversation, error={
                'type': 'access',
                'message': str(error),
            })
        schema_context = self._compact_schema(schema)
        if not schema_context['models']:
            return self._response(question, model_hints, conversation=conversation, schema_context=schema_context, error={
                'type': 'validation',
                'message': 'No schema context matched this question.',
            })
        try:
            plan = self._request_plan(question, schema_context, history)
        except GeminiError as error:
            return self._response(question, model_hints, conversation=conversation, schema_context=schema_context, error={
                'type': error.error_type,
                'message': str(error),
            })
        shape_error = self._plan_shape_error(plan)
        if shape_error:
            return self._response(
                question, model_hints, conversation=conversation, schema_context=schema_context, query_plan=plan,
                error={'type': 'validation', 'message': shape_error},
            )
        result = self.env['setu.ai.query.engine'].execute(plan)
        if not result.get('ok'):
            return self._response(
                question, model_hints, conversation=conversation, schema_context=schema_context, query_plan=plan,
                computed_result=result,
                error=result.get('error') or {
                    'type': 'validation',
                    'message': 'The query plan was rejected.',
                },
            )
        minimized = self._minimize_result(result)
        interpretation = self._explain(question, plan, minimized)
        conversation.record_turn(question, plan, minimized, interpretation)
        return self._response(
            question,
            model_hints,
            conversation=conversation,
            schema_context=schema_context,
            query_plan=plan,
            computed_result=result,
            interpretation=interpretation,
        )

    @api.model
    def _merge_hints(self, model_hints, remembered_models):
        hints = []
        if isinstance(model_hints, str):
            model_hints = [model_hints]
        for name in list(model_hints or []) + list(remembered_models or []):
            if isinstance(name, str) and name not in hints:
                hints.append(name)
        return hints

    @api.model
    def _request_plan(self, question, schema_context, history=None):
        prompt = (
            'Create one new read-only Odoo analytics query plan as JSON.\n'
            'Use only models and fields from the schema context.\n'
            'Allowed operations are count, search, aggregate, and group_aggregate.\n'
            'Do not write SQL, Python, or any other code.\n'
            'Do not reuse a previous plan unchanged. Build a complete plan for the current question.\n'
            'Words such as those, them, top, this year, last year, and their refer to the conversation context.\n'
            'Question: %s\n'
            'Schema context: %s\n'
            'Conversation context: %s'
        ) % (
            question,
            json.dumps(schema_context, default=str),
            json.dumps(history or {'turns': []}, default=str),
        )
        plan = self.env['setu.ai.gemini.client'].generate(prompt, _PLAN_SCHEMA)
        return self._restore_filter_values(plan)

    @api.model
    def _restore_filter_values(self, plan):
        """Structured output may stringify filter values. Restore obvious scalars."""
        if not isinstance(plan, dict):
            return plan
        filters = []
        for item in plan.get('filters') or []:
            if not isinstance(item, dict) or 'value' not in item:
                filters.append(item)
                continue
            updated = dict(item)
            updated['value'] = self._coerce_filter_value(item.get('value'), item.get('operator'))
            filters.append(updated)
        if filters:
            plan = dict(plan)
            plan['filters'] = filters
        return plan

    @api.model
    def _coerce_filter_value(self, value, operator):
        if not isinstance(value, str) or operator in {'like', 'ilike', '=like', '=ilike', 'not like', 'not ilike'}:
            return value
        lowered = value.strip().lower()
        if lowered == 'true':
            return True
        if lowered == 'false':
            return False
        if lowered == 'null':
            return None
        if re.fullmatch(r'-?\d+', value.strip()):
            return int(value.strip())
        if re.fullmatch(r'-?\d+\.\d+', value.strip()):
            return float(value.strip())
        if operator in {'in', 'not in'} and value.strip().startswith('['):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return value
            if isinstance(parsed, list):
                return parsed
        return value

    @api.model
    def _plan_shape_error(self, plan):
        if not isinstance(plan, dict):
            return 'Gemini returned a query plan that is not an object.'
        if plan.get('operation') not in _OPERATIONS:
            return 'Gemini returned an unsupported operation.'
        if not isinstance(plan.get('model'), str) or not plan.get('model').strip():
            return 'Gemini returned a query plan without a model.'
        return None

    @api.model
    def _explain(self, question, plan, minimized_result):
        factual = self._factual_explanation(minimized_result)
        try:
            payload = self.env['setu.ai.gemini.client'].generate(
                (
                    'Explain the computed query result in two or three sentences.\n'
                    'Use only numbers that appear in the computed result. Do not invent counts, totals, or amounts.\n'
                    'Do not mention hidden or redacted text values.\n'
                    'Question: %s\n'
                    'Query plan: %s\n'
                    'Computed result: %s'
                ) % (
                    question,
                    json.dumps(plan, default=str),
                    json.dumps(minimized_result, default=str),
                ),
                _EXPLANATION_SCHEMA,
            )
        except GeminiError:
            return {'source': 'computed', 'text': factual}
        explanation = payload.get('explanation') if isinstance(payload, dict) else None
        if not isinstance(explanation, str) or not explanation.strip():
            return {'source': 'computed', 'text': factual}
        allowed = json.dumps({'result': minimized_result, 'plan': {'limit': plan.get('limit'), 'offset': plan.get('offset')}})
        if not self._numbers_are_grounded(explanation, allowed):
            return {'source': 'computed', 'text': factual}
        return {'source': 'gemini', 'text': explanation.strip()}

    @api.model
    def _numbers_are_grounded(self, explanation, allowed_text):
        allowed = set(_NUMBER.findall(allowed_text))
        for number in _NUMBER.findall(explanation):
            if number not in allowed and number.rstrip('0').rstrip('.') not in allowed:
                return False
        return True

    @api.model
    def _factual_explanation(self, result):
        operation = result.get('operation')
        if operation == 'count':
            return 'The query counted %s records.' % result.get('result')
        if operation == 'aggregate':
            values = result.get('values') or {}
            pieces = ['%s=%s' % (key, value) for key, value in values.items()]
            return 'The query computed %s.' % ', '.join(pieces)
        if operation == 'group_aggregate':
            return 'The query returned %s groups.' % result.get('group_count')
        if operation == 'search':
            return 'The query returned %s records.' % result.get('record_count')
        return 'The query finished.'

    @api.model
    def _compact_schema(self, schema):
        models = []
        for model in schema.get('models') or []:
            fields = []
            for field in model.get('fields') or []:
                description = (field.get('description') or '')[:160]
                fields.append({
                    'name': field.get('name'),
                    'label': field.get('label'),
                    'type': field.get('type'),
                    'relation': field.get('relation'),
                    'description': description or None,
                })
            relationships = []
            for relation in model.get('relationships') or []:
                relationships.append({
                    'field': relation.get('field'),
                    'type': relation.get('type'),
                    'related_model': relation.get('related_model'),
                })
            models.append({
                'name': model.get('name'),
                'description': model.get('description'),
                'kind': model.get('model_kind'),
                'fields': fields,
                'relationships': relationships,
            })
        return {'models': models}

    @api.model
    def _minimize_result(self, result):
        if result.get('operation') == 'search':
            return {
                'operation': 'search',
                'model': result.get('model'),
                'record_count': result.get('record_count'),
                'records': [
                    self._redact_row(row) for row in (result.get('records') or [])[:5]
                ],
            }
        if result.get('operation') == 'group_aggregate':
            minimized = dict(result)
            minimized['groups'] = [self._redact_group(group) for group in result.get('groups') or []]
            return minimized
        return {
            'operation': result.get('operation'),
            'model': result.get('model'),
            'result': result.get('result'),
            'values': result.get('values'),
        }

    @api.model
    def _redact_row(self, row):
        redacted = {}
        for key, value in row.items():
            if key == 'id':
                continue
            redacted[key] = self._redact_value(key, value)
        return redacted

    @api.model
    def _redact_group(self, group):
        return {
            'key': {
                key: self._redact_value(key, value)
                for key, value in (group.get('key') or {}).items()
            },
            'values': group.get('values') or {},
        }

    @api.model
    def _redact_value(self, field_name, value):
        if isinstance(value, dict) and 'id' in value and 'name' in value:
            return {'related': True}
        if isinstance(value, str) and (field_name in _SENSITIVE_FIELDS or '@' in value):
            return '[redacted]'
        if isinstance(value, (int, float, bool)) or value is None:
            return value
        if isinstance(value, str):
            return value
        return '[redacted]'

    @api.model
    def _response(self, question, model_hints, schema_context=None, query_plan=None,
                  computed_result=None, interpretation=None, error=None, conversation=None):
        schema_context = schema_context or {'models': []}
        return {
            'ok': error is None,
            'question': question,
            'model_hints': model_hints or [],
            'conversation_id': conversation.id if conversation else None,
            'schema_context': schema_context,
            'query_plan': query_plan,
            'computed_result': computed_result,
            'interpretation': interpretation,
            'error': error,
        }
