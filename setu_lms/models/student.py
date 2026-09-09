from odoo import models, fields, api
from datetime import datetime


class Student(models.Model):
    _name = 'student'

    name = fields.Char(string='Student Name', required=True)
    roll_number = fields.Integer(string="Roll Number", required=True)
    date_of_birth = fields.Datetime(string='Date Of Birth', required=True, default=datetime.now())
    gender = fields.Selection(selection=[('female', 'Female'), ('male', 'Male'), ('other', 'Other')], string="Gender")
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone', required=True)