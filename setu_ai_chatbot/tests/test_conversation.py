from datetime import timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'setu_ai_conversation')
class TestConversation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.analytics = cls.env['setu.ai.analytics']
        partner = cls.env['setu.ai.schema.model'].search([('name', '=', 'res.partner')], limit=1)
        if not partner:
            partner = cls.env['setu.ai.schema.model'].create({
                'name': 'res.partner',
                'description': 'Contact',
                'module': 'base',
                'model_kind': 'model',
                'table_name': 'res_partner',
            })
        if not cls.env['setu.ai.schema.field'].search([
            ('schema_model_id', '=', partner.id),
            ('name', '=', 'email'),
        ], limit=1):
            cls.env['setu.ai.schema.field'].create({
                'schema_model_id': partner.id,
                'name': 'email',
                'field_label': 'Email',
                'field_type': 'char',
                'store': True,
            })
        cls.env['res.partner'].create({
            'name': 'Aaq Memory Contact',
            'email': 'aaq-memory@example.com',
        })

    def _generate(self, responses):
        iterator = iter(responses)

        def generate(prompt, response_schema):
            response = next(iterator)
            if isinstance(response, Exception):
                raise response
            response['_prompt'] = prompt
            generate.prompts.append(prompt)
            return {key: value for key, value in response.items() if key != '_prompt'}

        generate.prompts = []
        return generate

    def test_follow_up_builds_a_new_plan_from_history(self):
        count_plan = {
            'operation': 'count',
            'model': 'res.partner',
            'filters': [{
                'field': 'email',
                'operator': '=',
                'value': 'aaq-memory@example.com',
            }],
        }
        follow_plan = {
            'operation': 'search',
            'model': 'res.partner',
            'fields': ['email'],
            'filters': count_plan['filters'],
            'limit': 5,
            'order': 'email asc',
        }
        first = self._generate([count_plan, {'explanation': 'The query counted 1 records.'}])
        with patch('odoo.addons.setu_ai_chatbot.models.gemini_client.SetuAiGeminiClient.generate', first):
            opened = self.analytics.answer('How many aaqmemory contacts are there?')
        self.assertTrue(opened['ok'])
        self.assertEqual(opened['computed_result']['result'], 1)

        second = self._generate([follow_plan, {'explanation': 'The query returned 1 records.'}])
        with patch('odoo.addons.setu_ai_chatbot.models.gemini_client.SetuAiGeminiClient.generate', second):
            follow = self.analytics.answer('Show only the top 5.', conversation_id=opened['conversation_id'])
        self.assertTrue(follow['ok'])
        self.assertEqual(follow['query_plan']['operation'], 'search')
        self.assertEqual(follow['query_plan']['limit'], 5)
        self.assertIn('How many aaqmemory contacts are there?', second.prompts[0])
        self.assertIn('res.partner', second.prompts[0])
        stored = self.env['setu.ai.conversation.message'].search([
            ('conversation_id', '=', opened['conversation_id']),
            ('role', '=', 'assistant'),
        ])
        self.assertTrue(stored)
        self.assertNotIn('aaq-memory@example.com', stored[-1].result_summary or '')
        self.assertEqual(stored[-1].filters[0]['value'], '[redacted]')

    def test_missing_expired_and_other_user_sessions_are_hidden(self):
        missing = self.analytics.answer('How many contacts?', conversation_id=999999)
        self.assertFalse(missing['ok'])
        self.assertEqual(missing['error']['type'], 'conversation')

        conversation = self.env['setu.ai.conversation'].create({'name': 'Mine'})
        conversation.last_interaction = fields.Datetime.now() - timedelta(days=30)
        expired = self.analytics.answer('Show only the top 5.', conversation_id=conversation.id)
        self.assertEqual(expired['error']['type'], 'conversation')

        owner = self.env['res.users'].create({
            'name': 'Aaq Memory Owner',
            'login': 'aaq_memory_owner',
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        other = self.env['res.users'].create({
            'name': 'Aaq Memory Other',
            'login': 'aaq_memory_other',
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        owned = self.env['setu.ai.conversation'].with_user(owner).create({})
        self.assertFalse(self.env['setu.ai.conversation'].with_user(other).search([('id', '=', owned.id)]))
        hidden = self.analytics.with_user(other).answer('Show their order counts.', conversation_id=owned.id)
        self.assertEqual(hidden['error']['type'], 'conversation')
        self.assertFalse(hidden['schema_context']['models'])
