from odoo import models, fields, api

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    product_id = fields.Many2one(
        comodel_name='product.product',
        domain="[('company_id.company_registry', '=', 'REG030604')]"
    )

    total_quantity = fields.Float(
        string='Total Quantity',
        compute='_compute_total_quantity',
        digits=(16, 4)
    )

    @api.depends('product_id')
    def _compute_total_quantity(self):
        for record in self:
            record.total_quantity = record.product_qty * record.product_uom_id.relative_factor