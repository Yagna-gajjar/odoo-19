from odoo import models, fields

class BusinessTripEmployee(models.Model):
    _name = 'business.trip.employee'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(string='Employee', comodel_name='hr.employee')
    trip_id = fields.Many2one(string='Trip', comodel_name='business.trip')
    personal_expense_total = fields.Monetary(string='Total Personal Expenses', currency_field='currency_id')
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency')