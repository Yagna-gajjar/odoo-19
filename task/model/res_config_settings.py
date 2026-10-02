from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def action_open_credit_rules(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Credit Rules',
            'res_model': 'credit.rule',
            'view_mode': 'list,form',
            'target': 'current',
        }