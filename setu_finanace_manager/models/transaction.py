from odoo import models, fields

class Transaction(models.Model):
    _name = 'transaction'
    _rec_name = 'title'

    title = fields.Char(string='Transaction Title')
    transaction_date = fields.Datetime(string='Transaction Date')
    account_id = fields.Many2one(string='Account', comodel_name='accounts')
    category_id = fields.Many2one(string='Category', comodel_name='category')
    category_type = fields.Selection(
        related='category_id.category_type',
        store=False
    )
    amount = fields.Float(string='Amount')
    remark = fields.Text(string='Remarks')

