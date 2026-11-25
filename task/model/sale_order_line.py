from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    specification_ids = fields.One2many(
        comodel_name='sale.order.line.specification',
        inverse_name='order_line_id',
        string='Specifications'
    )

    @api.onchange('product_id', 'product_uom_qty', 'product_uom_id', 'price_unit', 'tax_ids', 'price_subtotal')
    def action_copy_product_specification(self):
        for rec in self:
            product_specification = self.env['product.specification'].search([('product_product_id', '=', rec.product_id)])
            print(rec.id)

            new_sale_specification = self.env['sale.order.line.specification'].create(
                [{
                    'order_line_id': rec.id,
                    'product_tmpl_id': product_specification.product_tmpl_id,
                    'product_product_id': rec.product_id.id,
                    'specification_name': product_specification.specification_name,
                    'expect_limit': product_specification.expect_limit,
                    'reject_limit': product_specification.reject_limit
                }]
            )
            print(new_sale_specification)

    def action_show_specification(self):
        all_sale_spec = self.env['sale.order.line.specification'].search([])
        print(all_sale_spec)
        print(self.id)
        spec_rec = self.env['sale.order.line.specification'].search([('order_line_id', '=', self.id)])
        print(spec_rec)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Specification',
            'res_model': 'sale.order.line.specification',
            'view_mode': 'form',
            'res_id': spec_rec.id,
            'target': 'current',
        }
