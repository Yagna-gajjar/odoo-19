from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'setu_ai_query')
class TestQueryEngine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls.env['setu.ai.query.engine']
        cls._ensure_partner_schema()
        cls.company = cls.env['res.partner'].create({
            'name': 'Aaq Query Co',
            'is_company': True,
            'email': 'aaq-query-co@example.com',
            'color': 4,
        })
        cls.person = cls.env['res.partner'].create({
            'name': 'Aaq Query Person',
            'is_company': False,
            'email': 'aaq-query-person@example.com',
            'color': 6,
        })

    @classmethod
    def _ensure_model(cls, name, description, kind='model'):
        schema_model = cls.env['setu.ai.schema.model'].search([('name', '=', name)], limit=1)
        if not schema_model:
            schema_model = cls.env['setu.ai.schema.model'].create({
                'name': name,
                'description': description,
                'module': 'base',
                'model_kind': kind,
                'table_name': name.replace('.', '_'),
            })
        return schema_model

    @classmethod
    def _ensure_field(cls, schema_model, name, label, field_type, relation=False):
        schema_field = cls.env['setu.ai.schema.field'].search([
            ('schema_model_id', '=', schema_model.id),
            ('name', '=', name),
        ], limit=1)
        if schema_field:
            return schema_field
        return cls.env['setu.ai.schema.field'].create({
            'schema_model_id': schema_model.id,
            'name': name,
            'field_label': label,
            'field_type': field_type,
            'relation': relation,
            'store': True,
        })

    @classmethod
    def _ensure_partner_schema(cls):
        partner = cls._ensure_model('res.partner', 'Contact')
        country = cls._ensure_model('res.country', 'Country')
        for name, label, field_type, relation in (
            ('name', 'Name', 'char', False),
            ('email', 'Email', 'char', False),
            ('color', 'Color', 'integer', False),
            ('is_company', 'Is Company', 'boolean', False),
            ('id', 'ID', 'integer', False),
            ('country_id', 'Country', 'many2one', 'res.country'),
        ):
            cls._ensure_field(partner, name, label, field_type, relation)
        cls._ensure_field(country, 'code', 'Code', 'char')

    def _partner_domain(self):
        return [[
            'email', 'in',
            ['aaq-query-co@example.com', 'aaq-query-person@example.com'],
        ]]

    def test_count_and_search(self):
        counted = self.engine.execute({
            'operation': 'count',
            'model': 'res.partner',
            'domain': self._partner_domain(),
        })
        self.assertTrue(counted['ok'])
        self.assertEqual(counted['result'], 2)

        searched = self.engine.execute({
            'operation': 'search',
            'model': 'res.partner',
            'fields': ['name', 'email'],
            'filters': [{
                'field': 'email',
                'operator': 'ilike',
                'value': 'aaq-query-',
            }],
            'order': 'name asc',
            'limit': 1,
        })
        self.assertTrue(searched['ok'])
        self.assertEqual(searched['record_count'], 1)
        self.assertEqual(searched['records'][0]['name'], 'Aaq Query Co')
        self.assertEqual(set(searched['records'][0]), {'id', 'name', 'email'})

    def test_aggregate_and_group(self):
        aggregated = self.engine.execute({
            'operation': 'aggregate',
            'model': 'res.partner',
            'domain': self._partner_domain(),
            'aggregations': [
                {'field': 'id', 'function': 'count', 'alias': 'partner_count'},
                {'field': 'color', 'function': 'sum', 'alias': 'color_sum'},
                {'field': 'color', 'function': 'avg', 'alias': 'color_avg'},
                {'field': 'color', 'function': 'min'},
                {'field': 'color', 'function': 'max'},
            ],
        })
        self.assertTrue(aggregated['ok'])
        self.assertEqual(aggregated['values']['partner_count'], 2)
        self.assertEqual(aggregated['values']['color_sum'], 10)
        self.assertEqual(aggregated['values']['color_avg'], 5)
        self.assertEqual(aggregated['values']['color_min'], 4)
        self.assertEqual(aggregated['values']['color_max'], 6)

        grouped = self.engine.execute({
            'operation': 'group_aggregate',
            'model': 'res.partner',
            'domain': self._partner_domain(),
            'groupby': ['is_company'],
            'aggregations': [
                {'field': 'id', 'function': 'count', 'alias': 'partner_count'},
            ],
            'order': [{'field': 'is_company', 'direction': 'asc'}],
        })
        self.assertTrue(grouped['ok'])
        self.assertEqual(grouped['group_count'], 2)
        self.assertEqual(
            [group['key']['is_company'] for group in grouped['groups']],
            [False, True],
        )
        self.assertTrue(all(group['values']['partner_count'] == 1 for group in grouped['groups']))

    def test_relationship_filter(self):
        country = self.env['res.country'].search([('code', '!=', False)], limit=1)
        self.company.country_id = country
        result = self.engine.execute({
            'operation': 'count',
            'model': 'res.partner',
            'filters': [{
                'field': 'country_id.code',
                'operator': '=',
                'value': country.code,
            }],
        })
        self.assertTrue(result['ok'])
        self.assertGreaterEqual(result['result'], 1)

    def test_invalid_plans_are_rejected(self):
        missing = self.engine.execute({'operation': 'count', 'model': 'aaq.not.registered'})
        self.assertFalse(missing['ok'])
        self.assertEqual(missing['error']['type'], 'validation')

        stale = self.env['setu.ai.schema.model'].create({
            'name': 'aaq.stale',
            'description': 'Stale',
            'model_kind': 'model',
        })
        stale.is_stale = True
        stale_result = self.engine.execute({'operation': 'count', 'model': 'aaq.stale'})
        self.assertEqual(stale_result['error']['type'], 'validation')

        abstract = self.env['setu.ai.schema.model'].create({
            'name': 'aaq.abstract',
            'description': 'Abstract',
            'model_kind': 'abstract',
        })
        abstract_result = self.engine.execute({'operation': 'count', 'model': abstract.name})
        self.assertIn('cannot be queried', abstract_result['error']['message'])

        rejected = [
            {'operation': 'unlink', 'model': 'res.partner'},
            {'operation': 'search', 'model': 'res.partner', 'fields': ['name'], 'values': {'name': 'x'}},
            {'operation': 'search', 'model': 'res.partner', 'fields': ['missing_field']},
            {'operation': 'search', 'model': 'res.partner', 'fields': ['name'], 'order': 'name;drop'},
            {
                'operation': 'aggregate',
                'model': 'res.partner',
                'aggregations': [{'field': 'name', 'function': 'sum'}],
            },
            {
                'operation': 'count',
                'model': 'res.partner',
                'filters': [{'field': 'name', 'operator': 'sql', 'value': 'select'}],
            },
        ]
        for query in rejected:
            result = self.engine.execute(query)
            self.assertFalse(result['ok'])
            self.assertEqual(result['error']['type'], 'validation')

    def test_user_without_schema_access_is_rejected(self):
        user = self.env['res.users'].create({
            'name': 'Aaq Query User',
            'login': 'aaq_query_user',
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        result = self.engine.with_user(user).execute({
            'operation': 'count',
            'model': 'res.partner',
        })
        self.assertFalse(result['ok'])
        self.assertEqual(result['error']['type'], 'access')
