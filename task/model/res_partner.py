from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'
    credits = fields.Float(string="Credits")