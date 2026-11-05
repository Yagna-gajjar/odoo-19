from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    profit_margin = fields.Float(string='Profit Margin (%)', compute='_calculate_profit_margin_amount')
    profit_amount = fields.Float(string='Profit Amount', compute='_calculate_profit_margin_amount')

    @api.depends('profit_margin')
    def _calculate_profit_margin_amount(self):
        for rec in self:
            rec.profit_margin = (rec.list_price - rec.standard_price)*100/rec.list_price
            rec.profit_amount = rec.list_price - rec.standard_price