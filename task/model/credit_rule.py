from odoo import models, fields

class CreditRule(models.Model):
    _name = 'credit.rule'
    _rec_name = 'rule_name'
    _description = 'Credit Rule'

    rule_name = fields.Char(
        string='Define Rule',
        required=True
    )
    min_amount = fields.Float(
        string='Min Amount',
        required=True
    )

    credit_per = fields.Float(
        string='Credit %',
        required=True
    )