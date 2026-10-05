from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # allowed_leave = fields.Float(string="Allowed Leave")
    # total_leave_taken = fields.Float(
    #     string="Total Leave Taken",
    #     # compute="_compute_leave_summary"
    # )
    # remaining_leave = fields.Float(
    #     string="Remaining Leave",
    #     # compute="_compute_leave_summary"
    # )


    leave_count = fields.Integer(
        string='Leave Count',
        compute='_compute_leave_count'
    )

    @api.depends()
    def _compute_leave_count(self):
        Leave = self.env['employee.leave']

        for employee in self:
            employee.leave_count = Leave.search_count([
                ('employee_id', '=', employee.id)
            ])

    def action_leave_stat_view(self):
        self.ensure_one()

        return {
            'name': 'Leaves',
            'type': 'ir.actions.act_window',
            'res_model': 'employee.leave',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
            },
        }