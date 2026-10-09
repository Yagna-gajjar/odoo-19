from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = ["sale.order",'mail.thread', 'mail.activity.mixin']
    credit_per = fields.Float(string='Credit (%)')
    credit_amount = fields.Float(string='Credit Amount')


    urgent_order = fields.Boolean(string='Urgent Order')
    transfer = fields.Boolean(string='Transfer')
    invoicing = fields.Boolean(string='Invoicing')

    def get_credit_per(self):
        self.ensure_one()
        self.credit_per = 1
        credit_rules = self.env['credit.rule'].search([])
        for rules in credit_rules:
            if self.amount_total >= rules['min_amount']:
                self.credit_per = rules['credit_per']
        self.credit_amount = (self.credit_per * self.amount_total) / 100

    def write(self, vals):
        res = super().write(vals)
        if 'order_line' in vals:
            for order in self:
                partner = self.partner_id
                temp_credit = partner.credits - self.credit_amount
                self.get_credit_per()
                final_credit = temp_credit + self.credit_amount

                partner.write({
                    'credits': final_credit
                })
        return res

    def action_confirm(self):
        res = super().action_confirm()
        partner = self.partner_id
        if partner:
            total_credit = partner.credits
            self.get_credit_per()
            self.credit_amount = (self.credit_per * self.amount_total) / 100
            total_credit += self.credit_amount
            partner.write({
                'credits': total_credit
            })
            if self.urgent_order:
                self.create_activity()
        return res

    def action_cancel(self):
        res = super().action_cancel()

        partner = self.partner_id
        if partner and self.credit_amount and self.credit_per:
            total_credit = partner.credits
            total_credit -= self.credit_amount

            partner.write({
                'credits': total_credit
            })

        return res

    def create_activity(self):
        for order in self:
            order_config = self.warehouse_id.order_configuration_ids
            for config in order_config:
                if config.type_of_order == 'sales':
                    all_users = config.user_ids
                    for picking in order.picking_ids:
                        if config.operation_type == picking.picking_type_id and order.urgent_order:
                            for user in all_users:
                                self.env['mail.activity'].create({
                                    'activity_type_id': config.type_of_activity.id,
                                    'res_model_id': self.env['ir.model']._get_id('stock.picking'),
                                    'res_id': picking.id,
                                    'user_id': user.id,
                                    'summary': 'Urgent Order',
                                    'note': '<p>Please review this urgent sale order</p>',
                                })