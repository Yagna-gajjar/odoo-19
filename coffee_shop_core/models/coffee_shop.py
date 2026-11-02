from odoo import models, fields


class CoffeeShop(models.Model):
    _name = 'coffee.shop'
    _description = 'Coffee Shop Branch'
    _order = 'name'

    _check_company_auto = True

    name = fields.Char(string='Shop Name', required=True)
    code = fields.Char(string='Shop Code', required=True)

    manager_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Shop Manager',
        check_company=True,
    )

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        check_company=True,
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )

    active = fields.Boolean(default=True)

    _unique_code = models.Constraint(
        definition='unique(code)',
        message='Code should be unique for every shop',
    )

    _unique_name = models.Constraint(
        definition='unique(name)',
        message='Name should be unique for every shop',
    )