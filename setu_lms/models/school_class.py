from odoo import models, fields


class SchoolClass(models.Model):
    _name = 'school.class'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True, tracking=True)
    code = fields.Char(string='Class Code', required=True)
    active = fields.Boolean(string='Active', default=True)
