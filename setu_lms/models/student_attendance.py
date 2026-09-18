from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StudentAttendance(models.Model):
    _name = 'student.attendance'
    _inherit = ['mail.thread']
    _order = 'date desc'
    _rec_name = 'enrolled_student_id'

    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    enrolled_student_id = fields.Many2one(
        comodel_name='student.enrollment',
        string='Student'
    )
    state = fields.Selection(
        selection=[
            ('present', 'Present'),
            ('absent', 'Absent')
        ],
        string='Status',
        default='present',
    )
    remarks = fields.Char(string='Remarks')


    _student_date_unique = models.Constraint(
        'unique(enrolled_student_id, date)', 'Attendance for this student on this date is already recorded.'
    )
