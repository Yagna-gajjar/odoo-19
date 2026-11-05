from odoo import models, fields, api
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_type = fields.Selection(
        selection=[
            ('raw', 'Raw Material'),
            ('manufactured', 'Manufactured Product'),
            ('final', 'Final Product'),
        ],
        string='Bakery Product Type',
        required=True,
        default='raw',
    )

    profit_margin = fields.Float(string='Profit Margin (%)', compute='_calculate_profit_margin_amount')
    profit_amount = fields.Float(string='Profit Amount', compute='_calculate_profit_margin_amount')

    @api.depends('profit_margin')
    def _calculate_profit_margin_amount(self):
        for rec in self:
            rec.profit_margin = (rec.list_price - rec.standard_price)*100/rec.list_price
            rec.profit_amount = rec.list_price - rec.standard_price

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('product_type') in ('raw', 'manufacture'):
                if 'standard_price' in vals:
                    vals['list_price'] = vals['standard_price']

        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)

        if 'standard_price' in vals:
            for product in self:
                if product.product_type in ('raw', 'manufacture'):
                    product.list_price = product.standard_price

        return result

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        product_type = self.env.context.get('default_product_type')

        if product_type in ('raw', 'manufactured', 'final'):
            company = self.env['res.company'].search([
                ('company_registry', '=', 'REG030604')
            ], limit=2)

            if len(company) != 1:
                raise UserError(
                    "Company with registration number REG030604 "
                    "must exist exactly once and be accessible."
                )

            res['company_id'] = company.id

        return res