from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'setu_ai_schema')
class TestSchemaRetrieval(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.retrieval = cls.env['setu.ai.schema.retrieval']
        cls.customer = cls._create_model('aaqcustomer', 'Aaq Customer Record', 'aaq_customer')
        cls.order = cls._create_model('aaqorder', 'Aaq Order', 'aaq_order')
        cls.country = cls._create_model('aaqcountry', 'Aaq Country', 'aaq_country')
        cls.line = cls._create_model('aaqline', 'Aaq Order Line', 'aaq_line')
        cls.card = cls._create_model('aaqcard', 'Violetbuyer', 'aaq_card')
        cls.archived = cls._create_model(
            'aaqarchived', 'Aaq Archived', 'aaq_archived', stale=True,
        )
        cls._create_field(cls.customer, 'aaqmail', 'Aaq Mail', 'char', help_text='Aaq mail address')
        cls._create_field(cls.customer, 'name', 'Name', 'char', store=True)
        cls._create_field(
            cls.customer, 'country_id', 'Country', 'many2one', relation='aaqcountry',
        )
        cls._create_field(cls.customer, 'note', 'Notes', 'text')
        cls._create_field(cls.customer, 'phone', 'Phone', 'char')
        cls._create_field(cls.customer, 'old_code', 'Old Code', 'char', stale=True)
        cls._create_field(
            cls.order, 'customer_id', 'Customer', 'many2one', relation='aaqcustomer',
        )
        cls._create_field(
            cls.order, 'missing_id', 'Missing', 'many2one', relation='aaqabsent',
        )
        cls._create_field(
            cls.line, 'order_id', 'Order', 'many2one', relation='aaqorder',
        )

    @classmethod
    def _create_model(cls, name, description, table_name, stale=False):
        return cls.env['setu.ai.schema.model'].create({
            'name': name,
            'description': description,
            'module': 'xqz',
            'model_kind': 'model',
            'table_name': table_name,
            'is_stale': stale,
        })

    @classmethod
    def _create_field(cls, schema_model, name, label, field_type, relation=False,
                      help_text=False, store=True, stale=False):
        return cls.env['setu.ai.schema.field'].create({
            'schema_model_id': schema_model.id,
            'name': name,
            'field_label': label,
            'field_type': field_type,
            'relation': relation,
            'help': help_text,
            'store': store,
            'is_stale': stale,
        })

    def _names(self, result):
        return [model['name'] for model in result['models']]

    def test_exact_and_partial_technical_name(self):
        exact = self.retrieval.lookup_models('aaqcustomer', relationship_depth=0)
        self.assertEqual(self._names(exact), ['aaqcustomer'])
        self.assertIn('technical_name', exact['models'][0]['match']['reasons'])

        partial = self.retrieval.lookup_models('aaqcust', relationship_depth=0, limit_models=5)
        self.assertEqual(partial['models'][0]['name'], 'aaqcustomer')
        self.assertIn('partial_name', partial['models'][0]['match']['reasons'])

    def test_field_name_and_description_lookup(self):
        by_field = self.retrieval.lookup_models('aaqmail', relationship_depth=0)
        self.assertEqual(self._names(by_field), ['aaqcustomer'])
        self.assertEqual(by_field['models'][0]['fields'][0]['name'], 'aaqmail')
        self.assertEqual(by_field['models'][0]['fields'][0]['type'], 'char')
        self.assertEqual(by_field['models'][0]['fields'][0]['description'], 'Aaq mail address')

        by_description = self.retrieval.lookup_models('violetbuyer', relationship_depth=0)
        self.assertEqual(self._names(by_description), ['aaqcard'])
        self.assertIn('description', by_description['models'][0]['match']['reasons'])

    def test_question_keywords_and_model_hint(self):
        result = self.retrieval.retrieve(
            question='show aaqmail',
            model_hints=['aaqcustomer', 'aaqcustomer'],
            relationship_depth=0,
        )
        self.assertEqual(result['models'][0]['name'], 'aaqcustomer')
        self.assertEqual(self._names(result).count('aaqcustomer'), 1)
        self.assertIn('hint', result['models'][0]['match']['reasons'])
        self.assertTrue(any(field['name'] == 'aaqmail' for field in result['models'][0]['fields']))

    def test_empty_question_and_unknown_hint(self):
        empty = self.retrieval.retrieve(question='   ')
        self.assertEqual(empty['models'], [])
        self.assertEqual(empty['keywords'], [])
        self.assertEqual(empty['unknown_hints'], [])

        unknown = self.retrieval.retrieve(
            question='',
            model_hints=['aaqmissingmodel', 'aaqcustomer'],
            relationship_depth=0,
        )
        self.assertEqual(unknown['unknown_hints'], ['aaqmissingmodel'])
        self.assertEqual(self._names(unknown), ['aaqcustomer'])

        only_unknown = self.retrieval.retrieve(model_hints='aaqdoesnotexist')
        self.assertEqual(only_unknown['models'], [])
        self.assertEqual(only_unknown['unknown_hints'], ['aaqdoesnotexist'])

    def test_relationship_depth_and_missing_target(self):
        depth_one = self.retrieval.retrieve(
            question='aaqline',
            relationship_depth=1,
            limit_models=10,
            limit_fields=10,
        )
        self.assertEqual(self._names(depth_one), ['aaqline', 'aaqorder'])
        order = depth_one['models'][1]
        self.assertEqual(order['match']['role'], 'related')
        relations = {item['field']: item for item in order['relationships']}
        self.assertTrue(relations['customer_id']['related_model'] == 'aaqcustomer')
        self.assertFalse(relations['customer_id']['included'])
        self.assertFalse(relations['customer_id']['missing'])
        self.assertTrue(relations['missing_id']['missing'])
        self.assertFalse(relations['missing_id']['included'])

        depth_two = self.retrieval.retrieve(
            question='aaqline',
            relationship_depth=2,
            limit_models=10,
            limit_fields=10,
        )
        self.assertEqual(self._names(depth_two)[:3], ['aaqline', 'aaqorder', 'aaqcustomer'])
        self.assertNotIn('aaqcountry', self._names(depth_two))

        depth_zero = self.retrieval.retrieve(
            question='aaqline',
            relationship_depth=0,
            limit_models=10,
        )
        self.assertEqual(self._names(depth_zero), ['aaqline'])
        self.assertEqual(depth_zero['models'][0]['relationships'][0]['related_model'], 'aaqorder')

    def test_limits_skip_stale_metadata_and_non_admin(self):
        limited = self.retrieval.retrieve(
            question='aaqmail',
            limit_models=1,
            limit_fields=2,
            relationship_depth=2,
        )
        self.assertEqual(self._names(limited), ['aaqcustomer'])
        self.assertEqual(
            [field['name'] for field in limited['models'][0]['fields']],
            ['aaqmail', 'country_id'],
        )
        self.assertNotIn('old_code', [field['name'] for field in limited['models'][0]['fields']])

        stale = self.retrieval.retrieve(question='aaqarchived', relationship_depth=0)
        self.assertNotIn('aaqarchived', self._names(stale))

        user = self.env['res.users'].create({
            'name': 'Aaq Retrieval User',
            'login': 'aaq_retrieval_user',
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        with self.assertRaises(AccessError):
            self.retrieval.with_user(user).retrieve(question='aaqcustomer')

    def test_config_parameter_limits(self):
        params = self.env['ir.config_parameter']
        params.set_param(self.retrieval._PARAM_MODEL_LIMIT, '1')
        params.set_param(self.retrieval._PARAM_FIELD_LIMIT, '1')
        params.set_param(self.retrieval._PARAM_RELATIONSHIP_DEPTH, '0')
        self.addCleanup(self.env.registry.clear_cache)
        result = self.retrieval.retrieve(question='aaq')
        self.assertEqual(result['limits'], {
            'models': 1,
            'fields': 1,
            'relationship_depth': 0,
        })
        self.assertEqual(len(result['models']), 1)
        self.assertEqual(len(result['models'][0]['fields']), 1)
