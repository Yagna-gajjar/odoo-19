from odoo import models, fields

class TeacherSubjectAddWizard(models.TransientModel):
    _name = 'teacher.subject.add.wizard'
    _description = 'Add Subjects to Teacher'

    teacher_id = fields.Many2one('teacher', required=True)
    class_subject_ids = fields.Many2many('class.subject', string='Subjects to Add')

    def action_add_class_subjects(self):
        class_subject_teacher = self.env['class.subject.teacher']
        for class_subject in self.class_subject_ids:
            exists = class_subject_teacher.search([
                ('teacher_id', '=', self.teacher_id.id),
                ('class_subject_id', '=', class_subject.id),
            ], limit=1)
            if not exists:
                class_subject_teacher.create({
                    'teacher_id': self.teacher_id.id,
                    'class_subject_id': class_subject.id,
                    'start_date': class_subject.class_year_id.year_id.start_date,
                    'end_date': class_subject.class_year_id.year_id.start_date,
                })