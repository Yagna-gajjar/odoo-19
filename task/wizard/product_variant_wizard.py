from odoo import models, fields, api, Command
from odoo.exceptions import UserError

class ProductVariantWizard(models.TransientModel):
    _name = 'product.variant.wizard'
    _description = 'Manual Product Variant Creation'

    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product',
        required=True,
        readonly=True
    )

    line_ids = fields.One2many(
        'product.variant.wizard.line',
        'wizard_id',
        string='Attributes'
    )

    def action_create_variant(self):
        self.ensure_one()

        template = self.product_tmpl_id
        attribute_lines = template.valid_product_template_attribute_line_ids

        if not template.has_dynamic_attributes():
            raise UserError(
                "At least one attribute must use Dynamic variant creation."
            )

        selected_values = self.line_ids.mapped('value_id')

        if len(self.line_ids) != len(attribute_lines):
            raise UserError("The attribute configuration has changed. Reopen the wizard.")

        for attribute_line in attribute_lines:
            wizard_line = self.line_ids.filtered(
                lambda line: line.attribute_line_id == attribute_line
            )

            if len(wizard_line) != 1 or not wizard_line.value_id:
                raise UserError(
                    "Please select a value for every attribute."
                )

            if wizard_line.value_id.attribute_line_id != attribute_line:
                raise UserError(
                    "Selected value does not belong to the correct attribute."
                )

        variant = template._create_product_variant(selected_values)

        if not variant:
            raise UserError(
                "This combination is not valid or cannot be created."
            )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Variant',
            'res_model': 'product.product',
            'view_mode': 'form',
            'res_id': variant.id,
            'target': 'current',
        }