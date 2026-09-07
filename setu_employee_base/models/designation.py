from odoo import models, fields


class Designation(models.Model):
    _name = 'designation'
    name = fields.Char(string="Designation Name", required=True)
    department_id = fields.Many2one(comodel_name='department', string="Department", required=True)
    employee_base_id = fields.One2many(comodel_name='employee.base', inverse_name='designation_id', string="Employees")
