from odoo import models, fields, api
from datetime import datetime

class Teacher(models.Model):
    _name = 'teacher'

    name = fields.Char(string='Teacher Name', required=True)
    employee_no = fields.Integer(string='Employee NO', required=True)
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone', required=True)