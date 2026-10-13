import re

from odoo import http
from odoo.http import request

from odoo.addons.setu_ai_chatbot.models.conversation import ConversationUnavailable

_MODEL_NAME = re.compile(r'^[a-z][a-z0-9_.]{0,80}$')
_QUESTION_LIMIT = 500
_HINT_LIMIT = 8
_CONVERSATION_LIMIT = 20
_DISPLAY_TYPES = {
    'integer': 'integer',
    'float': 'float',
    'monetary': 'monetary',
    'date': 'date',
    'datetime': 'datetime',
    'boolean': 'boolean',
    'many2one': 'many2one',
}
_VALIDATION_MESSAGES = {
    'Enter a question.',
    'No schema context matched this question.',
    'Gemini returned a query plan that is not an object.',
    'Gemini returned an unsupported operation.',
    'Gemini returned a query plan without a model.',
    'The query plan was rejected.',
}


class AnalystInputError(Exception):
    """The browser sent a question, hint, or session id that cannot be used."""


def clean_question(question):
    if not isinstance(question, str):
        raise AnalystInputError('Enter a question.')
    question = question.strip()
    if not question:
        raise AnalystInputError('Enter a question.')
    if len(question) > _QUESTION_LIMIT:
        raise AnalystInputError('Enter a shorter question.')
    return question


def clean_conversation_id(conversation_id):
    if conversation_id in (None, False):
        return None
    if isinstance(conversation_id, bool) or not isinstance(conversation_id, int) or conversation_id <= 0:
        raise ConversationUnavailable('This conversation is not available.')
    return conversation_id


def clean_hints(model_hints):
    if model_hints in (None, False, ''):
        return None
    if isinstance(model_hints, str):
        model_hints = [part.strip() for part in model_hints.split(',') if part.strip()]
    if not isinstance(model_hints, list) or len(model_hints) > _HINT_LIMIT:
        raise AnalystInputError('Model hints must be a short list of technical model names.')
    cleaned = []
    for name in model_hints:
        if not isinstance(name, str) or not _MODEL_NAME.match(name) or name in cleaned:
            if not isinstance(name, str) or not _MODEL_NAME.match(name):
                raise AnalystInputError('Model hints must be a short list of technical model names.')
            continue
        cleaned.append(name)
    return cleaned or None


def present_answer(result):
    """Return the fields the chat screen needs, without plans or schema slices."""
    result = result or {}
    conversation_id = result.get('conversation_id')
    payload = {
        'ok': False,
        'conversation_id': conversation_id if isinstance(conversation_id, int) and conversation_id > 0 else None,
        'explanation': '',
        'table': None,
        'error': None,
    }
    error = result.get('error')
    if error or not result.get('ok'):
        payload['error'] = public_error(error)
        if payload['error']['type'] == 'conversation':
            payload['conversation_id'] = None
        return payload
    interpretation = result.get('interpretation') or {}
    text = interpretation.get('text') if isinstance(interpretation, dict) else ''
    payload['ok'] = True
    payload['explanation'] = text if isinstance(text, str) else ''
    payload['table'] = build_table(
        result.get('computed_result'),
        result.get('schema_context'),
        result.get('query_plan'),
    )
    return payload


def public_error(error):
    error = error if isinstance(error, dict) else {}
    error_type = error.get('type') if isinstance(error.get('type'), str) else 'execution'
    message = error.get('message') if isinstance(error.get('message'), str) else ''
    if error_type == 'conversation':
        return {'type': 'conversation', 'message': 'This conversation is not available.'}
    if error_type == 'access':
        return {'type': 'access', 'message': 'You do not have permission to answer this question.'}
    if error_type == 'rate_limit':
        return {'type': 'rate_limit', 'message': 'The analytics service is busy. Wait a moment and try again.'}
    if error_type == 'configuration':
        return {'type': 'configuration', 'message': 'The analytics service is not configured.'}
    if error_type == 'api':
        if _safe_api_message(message):
            return {'type': 'api', 'message': message}
        return {'type': 'api', 'message': 'The analytics service could not complete the request.'}
    if error_type == 'malformed':
        return {'type': 'malformed', 'message': 'The analytics service returned an unexpected response.'}
    if error_type == 'validation':
        if message in _VALIDATION_MESSAGES or _safe_validation_message(message):
            return {'type': 'validation', 'message': message}
        return {'type': 'validation', 'message': 'The question could not be answered.'}
    return {'type': 'execution', 'message': 'The question could not be answered.'}


