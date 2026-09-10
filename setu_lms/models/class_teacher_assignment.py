from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ClassTeacherAssignment(models.Model):
    _name = 'class.teacher.assignment'
    _order = 'start_date desc'
    _rec_name = 'class_term_id'

    class_term_id = fields.Many2one(
        comodel_name='class.term',
        string='Class Term',
        required=True
    )
    teacher_id = fields.Many2one(
        comodel_name='teacher',
        string='Teacher'
    )
    start_date = fields.Datetime(
        string='Start Date',
        required=True
    )
    end_date = fields.Datetime(
        string='End Date'
    )

    status = fields.Selection(
        [
            ('active', 'Active'),
            ('inactive', 'Inactive'),
        ],
        string='Status',
        default='active',
        required=True
    )

    @api.onchange('class_term_id')
    def _change_dates(self):
        self.start_date = self.class_term_id.term_id.start_date
        self.end_date = self.class_term_id.term_id.end_date

    @api.onchange('teacher_id', 'status')
    def _check_active_teacher(self):
        if self.teacher_id and self.status == 'active':
            duplicate = self.search([
                ('id', '!=', self.id),
                ('teacher_id', '=', self.teacher_id.id),
                ('status', '=', 'active')
            ])

            if duplicate:
                raise ValidationError(f"{self.teacher_id.name} is already assigned to an active class")