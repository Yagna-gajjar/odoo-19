from odoo import models, fields

class BusinessTrip(models.Model):
    _name = 'business.trip'

    name = fields.Char(string='Name')
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee')
    manager_id = fields.Many2one(comodel_name='hr.employee', string='Manager')
    destination = fields.Char(string='Destination')
    purpose = fields.Text(string='Purpose')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    budget = fields.Monetary(string='Budget', currency_field='currency_id')
    expense_ids = fields.One2many(string='Expenses', comodel_name='business.trip.expense', inverse_name='trip_id')
    total_expenses = fields.Monetary(string='Total Amount', currency_field='currency_id')
    currency_id = fields.Many2one(string='Currency', comodel_name='res.currency')
    state = fields.Selection(selection=[('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('in_progress', 'In Progress'), ('completed', 'Completed')])