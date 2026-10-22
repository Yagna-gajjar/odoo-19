from odoo import models, fields, api


class BusinessTripExpense(models.Model):
    _name = 'business.trip.expense'

    trip_id = fields.Many2one(string='Trip', comodel_name='business.trip')
    description = fields.Char(string='Description')
    expense_type = fields.Selection(selection=[('meals', 'Meals'), ('transport', 'Transport'), ('hotel', 'Hotel'),
                                               ('client_meeting', 'Client Meeting'), ('other', 'Other')])
    expense_date = fields.Date(string='Expense Date')
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    currency_id = fields.Many2one(string='Currency', comodel_name='res.currency')
    receipt_reference = fields.Char(string='Receipt Reference')

    state = fields.Selection(
        string='state',
        default='draft',
        selection=[('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected')])

    def change_expense_state(self):
        state = self.env.context.get('state')
        if state:
            self.state = state