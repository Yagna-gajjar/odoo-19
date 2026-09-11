import datetime
import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SchoolTerm(models.Model):
    _name = 'school.term'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True, tracking=True)
    start_date = fields.Datetime(string="Start Date", required=True, tracking=True)
    end_date = fields.Datetime(string="End Date", required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True)

    class_term_ids = fields.One2many(
        comodel_name='class.term',
        inverse_name='term_id',
        string='Classes', tracking=True
    )
    def write(self, vals):
        result = super().write(vals)

        if 'class_term_ids' in vals:
            for command in vals['class_term_ids']:
                if command[0] == 1:
                    class_term_id = command[1]
                    changed_values = command[2]

                    if 'current_class_teacher_id' not in changed_values:
                        continue

                    teacher_id = changed_values['current_class_teacher_id']

                    active_class_teacher = self.env[
                        'class.teacher.assignment'
                    ].search(
                        [
                            ('class_term_id', '=', class_term_id),
                            ('teacher_id', '!=', False),
                            ('active', '=', True)
                        ],
                        limit=1
                    )
                    class_term = self.env['class.term'].browse(class_term_id)
                    new_start_date = class_term.term_id.start_date
                    if active_class_teacher.ids:
                        active_class_teacher.write({
                            'end_date': datetime.datetime.now(),
                            'active': False
                        })
                        new_start_date = datetime.datetime.now()

                    self.env['class.teacher.assignment'].create({
                        'class_term_id': class_term_id,
                        'teacher_id': teacher_id,
                        'start_date': new_start_date,
                        'end_date': class_term.term_id.end_date,
                    })

        if 'active' in vals:
            class_term = self.env['class.term'].search(
                [('term_id', 'in', self.ids)]
            )
            class_term.write({
                'active': vals['active']
            })

            class_teacher_records = self.env[
                'class.teacher.assignment'
            ].search(
                domain=[('class_term_id.term_id', 'in', self.ids)]
            )
            class_teacher_records.write({
                'active': vals['active']
            })

            student_enrolled = self.env['student.enrollment'].search(
                [('class_term_id.term_id', 'in', self.ids)]
            )
            student_enrolled.write({
                'active': vals['active']
            })

        return result
    def create(self, vals_list):
        terms = super().create(vals_list)
        classes = self.env['school.class'].search([
            ('active', '=', True)
        ])

        class_term_vals = []

        for term in terms:
            for school_class in classes:
                class_term_vals.append({
                    'class_id': school_class.id,
                    'term_id': term.id,
                })

        if class_term_vals:
            self.env['class.term'].create(class_term_vals)

        return terms

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if record.name:
                match = re.match(pattern=r'^\d{4}-\d{2}$', string=str(record.name))
                if not match:
                    raise ValidationError(
                        "The Name should be like 20xx-xx"
                    )
