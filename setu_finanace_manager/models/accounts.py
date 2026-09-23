from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Accounts(models.Model):
    _name = 'accounts'
    _rec_name = 'name'

    name = fields.Char(string='Account Name', required=True)
    account_type = fields.Char(string='Account Type', required=True)
    opening_balance = fields.Float(string='Opening Balance', required=True)
    current_balance = fields.Float(string='Current Balance', compute='_compute_current_balance')
    active = fields.Boolean(string='Active', required=True)
    transaction_ids = fields.One2many(string='Transaction', comodel_name='transaction', inverse_name='account_id')

    _account_name_unique = models.Constraint(
        'unique(name)',
        'You cannot repeat account name'
    )
    _check_opening_balance = models.Constraint(
        'CHECK(opening_balance >= 1000)',
        'Minimum balance should be 1000'
    )

    @api.depends("opening_balance", "transaction_ids")
    def _compute_current_balance(self):
        for records in self:
            expense_amount = 0
            income_amount = 0
            for tran_records in records.transaction_ids:
                if tran_records.category_id.category_type == 'expense':
                    expense_amount += tran_records.amount
                elif tran_records.category_id.category_type == 'income':
                    income_amount += tran_records.amount

            records.current_balance = records.opening_balance - expense_amount + income_amount