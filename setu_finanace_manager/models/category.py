from odoo import models, fields


class Category(models.Model):
    _name = 'category'

    name = fields.Char(string='Category Name')
    category_type = fields.Selection(string='Category Type', selection=([
        ('expense', 'Expense'),
        ('income', 'Income')
    ]))
    active = fields.Boolean(string='Active')