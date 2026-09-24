from odoo import models

class Dashboard(models.AbstractModel):
    _name = "my.dashboard"

    def get_dashboard_data(self):
        return {
            "total_students": 100,
            "total_teachers": 20,
        }