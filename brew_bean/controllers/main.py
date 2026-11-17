from odoo import http
from odoo.http import request


class CafeDashboard(http.Controller):

    @http.route(
        '/cafe/dashboard',
        type='http',
        auth='user',
        website=True
    )
    def dashboard(self, **kwargs):
        return request.render('brew_bean.cafe_dashboard')