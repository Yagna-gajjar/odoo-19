from odoo import models, fields


class ClassSubjectTeacher(models.Model):
    _name = 'class.subject.teacher'

    class_term_id = fields.Many2one(
        comodel_name='class.term',
        string="Class",
        required=True
    )

    subject_id = fields.Many2one(
        comodel_name='subject',
        string='Subject',
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

    status = fields.Selection(
        [
            ('active', 'Active'),
            ('inactive', 'Inactive'),
        ],
        string='Status',
        default='active',
        required=True
    )