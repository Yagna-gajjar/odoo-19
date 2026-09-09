from odoo import models, fields

class Subject(models.Model):
    _name = 'subject'

    name = fields.Char(string='Subject Name', required=True)
    code = fields.Char(string='Subject Code', required=True)
    description = fields.Text(string='Description')