from odoo.fields import Command
from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    specification_ids = fields.One2many(
        comodel_name='sale.order.line.specification',
        inverse_name='order_line_id',
        string='Specifications'
    )

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.product_id:
                product_specifications = self.env['product.specification'].search(
                    [('product_product_id', '=', line.product_id.id), ('show_to_customer', '=', True)])
                line.specification_ids = [Command.clear()] + [
                    Command.create({
                        'product_tmpl_id': spec.product_tmpl_id.id,
                        'product_product_id': spec.product_product_id.id,
                        'specification_name': spec.specification_name,
                        'expect_limit': spec.expect_limit,
                        'reject_limit': spec.reject_limit,
                    })
                    for spec in product_specifications
                ]
        return lines

    def write(self, vals):
        result = super().write(vals)
        if 'product_id' in vals.keys():
            product_specifications = self.env['product.specification'].search(
                [('product_product_id', '=', vals['product_id']), ('show_to_customer', '=', True)])
            self.specification_ids = [Command.clear()] + [
                Command.create({
                    'product_tmpl_id': spec.product_tmpl_id.id,
                    'product_product_id': spec.product_product_id.id,
                    'specification_name': spec.specification_name,
                    'expect_limit': spec.expect_limit,
                    'reject_limit': spec.reject_limit,
                })
                for spec in product_specifications
            ]
        return result

    def action_show_specification(self):
        self.ensure_one()

        spec_rec = self.specification_ids
        if spec_rec:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Specification',
                'res_model': 'sale.order.line.specification',
                'view_mode': 'list',
                'views': [(self.env.ref('task.view_sale_order_line_spec_list').id, 'list')],
                'domain': [('id', 'in', spec_rec.ids)],
                'target': 'new',
            }
        return {
            'warning': {
                'title': 'Warning',
                'message': 'No specification for this order line',
            }
        }
