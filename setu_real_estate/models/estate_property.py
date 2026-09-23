from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare


class EstateProperty(models.Model):
    _name = 'estate.property'
    _order = "id desc"
    _rec_name =  'name'

    name = fields.Char(string='Title', required=True)
    description = fields.Text(string='Description')
    postcode = fields.Char(string='Postcode')
    date_availability = fields.Date(string='Available From')
    expected_price = fields.Float(string='Expected Price', required=True)
    selling_price = fields.Float(string='Selling Price')
    bedrooms = fields.Integer(string='Bedrooms')
    living_area = fields.Integer(string='Living Area (sqm)')
    garden_area = fields.Integer(string='Garden Area')
    total_area = fields.Integer(string='Total Area', compute='_compute_total_area')
    facades = fields.Integer(string='Facades')
    garage = fields.Boolean(string='Garage')
    garden = fields.Boolean(string='Garden')
    garden_orientation = fields.Selection(string='Garden Orientation', selection=[
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West')
    ])
    property_type_id = fields.Many2one(string='Property Type', comodel_name='estate.property.type')
    property_tag = fields.Many2many(string='Property Tag', comodel_name='estate.property.tag')
    user_id = fields.Many2one(comodel_name="res.users", string="Salesman")
    buyer_id = fields.Many2one(comodel_name="res.partner", string="Buyer")
    offer_ids = fields.One2many(comodel_name="estate.property.offer", inverse_name="property_id", string="Offers")
    best_offer = fields.Float(string='Best Offer', compute='_compute_best_offer')
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection(string='State', selection=[
        ('new', 'New'),
        ('offer_received', 'Offer Received'),
        ('offer_accepted', 'Offer Accepted'),
        ('sold', 'Sold'),
        ('cancelled', 'Cancelled')
    ], default='new', store=True, compute='_compute_property_state')

    offer_count = fields.Integer(string='Offer Count', compute='_compute_offer_count')

    _expected_price_constraint = models.Constraint(
        'CHECK(expected_price > 0)',
        'expected price must be positive'
    )
    _selling_price_constraint = models.Constraint(
        'CHECK(selling_price > 0)',
        'selling price must be positive'
    )

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)

    @api.depends('garden_area', 'living_area')
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends('offer_ids')
    def _compute_best_offer(self):
        for record in self:
            if record.offer_ids:
                best_amount = max(record.offer_ids.mapped('price'))
                record.best_offer = best_amount

            else:
                record.best_offer = 0

    @api.onchange('garden_area', 'garden_orientation')
    def _onchange_garden_values(self):
        if self.garden_area or self.garden_orientation:
            self.garden = True

    @api.onchange('garden')
    def _onchange_garden_boolean(self):
        if not self.garden:
            self.garden_area = False
            self.garden_orientation = False

    @api.depends('offer_ids', 'offer_ids.status')
    def _compute_property_state(self):
        for record in self:
            if record.state not in ('cancelled', 'sold'):
                if record.offer_ids:
                    if any(offer.status == 'accepted' for offer in record.offer_ids):
                        record.state = 'offer_accepted'
                    else:
                        record.state = 'offer_received'
                else:
                    record.state = 'new'

    def action_sold(self):
        self.ensure_one()
        if self.state == 'cancelled':
            raise ValidationError('Cancelled Property cannot be sold')
        else:
            self.state = 'sold'

    def action_cancel(self):
        self.ensure_one()
        if self.state == 'sold':
            raise ValidationError('Sold Property cannot be cancel')
        else:
            self.state = 'cancelled'

    @api.constrains('selling_price')
    def _check_selling_price(self):
        if self.state != 'new':
            valid_min_selling_price = self.expected_price * 0.9
            compare = float_compare(self.selling_price, valid_min_selling_price, 2)
            if compare < 0:
                raise ValidationError("the selling price cannot be lower than 90% of the expected price.")

    @api.ondelete(at_uninstall=False)
    def _unlink_property(self):
        flag = False
        for record in self:
            if record.state in ('offer_received', 'offer_accepted', 'sold'):
                flag = True
        if flag:
            raise UserError("Can't delete this property!")

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
            'domain': [('property_id', '=', self.id)],
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
            'domain': [('property_id', '=', self.id)],
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