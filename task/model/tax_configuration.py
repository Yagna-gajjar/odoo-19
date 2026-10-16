from odoo import models, fields

class TaxConfiguration(models.Model):
    _name = 'tax.configuration'

    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    limit = fields.Float(string='Limit')
    tax_id = fields.Many2one(string='Tax', comodel_name='account.tax')
    partner_id = fields.Many2one(string='Vendors', comodel_name='res.partner')