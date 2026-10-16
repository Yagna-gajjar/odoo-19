from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VendorAllowedProducts(models.Model):
    _name = 'vendor.allowed.products'
    _description = 'Vendor Allowed Products'

    name = fields.Char(string='Name', required=True)
    partner_ids = fields.Many2many(string='Vendors', comodel_name='res.partner', required=True)
    allowed_product_lines_ids = fields.One2many(string='Products', comodel_name='product.quantity', inverse_name='allowed_vendors_products_id')

    @api.constrains('allowed_product_lines_ids')
    def _check_allowed_product_lines_ids(self):
        new_product = self.allowed_product_lines_ids.product_id
        data = self.env['vendor.allowed.products'].search([('id', '!=', self.id)])

        allowed_products = data.allowed_product_lines_ids
        for product_quantity in allowed_products:
            if new_product == product_quantity.product_id:
                raise ValidationError(f'{new_product.name} already exist')

    @api.constrains('partner_ids')
    def _check_partner_ids(self):
        new_vendor = self.partner_ids
        data = self.env['vendor.allowed.products'].search([('id', '!=', self.id)])

        all_vendors = data.partner_ids
        for partner in all_vendors:
            if new_vendor == partner:
                raise ValidationError(f'{new_vendor.name} already exist')