{
    "name": "Coffee Shop Core",
    "version": "1.4",
    "depends": ["base", "stock", "hr"],
    "data": [
        'security/ir.model.access.csv',
        'views/coffee_shop_action.xml',
    ],
    'assets': {
        'web.assets_backend': [
        'coffee_shop_core/static/src/components/app_layout/app_action.js',
            'coffee_shop_core/static/src/components/app_layout/app_layout.js',
            'coffee_shop_core/static/src/components/app_layout/app_layout.xml',
            'coffee_shop_core/static/src/components/app_layout/app_layout.scss',
        ],
    },
    "installable": True,
}
