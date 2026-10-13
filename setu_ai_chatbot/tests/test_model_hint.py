from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

from odoo.addons.setu_ai_chatbot.models.model_hint import TfidfBinaryRelevance, trained_classifier
from odoo.addons.setu_ai_chatbot.models.model_hint_examples import EXAMPLES


@tagged('post_install', '-at_install', 'setu_ai_model_hint')
class TestModelHint(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hint = cls.env['setu.ai.model.hint']
        cls.retrieval = cls.env['setu.ai.schema.retrieval']
        cls._ensure('res.partner', 'Contact')
        cls._ensure('sale.order', 'Sales Order')

    @classmethod
    def _ensure(cls, name, description):
        record = cls.env['setu.ai.schema.model'].search([('name', '=', name)], limit=1)
        if record:
            return record
        return cls.env['setu.ai.schema.model'].create({
            'name': name,
            'description': description,
            'module': 'xqz',
            'model_kind': 'model',
            'table_name': name.replace('.', '_'),
        })

    def test_classifier_ranks_multiple_models_and_rejects_unknown_questions(self):
        classifier = TfidfBinaryRelevance().fit(EXAMPLES)
        ranked = classifier.predict('Which customers have the highest sales?')
        names = [item['model'] for item in ranked]
        self.assertIn('res.partner', names)
        self.assertIn('sale.order', names)
        self.assertGreaterEqual(ranked[0]['score'], ranked[-1]['score'])
        self.assertEqual(classifier.predict('zzzz quantum weather'), [])
        again = trained_classifier()
        self.assertIs(trained_classifier(), again)

    def test_predictions_come_from_the_registry(self):
        ranked = self.hint.predict_models('Which customers have the highest sales?')
        names = [item['model'] for item in ranked]
        self.assertIn('res.partner', names)
        self.assertIn('sale.order', names)
        for item in ranked:
            self.assertGreater(item['score'], 0)
            self.assertLessEqual(item['score'], 1)

        stale = self._ensure('sale.order', 'Sales Order')
        stale.is_stale = True
        without_sales = [item['model'] for item in self.hint.predict_models(
            'Which customers have the highest sales?',
        )]
        self.assertNotIn('sale.order', without_sales)
        self.assertEqual(self.hint.predict_models(''), [])
        self.assertEqual(self.hint.predict_models('zzzz quantum weather'), [])

    def test_retrieval_keeps_user_hints_and_model_limit(self):
        result = self.retrieval.retrieve(
            question='Which customers have the highest sales?',
            model_hints=['res.partner'],
            relationship_depth=0,
            limit_models=2,
        )
        self.assertEqual(result['model_hints'][0], 'res.partner')
        self.assertIn('sale.order', result['model_hints'])
        self.assertLessEqual(len(result['models']), 2)
        self.assertEqual(result['limits']['models'], 2)

        user = self.env['res.users'].create({
            'name': 'Aaq Hint User',
            'login': 'aaq_hint_user',
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        with self.assertRaises(AccessError):
            self.hint.with_user(user).predict_models('Which customers have the highest sales?')
