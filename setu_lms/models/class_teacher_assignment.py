from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ClassTeacherAssignment(models.Model):
    _name = 'class.teacher.assignment'
    _order = 'start_date desc'
    _rec_name = 'class_year_id'
    _inherit = ['mail.thread']

    class_year_id = fields.Many2one(
        comodel_name='class.year',
        string='Class Year',
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

    active = fields.Boolean(string='Active', default=True)

    @api.onchange('class_year_id')
    def _change_dates(self):
        self.start_date = self.class_year_id.year_id.start_date
        self.end_date = self.class_year_id.year_id.end_date

    @api.constrains('teacher_id', 'active')
    def _check_active_teacher(self):
        if self.teacher_id and self.active:
            duplicate = self.search([
                ('id', '!=', self.id),
                ('teacher_id', '=', self.teacher_id.id),
                ('active', '=', True)
            ])

            if duplicate:
                raise ValidationError(f"{self.teacher_id.name} is already assigned to an active class")