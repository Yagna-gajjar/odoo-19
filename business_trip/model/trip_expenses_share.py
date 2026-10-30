from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TripExpensesShare(models.Model):
    _name = 'trip.expenses.share'
    _rec_name = 'trip_expense_id'
    _description = 'Trip Expense Share'


    employee_ids = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee'
    )

    trip_expense_id = fields.Many2one(
        comodel_name='business.trip.expense',
        string='Expense',
        required=True,
        ondelete='cascade',
    )

    per_or_amount = fields.Selection(
        related='trip_expense_id.per_or_amount',
    )

    distribute_equally = fields.Boolean(
        related='trip_expense_id.distribute_equally',
    )


    amount = fields.Float(string='Amount', store=True)
    percentage = fields.Float(string='Percentage', store=True)



    @api.onchange('percentage')
    def _onchange_percentage(self):
        for share in self:
            expense = share.trip_expense_id

            if (
                expense
                and expense.per_or_amount == 'percentage'
                and expense.amount
            ):
                share.amount = (
                    expense.amount * share.percentage / 100
                )

    @api.onchange('amount')
    def _onchange_amount(self):
        for share in self:
            expense = share.trip_expense_id

            if (
                expense
                and expense.per_or_amount == 'amount'
                and expense.amount
            ):
                share.percentage = (
                    share.amount * 100 / expense.amount
                )

    def _sync_share_values(self, changed_fields):
        for share in self:
            expense = share.trip_expense_id

            if not expense or not expense.amount:
                continue

            if expense.distribute_equally or expense.company_sponsored:
                continue

            if (
                expense.per_or_amount == 'percentage'
                and 'percentage' in changed_fields
            ):
                share.amount = expense.amount * share.percentage / 100

            elif (
                expense.per_or_amount == 'amount'
                and 'amount' in changed_fields
            ):
                share.percentage = share.amount * 100 / expense.amount

    @api.model_create_multi
    def create(self, vals_list):
        shares = super().create(vals_list)

        for share, vals in zip(shares, vals_list):
            share._sync_share_values(set(vals))

        return shares

    def write(self, vals):
        result = super().write(vals)
        self._sync_share_values(set(vals))
        return result

    @api.constrains('amount', 'percentage', 'trip_expense_id')
    def _check_share_values(self):
        for share in self:
            expense = share.trip_expense_id

            if share.amount < 0:
                raise ValidationError("Share amount cannot be negative.")

            if share.percentage < 0:
                raise ValidationError("Share percentage cannot be negative.")

            if share.percentage > 100:
                raise ValidationError("Share percentage cannot exceed 100%.")

            if expense and share.amount > expense.amount:
                raise ValidationError(
                    f"Employee share amount cannot exceed the total expense of {expense.amount}."
                )

            if not expense or expense.company_sponsored:
                continue

            if expense.per_or_amount == 'percentage':
                total_percentage = sum(
                    expense.share_employees_ids.mapped('percentage')
                )

                if total_percentage > 100.000001:
                    raise ValidationError(
                        "Total employee share percentages cannot exceed 100%."
                    )

            elif expense.per_or_amount == 'amount':
                total_amount = sum(
                    expense.share_employees_ids.mapped('amount')
                )

                if total_amount > expense.amount + 0.000001:
                    raise ValidationError(
                        "Total employee share amounts cannot exceed the total expense."
                    )