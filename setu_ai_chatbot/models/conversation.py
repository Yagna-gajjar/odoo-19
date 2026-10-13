import json
from datetime import timedelta

from odoo import api, fields, models


class ConversationUnavailable(Exception):
    """The session is missing, expired, or not visible to this user."""


class SetuAiConversation(models.Model):
    _name = 'setu.ai.conversation'
    _description = 'AI Conversation'
    _order = 'last_interaction desc, id desc'

    _SESSION_DAYS = 14
    _MAX_MESSAGES = 20
    _CONTEXT_TURNS = 3

    name = fields.Char(required=True, default='New conversation')
    user_id = fields.Many2one(
        'res.users',
        required=True,
        index=True,
        default=lambda self: self.env.user,
    )
    last_interaction = fields.Datetime(default=fields.Datetime.now, index=True)
    selected_models = fields.Json()
    last_filters = fields.Json()
    last_operation = fields.Char()
    last_result_summary = fields.Char()
    message_ids = fields.One2many('setu.ai.conversation.message', 'conversation_id')

    @api.model_create_multi
    def create(self, vals_list):
        user_id = self.env.user.id
        for vals in vals_list:
            vals['user_id'] = user_id
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        vals.pop('user_id', None)
        return super().write(vals)

    @api.model
    def prepare_session(self, conversation_id):
        """Return this user's conversation, or create one when no id is given."""
        if not conversation_id:
            return self.create({})
        if isinstance(conversation_id, bool) or not isinstance(conversation_id, int):
            raise ConversationUnavailable('This conversation is not available.')
        conversation = self.search([('id', '=', conversation_id)], limit=1)
        if not conversation or conversation._is_expired():
            raise ConversationUnavailable('This conversation is not available.')
        return conversation

    def context_payload(self):
        """Return compact prior turns for a new query plan."""
        self.ensure_one()
        turns = []
        assistants = self.message_ids.filtered(lambda message: message.role == 'assistant').sorted('id')
        for message in assistants[-self._CONTEXT_TURNS:]:
            turns.append({
                'question': message.question or '',
                'operation': message.operation or '',
                'models': message.selected_models or [],
                'filters': message.filters or [],
                'result_summary': message.result_summary or '',
            })
        return {'turns': turns}

    def hint_models(self):
        self.ensure_one()
        models = []
        for name in self.selected_models or []:
            if isinstance(name, str) and name not in models:
                models.append(name)
        return models

    def record_turn(self, question, plan, result, interpretation):
        """Store a compact turn. Full query rows are not retained."""
        self.ensure_one()
        summary = self._result_summary(result)
        filters = self._stored_filters(plan)
        models = [plan.get('model')] if plan.get('model') else []
        text = ((interpretation or {}).get('text') or summary or '')[:500]
        self.env['setu.ai.conversation.message'].create([
            {
                'conversation_id': self.id,
                'role': 'user',
                'question': (question or '')[:500],
                'body': (question or '')[:500],
            },
            {
                'conversation_id': self.id,
                'role': 'assistant',
                'question': (question or '')[:500],
                'body': text,
                'operation': plan.get('operation'),
                'query_plan': self._compact_plan(plan),
                'result_summary': summary[:300],
                'selected_models': models,
                'filters': filters,
            },
        ])
        self.write({
            'name': self.name if self.name != 'New conversation' else (question or 'New conversation')[:80],
            'last_interaction': fields.Datetime.now(),
            'selected_models': models,
            'last_filters': filters,
            'last_operation': plan.get('operation'),
            'last_result_summary': summary[:300],
        })
        self._trim_messages()

    def _is_expired(self):
        self.ensure_one()
        if not self.last_interaction:
            return False
        deadline = fields.Datetime.now() - timedelta(days=self._SESSION_DAYS)
        return self.last_interaction < deadline

    def _trim_messages(self):
        messages = self.env['setu.ai.conversation.message'].search([
            ('conversation_id', '=', self.id),
        ], order='id')
        overflow = len(messages) - self._MAX_MESSAGES
        if overflow > 0:
            messages[:overflow].unlink()

    @api.model
    def _stored_filters(self, plan):
        stored = []
        for item in (plan.get('filters') or [])[:10]:
            if not isinstance(item, dict):
                continue
            value = item.get('value')
            if isinstance(value, str):
                value = '[redacted]'
            stored.append({
                'field': item.get('field'),
                'operator': item.get('operator'),
                'value': value,
            })
        return stored

    @api.model
    def _compact_plan(self, plan):
        compact = {
            'operation': plan.get('operation'),
            'model': plan.get('model'),
            'fields': (plan.get('fields') or [])[:12],
            'filters': self._stored_filters(plan),
            'groupby': plan.get('groupby') or [],
            'limit': plan.get('limit'),
            'order': plan.get('order'),
        }
        encoded = json.dumps(compact, default=str)
        if len(encoded) <= 2000:
            return compact
        compact.pop('fields', None)
        return compact

    @api.model
    def _result_summary(self, result):
        operation = result.get('operation')
        if operation == 'count':
            return 'counted %s records' % result.get('result')
        if operation == 'aggregate':
            return 'computed %s' % json.dumps(result.get('values') or {}, default=str)[:300]
        if operation == 'group_aggregate':
            return 'returned %s groups' % result.get('group_count')
        if operation == 'search':
            return 'returned %s records' % result.get('record_count')
        return 'query finished'


class SetuAiConversationMessage(models.Model):
    _name = 'setu.ai.conversation.message'
    _description = 'AI Conversation Message'
    _order = 'id'

    conversation_id = fields.Many2one(
        'setu.ai.conversation',
        required=True,
        ondelete='cascade',
        index=True,
    )
    role = fields.Selection([('user', 'User'), ('assistant', 'Assistant')], required=True)
    question = fields.Char()
    body = fields.Text()
    operation = fields.Char()
    query_plan = fields.Json()
    result_summary = fields.Char()
    selected_models = fields.Json()
    filters = fields.Json()
