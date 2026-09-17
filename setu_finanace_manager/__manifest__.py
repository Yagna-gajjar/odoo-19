{
    "name": "Finance Manager",
    "version": '1.4',
    'depends': ['base', 'web'],
    "data": [
        'security/ir.model.access.csv',
        'views/main_menu.xml',
        'views/accounts_view.xml',
        'views/category_view.xml',
        'views/transaction_view.xml'
    ],
    "assets": {
        "web.assets_backend": [
            "setu_finanace_manager/static/src/scss/transaction.scss",
            "setu_finanace_manager/static/src/js/transaction.js"
        ],
    }
}
