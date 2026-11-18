from odoo import models, fields


class CafeTable(models.Model):
    _name = 'cafe.table'

    name = fields.Char(string='Name', required=True)
    table_number = fields.Integer(string='Table Number', required=True)
    capacity = fields.Integer(string='Capacity', required=True)
    status = fields.Selection(
        selection=[('available', 'Available'), ('occupied', 'Occupied'), ('reserved', 'Reserved')], string='Status',
        required=True, default='available')
    active = fields.Boolean(string='Active', default=True)
