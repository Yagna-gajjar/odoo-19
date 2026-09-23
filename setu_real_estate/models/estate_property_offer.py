from odoo import models, fields, api
from datetime import timedelta

from odoo.exceptions import ValidationError


class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _order = "price desc"
    _rec_name = 'display_name'

    price = fields.Float(string='Price', required=True)

    status = fields.Selection(
        selection=[
            ('accepted', 'Accepted'),
            ('refused', 'Refused')
        ]
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string='Partner',
        required=True
    )

    property_id = fields.Many2one(
        comodel_name="estate.property",
        string='Property',
        required=True
    )
    property_type_id = fields.Many2one(
        related='property_id.property_type_id',
        string='Property Type'
    )

    validity = fields.Integer(string='Validity')

    date_deadline = fields.Date(
        string='Date Deadline',
        compute='_compute_date_deadline',
        inverse='_inverse_date_deadline'
    )
    property_state = fields.Selection(
        related='property_id.state',
        string='Property State',
    )

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name'
    )

    _price_constraint = models.Constraint(
        'CHECK(price >= 0)',
        f'Offer Price must be positive'
    )

    @api.depends('price', 'partner_id')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.partner_id.name} / {record.price}"

    @api.depends('validity', 'create_date')
    def _compute_date_deadline(self):
        for record in self:
            if record.validity and record.create_date:
                record.date_deadline = (
                        record.create_date.date()
                        + timedelta(days=record.validity)
                )

    def _inverse_date_deadline(self):
        for record in self:
            if record.date_deadline and record.create_date:
                diff = record.date_deadline - record.create_date.date()
                record.validity = diff.days

    def action_accept_refuse(self):
        self.ensure_one()
        if self.property_id.state in ('sold', 'cancelled'):
            raise ValidationError(
                "You cannot modify an offer for a sold or cancelled property."
            )
        status = self.env.context.get('status')

        if status == 'refuse':
            self.status = 'refused'
        if status == 'accept':
            self.status = 'accepted'
            accepted_partner = self.partner_id
            all_records = self.env['estate.property.offer'].search([('partner_id', 'not in', accepted_partner), ('property_id', '=', self.property_id.id)])
            for record in all_records:
                record.status = 'refused'
            self.property_id.buyer_id = self.partner_id
            self.property_id.selling_price = self.price
            self.property_id.state = 'offer_accepted'

    @api.model
    def create(self, vals_list):
        for val in vals_list:
            property_id = val.get('property_id')
            max_price_data = self.env['estate.property.offer'].search(
                [('property_id', '=', property_id)],
                order='price desc',
                limit=1
            )
            new_price = val.get('price')
            max_price = max_price_data.price
            if max_price > new_price:
                raise ValidationError(f"min price is {max_price}")

        return super().create(vals_list)