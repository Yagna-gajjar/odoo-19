from odoo import models, fields

class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    company_id = fields.Many2one(comodel_name='res.partner', string='Company')