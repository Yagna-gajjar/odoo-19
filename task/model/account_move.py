from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'
    tax_id = fields.Many2one(string='Tax', comodel_name='account.tax')
    tax_amount = fields.Float(string='Tax Amount', default='0')

    def calculate_tax_amount(self):
        partners = self.env['account.move'].search([('partner_id', '=', self.partner_id), ('state', '=', 'posted')])
        total_bill = 0
        for partner in partners:
            total_bill += partner.amount_untaxed

        vendor = self.env['res.partner'].search([('id', '=', self.partner_id)])
        tax_slot = vendor.tax_configuration_ids.search(
            [('start_date', '<=', self.invoice_date), ('end_date', '>=', self.invoice_date),
             ('company_id', '=', self.company_id), ('limit', '<', total_bill), ('tax_id', '=', self.tax_id)])

        self.tax_amount = 0
        for tax in tax_slot:
            extra_amount = total_bill - tax.limit
            self.tax_amount += extra_amount * (tax.tax_id.amount / 100)