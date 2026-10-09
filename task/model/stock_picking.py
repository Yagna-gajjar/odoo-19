from odoo import models, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    urgent_order = fields.Boolean(string='Urgent Order')
    transfer = fields.Boolean(string='Transfer')
    invoicing = fields.Boolean(string='Invoicing')