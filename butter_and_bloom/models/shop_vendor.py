from odoo import models, fields

class ShopVendor(models.Model):
    _name = 'shop.vendor'

    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Vendor')
    active = fields.Boolean(string='Active', default=True)