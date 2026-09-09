import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SchoolTerm(models.Model):
    _name = 'school.term'

    name = fields.Char(string='Name', required=True)
    start_date = fields.Datetime(string="Start Date", required=True)
    end_date = fields.Datetime(string="End Date", required=True)
    status = fields.Selection(
        string="Status",
        selection=[
            ('active', 'Active'),
            ('inactive', 'Inactive')
        ],
        required=True
    )

    def write(self, vals):
        result = super().write(vals)
        if 'status' in vals:
            class_tems_records = self.env['class.term'].search([('school_term_id', 'in', self.ids)])
            class_tems_records.write({'status': vals['status']})
        return result

    @api.model_create_multi
    def create(self, vals_list):
        terms = super().create(vals_list)

        classes = self.env['school.class'].search([])

        class_term_vals = []
        for term in terms:
            for school_class in classes:
                class_term_vals.append({
                    'class_id': school_class.id,
                    'term_id': term.id,
                    'status': 'active',
                })

        if class_term_vals:
            self.env['class.term'].create(class_term_vals)

        return terms

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if record.name:
                match = re.match(r'^\d{4}-\d{2}$', record.name)
                if not match:
                    raise ValidationError(
                        "The Name should be like 20xx-xx"
                    )