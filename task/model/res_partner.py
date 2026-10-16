from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    credits = fields.Float(string="Credits")
    purchase_capacity = fields.Float(string="Purchase Capacity")
    tax_configuration_ids = fields.One2many(comodel_name='tax.configuration', string='Tax Configuration', inverse_name='partner_id')