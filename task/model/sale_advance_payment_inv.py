from odoo import models

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _create_invoices(self, sale_orders):
        res = super()._create_invoices(sale_orders)
        if sale_orders.invoicing:
            summary = 'Validate Invoice',
            note = '<p>Please review this sale order invoice</p>'
            self.create_activity(sale_orders, self.env['ir.model']._get_id('account.move'), summary, note)
        return res

    def create_activity(self, sale_orders, model, summary, note):
        for order in sale_orders:
            order_config = order.warehouse_id.order_configuration_ids
            for config in order_config:
                if config.type_of_order == 'sales' and config.invoicing:
                    all_users = config.user_ids
                    for invoice in order.invoice_ids:
                        for user in all_users:
                            self.env['mail.activity'].create({
                                'activity_type_id': config.type_of_activity.id,
                                'res_model_id': model,
                                'res_id': invoice.id,
                                'user_id': user.id,
                                'summary': summary,
                                'note': note,
                                })