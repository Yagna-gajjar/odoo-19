from odoo import models, fields

class ProductVariantWizardLine(models.TransientModel):
    _name = 'product.variant.wizard.line'
    _description = 'Product Variant Wizard Attribute Line'

    wizard_id = fields.Many2one(
        'product.variant.wizard',
        required=True,
        ondelete='cascade'
    )

    attribute_line_id = fields.Many2one(
        'product.template.attribute.line',
        string='Attribute',
        required=True,
        readonly=True
    )

    value_id = fields.Many2one(
        'product.template.attribute.value',
        string='Attribute Value',
        domain="[('attribute_line_id', '=', attribute_line_id), ('ptav_active', '=', True)]"
    )