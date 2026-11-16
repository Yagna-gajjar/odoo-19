from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        company = self.env['res.company'].search(domain=[
            ('company_registry', '=', 'REG030604')
        ], limit=2)
        res['company_id'] = company.id
        return res