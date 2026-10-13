from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.setu_ai_chatbot.controllers.main import (
    AnalystInputError,
    clean_conversation_id,
    clean_hints,
    clean_question,
    present_answer,
)
from odoo.addons.setu_ai_chatbot.models.conversation import ConversationUnavailable


@tagged('post_install', '-at_install', 'setu_ai_analyst')
class TestAnalystPresentation(TransactionCase):

    def test_search_table_uses_labels_dates_and_currency(self):
        payload = present_answer({
            'ok': True,
            'conversation_id': 7,
            'schema_context': {
                'models': [{
                    'name': 'sale.order',
                    'fields': [
                        {'name': 'date_order', 'label': 'Order Date', 'type': 'datetime'},
                        {'name': 'amount_total', 'label': 'Total', 'type': 'monetary'},
                    ],
                }],
            },
            'query_plan': {'operation': 'search', 'model': 'sale.order'},
            'computed_result': {
                'operation': 'search',
                'model': 'sale.order',
                'fields': ['date_order', 'amount_total', 'partner_id'],
                'records': [{
                    'date_order': '2026-03-01 09:30:00',
                    'amount_total': 12.5,
                    'partner_id': {'id': 4, 'name': 'Aaq Customer'},
                }],
            },
            'interpretation': {'source': 'computed', 'text': 'The query returned 1 records.'},
        })
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['conversation_id'], 7)
        self.assertEqual(payload['explanation'], 'The query returned 1 records.')
        self.assertNotIn('query_plan', payload)
        self.assertNotIn('schema_context', payload)
        columns = {column['key']: column for column in payload['table']['columns']}
        self.assertEqual(columns['date_order']['type'], 'datetime')
        self.assertEqual(columns['amount_total']['type'], 'monetary')
        self.assertEqual(columns['amount_total']['label'], 'Total')
        self.assertEqual(payload['table']['rows'][0]['partner_id'], 'Aaq Customer')

    def test_group_table_formats_count_and_sum(self):
        payload = present_answer({
            'ok': True,
            'conversation_id': 3,
            'schema_context': {
                'models': [{
                    'name': 'sale.order',
                    'fields': [
                        {'name': 'partner_id', 'label': 'Customer', 'type': 'many2one'},
                        {'name': 'amount_total', 'label': 'Total', 'type': 'monetary'},
                    ],
                }],
            },
            'query_plan': {
                'aggregations': [
                    {'field': 'id', 'function': 'count', 'alias': 'order_count'},
                    {'field': 'amount_total', 'function': 'sum', 'alias': 'amount_sum'},
                ],
            },
            'computed_result': {
                'operation': 'group_aggregate',
                'model': 'sale.order',
                'groupby': ['partner_id'],
                'groups': [{
                    'key': {'partner_id': {'id': 4, 'name': 'Aaq Customer'}},
                    'values': {'order_count': 2, 'amount_sum': 40},
                }],
            },
            'interpretation': {'text': 'The query returned 1 groups.'},
        })
        columns = {column['key']: column for column in payload['table']['columns']}
        self.assertEqual(columns['partner_id']['label'], 'Customer')
        self.assertEqual(columns['order_count']['type'], 'integer')
        self.assertEqual(columns['amount_sum']['type'], 'monetary')
        self.assertEqual(columns['amount_sum']['label'], 'Total (sum)')
        self.assertEqual(payload['table']['rows'][0]['partner_id'], 'Aaq Customer')

    def test_errors_do_not_include_schema_or_plans(self):
        payload = present_answer({
            'ok': False,
            'conversation_id': 9,
            'schema_context': {'models': [{'name': 'res.partner'}]},
            'query_plan': {'operation': 'search', 'model': 'res.partner'},
            'error': {'type': 'access', 'message': 'private model detail'},
        })
        self.assertFalse(payload['ok'])
        self.assertEqual(payload['error']['type'], 'access')
        self.assertNotIn('private', payload['error']['message'])
        self.assertIsNone(payload['table'])
        self.assertNotIn('schema_context', payload)

    def test_other_users_session_is_hidden(self):
        payload = present_answer({
            'ok': False,
            'conversation_id': 4,
            'error': {'type': 'conversation', 'message': 'This conversation is not available.'},
        })
        self.assertIsNone(payload['conversation_id'])
        self.assertEqual(payload['error']['message'], 'This conversation is not available.')

    def test_api_error_shows_redacted_gemini_detail(self):
        payload = present_answer({
            'ok': False,
            'error': {'type': 'api', 'message': 'Gemini request failed (400): API key not valid.'},
        })
        self.assertEqual(payload['error']['message'], 'Gemini request failed (400): API key not valid.')
        hidden = present_answer({
            'ok': False,
            'error': {'type': 'api', 'message': 'Traceback: secret'},
        })
        self.assertEqual(hidden['error']['message'], 'The analytics service could not complete the request.')

    def test_input_limits(self):
        self.assertEqual(clean_question('  How many customers?  '), 'How many customers?')
        with self.assertRaises(AnalystInputError):
            clean_question('x' * 501)
        with self.assertRaises(AnalystInputError):
            clean_hints(['res.partner;drop'])
        self.assertEqual(clean_hints('res.partner, sale.order'), ['res.partner', 'sale.order'])
        self.assertIsNone(clean_conversation_id(None))
        with self.assertRaises(ConversationUnavailable):
            clean_conversation_id(True)
        with self.assertRaises(ConversationUnavailable):
            clean_conversation_id('4')
