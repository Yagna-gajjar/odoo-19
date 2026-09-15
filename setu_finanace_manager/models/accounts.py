from odoo import models, fields, api


class Accounts(models.Model):
    _name = 'accounts'

    name = fields.Char(string='Account Name')
    account_type = fields.Char(string='Account Type')
    opening_balance = fields.Float(string='Opening Balance')
    current_balance = fields.Float(string='Current Balance', compute='_compute_current_balance')
    active = fields.Boolean(string='Active')
    transaction_id = fields.One2many(string='Transaction', comodel_name='transaction', inverse_name='account_id')

    @api.depends('transaction_id')
    def _compute_current_balance(self):
        for records in self:
            expense_amount = 0
            income_amount = 0
            for tran_records in records.transaction_id:
                if tran_records.category_id.category_type == 'expense':
                    expense_amount += tran_records.amount
                elif tran_records.category_id.category_type == 'income':
                    income_amount += tran_records.amount

            records.current_balance = records.opening_balance - expense_amount + income_amount
