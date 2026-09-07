from odoo import models, fields, api
from datetime import datetime

class Teacher(models.Model):
    _name = 'teacher'

    name = fields.Char(string='Teacher Name', required=True)
    employee_no = fields.Integer(string='Employee NO', required=True)
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone', required=True)
    # subject_ids = fields.Many2many(comodel_name='subject', string='Subject Taught')
    # subject_names = fields.Char(string="Subjects Name", compute='_compute_subject_name')
    # class_ids = fields.Many2many(comodel_name='class.model', string='Classes')
    # class_names = fields.Char(string='Class Names', compute='_compute_class_name')
    # student_ids = fields.Many2many(comodel_name='student', string='Student')
    #
    # @api.depends('subject_ids')
    # def _compute_subject_name(self):
    #     for record in self:
    #         names = record.subject_ids.mapped('name')
    #         record.subject_names = ', '.join(filter(None, names))
    #
    # @api.depends('class_ids')
    # def _compute_class_name(self):
    #     for record in self:
    #         names = record.class_ids.mapped('name')
    #         record.class_names = ', '.join(filter(None, names))