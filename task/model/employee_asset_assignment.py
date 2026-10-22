from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta, datetime

class EmployeeAssetAssignment(models.Model):
    _name = 'employee.asset.assignment'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', required=True)
    assets_id = fields.Many2one(comodel_name='employee.asset', string='Product', required=True)
    assignment_date = fields.Date(string='Assignment Date', required=True)
    return_date = fields.Date(string='Return Date')
    state = fields.Selection(selection=[('assigned', 'Assigned'), ('returned', 'Returned')], default='assigned')
    notes = fields.Text(string='Notes')

    @api.constrains('assignment_date', 'return_date')
    def _check_dates(self):
        if self.return_date and self.assignment_date:
            if self.return_date < self.assignment_date:
                raise ValidationError('Return Date cannot be before Assignment Date')

    @api.constrains('product_id')
    def _check_product_duplicate(self):
        new_product = self.product_id
        data = self.env['employee.asset.assignment'].search([('id', '!=', self.id), ('state', '=', 'assigned')])
        if len(data) > 0:
            matched_product = new_product & data.product_id
            if bool(matched_product):
                raise ValidationError(f"{matched_product.name} already assigned")

    def return_asset(self):
        today = date.today()
        self.return_date = today
        self.state = 'returned'

    @api.constrains('assets_id')
    def _check_asset_capacity(self):
        for rec in self:
            asset = rec.assets_id
            if asset and len(asset.employee_assignment_ids) > asset.total:
                raise ValidationError(
                    'No assets are left.'
                )

    @api.model
    def cron_return_data(self):
        today = fields.Date.today()

        assignments = self.search([
            ('state', '=', 'assigned'),
            ('return_date', '!=', False),
            ('return_date', '<', today),
        ])

        assignments.write({
            'state': 'returned',
        })