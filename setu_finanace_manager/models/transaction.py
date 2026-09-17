from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Transaction(models.Model):
    _name = 'transaction'
    _rec_name = 'title'

    title = fields.Char(string='Transaction Title', required=True)
    transaction_date = fields.Datetime(string='Transaction Date', required=True)
    account_id = fields.Many2one(string='Account', comodel_name='accounts', required=True)
    category_id = fields.Many2one(string='Category', comodel_name='category', required=True)
    category_type = fields.Selection(
        related='category_id.category_type',
        store=False
    )
    amount = fields.Float(string='Amount', required=True)
    remark = fields.Text(string='Remarks')


    @api.constrains('account_id', 'category_id', 'amount')
    def _check_account_balance(self):
        for record in self:
            account = record.account_id

            if not account:
                continue

            if record.category_id.category_type == 'expense':
                new_balance = account.current_balance - record.amount
            else:
                new_balance = account.current_balance + record.amount

            if new_balance < 0:
                raise ValidationError(
                    "You don't have enough money in this account."
                )