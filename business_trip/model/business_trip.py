from odoo import models, fields, api

class BusinessTrip(models.Model):
    _name = 'business.trip'

    name = fields.Char(string='Name')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employee')
    trip_employee_ids = fields.One2many(comodel_name='business.trip.employee', inverse_name='trip_id')
    manager_id = fields.Many2one(comodel_name='hr.employee', string='Manager', domain="[('id', 'in', employee_ids)]")
    destination = fields.Char(string='Destination')
    purpose = fields.Text(string='Purpose')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    budget_per_person = fields.Monetary(string='Budget Per Person', currency_field='currency_id')
    total_budget = fields.Monetary(string='Total Budget', currency_field='currency_id', compute='_calculate_total_budget')
    expense_ids = fields.One2many(string='Expenses', comodel_name='business.trip.expense', inverse_name='trip_id')
    total_expenses = fields.Monetary(string='Total Amount', currency_field='currency_id', compute='_calculate_total_expenses')
    remaining_amount = fields.Monetary(string='Remaining Amount', currency_field='currency_id', compute='_calculate_total_expenses')
    currency_id = fields.Many2one(string='Currency', comodel_name='res.currency')
    state = fields.Selection(string='State', default='draft',
                             selection=[('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'),
                                        ('in_progress', 'In Progress'), ('completed', 'Completed'),
                                        ('cancelled', 'Cancelled')])
    number_of_employee = fields.Integer(string='Total Employee', compute='_calculate_employee')

    @api.depends('trip_employee_ids')
    def _calculate_employee(self):
        for rec in self:
            rec.number_of_employee = len(rec.trip_employee_ids)

    @api.depends('budget_per_person', 'employee_ids')
    def _calculate_total_budget(self):
        for rec in self:
            rec.total_budget = len(rec.employee_ids) * rec.budget_per_person

    def change_state(self):
        state = self.env.context.get('state')
        if state:
            self.state = state

    @api.depends('total_expenses')
    def _calculate_total_expenses(self):
        for rec in self:
            rec.total_expenses = sum(
                rec.expense_ids.mapped('amount')
            )
            rec.remaining_amount = rec.total_budget - rec.total_expenses

    @api.onchange('employee_ids')
    def _create_trip_employee(self):
        self.trip_employee_ids = [(5, 0, 0)] + [
            (0, 0, {
                'employee_id': employee.id,
            })
            for employee in self.employee_ids
        ]