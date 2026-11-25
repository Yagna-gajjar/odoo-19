from odoo import http
from odoo.http import request, route

class BrewBean(http.Controller):
    @http.route(['/brew_bean'], type='http', auth='public')
    def show_playground(self):
        return request.render('brew_bean.adminpanel')