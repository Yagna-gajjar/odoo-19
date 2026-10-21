from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EmployeeAsset(models.Model):
    _name = 'employee.asset'
    _rec_name = 'product_id'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True
    )

    total = fields.Integer(
        string='Number Of Assets',
        required=True
    )

    occupied = fields.Integer(
        string='Occupied No.',
        compute='_compute_occupied_product'
    )

    employee_assignment_ids = fields.One2many(
        string='Employees Assigned',
        comodel_name='employee.asset.assignment',
        inverse_name='assets_id'
    )

    @api.depends('employee_assignment_ids')
    def _compute_occupied_product(self):
        for rec in self:
            rec.occupied = len(rec.employee_assignment_ids)