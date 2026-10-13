{
    'name': 'AI Odoo Assistant',
    'version': '1.6',
    'category': 'Tools',
    'summary': 'AI assistant and schema registry for Odoo',
    'depends': ['base', 'web'],

    'assets': {
        'web.assets_backend': [
            'setu_ai_chatbot/static/src/components/assistant.js',
            'setu_ai_chatbot/static/src/components/assistant.xml',
            'setu_ai_chatbot/static/src/components/assistant.scss',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/conversation_rules.xml',
        'views/schema_views.xml',
        'views/analyst_views.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'application': True,
}
