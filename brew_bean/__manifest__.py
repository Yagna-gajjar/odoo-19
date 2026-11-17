{
    "name": "Brew Bean",
    "version": "1.4",
    "depends": ['base', 'web'],
    "data": [
        'views/dashboard_templates.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'brew_bean/static/src/scss/dashboard.scss',
        ],
    },
    "installable": True,
}
