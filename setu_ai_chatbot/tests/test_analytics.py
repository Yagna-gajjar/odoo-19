import os
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.setu_ai_chatbot.models.gemini_client import (
    GeminiRateLimitError,
    GeminiResponseError,
)


@tagged('post_install', '-at_install', 'setu_ai_analytics')
class TestAnalytics(TransactionCase):

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
            'name': 'Aaq Gemini Contact',
            'email': 'aaq-gemini@example.com',
        })

    def test_empty_question(self):
        result = self.analytics.answer('   ')
        self.assertFalse(result['ok'])
        self.assertEqual(result['error']['type'], 'validation')
        self.assertIsNone(result['computed_result'])
        self.assertIsNone(result['interpretation'])

    def test_malformed_and_rate_limit_responses(self):
        with patch(
            'odoo.addons.setu_ai_chatbot.models.gemini_client.SetuAiGeminiClient.generate',
            side_effect=GeminiResponseError('Gemini returned malformed JSON.'),
        ):
            malformed = self.analytics.answer('how many contacts', model_hints=['res.partner'])
        self.assertFalse(malformed['ok'])
        self.assertEqual(malformed['error']['type'], 'malformed')
        self.assertIsNone(malformed['computed_result'])

        with patch(
            'odoo.addons.setu_ai_chatbot.models.gemini_client.SetuAiGeminiClient.generate',
            side_effect=GeminiRateLimitError('Gemini rate limit was reached. Try again later.'),
        ):
            limited = self.analytics.answer('how many contacts', model_hints=['res.partner'])
        self.assertEqual(limited['error']['type'], 'rate_limit')

    def test_plan_is_executed_and_invented_numbers_are_discarded(self):
        plan = {
            'operation': 'count',
            'model': 'res.partner',
            'filters': [{
                'field': 'email',
                'operator': '=',
                'value': 'aaq-gemini@example.com',
            }],
        }
        with patch(
            'odoo.addons.setu_ai_chatbot.models.gemini_client.SetuAiGeminiClient.generate',
            side_effect=[plan, {'explanation': 'There is 1 contact.'}],
        ):
            accepted = self.analytics.answer('how many contacts', model_hints=['res.partner'])
        self.assertTrue(accepted['ok'])
        self.assertEqual(accepted['computed_result']['result'], 1)
        self.assertEqual(accepted['interpretation']['source'], 'gemini')
        self.assertIn('1', accepted['interpretation']['text'])
        self.assertEqual(accepted['schema_context']['models'][0]['name'], 'res.partner')

        with patch(
            'odoo.addons.setu_ai_chatbot.models.gemini_client.SetuAiGeminiClient.generate',
            side_effect=[plan, {'explanation': 'There are 99 contacts.'}],
        ):
            rejected = self.analytics.answer('how many contacts', model_hints=['res.partner'])
        self.assertTrue(rejected['ok'])
        self.assertEqual(rejected['computed_result']['result'], 1)
        self.assertEqual(rejected['interpretation']['source'], 'computed')
        self.assertNotIn('99', rejected['interpretation']['text'])

    def test_unsupported_plan_is_not_explained(self):
        with patch(
            'odoo.addons.setu_ai_chatbot.models.gemini_client.SetuAiGeminiClient.generate',
            return_value={'operation': 'unlink', 'model': 'res.partner'},
        ) as generate:
            result = self.analytics.answer('delete contacts', model_hints=['res.partner'])
        self.assertFalse(result['ok'])
        self.assertEqual(result['error']['type'], 'validation')
        self.assertIsNone(result['interpretation'])
        self.assertEqual(generate.call_count, 1)

    def test_missing_api_key(self):
        self.env['ir.config_parameter'].set_param('setu_ai_chatbot.gemini_api_key', '')
        with patch.dict(os.environ, {'GEMINI_API_KEY': ''}):
            result = self.analytics.answer('how many contacts', model_hints=['res.partner'])
        self.assertFalse(result['ok'])
        self.assertEqual(result['error']['type'], 'configuration')

    def test_search_results_sent_for_explanation_are_redacted(self):
        minimized = self.analytics._minimize_result({
            'ok': True,
            'operation': 'search',
            'model': 'res.partner',
            'record_count': 1,
            'records': [{
                'id': 5,
                'name': 'Aaq Gemini Contact',
                'email': 'aaq-gemini@example.com',
                'color': 4,
            }],
        })
        self.assertNotIn('id', minimized['records'][0])
        self.assertEqual(minimized['records'][0]['name'], '[redacted]')
        self.assertEqual(minimized['records'][0]['email'], '[redacted]')
        self.assertEqual(minimized['records'][0]['color'], 4)
