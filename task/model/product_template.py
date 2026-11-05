from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def create_attribute(self):
        print(self)