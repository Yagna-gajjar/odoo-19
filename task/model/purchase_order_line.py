
from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _reset_price_unit(self, price_unit):
        self.ensure_one()

        product = self.product_id
        if product:
            extra_price = product.price_extra

            company = self.company_id or self.env.company
            order_currency = self.currency_id or company.currency_id

            if company.currency_id != order_currency:
                extra_price = company.currency_id._convert(
                    extra_price,
                    order_currency,
                    company,
                    self.date_order.date()
                    if self.date_order
                    else fields.Date.context_today(self),
                    round=False,
                )

            price_unit += extra_price

        return super()._reset_price_unit(price_unit)
