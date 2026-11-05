from odoo import models, fields

class ShopVendor(models.Model):
    _name = 'shop.vendor'
    _rec_name = 'partner_id'

    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Vendor')
    active = fields.Boolean(string='Active', default=True)
    allowed_product_lines_ids = fields.Many2many(string='Products',
                                                 comodel_name='product.template',
                                                 inverse_name='allowed_vendor_id',
                                                 domain="[('company_id', '=', company_id), ('product_type', '=', 'raw')]"
                                                 )

    # display_name = fields.Char(string='Display Name')
    #
    # def _compute_display_name(self):
    #     for rec in self:
    #         rec.display_name = f"{rec.partner_id.name}/{rec.company_id.name}"
