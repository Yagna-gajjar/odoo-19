from odoo import http
from odoo.http import request

class BusinessTripController(http.Controller):
    @http.route('/trip/page', type='http', auth='user')
    def trip_page(self):
        return request.render('business_trip.dashboard_template')

    @http.route('/trip/data', type='jsonrpc', auth='user')
    def trip_data(self):
        trips = request.env['business.trip'].search([])
        return [
            {
                'id': trip.id,
                'name': trip.name,
            }
            for trip in trips
        ]