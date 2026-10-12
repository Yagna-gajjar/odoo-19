from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'
    urgent_order = fields.Boolean(string='Urgent Order', compute='_compute_order_configs')
    transfer = fields.Boolean(string='Transfer', compute='_compute_order_configs')
    invoicing = fields.Boolean(string='Invoicing', compute='_compute_order_configs')

    def _compute_order_configs(self):
        for record in self:
            print(record)
            record.urgent_order = record.sale_id.urgent_order
            record.transfer = record.sale_id.transfer
            record.invoicing = record.sale_id.invoicing
