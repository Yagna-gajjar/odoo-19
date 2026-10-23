from odoo import models, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    urgent_order = fields.Boolean(string='Urgent Order', compute='_compute_order_configs', default=False)
    transfer = fields.Boolean(string='Transfer', compute='_compute_order_configs', default=False)
    invoicing = fields.Boolean(string='Invoicing', compute='_compute_order_configs', default=False)
    is_invoiced = fields.Boolean(string='Is Invoiced', default=False)

    def _compute_order_configs(self):
        for record in self:
            record.urgent_order = False
            record.transfer = False
            record.invoicing = False
            if record.sale_id:
                record.urgent_order = record.sale_id.urgent_order
                record.transfer = record.sale_id.transfer
                record.invoicing = record.sale_id.invoicing

            if record.reference_ids:
                for ref in record.reference_ids:
                    if ref.purchase_ids:
                        record.urgent_order = ref.purchase_ids.urgent_order
                        record.transfer = ref.purchase_ids.transfer
                        record.invoicing = ref.purchase_ids.invoicing

    def button_validate(self):
        res = super().button_validate()
        for record in self:
            if record.urgent_order or record.transfer or record.invoicing:
                record.create_activity()
        return res

    def create_activity(self):
        for order in self:
            order_config = order.location_dest_id.warehouse_id.order_configuration_ids
            for config in order_config:
                if order.sale_id:
                    condition = config.transfer and config.sales_team == order.sale_id.team_id
                else:
                    condition = config.transfer
                if condition:
                    all_users = config.user_ids
                    pack_pickings = order.move_ids.mapped('move_dest_ids').mapped('picking_id')
                    for pack in pack_pickings:
                        if config.operation_type.id == pack.picking_type_id.id:
                            for user in all_users:
                                self.env['mail.activity'].create({
                                    'activity_type_id': config.type_of_activity.id,
                                    'res_model_id': self.env['ir.model']._get_id('stock.picking'),
                                    'res_id': pack.id,
                                    'user_id': user.id,
                                    'summary': 'Transfer',
                                    'note': '<p>Please review this urgent transfer</p>',
                                })