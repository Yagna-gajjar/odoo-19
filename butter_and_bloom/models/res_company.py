from odoo import models, api
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.constrains('company_registry')
    def _check_company_registry(self):
        for company in self:
            if not company.company_registry:
                continue

            duplicate = self.search([
                ('company_registry', '=', company.company_registry),
                ('id', '!=', company.id),
            ], limit=1)

            if duplicate:
                raise ValidationError(
                    "Company registration number must be unique!"
                )