from odoo import models, fields

class Subject(models.Model):
    _name = 'subject'

    name = fields.Char(string='Subject Name', required=True)
    code = fields.Char(string='Subject Code', required=True)
    description = fields.Text(string='Description')
    # teacher_ids = fields.Many2many(
    #     comodel_name='teacher',
    #     string='Teachers'
    # )
    # student_ids = fields.Many2many(
    #     comodel_name='student',
    #     string='Students'
    # )
    # class_ids = fields.Many2many(
    #     comodel_name='class.model',
    #     string='Classes'
    # )