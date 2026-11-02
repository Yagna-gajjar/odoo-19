from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_coffee_ingredient = fields.Boolean(
        string='Coffee Ingredient',
        default=False,
    )