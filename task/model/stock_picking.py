from odoo import models, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()
        for record in self:
            if record.sale_id.transfer and record.sale_id.warehouse_id.delivery_steps == 'pick_pack_ship':
                self.create_activity()

    def create_activity(self):
        pack_picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'pack'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        for order in self:
            order_config = order.sale_id.warehouse_id.order_configuration_ids
            for config in order_config:
                if config.type_of_order == 'sales' and config.transfer:
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