from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ClassTermTeacher(models.Model):
    _name = 'class.term.teacher'

    class_term_id = fields.Many2one(
        comodel_name='class.term',
        string='Class Term',
        required=True
    )

    teacher_id = fields.Many2one(
        comodel_name='teacher',
        string='Teacher',
        required=True
    )

    start_date = fields.Datetime(
        string='Start Date',
        required=True
    )

    end_date = fields.Datetime(
        string='End Date',
        required=True
    )

    status = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('inactive', 'Inactive')
        ],
        required=True
    )

    @api.onchange('class_term_id')
    def _check_active_teacher(self):
        for record in self:
            existing = self.search([
                ('class_term_id', '=', record.class_term_id.id),
                ('status', '=', 'active'),
                ('id', '!=', record.id),
            ], limit=1)

            if existing:
                raise ValidationError(
                    'This teacher is already active for this class and term.'
                )

    @api.onchange('class_term_id', 'teacher_id')
    def _change_date_status(self):
        if self.class_term_id:
            self.start_date = self.class_term_id.term_id.start_date
            self.end_date = self.class_term_id.term_id.end_date
            self.status = self.class_term_id.term_id.status
    @api.onchange('end_date')
    def _change_status(self):
        if self.end_date < self.class_term_id.term_id.end_date:
            self.status = 'inactive'