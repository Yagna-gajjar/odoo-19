from odoo import models, fields, api


class ClassSubject(models.Model):
    _name = 'class.subject'
    _rec_name = 'display_name'

    class_term_id = fields.Many2one(
        comodel_name='class.term',
        string='Class Term',
        required=True
    )

    subject_id = fields.Many2one(
        comodel_name='subject',
        string='Subject',
        required=True
    )


    class_subject_teacher_ids = fields.One2many(
        comodel_name='class.subject.teacher',
        inverse_name='class_subject_id',
        string='Teacher',
        required=True
    )
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    @api.depends('class_term_id', 'subject_id')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.class_term_id.display_name} / {record.subject_id.name}"