def present_conversation(conversation):
    return {
        'ok': True,
        'conversation_id': conversation.id,
        'name': conversation.name or 'Conversation',
        'messages': [present_message(message) for message in conversation.message_ids],
        'error': None,
    }


def present_message(message):
    payload = {
        'role': message.role,
        'body': message.body or '',
    }
    if message.role == 'assistant':
        payload['explanation'] = message.body or ''
        payload['summary'] = message.result_summary or ''
    return payload


def build_table(computed, schema_context, query_plan):
    if not isinstance(computed, dict):
        return None
    operation = computed.get('operation')
    schema_fields = _schema_fields(schema_context, computed.get('model'))
    if operation == 'count':
        return {
            'columns': [{'key': 'count', 'label': 'Count', 'type': 'integer'}],
            'rows': [{'count': _cell(computed.get('result'))}],
        }
    if operation == 'aggregate':
        return _aggregate_table(computed, schema_fields, query_plan)
    if operation == 'search':
        return _search_table(computed, schema_fields)
    if operation == 'group_aggregate':
        return _group_table(computed, schema_fields, query_plan)
    return None


def _schema_fields(schema_context, model_name):
    fields_by_name = {}
    if not isinstance(schema_context, dict):
        return fields_by_name
    for model in schema_context.get('models') or []:
        if not isinstance(model, dict) or model.get('name') != model_name:
            continue
        for field in model.get('fields') or []:
            if isinstance(field, dict) and isinstance(field.get('name'), str):
                fields_by_name[field['name']] = field
    return fields_by_name


def _search_table(computed, schema_fields):
    columns = []
    for name in computed.get('fields') or []:
        if not isinstance(name, str):
            continue
        meta = schema_fields.get(name) or {}
        columns.append({
            'key': name,
            'label': meta.get('label') or ('ID' if name == 'id' else name),
            'type': 'integer' if name == 'id' else _display_type(meta.get('type')),
        })
    rows = []
    for record in computed.get('records') or []:
        if not isinstance(record, dict):
            continue
        rows.append({column['key']: _cell(record.get(column['key'])) for column in columns})
    return {'columns': columns, 'rows': rows}


def _aggregate_table(computed, schema_fields, query_plan):
    aggregations = _aggregations(query_plan)
    values = computed.get('values') if isinstance(computed.get('values'), dict) else {}
    aliases = list(aggregations) or list(values)
    columns = []
    row = {}
    for alias in aliases:
        item = aggregations.get(alias) or {}
        meta = schema_fields.get(item.get('field')) or {}
        columns.append({
            'key': alias,
            'label': _aggregation_label(alias, meta, item.get('function')),
            'type': _aggregation_type(meta.get('type'), item.get('function')),
        })
        row[alias] = _cell(values.get(alias))
    return {'columns': columns, 'rows': [row] if columns else []}


def _group_table(computed, schema_fields, query_plan):
    aggregations = _aggregations(query_plan)
    columns = []
    for field_name in computed.get('groupby') or []:
        if not isinstance(field_name, str):
            continue
        meta = schema_fields.get(field_name) or {}
        columns.append({
            'key': field_name,
            'label': meta.get('label') or field_name,
            'type': _display_type(meta.get('type')),
        })
    groups = [group for group in (computed.get('groups') or []) if isinstance(group, dict)]
    aliases = list(aggregations)
    if not aliases and groups:
        aliases = list((groups[0].get('values') or {}))
    for alias in aliases:
        item = aggregations.get(alias) or {}
        meta = schema_fields.get(item.get('field')) or {}
        columns.append({
            'key': alias,
            'label': _aggregation_label(alias, meta, item.get('function')),
            'type': _aggregation_type(meta.get('type'), item.get('function')),
        })
    rows = []
    for group in groups:
        key = group.get('key') if isinstance(group.get('key'), dict) else {}
        values = group.get('values') if isinstance(group.get('values'), dict) else {}
        row = {}
        for column in columns:
            if column['key'] in key:
                row[column['key']] = _cell(key.get(column['key']))
            else:
                row[column['key']] = _cell(values.get(column['key']))
        rows.append(row)
    return {'columns': columns, 'rows': rows}


