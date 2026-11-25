{
    "name": "Brew Bean",
    "version": "1.0",
    "depends": ["base", "web"],

    'data': [
        'views/templates.xml',
    ],

    'assets': {
        'brew_bean.assets_adminpanel': [
            ('include', 'web._assets_helpers'),
            ('include', 'web._assets_backend_helpers'),
            'web/static/src/scss/pre_variables.scss',
            'web/static/lib/bootstrap/scss/_variables.scss',
            'web/static/lib/bootstrap/scss/_maps.scss',
            ('include', 'web._assets_bootstrap'),
            ('include', 'web._assets_core'),
            'web/static/src/libs/fontawesome/css/font-awesome.css',
            'brew_bean/static/src/**/*',
            'brew_bean/static/src/scss/**/*',
            'brew_bean/static/src/components/dashboard/**/*'
        ],
    }
}
