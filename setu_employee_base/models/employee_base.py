from odoo import models, fields, api
from datetime import datetime

class EmployeeBase(models.Model):
    _name = "employee.base"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, placeholder='Enter Your Name', tracking=True)
    salary = fields.Integer(string='Salary', required=True, tracking=True)
    bonus = fields.Float(string='Bonus', required=True, tracking=True)
    total_salary = fields.Float(compute="_total_salary", string='Total Salary')
    total_salary_1 = fields.Float(compute="_total_salary", string='Total Salary')
    final_salary = fields.Float(string='Final Salary')
    final_salary_1 = fields.Float(string='Final Salary')
    is_active = fields.Boolean(string='Active', required=True, tracking=True)
    joining_date = fields.Datetime(string='Joining Date', required=True, default=datetime.now(), tracking=True)
    profile = fields.Image(string='Profile Picture')
    department_id = fields.Many2one(comodel_name='department', string="Department", required=True, tracking=True)
    designation_id = fields.Many2one(comodel_name='designation', string="Designation", required=True, tracking=True)

    @api.depends('bonus', 'salary')
    def _total_salary(self):
        for record in self:
            record.total_salary = record.salary * (1 + (record.bonus/100))
            record.total_salary_1 = record.salary * (1 + (record.bonus/100))

    @api.onchange('bonus', 'salary')
    def _final_salary(self):
        self.final_salary = self.salary * (1 + (self.bonus/100))
        self.final_salary_1 = self.salary * (1 + (self.bonus/100))
        return {'warning': {'title': "Hello", 'message': "Hello New employee"}}