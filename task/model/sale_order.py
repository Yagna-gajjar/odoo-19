from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = "sale.order"
    credit_per = fields.Float(string='Credit (%)')
    credit_amount = fields.Float(string='Credit Amount')
    def get_credit_per(self):
        self.ensure_one()
        self.credit_per = 1
        if self.amount_total > 500:
            self.credit_per = 2
        if self.amount_total > 1000:
            self.credit_per = 4
        if self.amount_total > 1500:
            self.credit_per = 6
        self.credit_amount = (self.credit_per * self.amount_total) / 100

    def write(self, vals):
        res = super().write(vals)
        if 'order_line' in vals:
            for order in self:
                partner = self.partner_id
                temp_credit = partner.credits - self.credit_amount
                self.get_credit_per()
                final_credit = temp_credit + self.credit_amount

                partner.write({
                    'credits': final_credit
                })
        return res


    def action_confirm(self):
        res = super().action_confirm()
        partner = self.partner_id
        if partner:
            total_credit = partner.credits
            self.get_credit_per()
            self.credit_amount = (self.credit_per * self.amount_total) / 100
            total_credit += self.credit_amount

            partner.write({
                'credits': total_credit
            })

        return res

    def action_cancel(self):
        res = super().action_confirm()
        partner = self.partner_id
        if partner and self.credit_amount and self.credit_per:
            total_credit = partner.credits
            total_credit -= self.credit_amount

            partner.write({
                'credits': total_credit
            })

        return res