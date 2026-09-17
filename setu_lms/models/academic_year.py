import datetime
import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AcademicYear(models.Model):
    _name = 'academic.year'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True, tracking=True)
    start_date = fields.Datetime(string="Start Date", required=True, tracking=True)
    end_date = fields.Datetime(string="End Date", required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True)

    class_year_ids = fields.One2many(
        comodel_name='class.year',
        inverse_name='year_id',
        string='Classes', tracking=True
    )

    def action_close_year(self):
        self.write({'active': False})
        self.class_year_ids.write({'active': False})
        self.env['class.teacher.assignment'].search(
            [('class_year_id.academic_year_id', 'in', self.ids)]
        ).write({'active': False})
        self.env['student.enrollment'].search(
            [('class_year_id.academic_year_id', 'in', self.ids)]
        ).write({'active': False})

    def action_activate_year(self):
        self.write({'active': True})
        self.class_year_ids.write({'active': True})

    def create(self, vals_list):
        years = super().create(vals_list)
        classes = self.env['school.class'].search([
            ('active', '=', True)
        ])

        class_year_vals = []

        for year in years:
            for school_class in classes:
                class_year_vals.append({
                    'class_id': school_class.id,
                    'year_id': year.id,
                })

        if class_year_vals:
            self.env['class.year'].create(class_year_vals)

        return years

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if record.name:
                match = re.match(pattern=r'^\d{4}-\d{2}$', string=str(record.name))
                if not match:
                    raise ValidationError(
                        "The Name should be like 20xx-xx"
                    )
