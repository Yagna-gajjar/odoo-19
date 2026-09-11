from odoo import models, fields


class SchoolClass(models.Model):
    _name = 'school.class'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True, tracking=True)
    code = fields.Char(string='Class Code', required=True)
    status = fields.Selection(
        [
            ('active', 'Active'),
            ('inactive', 'Inactive'),
        ],
        string='Status',
        default='active',
        required=True
    )
