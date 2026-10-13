# Add a question and the Odoo models it should suggest.
# Names are training labels. Predictions are kept only when that model
# exists in the schema registry.

EXAMPLES = [
    {'question': 'How many customers do we have?', 'models': ['res.partner']},
    {'question': 'List all contacts', 'models': ['res.partner']},
    {'question': 'Show vendors and supplier companies', 'models': ['res.partner']},
    {'question': 'Which partners are companies?', 'models': ['res.partner']},
    {'question': 'Find customer addresses and phone numbers', 'models': ['res.partner']},

    {'question': 'What are total sales this year?', 'models': ['sale.order']},
    {'question': 'Show open sale orders', 'models': ['sale.order']},
    {'question': 'How many quotations were sent?', 'models': ['sale.order']},
    {'question': 'List confirmed sales orders', 'models': ['sale.order']},
    {'question': 'Count cancelled quotations', 'models': ['sale.order']},

    {'question': 'Which customers have the highest sales?', 'models': ['res.partner', 'sale.order']},
    {'question': 'Top customers by sales order amount', 'models': ['res.partner', 'sale.order']},
    {'question': 'Show customer sales', 'models': ['res.partner', 'sale.order']},
    {'question': 'Which clients bought the most?', 'models': ['res.partner', 'sale.order']},
    {'question': 'Customers with the highest sale orders', 'models': ['res.partner', 'sale.order']},

    {'question': 'Show sale order lines and quantities', 'models': ['sale.order.line']},
    {'question': 'Which products are on sales order lines?', 'models': ['sale.order.line', 'product.product']},

    {'question': 'How many invoices are posted?', 'models': ['account.move']},
    {'question': 'Total invoiced amount this month', 'models': ['account.move']},
    {'question': 'List vendor bills', 'models': ['account.move']},
    {'question': 'Show unpaid customer invoices', 'models': ['account.move', 'res.partner']},
    {'question': 'Which customers have overdue invoices?', 'models': ['account.move', 'res.partner']},
    {'question': 'Show invoice lines and taxes', 'models': ['account.move.line']},

    {'question': 'Which products are sold most?', 'models': ['product.product']},
    {'question': 'List storable products', 'models': ['product.product']},
    {'question': 'Show product templates and variants', 'models': ['product.template', 'product.product']},
    {'question': 'Which products have the highest sales?', 'models': ['product.product', 'sale.order']},
    {'question': 'Top selling products', 'models': ['product.product', 'sale.order']},

    {'question': 'Which deliveries are late?', 'models': ['stock.picking']},
    {'question': 'Show incoming shipments and receipts', 'models': ['stock.picking']},
    {'question': 'List pending stock transfers', 'models': ['stock.picking']},
    {'question': 'Show stock moves for products', 'models': ['stock.move', 'product.product']},

    {'question': 'Show draft purchase orders', 'models': ['purchase.order']},
    {'question': 'How much did we purchase this year?', 'models': ['purchase.order']},
    {'question': 'Which vendors have the highest purchases?', 'models': ['purchase.order', 'res.partner']},

    {'question': 'How many employees are there?', 'models': ['hr.employee']},
    {'question': 'List employees by department', 'models': ['hr.employee']},
    {'question': 'Show employee job titles', 'models': ['hr.employee']},

    {'question': 'Show open leads', 'models': ['crm.lead']},
    {'question': 'Which opportunities are won?', 'models': ['crm.lead']},
    {'question': 'List the sales pipeline', 'models': ['crm.lead']},

    {'question': 'Which tasks are overdue?', 'models': ['project.task']},
    {'question': 'List open project tasks', 'models': ['project.task']},

    {'question': 'Show customer payments', 'models': ['account.payment', 'res.partner']},
    {'question': 'List payments this month', 'models': ['account.payment']},
    {'question': 'Show manufacturing orders in progress', 'models': ['mrp.production']},
]
