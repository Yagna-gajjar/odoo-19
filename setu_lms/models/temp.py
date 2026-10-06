from odoo import models, fields

class Temp(models):
    _name = 'temp'

    name = fields.Char(string='Name')
    res_