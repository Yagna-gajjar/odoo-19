from odoo import models, fields

class CreditRule(models.Model):
    _name = 'credit.rule'
    _rec_name = 'rule_name'
    _description = 'Credit Rule'

    rule_name = fields.Char(
        string='Define Rule',
        required=True
    )
    amount_from = fields.Float(
        string='Amount From',
        required=True
    )

    amount_to = fields.Float(
        string='Amount To'
    )

    credit_per = fields.Float(
        string='Credit %',
        required=True
    )