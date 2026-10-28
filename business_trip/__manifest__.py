{
    "name": "Business Trip",
    "version": "1.4",
    "depends": ["base", "mail", "hr"],
    "data": [
        'security/business_trip_security.xml',
        'security/ir.model.access.csv',
        "views/business_trip_view.xml",
        "views/business_trip_expenses_view.xml",
    ],
    "installable": True,
}