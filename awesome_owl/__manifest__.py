{
    "name": "Awesome Owl",
    "version": "1.0",
    "depends": ["base","web"],
    'data': [
        'view/templates.xml',
    ],
    'assets': {
        'awesome_owl.assets_playground': [
            ('include', 'web._assets_helpers'),
            ('include', 'web._assets_backend_helpers'),
            'web/static/src/scss/pre_variables.scss',
            'web/static/lib/bootstrap/scss/_variables.scss',
            'web/static/lib/bootstrap/scss/_maps.scss',
            ('include', 'web._assets_bootstrap'),
            ('include', 'web._assets_core'),
            'web/static/src/libs/fontawesome/css/font-awesome.css',
            'awesome_owl/static/src/**/*',
        ],
    },
}