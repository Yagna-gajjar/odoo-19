from odoo import models, fields

class ProductSpecification(models.Model):
    _name = 'product.specification'

    product_tmpl_id = fields.Many2one(string='Product Name', comodel_name='product.template')
    product_product_id = fields.Many2one(string='Product', comodel_name='product.product', domain="[('product_tmpl_id', '=', product_tmpl_id)]")
    specification_name = fields.Char(string='Specification Name')
    expect_limit = fields.Float(string='Expected Limit')
    reject_limit = fields.Float(string='Reject Limit')
    show_to_customer = fields.Boolean(string='Show to Customer')
