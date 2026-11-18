from odoo import models, fields

class MenuItem(models.Model):
    _name = 'menu.item'

    name = fields.Char(string='Name', required=True)
    price = fields.Float(string='Price', required=True)
    category = fields.Selection(string='Category',
                                selection=[('coffee', 'Coffee'), ('tea', 'Tea'), ('snacks', 'Snacks'),
                                           ('desserts', 'Desserts'), ('other', 'Other')], required=True)
    description = fields.Text(string='Description')
    available = fields.Boolean(default=True)
    image = fields.Image(string='Image')