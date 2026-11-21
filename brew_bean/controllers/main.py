from odoo import http
from odoo.http import request


class BrewBean(http.Controller):

    @http.route('/home', type='http', auth='user')
    def home(self):
        return request.render(
            'brew_bean.page'
        )