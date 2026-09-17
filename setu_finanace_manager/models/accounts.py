from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Accounts(models.Model):
    _name = 'accounts'
    _rec_name = 'name'

    name = fields.Char(string='Account Name')
    account_type = fields.Char(string='Account Type')
    opening_balance = fields.Float(string='Opening Balance')
    current_balance = fields.Float(string='Current Balance', compute='_compute_current_balance')
    active = fields.Boolean(string='Active')
    transaction_ids = fields.One2many(string='Transaction', comodel_name='transaction', inverse_name='account_id')

    @api.onchange("opening_balance")
    def _check_opening_balance(self):
        print("_check_opening_balance called")
        if float(self.opening_balance) < 1000:
            raise ValidationError("Opening Balance needs to be more than 1000")

    @api.depends("opening_balance", "transaction_ids")
    def _compute_current_balance(self):
        print("_compute_current_balance called")
        for records in self:
            expense_amount = 0
            income_amount = 0
            for tran_records in records.transaction_ids:
                if tran_records.category_id.category_type == 'expense':
                    expense_amount += tran_records.amount
                elif tran_records.category_id.category_type == 'income':
                    income_amount += tran_records.amount

            records.current_balance = records.opening_balance - expense_amount + income_amount