from odoo import models, fields, api


class Teacher(models.Model):
    _name = 'teacher'
    _description = 'Teacher'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Teacher Name', required=True)
    employee_no = fields.Char(string='Employee NO', required=True, copy=False, readonly=True, default='New')
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone', required=True)

    class_teacher_id = fields.One2many(
        comodel_name='class.teacher.assignment',
        string='Class Teacher',
        inverse_name='teacher_id',
    )
    class_subject_id = fields.One2many(
        comodel_name='class.subject.teacher',
        string='Class and Subject',
        inverse_name='teacher_id',
    )

    _employee_no_unique = models.Constraint(
        'unique(employee_no)', 'Employee Number must be unique.'
    )
    _email_unique = models.Constraint(
        'unique(email)', 'A teacher with this email already exists.'
    )


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('employee_no', 'New') == 'New':
                vals['employee_no'] = self.env['ir.sequence'].next_by_code('teacher.employee.no') or 'New'
        return super().create(vals_list)