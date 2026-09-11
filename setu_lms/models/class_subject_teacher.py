from odoo import models, fields, api


class ClassSubjectTeacher(models.Model):
    _name = 'class.subject.teacher'
    _rec_name = 'class_subject_id'

    class_subject_id = fields.Many2one(
        comodel_name='class.subject',
        string="Class",
        required=True
    )

    teacher_id = fields.Many2one(
        comodel_name='teacher',
        string='Teacher',
        required=True
    )

    start_date = fields.Datetime(
        string='Start Date',
        required=True)
    end_date = fields.Datetime(string='End Date')

    active = fields.Boolean(string='Active', default=True)

    @api.onchange('class_subject_id')
    def _change_dates(self):
        print(self.class_subject_id.class_term_id)
        if self.class_subject_id.class_term_id:
            self.start_date = self.class_subject_id.class_term_id.term_id.start_date
            self.end_date = self.class_subject_id.class_term_id.term_id.end_date
