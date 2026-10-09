from odoo import models, fields

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    order_configuration_ids = fields.One2many(comodel_name='order.configuration', string='Order Configuration', inverse_name='stock_warehouse_id')