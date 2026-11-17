from odoo import models, fields


class MenuItem(models.Model):
    _name = 'menu.item'

    name = fields.Char(string='Name')
    price = fields.Float(string='Price')
    category = fields.Selection(string='Category',
                                selection=[('coffee', 'Coffee'), ('tea', 'Tea'), ('snacks', 'Snacks'),
                                           ('desserts', 'Desserts'), ('other', 'Other')])
    description = fields.Text(string='Description')
    available = fields.Boolean(string='Available')
    image = fields.Image(string='Image')