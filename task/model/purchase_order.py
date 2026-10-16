from odoo import models, fields, api, Command
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    urgent_order = fields.Boolean(string='Urgent Order')
    transfer = fields.Boolean(string='Transfer')
    invoicing = fields.Boolean(string='Invoicing')

    allowed_vendors_products_id = fields.Many2one(comodel_name='vendor.allowed.products', string='Allowed Products')
    allowed_product_lines_ids = fields.One2many(comodel_name='product.quantity', related='allowed_vendors_products_id.allowed_product_lines_ids', string='Allowed product lines')

    @api.constrains('amount_untaxed')
    def _check_untaxed_amount_limit(self):
        if self.partner_id.purchase_capacity:
            if self.amount_untaxed > self.partner_id.purchase_capacity:
                raise ValidationError(f'Untaxed amount exceded limit of {self.partner_id.purchase_capacity}')

    @api.onchange('partner_id')
    def _compute_allowed_products(self):
        for record in self:
            record.allowed_vendors_products_id = False

            if not record.partner_id:
                continue

            allowed_products = self.env['vendor.allowed.products'].search([
                ('partner_ids', 'in', record.partner_id.id)
            ])

            if not allowed_products:
                continue

            allowed_product = allowed_products[0]
            record.allowed_vendors_products_id = allowed_product

            commands = [
                Command.create({
                    'product_id': line.product_id.id,
                    'product_qty': line.quantity,
                })
                for line in allowed_product.allowed_product_lines_ids
                if line.product_id
            ]

            record.order_line = commands

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