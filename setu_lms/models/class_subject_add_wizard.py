from odoo import models, fields

class ClassSubjectAddWizard(models.TransientModel):
    _name = 'class.subject.add.wizard'
    _description = 'Add Subjects to Class'

    class_year_id = fields.Many2one('class.year', required=True)
    subject_ids = fields.Many2many('subject', string='Subjects to Add')

    def action_add_subjects(self):
        class_subject = self.env['class.subject']
        for subject in self.subject_ids:
            exists = class_subject.search([
                ('class_year_id', '=', self.class_year_id.id),
                ('subject_id', '=', subject.id),
            ], limit=1)
            if not exists:
                class_subject.create({
                    'class_year_id': self.class_year_id.id,
                    'subject_id': subject.id,
                })