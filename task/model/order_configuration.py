from odoo import models, fields

class OrderConfiguration(models.Model):
    _name = 'order.configuration'

    type_of_order = fields.Selection(string='Type Of Order', selection=[('sales', 'Sales'), ('purchase', 'Purchase')])
    sales_team = fields.Many2one(string='Sales Team', comodel_name='crm.team')
    operation_type = fields.Many2one(string='Operation Type', comodel_name='stock.picking.type')
    user_ids = fields.Many2many(string='Users', comodel_name='res.users')
    type_of_activity = fields.Many2one(string='Activity', comodel_name='mail.activity.type')
    stock_warehouse_id = fields.Many2one(string='Stock Warehouse', comodel_name='stock.warehouse')