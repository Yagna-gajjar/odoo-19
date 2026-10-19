from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductQuantity(models.Model):
    _name = 'product.quantity'

    product_id = fields.Many2one(comodel_name='product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    allowed_vendors_products_id = fields.Many2one(comodel_name='vendor.allowed.products', string='Allowed Vendors Products')

    @api.constrains('quantity')
    def _check_quantity(self):
        if self.quantity <= 0:
            raise ValidationError('Quantity Cannot be negative or Zero')