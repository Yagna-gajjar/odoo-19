from odoo import models, fields, api


class Student(models.Model):
    _name = 'student'
    _description = 'Student'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Student Name', required=True)
    date_of_birth = fields.Date(string='Date Of Birth', required=True)
    gender = fields.Selection(
        selection=[('female', 'Female'), ('male', 'Male'), ('other', 'Other')],
        string="Gender",
    )
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone', required=True)

    _sql_constraints = [
        ('email_unique', 'unique(email)', 'A student with this email already exists.'),
    ]