from odoo import models, fields, api


class ClassYear(models.Model):
    _name = 'class.year'
    _rec_name = 'display_name'
    _inherit = ['mail.thread']

    class_id = fields.Many2one(
        comodel_name='school.class',
        string='Class',
        required=True,
    )
    year_id = fields.Many2one(
        comodel_name='academic.year',
        string='Year',
        required=True,
    )
    current_class_teacher_id = fields.Many2one(
        comodel_name='teacher', compute='_compute_current_teacher', store=True
    )

    display_name = fields.Char(
        compute='_compute_display_name'
    )

    class_teacher_assignment_ids = fields.One2many(
        comodel_name='class.teacher.assignment',
        inverse_name='class_year_id',
        string='Class Teacher Assignments'
    )

    class_subject_ids = fields.One2many(
        comodel_name='class.subject',
        inverse_name='class_year_id',
        string='Class Subjects'
    )

    active = fields.Boolean(string='Active', default=True)

    @api.depends('class_id', 'year_id')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.class_id.name} / {record.year_id.name}"

    @api.depends('class_teacher_assignment_ids.active', 'class_teacher_assignment_ids.teacher_id',
                 'class_teacher_assignment_ids.start_date')
    def _compute_current_teacher(self):
        for record in self:
            assignment = record.class_teacher_assignment_ids.filtered('active').sorted(
                key=lambda a: a.start_date, reverse=True
            )[:1]
            record.current_class_teacher_id = assignment.teacher_id

    def action_generate_todays_attendance(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        enrollments = self.env['student.enrollment'].search([
            ('class_year_id', '=', self.id),
            ('active', '=', True),
        ])
        Attendance = self.env['student.attendance']
        for enrollment in enrollments:
            exists = Attendance.search([
                ('student_id', '=', enrollment.student_id.id),
                ('date', '=', today),
            ], limit=1)
            if not exists:
                Attendance.create({
                    'date': today,
                    'class_year_id': self.id,
                    'student_id': enrollment.student_id.id,
                    'state': 'present',
                })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Attendance',
            'res_model': 'student.attendance',
            'view_mode': 'list',
            'domain': [('class_year_id', '=', self.id), ('date', '=', today)],
        }
