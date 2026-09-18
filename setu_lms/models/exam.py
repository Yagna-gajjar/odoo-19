from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Exam(models.Model):
    _name = 'exam'
    _inherit = ['mail.thread']
    _order = 'start_date desc'

    name = fields.Char(string='Exam Name', required=True)
    class_year_id = fields.Many2one(
        comodel_name='class.year',
        string='Class',
        required=True,
    )
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    active = fields.Boolean(string='Active', default=True)

    exam_subject_ids = fields.One2many(
        comodel_name='exam.subject',
        inverse_name='exam_id',
        string='Subjects',
    )

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError("Start Date cannot be after End Date.")

    def action_generate_result_sheets(self):
        self.ensure_one()
        enrollments = self.env['student.enrollment'].search([
            ('class_year_id', '=', self.class_year_id.id),
            ('active', '=', True),
        ])
        Result = self.env['exam.result']
        for exam_subject in self.exam_subject_ids:
            for enrollment in enrollments:
                exists = Result.search([
                    ('student_id', '=', enrollment.student_id.id),
                    ('exam_subject_id', '=', exam_subject.id),
                ], limit=1)
                if not exists:
                    Result.create({
                        'student_id': enrollment.student_id.id,
                        'exam_subject_id': exam_subject.id,
                        'marks_obtained': 0,
                    })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Results',
            'res_model': 'exam.result',
            'view_mode': 'list',
            'domain': [('exam_id', '=', self.id)],
        }