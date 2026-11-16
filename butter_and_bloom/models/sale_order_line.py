from odoo import models, fields

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_template_id = fields.Many2one('product.template', domain=[('company_id.company_registry', '=', 'REG030604'), ('sale_ok', '=', True)])