def _aggregations(query_plan):
    aggregations = {}
    if not isinstance(query_plan, dict):
        return aggregations
    for item in query_plan.get('aggregations') or []:
        if isinstance(item, dict) and isinstance(item.get('alias'), str):
            aggregations[item['alias']] = item
    return aggregations


def _aggregation_label(alias, meta, function):
    label = meta.get('label') if isinstance(meta, dict) else None
    if isinstance(label, str) and label and function in {'count', 'sum', 'avg', 'min', 'max'}:
        return '%s (%s)' % (label, function)
    return alias.replace('_', ' ')


def _aggregation_type(field_type, function):
    if function == 'count':
        return 'integer'
    if function in {'sum', 'avg'}:
        return 'monetary' if field_type == 'monetary' else 'float'
    if function in {'min', 'max'} and field_type in {'date', 'datetime', 'monetary', 'integer'}:
        return field_type
    if function in {'min', 'max'}:
        return 'float'
    return _display_type(field_type)


def _display_type(field_type):
    return _DISPLAY_TYPES.get(field_type, 'char')


def _cell(value):
    if isinstance(value, dict):
        name = value.get('name')
        return name if isinstance(name, str) else ''
    if isinstance(value, list):
        parts = []
        for item in value:
            cell = _cell(item)
            if cell not in (None, ''):
                parts.append(str(cell))
        return ', '.join(parts)
    if isinstance(value, bool) or value is None or isinstance(value, (int, float, str)):
        return value
    return None


def _safe_api_message(message):
    if not message.startswith('Gemini request failed'):
        return False
    if len(message) > 360 or '\n' in message or '\r' in message:
        return False
    lowered = message.lower()
    return 'traceback' not in lowered and 'select ' not in lowered


def _safe_validation_message(message):
    if not message or len(message) > 200 or '\n' in message or '\r' in message:
        return False
    lowered = message.lower()
    return 'traceback' not in lowered and 'select ' not in lowered and 'api key' not in lowered


class AIAssistantController(http.Controller):

    @http.route('/setu_ai_chatbot/ask', type='jsonrpc', auth='user')
    def ask(self, question=None, conversation_id=None, model_hints=None):
        denied = self._internal_user_required()
        if denied:
            return denied
        try:
            question = clean_question(question)
            conversation_id = clean_conversation_id(conversation_id)
            model_hints = clean_hints(model_hints)
        except AnalystInputError as error:
            return present_answer({
                'ok': False,
                'error': {'type': 'validation', 'message': str(error)},
            })
        except ConversationUnavailable as error:
            return present_answer({
                'ok': False,
                'error': {'type': 'conversation', 'message': str(error)},
            })
        result = request.env['setu.ai.analytics'].answer(
            question,
            model_hints=model_hints,
            conversation_id=conversation_id,
        )
        return present_answer(result)

    @http.route('/setu_ai_chatbot/conversations', type='jsonrpc', auth='user')
    def conversations(self):
        denied = self._internal_user_required()
        if denied:
            return denied
        conversations = request.env['setu.ai.conversation'].search([], limit=40)
        visible = conversations.filtered(lambda conversation: not conversation._is_expired())[:_CONVERSATION_LIMIT]
        return {
            'ok': True,
            'conversations': [{
                'id': conversation.id,
                'name': conversation.name or 'Conversation',
            } for conversation in visible],
            'error': None,
        }

    @http.route('/setu_ai_chatbot/conversation', type='jsonrpc', auth='user')
    def conversation(self, conversation_id=None):
        denied = self._internal_user_required()
        if denied:
            return denied
        try:
            conversation_id = clean_conversation_id(conversation_id)
            if not conversation_id:
                raise ConversationUnavailable('This conversation is not available.')
            conversation = request.env['setu.ai.conversation'].prepare_session(conversation_id)
        except ConversationUnavailable as error:
            return present_answer({
                'ok': False,
                'error': {'type': 'conversation', 'message': str(error)},
            })
        return present_conversation(conversation)

    def _internal_user_required(self):
        if request.env.user.has_group('base.group_user'):
            return None
        return present_answer({
            'ok': False,
            'error': {'type': 'access', 'message': 'You do not have permission to answer this question.'},
        })
