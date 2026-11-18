
{
    "name": "Brew Bean",
    "version": "1.4",
    "depends": ['base', 'web'],

    "data": [
        'security/ir.model.access.csv',
        'views/cafe_menus.xml',
        'views/main_menu.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'brew_bean/static/src/xml/components/cafe_layout.xml',
            'brew_bean/static/src/xml/dashboard_templates.xml',
            'brew_bean/static/src/scss/dashboard.scss',

            'brew_bean/static/src/js/components/cafe_layout.js',
            'brew_bean/static/src/js/cafe_dashboard.js',
        ],
    },

    "installable": True,
}
