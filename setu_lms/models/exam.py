from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Exam(models.Model):
    _name = 'exam'
    _inherit = ['mail.thread']
    _order = 'start_date desc'

    name = fields.Char(string='Exam Name', required=True)
    class_year_id = fields.Many2one(
        comodel_name='class.year',
        string='Class',
        required=True,
    )
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    active = fields.Boolean(string='Active', default=True)

    exam_subject_ids = fields.One2many(
        comodel_name='exam.subject',
        inverse_name='exam_id',
        string='Subjects',
    )

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError("Start Date cannot be after End Date.")