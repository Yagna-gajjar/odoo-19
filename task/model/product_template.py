from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    profit_margin = fields.Float(string='Profit Margin (%)', compute='_calculate_margin')

    @api.depends('profit_margin')
    def _calculate_margin(self):
        for rec in self:
            rec.profit_margin = (rec.list_price - rec.standard_price)*100/rec.list_price