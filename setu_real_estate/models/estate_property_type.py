from odoo import models, fields, api


class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _order = "name"

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(string='Active', default=True)
    property_ids = fields.One2many(string='Properties', comodel_name='estate.property', inverse_name='property_type_id')
    offer_ids = fields.One2many(comodel_name="estate.property.offer",
                                inverse_name="property_type_id",
                                string="Offers")
    offer_count = fields.Integer(string='Offer Count', compute='_compute_offer_count')

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for record in self:
            print(record.offer_ids)
            record.offer_count = len(record.offer_ids)
