from odoo import models, fields, api

class CafeOrder(models.Model):
    _name = 'cafe.order'

    name = fields.Char(string='Name')
    table_id = fields.Many2one(string='Table', comodel_name='cafe.table')
    order_line_ids = fields.One2many(string='Orders', comodel_name='cafe.order.line', inverse_name='order_id')
    order_date = fields.Datetime(string='Order Date')
    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('served', 'Served'),
        ('cancelled', 'Cancelled')
    ])
    total_amount = fields.Float(string='Total Amount', compute='_calculate_total_amount')

    @api.depends('order_line_ids.subtotal')
    def _calculate_total_amount(self):
        for rec in self:
            total_amount = 0
            for order in rec.order_line_ids:
                total_amount += order.subtotal
            rec.total_amount = total_amount
