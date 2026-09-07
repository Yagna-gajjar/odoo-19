from odoo import models, fields, api

class ClassTerm(models.Model):
    _name = 'class.term'
    _rec_name = 'display_name'

    class_id = fields.Many2one(
        comodel_name='school.class',
        string='Class',
        required=True
    )

    term_id = fields.Many2one(
        comodel_name='school.term',
        string='Term',
        required=True
    )

    status = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('inactive', 'Inactive')
        ],
        required=True
    )

    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    @api.depends('class_id', 'term_id')
    def _compute_display_name(self):
        for record in self:
            record.display_name = (
                f"{record.class_id.name} - {record.term_id.name}"
            )