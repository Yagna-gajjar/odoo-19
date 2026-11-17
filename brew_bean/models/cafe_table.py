from odoo import models, fields

class CafeTable(models.Model):
    _name = 'cafe.table'

    name = fields.Char(string='Name')
    table_number = fields.Integer(string='Table Number')
    capacity = fields.Integer(string='Capacity')
    status = fields.Selection(
        selection=[('available', 'Available'), ('occupied', 'Occupied'), ('reserved', 'Reserved')], string='Status')
    active = fields.Boolean(string='Active')