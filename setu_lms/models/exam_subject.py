from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ExamSubject(models.Model):
    _name = 'exam.subject'
    _rec_name = 'class_subject_id'

    exam_id = fields.Many2one(comodel_name='exam', string='Exam', required=True)
    class_subject_id = fields.Many2one(
        comodel_name='class.subject',
        string='Class Subject',
        required=True,
    )
    max_marks = fields.Float(string='Max Marks', required=True, default=100.0)
    passing_marks = fields.Float(string='Passing Marks', required=True, default=35.0)
    exam_date = fields.Date(string='Exam Date')

    @api.constrains('exam_id', 'class_subject_id')
    def _check_unique_subject_per_exam(self):
        for record in self:
            duplicate = self.search([
                ('id', '!=', record.id),
                ('exam_id', '=', record.exam_id.id),
                ('class_subject_id', '=', record.class_subject_id.id),
            ])
            if duplicate:
                raise ValidationError("This subject is already added to this exam.")

    @api.constrains('class_subject_id', 'exam_id')
    def _check_subject_belongs_to_class(self):
        for record in self:
            if record.class_subject_id.class_year_id != record.exam_id.class_year_id:
                raise ValidationError(
                    "This subject does not belong to the class this exam is for."
                )

    @api.constrains('max_marks', 'passing_marks')
    def _check_marks(self):
        for record in self:
            if record.passing_marks > record.max_marks:
                raise ValidationError("Passing Marks cannot exceed Max Marks.")