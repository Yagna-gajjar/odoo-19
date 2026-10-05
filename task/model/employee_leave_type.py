from odoo import models, fields

class EmployeeLeaveType(models.Model):
    _name = "employee.leave.type"

    name = fields.Char(string='Name')
    code = fields.Char(string='code')
    max_days = fields.Char(string='Max Days')
    requires_approval = fields.Boolean(string='Requires Approval')
