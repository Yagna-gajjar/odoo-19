from odoo import models, fields, Command
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_specification_id = fields.One2many(string='Product Specification', comodel_name='product.specification', inverse_name='product_tmpl_id')

    def update_sale_specification(self):
        product_spec = self.product_specification_id.filtered(lambda spec: spec.show_to_customer)
        sale_order_line = self.env['sale.order.line'].search([('state', '=', 'draft'), ('product_id', 'in', product_spec.product_product_id)])
        for order in sale_order_line:
            prod_for_sale_spec = product_spec.filtered(lambda spec: spec.product_product_id == order.product_id)
            order.specification_ids = [Command.clear()] + [
                Command.create({
                        'product_tmpl_id': spec.product_tmpl_id.id,
                        'product_product_id': spec.product_product_id.id,
                        'specification_name': spec.specification_name,
                        'expect_limit': spec.expect_limit,
                        'reject_limit': spec.reject_limit,
                    })
                for spec in prod_for_sale_spec
            ]

    def action_open_manual_variant_wizard(self):
        self.ensure_one()

        if not self.attribute_line_ids:
            raise UserError("Please configure product attributes first.")

        wizard = self.env['product.variant.wizard'].create({
            'product_tmpl_id': self.id,
            'line_ids': [
                Command.create({
                    'attribute_line_id': line.id
                })
                for line in self.attribute_line_ids
            ]
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Product Variant',
            'res_model': 'product.variant.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }
