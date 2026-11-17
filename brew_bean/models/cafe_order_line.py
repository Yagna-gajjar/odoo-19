from odoo import models, fields, api

class CafeOrderLine(models.Model):
    _name = 'cafe.order.line'

    order_id = fields.Many2one(string='Order', comodel_name='cafe.order.line')
    menu_item_id = fields.Many2one(string='Menu Item', comodel_name='menu.item')
    quantity = fields.Integer(string='Quantity')
    price_unit = fields.Float(string='Price Unit')
    subtotal = fields.Float(string='Sub Total', compute='_compute_subtotal')

    @api.depends('menu_item_id', 'quantity')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.menu_item_id.price