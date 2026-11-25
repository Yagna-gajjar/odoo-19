from odoo import models, fields

class SaleOrderLineSpecification(models.TransientModel):
    _name = 'sale.order.line.specification'

    order_line_id = fields.Many2one(comodel_name='sale.order.line', string='Sale Order Line')
    product_tmpl_id = fields.Many2one(string='Product Name', comodel_name='product.template')
    product_product_id = fields.Many2one(string='Product', comodel_name='product.product', domain="[('product_tmpl_id', '=', product_tmpl_id)]")
    specification_name = fields.Char(string='Specification Name')
    expect_limit = fields.Float(string='Expected Limit')
    reject_limit = fields.Float(string='Reject Limit')

