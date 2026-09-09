from odoo import models, fields, api


class ClassTerm(models.Model):
    _name = 'class.term'
    _rec_name = 'display_name'

    class_id = fields.Many2one(
        comodel_name='school.class',
        string='Class',
        required=True,
    )
    term_id = fields.Many2one(
        comodel_name='school.term',
        string='Term',
        required=True,
    )
    current_class_teacher_id = fields.Many2one(
        comodel_name='teacher',
        string='Current Class Teacher',
        compute='_compute_current_teacher'
    )

    subject_ids = fields.Many2many(
        comodel_name='subject',
        string='Subjects'
    )

    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    @api.depends('class_id', 'term_id')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.class_id.name} / {record.term_id.name}"

    def _compute_current_teacher(self):
        for record in self:
            teacher = self.env['class.teacher.assignment'].search([
                ('class_term_id','=', record.id)
            ],
                order='start_date desc',
                limit=1
            )

            record.current_class_teacher_id = teacher.teacher_id