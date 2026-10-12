from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    urgent_order = fields.Boolean(string='Urgent Order')
    transfer = fields.Boolean(string='Transfer')
    invoicing = fields.Boolean(string='Invoicing')

    def button_confirm(self):
        res = super().button_confirm()
        if self.transfer or self.urgent_order or self.invoicing:
            self.create_activity()
        return res

    def create_activity(self):
        for order in self:
            company = order.picking_type_id.company_id
            warehouses = self.env['stock.warehouse'].search([('company_id', '=', company)])
            for warehouse in warehouses:
                for config in warehouse.order_configuration_ids:
                    if config.type_of_order == 'purchase' and config.urgent_order:
                        all_users = config.user_ids
                        for picking in order.picking_ids:
                            if config.operation_type == picking.picking_type_id:
                                for user in all_users:
                                    self.env['mail.activity'].create({
                                        'activity_type_id': config.type_of_activity.id,
                                        'res_model_id': self.env['ir.model']._get_id('stock.picking'),
                                        'res_id': picking.id,
                                        'user_id': user.id,
                                        'summary': 'Validate Receipt',
                                        'note': '<p>Please review this sale order transfer</p>',
                                    })