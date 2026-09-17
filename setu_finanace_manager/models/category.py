from odoo import models, fields


class Category(models.Model):
    _name = 'category'
    _rec_name = 'name'

    name = fields.Char(string='Category Name')
    category_type = fields.Selection(string='Category Type', selection=([
        ('expense', 'Expense'),
        ('income', 'Income')
    ]))
    active = fields.Boolean(string='Active')