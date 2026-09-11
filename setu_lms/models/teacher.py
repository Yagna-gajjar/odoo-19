from odoo import models, fields, api


class Teacher(models.Model):
    _name = 'teacher'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Teacher Name', required=True)
    employee_no = fields.Integer(string='Employee NO', required=True)
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone', required=True)

    class_term_id = fields.One2many(
        comodel_name='class.teacher.assignment',
        string='Class Teacher',
        inverse_name='teacher_id',
    )

    class_subject_id = fields.One2many(
        comodel_name='class.subject.teacher',
        string='Class and Subject',
        inverse_name='teacher_id',
    )

    @api.onchange('name')
    def _change_employee_no(self):
        last_teacher = self.search(
            [],
            order='employee_no desc',
            limit=1
        )

        next_employee_no = (
            last_teacher.employee_no + 1
            if last_teacher
            else 1
        )

        self.employee_no = next_employee_no
