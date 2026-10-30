from odoo import models, fields, api


class BusinessTripEmployee(models.Model):
    _name = 'business.trip.employee'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(string='Employee', comodel_name='hr.employee')
    trip_id = fields.Many2one(string='Trip', comodel_name='business.trip')
    personal_expense_total = fields.Monetary(string='Total Personal Expenses', currency_field='currency_id', compute='_compute_personal_expense_total')
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency')

    @api.depends(
        'employee_id',
        'trip_id.expense_ids.share_employees_ids.amount',
        'trip_id.expense_ids.share_employees_ids.employee_ids',
    )
    def _compute_personal_expense_total(self):
        for trip_employee in self:
            total = 0.0

            if trip_employee.employee_id and trip_employee.trip_id:
                for expense in trip_employee.trip_id.expense_ids:
                    if expense.company_sponsored:
                        continue

                    for share in expense.share_employees_ids:
                        if trip_employee.employee_id in share.employee_ids:
                            total += share.amount / len(share.employee_ids)

            trip_employee.personal_expense_total = total