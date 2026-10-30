{
    "name": "Business Trip",
    "version": "1.4",
    "depends": ["base", "mail", "hr"],
    "data": [
        'security/business_trip_security.xml',
        'security/ir.model.access.csv',
        "views/business_trip_view.xml",
        "views/business_trip_expenses_view.xml",
        'views/dashboard_template.xml',
    ],
    "assets": {
        "web.assets_frontend": [
            "business_trip/static/src/js/dashboard.js",
        ],
    },
    "installable": True,
}
