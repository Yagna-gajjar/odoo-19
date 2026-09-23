{
    "name": "Real Estate",
    "version": '1.4',
    "depends": ['base', 'mail'],
    'assets': {
        'web.assets_backend': [
            'setu_real_estate/static/src/css/estate_property.css'
        ],
    },
    "data": [
        'security/ir.model.access.csv',
        'views/estate_property_view.xml',
        'views/property_type_view.xml',
        'views/estate_property_tag_view.xml',
        'views/estate_property_offer_view.xml',
        'views/res_users_views.xml',
        'views/main_menu.xml'
    ]
}
