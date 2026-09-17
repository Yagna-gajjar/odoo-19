from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StudentAttendance(models.Model):
    _name = 'student.attendance'
    _inherit = ['mail.thread']
    _order = 'date desc'
    _rec_name = 'student_id'

    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    class_year_id = fields.Many2one(comodel_name='class.year', string='Class', required=True)
    student_id = fields.Many2one(
        comodel_name='student',
        string='Student',
        required=True,
    )
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

    _sql_constraints = [
        ('student_date_unique', 'unique(student_id, date)', 'Attendance for this student on this date is already recorded.'),
    ]

    @api.constrains('student_id', 'class_year_id', 'date')
    def _check_student_enrolled(self):
        for record in self:
            enrolled = self.env['student.enrollment'].search([
                ('student_id', '=', record.student_id.id),
                ('class_year_id', '=', record.class_year_id.id),
                ('active', '=', True),
            ], limit=1)
            if not enrolled:
                raise ValidationError(
                    f"{record.student_id.name} is not actively enrolled in this class."
                )