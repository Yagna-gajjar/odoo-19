from odoo import models, fields, api

class AttendanceWizard(models.TransientModel):
    _name = 'attendance.wizard'

    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    class_year_id = fields.Many2one(
        comodel_name='class.year',
        string='Class',
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name='attendance.student.line.wizard',
        inverse_name='wizard_id',
        string='Students',
    )

    @api.onchange('class_year_id', 'date')
    def _onchange_load_students(self):
        if not self.class_year_id or not self.date:
            self.line_ids = [(5, 0, 0)]
            return

        enrollments = self.env['student.enrollment'].search([
            ('class_year_id', '=', self.class_year_id.id),
            ('active', '=', True),
        ])

        existing = self.env['student.attendance'].search([
            ('enrolled_student_id.class_year_id', '=', self.class_year_id.id),
            ('date', '=', self.date),
        ])
        existing_by_enrollment = {rec.student_enrollment_id.id: rec.state for rec in existing}

        lines = [(5, 0, 0)]
        for enrollment in enrollments:
            lines.append((0, 0, {
                'student_enrollment_id': enrollment.id,
                'state': existing_by_enrollment.get(enrollment.id, 'present'),
            }))
        self.line_ids = lines

    def action_save_attendance(self):
        self.ensure_one()
        Attendance = self.env['student.attendance']

        for line in self.line_ids:
            print(line.student_enrollment_id.id)
            record = Attendance.search([
                ('enrolled_student_id', '=', line.student_enrollment_id.id),
                ('date', '=', self.date),
            ], limit=1)
            if record:
                record.write({'state': line.state, 'remarks': line.remarks})
            else:
                print(self.date)
                print(line.student_enrollment_id)
                print(line.remarks)
                Attendance.create({
                    'date': self.date,
                    'enrolled_student_id': line.student_enrollment_id.id,
                    'state': line.state,
                    'remarks': line.remarks,
                })
        return {'type': 'ir.actions.act_window_close'}
