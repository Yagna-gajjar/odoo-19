import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SchoolTerm(models.Model):
    _name = 'school.term'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    start_date = fields.Datetime(string="Start Date", required=True, tracking=True)
    end_date = fields.Datetime(string="End Date", required=True, tracking=True)
    status = fields.Selection(
        string="Status",
        selection=[
            ('active', 'Active'),
            ('inactive', 'Inactive')
        ],
        required=True, tracking=True
    )

    class_term_ids = fields.One2many(
        comodel_name='class.term',
        inverse_name='term_id',
        string='Classes', tracking=True
    )

    def write(self, vals):
        result = super().write(vals)

        if 'class_term_ids' in vals:
            for command in vals['class_term_ids']:

                # 1 = update existing class.term record
                if command[0] == 1:
                    class_term_id = command[1]
                    changed_values = command[2]

                    # Only continue if teacher was changed
                    if 'current_class_teacher_id' not in changed_values:
                        continue

                    teacher_id = changed_values['current_class_teacher_id']

                    active_class_teacher = self.env[
                        'class.teacher.assignment'
                    ].search(
                        [
                            ('class_term_id', '=', class_term_id),
                            ('status', '=', 'active')
                        ],
                        limit=1
                    )

                    class_term = self.env['class.term'].browse(class_term_id)

                    if active_class_teacher:
                        active_class_teacher.write({
                            'status': 'inactive'
                        })

                    self.env['class.teacher.assignment'].create({
                        'class_term_id': class_term_id,
                        'teacher_id': teacher_id,
                        'start_date': class_term.term_id.start_date,
                        'end_date': class_term.term_id.end_date,
                    })

        if 'status' in vals:
            class_teacher_records = self.env[
                'class.teacher.assignment'
            ].search(
                [('class_term_id.term_id', 'in', self.ids)]
            )
            class_teacher_records.write({
                'status': vals['status']
            })

            class_subject_teacher_records = self.env[
                'class.subject.teacher'
            ].search(
                [('class_term_id.term_id', 'in', self.ids)]
            )
            class_subject_teacher_records.write({
                'status': vals['status']
            })

        return result
    def create(self, vals_list):
        terms = super().create(vals_list)
        classes = self.env['school.class'].search([
            ('status', '=', 'active')
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

        class_terms = self.env['class.term'].search([
            ('term_id', 'in', terms.ids)
        ])

        class_teacher_vals = []

        for class_term in class_terms:
            class_teacher_vals.append({
                'class_term_id': class_term.id,
                'start_date': class_term.term_id.start_date,
                'end_date': class_term.term_id.end_date,
            })

        if class_teacher_vals:
            self.env['class.teacher.assignment'].create(
                class_teacher_vals
            )

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
