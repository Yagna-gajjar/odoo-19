from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ExamResult(models.Model):
    _name = 'exam.result'
    _rec_name = 'student_id'

    exam_subject_id = fields.Many2one(comodel_name='exam.subject', string='Exam Subject', required=True)
    exam_id = fields.Many2one(related='exam_subject_id.exam_id', store=True, string='Exam')
    class_year_id = fields.Many2one(related='exam_subject_id.class_subject_id.class_year_id', store=False, string='Exam')
    subject_id = fields.Many2one(related='exam_subject_id.class_subject_id.subject_id', store=False, string='Exam')
    student_id = fields.Many2one(comodel_name='student', string='Student', required=True)
    marks_obtained = fields.Float(string='Marks Obtained', required=True)
    max_marks = fields.Float(related='exam_subject_id.max_marks', store=True)
    passing_marks = fields.Float(related='exam_subject_id.passing_marks', store=True)

    result_state = fields.Selection(
        selection=[('pass', 'Pass'), ('fail', 'Fail')],
        string='Result',
        compute='_compute_result_state',
        store=True,
    )
    percentage = fields.Float(string='Percentage', compute='_compute_result_state', store=True)

    @api.depends('marks_obtained', 'max_marks', 'passing_marks')
    def _compute_result_state(self):
        for record in self:
            record.percentage = (record.marks_obtained / record.max_marks * 100) if record.max_marks else 0
            record.result_state = 'pass' if record.marks_obtained >= record.passing_marks else 'fail'

    @api.constrains('student_id', 'exam_subject_id')
    def _check_unique_result(self):
        for record in self:
            duplicate = self.search([
                ('id', '!=', record.id),
                ('student_id', '=', record.student_id.id),
                ('exam_subject_id', '=', record.exam_subject_id.id),
            ])
            if duplicate:
                raise ValidationError(
                    "Marks for this student in this exam subject are already recorded."
                )

    @api.constrains('marks_obtained', 'max_marks')
    def _check_marks_range(self):
        for record in self:
            if record.marks_obtained < 0 or record.marks_obtained > record.max_marks:
                raise ValidationError(f"Marks Obtained must be between 0 and {record.max_marks}.")

    @api.constrains('student_id', 'exam_subject_id')
    def _check_student_enrolled(self):
        for record in self:
            exam = record.exam_subject_id.exam_id
            enrolled = self.env['student.enrollment'].search([
                ('student_id', '=', record.student_id.id),
                ('class_year_id', '=', exam.class_year_id.id),
                ('active', '=', True),
            ], limit=1)
            if not enrolled:
                raise ValidationError(
                    f"{record.student_id.name} is not enrolled in the class this exam belongs to."
                )