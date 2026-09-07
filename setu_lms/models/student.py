from odoo import models, fields, api
from datetime import datetime


class Student(models.Model):
    _name = 'student'

    name = fields.Char(string='Student Name', required=True)
    roll_number = fields.Integer(string="Roll Number", required=True)
    date_of_birth = fields.Datetime(string='Date Of Birth', required=True, default=datetime.now())
    gender = fields.Selection(selection=[('female', 'Female'), ('male', 'Male'), ('other', 'Other')], string="Gender")
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone', required=True)
    # class_id = fields.Many2one(
    #     comodel_name='class.model', string='Classes'
    # )
    # subject_ids = fields.Many2many(
    #     comodel_name='subject', string='Subject'
    # )
    # teacher_ids = fields.Many2many(
    #     comodel_name='teacher', string='Teacher'
    # )
    #
    # @api.onchange('class_id', 'subject_ids')
    # def _add_teacher(self):
    #     teachers = self.env['teacher'].search([
    #         ('class_ids', 'in', self.class_id.id),
    #         ('subject_ids', 'in', self.subject_ids.ids),
    #     ])
    #
    #     self.teacher_ids = [(0, 0, teachers.ids)]