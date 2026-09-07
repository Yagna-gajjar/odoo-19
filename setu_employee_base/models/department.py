from odoo import models, fields, api


class Department(models.Model):
    _name = 'department'

    name = fields.Char(string="Department Name", required=True)
    employee_base_id = fields.One2many(comodel_name='employee.base', inverse_name='department_id', string="Employees")
    designation_id = fields.One2many(comodel_name='designation', inverse_name='department_id', string="Designation")