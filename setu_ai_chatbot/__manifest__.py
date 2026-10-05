{
    'name': 'AI Odoo Assistant',
    'version': '1.4',
    'category': 'Tools',
    'summary': 'AI assistant for Odoo',
    'depends': ['base', 'web'],

    'assets': {
        'web.assets_backend': [
            'setu_ai_chatbot/static/src/components/assistant.js',
            'setu_ai_chatbot/static/src/components/assistant.xml',
            'setu_ai_chatbot/static/src/components/assistant.scss',
        ],
    },
    'data': [
        'views/templates.xml',
    ],
    'installable': True,
    'application': True,
}