from odoo import models, fields, api


class StudentEnrollment(models.Model):
    _name = 'student.enrollment'

    enrollment_no = fields.Char(string='Enrollment Number')
    student_id = fields.Many2one(
        comodel_name='student',
        string='Student',
        required=True
    )

    class_term_id = fields.Many2one(
        comodel_name='class.term',
        string='Class',
        required=True
    )

    start_date = fields.Datetime(string='Start Date', required=True)
    end_date = fields.Datetime(string='End Date', required=True)
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
    def _create_enrollment(self):
        if self.class_term_id.term_id and self.class_term_id.class_id:
            pref = self.class_term_id.term_id.name[2:4]
            class_code = self.class_term_id.class_id.code.zfill(2)
            last_enrollment = self.search(
                domain=[('class_term_id','=',self.class_term_id)],
                order='enrollment_no desc',
                limit=1
            )
            print(last_enrollment.enrollment_no)
            if last_enrollment:
                self.enrollment_no =  f'{pref}{class_code}{format(int(last_enrollment.enrollment_no[4:])+1, "04d")}'
            else:
                self.enrollment_no =  f'{pref}{class_code}{format(1, "04d")}'