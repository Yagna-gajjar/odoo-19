from odoo import models, fields, api

class AttendanceStudentLineWizard(models.TransientModel):
    _name = 'attendance.student.line.wizard'
    _description = 'Attendance Wizard Line'

    wizard_id = fields.Many2one(comodel_name='attendance.wizard', string='Wizard', ondelete='cascade')
    student_enrollment_id = fields.Many2one(comodel_name='student.enrollment', string='Enrollment', required=True)
    student_name = fields.Char(string='Student', compute='_compute_student_class_name')
    class_year_name = fields.Char(string='Class Year', compute='_compute_student_class_name')
    state = fields.Selection(
        selection=[
            ('present', 'Present'),
            ('absent', 'Absent')
        ],
        string='Status',
        required=True,
        default='present',
    )
    remarks = fields.Char(string='Remarks')

    @api.depends('student_enrollment_id')
    def _compute_student_class_name(self):
        print("_compute_student_class_name called")
        for record in self:
            record.student_name = record.student_enrollment_id.student_id.name
            record.class_year_name = record.student_enrollment_id.class_year_id.display_name