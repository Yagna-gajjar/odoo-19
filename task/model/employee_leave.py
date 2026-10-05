from email.policy import default

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class EmployeeLeave(models.Model):
    _name = "employee.leave"
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee',
    tracking=True)
    leave_type_id = fields.Many2one(comodel_name='employee.leave.type', string='Leave Type',
    tracking=True)
    start_date = fields.Date(string='Start Date',
    tracking=True)
    end_date = fields.Date(string='End Date',
    tracking=True)
    number_of_days = fields.Integer(string='Number of Days',  compute="_compute_number_of_days")
    reason = fields.Char(string='Reason')
    state = fields.Selection(string="State", selection=[
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    ], default='draft',
    tracking=True)
    assigned_to = fields.Many2one(comodel_name='hr.employee', string='Assigned To')
    approved_date = fields.Datetime(string="Approved Date")
    can_approve = fields.Boolean(
        compute="_compute_can_approve"
    )

    @api.depends('assigned_to')
    def _compute_can_approve(self):
        for leave in self:
            leave.can_approve = (
                    leave.assigned_to.user_id == self.env.user
            )

    def action_request(self):
        for leave in self:
            manager = leave.employee_id.parent_id
            self.assigned_to = manager
            if not manager:
                raise ValidationError(
                    "This employee does not have a manager."
                )
            if not manager.user_id:
                raise ValidationError(
                    "The manager does not have a user."
                )
            leave.state = 'requested'

            leave.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=manager.user_id.id,
                summary='Review Leave Request',
                note='Please approve or reject this leave request.'
            )

    def action_approve(self):
        for leave in self:

            if leave.state != 'requested':
                raise ValidationError(
                    "Only requested leave can be approved."
                )

            if leave.assigned_to.user_id != self.env.user:
                raise ValidationError(
                    "You are not authorized to approve this leave."
                )

            leave.write({
                'state': 'approved',
                'approved_date': fields.Datetime.now(),
            })

    def action_reject(self):
        for leave in self:

            if leave.state != 'requested':
                raise ValidationError(
                    "Only requested leave can be rejected."
                )

            if leave.assigned_to.user_id != self.env.user:
                raise ValidationError(
                    "You are not authorized to rejected this leave."
                )

            leave.write({
                'state': 'rejected',
                'approved_date': fields.Datetime.now(),
            })

    @api.depends('start_date', 'end_date')
    def _compute_number_of_days(self):
        for record in self:
            if not record.start_date or not record.end_date:
                record.number_of_days = 0
                continue

            current_date = record.start_date
            count = 0

            while current_date <= record.end_date:
                if current_date.weekday() not in (5, 6):
                    count += 1

                current_date += timedelta(days=1)

            record.number_of_days = count

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if not record.start_date or not record.end_date:
                continue
            if record.start_date < date.today():
                print("Start Date cannot be before today")
                raise ValidationError("Start Date cannot be before today")
            if record.start_date > record.end_date:
                raise ValidationError("Start Date cannot be after End Date")
