from odoo import models, fields, api, Command


class BusinessTripExpense(models.Model):
    _name = 'business.trip.expense'
    _rec_name = 'description'


    trip_id = fields.Many2one(string='Trip', comodel_name='business.trip')
    description = fields.Char(string='Description')
    expense_type = fields.Selection(selection=[('meals', 'Meals'), ('transport', 'Transport'), ('hotel', 'Hotel'),
                                               ('client_meeting', 'Client Meeting'), ('other', 'Other')])
    expense_date = fields.Date(string='Expense Date')
    per_or_amount = fields.Selection(string='percentage/Amount',
                                     selection=[('percentage', 'Percentage'), ('amount', 'Amount')],
                                     default='percentage')
    trip_employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        related='trip_id.employee_ids',
        string='Trip Employees',
    )
    paid_by = fields.Many2one(
        string='Paid By',
        comodel_name='hr.employee',
        domain="[('id', 'in', trip_employee_ids)]"
    )
    share_employees_ids = fields.One2many(string='Share', comodel_name='trip.expenses.share',
                                          inverse_name='trip_expense_id')
    company_sponsored = fields.Boolean(string='Company Sponsored', store=True)
    distribute_equally = fields.Boolean(string='Distribute Equally', default=True, store=True)
    all_employees = fields.Boolean(string='All Employees', store=True)
    amount = fields.Monetary(string='Amount', currency_field='currency_id', store=True)
    currency_id = fields.Many2one(string='Currency', comodel_name='res.currency')
    receipt_reference = fields.Char(string='Receipt Reference')
    state = fields.Selection(
        string='state',
        default='draft',
        selection=[('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected')])
    remaining_amount = fields.Monetary(
        string='Remaining Amount',
        compute='_compute_remaining',
        store=True,
        currency_field='currency_id',
    )

    remaining_percentage = fields.Float(
        string='Remaining Percentage',
        compute='_compute_remaining',
        store=True,
    )
    number_of_employee = fields.Integer(
        string='Number Of Employee',
        related='trip_id.number_of_employee'
    )

    @api.depends(
        'amount',
        'per_or_amount',
        'share_employees_ids.amount',
        'share_employees_ids.percentage',
    )
    def _compute_remaining(self):
        for expense in self:
            if expense.company_sponsored:
                total_amount = sum(
                    expense.share_employees_ids.mapped('amount')
                )
                total_percentage = sum(
                    expense.share_employees_ids.mapped('percentage')
                )

                expense.remaining_amount = expense.amount - total_amount
                expense.remaining_percentage = 100.0 - total_percentage
            else:
                print(expense.trip_id.employee_ids)

    def change_expense_state(self):
        state = self.env.context.get('state')
        if state:
            self.state = state

    def _recompute_shares(self):
        for expense in self:
            if expense.all_employees:
                trip_employees = expense.trip_id.employee_ids
                existing_employees = expense.share_employees_ids.mapped('employee_ids')

                missing_employees = set(trip_employees.ids) - set(existing_employees.ids)

                if missing_employees:
                    expense.with_context(skip_recompute=True).write({
                        'share_employees_ids': [
                            Command.create({'employee_ids': employee_id})
                            for employee_id in missing_employees
                        ]
                    })

            shares = expense.share_employees_ids

            if expense.company_sponsored:
                expense.with_context(skip_recompute=True).write({
                    'paid_by': False,
                    'distribute_equally': False,
                })

                shares.write({
                    'amount': 0.0,
                    'percentage': 0.0,
                })
                continue

            if not expense.distribute_equally:
                continue

            count = len(shares)

            if not count:
                continue

            share_amount = expense.amount / count
            share_percentage = 100.0 / count

            shares.write({
                'amount': share_amount,
                'percentage': share_percentage,
            })


    @api.onchange(
        'amount',
        'distribute_equally',
        'all_employees',
        'company_sponsored',
    )
    def _onchange_recompute_shares(self):
        self._recompute_shares()

    @api.model_create_multi
    def create(self, vals_list):
        expenses = super().create(vals_list)
        expenses._recompute_shares()
        return expenses

    def write(self, vals):
        result = super().write(vals)

        if not self.env.context.get('skip_recompute'):
            if {'amount', 'distribute_equally', 'company_sponsored',
                'all_employees', 'share_employees_ids'} & vals.keys():
                self._recompute_shares()

        return result
