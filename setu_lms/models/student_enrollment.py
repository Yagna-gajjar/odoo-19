from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StudentEnrollment(models.Model):
    _name = 'student.enrollment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'enrollment_no'

    enrollment_no = fields.Char(string='Enrollment Number', copy=False, readonly=True, default='New')
    student_id = fields.Many2one(
        comodel_name='student',
        string='Student',
        required=True
    )

    class_year_id = fields.Many2one(
        comodel_name='class.year',
        string='Class',
        required=True
    )

    start_date = fields.Datetime(string='Start Date', required=True)
    end_date = fields.Datetime(string='End Date', required=True)
    active = fields.Boolean(string='Active', default=True)

    @api.onchange('class_year_id')
    def _create_enrollment(self):
        if self.class_year_id.year_id and self.class_year_id.class_id:
            pref = self.class_year_id.year_id.name[2:4]
            class_code = self.class_year_id.class_id.code.zfill(2)
            last_enrollment = self.search(
                domain=[('class_year_id','=',self.class_year_id)],
                order='enrollment_no desc',
                limit=1
            )
            self.start_date = self.class_year_id.year_id.start_date
            self.end_date = self.class_year_id.year_id.end_date
            if last_enrollment:
                self.enrollment_no =  f'{pref}{class_code}{format(int(last_enrollment.enrollment_no[4:])+1, "04d")}'
            else:
                self.enrollment_no =  f'{pref}{class_code}{format(1, "04d")}'

    @api.onchange('student_id', 'active')
    def _check_active_teacher(self):
        if self.student_id and self.active:
            duplicate = self.search([
                ('id', '!=', self.id),
                ('student_id', '=', self.student_id.id),
                ('active', '=', True)
            ])

            if duplicate:
                raise ValidationError(f"{self.student_id.name} is already enrolled")