from odoo import models, fields, api


class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _order = "name"
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(string='Active', default=True)
    property_ids = fields.One2many(string='Properties', comodel_name='estate.property', inverse_name='property_type_id')
    offer_ids = fields.One2many(comodel_name="estate.property.offer",
                                inverse_name="property_type_id",
                                string="Offers")
    offer_count = fields.Integer(string='Offer Count', compute='_compute_offer_count')
    property_count = fields.Integer(string='Property Count', compute='_compute_property_count')

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)

    @api.depends('property_ids')
    def _compute_property_count(self):
        for record in self:
            record.property_count = len(record.property_ids)

    def action_offer_stat_view(self):
        self.ensure_one()
        if self.offer_count == 1:
            record = self.env['estate.property.offer'].search([('property_id', '=', self.id)], limit=1)
            print(record)
            return {
                'name': 'Offers',
                'type': 'ir.actions.act_window',
                'res_model': 'estate.property.offer',
                'view_mode': 'form',
                'res_id': record.id,
                'domain': [('property_type_id', '=', self.id)],
                'arch': """
                <form>
                    <field name="price"/>
                    <field name="partner_id"/>
                    <field name="validity"/>
                    <field name="date_deadline"/>
                    <field name="status"/>
                </list>
            """,
            }

        return {
            'name': 'Offers',
            'type': 'ir.actions.act_window',
            'res_model': 'estate.property.offer',
            'view_mode': 'list',
            'domain': [('property_type_id', '=', self.id)],
            'arch': """
                <list decoration-danger="status == 'refused'"
                      decoration-success="status == 'accepted'"
                      editable="bottom">
                    <field name="price"/>
                    <field name="partner_id"/>
                    <field name="validity"/>
                    <field name="date_deadline"/>
                    <field name="status"/>
                </list>
            """,
        }

    def action_property_stat_view(self):
        self.ensure_one()
        if self.property_count == 1:
            record = self.env['estate.property'].search([('property_type_id', '=', self.id)], limit=1)
            return {
                'name': 'Properties',
                'type': 'ir.actions.act_window',
                'res_model': 'estate.property',
                'view_mode': 'form',
                'res_id': record.id,
                'domain': [('property_type_id', '=', self.id)],
                'arch': """
                <form>
                    <field name="name"/>
                    <field name="postcode"/>
                    <field name="bedrooms"/>
                    <field name="living_area"/>
                    <field name="expected_price"/>
                    <field name="selling_price"/>
                    <field name="date_availability"/>
                </form>
            """,
            }

        return {
            'name': 'Properties',
            'type': 'ir.actions.act_window',
            'res_model': 'estate.property',
            'view_mode': 'list',
            'domain': [('property_type_id', '=', self.id)],
            'arch': """
                <list decoration-muted="state == 'sold'" decoration-danger="state == 'cancelled'" decoration-success="state in ('offer_received', 'offer_accepted')"
                  decoration-bf="state in ('offer_accepted', 'sold')">
                <field name="name"/>
                <field name="postcode"/>
                <field name="bedrooms"/>
                <field name="living_area"/>
                <field name="expected_price"/>
                <field name="selling_price"/>
                <field name="date_availability"/>
            </list>
            """,
        }
