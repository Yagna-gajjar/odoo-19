from odoo import models, fields


class EstateProperTag(models.Model):
    _name = 'estate.property.tag'
    _order = "name"

    name = fields.Char(string='Name')
    color = fields.Integer(string='Color')
    active = fields.Boolean(string='Active', default=True)

    _unique_tag_name = models.Constraint(
        'unique(name)',
        'Tag Name must be unique'
    )
