from odoo import models, fields


class Category(models.Model):
    _name = 'category'
    _rec_name = 'name'

    name = fields.Char(string='Category Name', required=True)
    category_type = fields.Selection(string='Category Type', selection=([
        ('expense', 'Expense'),
        ('income', 'Income')
    ]), required=True)
    active = fields.Boolean(string='Active')