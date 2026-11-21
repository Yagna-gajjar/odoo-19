{
    "name": "Brew Bean",
    "version": "1.4",
    "depends": ["base", "web"],

    'data': [
        'views/template.xml',
    ],

    'assets': {
        'brew_bean.assets_standalone_app': [
            ('include', 'web._assets_helpers'),
            'web/static/src/scss/pre_variables.scss',
            'web/static/lib/bootstrap/scss/_variables.scss',
            ('include', 'web._assets_bootstrap'),
            ('include', 'web._assets_core'),

            'brew_bean/static/src/js/*',
            'brew_bean/static/src/xml/*',
            'brew_bean/static/src/css/*',
        ],
    },

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
