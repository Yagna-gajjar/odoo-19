from odoo import models, fields, api
from odoo.exceptions import ValidationError


class OrderConfiguration(models.Model):
    _name = 'order.configuration'

    type_of_order = fields.Selection(string='Type Of Order', selection=[('sales', 'Sales'), ('purchase', 'Purchase')], required='True')
    sales_team = fields.Many2one(string='Sales Team', comodel_name='crm.team')
    operation_type = fields.Many2one(string='Operation Type', comodel_name='stock.picking.type')
    user_ids = fields.Many2many(string='Users', comodel_name='res.users', required='True')
    type_of_activity = fields.Many2one(string='Activity', comodel_name='mail.activity.type', required='True')
    stock_warehouse_id = fields.Many2one(string='Stock Warehouse', comodel_name='stock.warehouse')
    urgent_order = fields.Boolean(string='Urgent Order')
    transfer = fields.Boolean(string='Transfer')
    invoicing = fields.Boolean(string='Invoicing')

    @api.onchange('type_of_order')
    def _change_sales_team(self):
        if self.type_of_order == 'purchase':
            self.sales_team = False

    @api.constrains('type_of_order', 'sales_team')
    def _constrain_sales_team(self):
        for record in self:
            if record.type_of_order != 'sales' and len(record.sales_team) > 0:
                raise ValidationError("can't choose sales teams for order type purchase")
