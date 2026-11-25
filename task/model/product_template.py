from odoo import models, fields, Command
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_specification_id = fields.One2many(string='Product Specification', comodel_name='product.specification', inverse_name='product_tmpl_id')

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
