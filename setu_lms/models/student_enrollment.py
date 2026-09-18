from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StudentEnrollment(models.Model):
    _name = 'student.enrollment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'enrollment_no'

    enrollment_no = fields.Char(
        string='Enrollment Number',
        copy=False,
        readonly=True,
        default='New',
    )
    student_id = fields.Many2one(
        comodel_name='student',
        string='Student',
        required=True,
    )
    class_year_id = fields.Many2one(
        comodel_name='class.year',
        string='Class',
        required=True,
    )
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    active = fields.Boolean(string='Active', default=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')
    @api.depends('student_id', 'class_year_id')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.class_year_id.display_name} / {record.student_id.name}"

    @api.onchange('class_year_id')
    def _prefill_dates(self):
        if self.class_year_id.year_id:
            self.start_date = self.class_year_id.year_id.start_date
            self.end_date = self.class_year_id.year_id.end_date

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('enrollment_no', 'New') == 'New' and vals.get('class_year_id'):
                class_year = self.env['class.year'].browse(vals['class_year_id'])
                year_name = class_year.year_id.name or ''
                pref = year_name[2:4] if len(year_name) >= 4 else '00'
                class_code = (class_year.class_id.code or '').zfill(2)
                seq_code = f'student.enrollment.{class_year.id}'

                sequence = self.env['ir.sequence'].search([('code', '=', seq_code)], limit=1)
                if not sequence:
                    sequence = self.env['ir.sequence'].create({
                        'name': f'Student Enrollment - {class_year.display_name}',
                        'code': seq_code,
                        'padding': 4,
                        'number_next': 1,
                        'number_increment': 1,
                    })

                next_no = self.env['ir.sequence'].next_by_code(seq_code)
                vals['enrollment_no'] = f'{pref}{class_code}{next_no}'

                if not vals.get('start_date'):
                    vals['start_date'] = class_year.year_id.start_date
                if not vals.get('end_date'):
                    vals['end_date'] = class_year.year_id.end_date

        return super().create(vals_list)

    @api.constrains('student_id', 'active')
    def _check_active_enrollment(self):
        for record in self:
            if record.student_id and record.active:
                duplicate = self.search([
                    ('id', '!=', record.id),
                    ('student_id', '=', record.student_id.id),
                    ('active', '=', True),
                ])
                if duplicate:
                    raise ValidationError(f"{record.student_id.name} is already enrolled")