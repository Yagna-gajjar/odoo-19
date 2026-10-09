{
    "name": "Tasks",
    "version": "1.4",
    "depends": ["base", "sale", "mail"],
    "data": [
        'security/ir.model.access.csv',
        "views/res_partner_views.xml",
        "views/res_config_settings_view.xml",
        "views/employee_leave_view.xml",
        "views/employee_leave_type_view.xml",
        "views/employee_leave_main_menu.xml",
        "views/hr_employee_view.xml",
        "views/stock_warehouse_view.xml",
        "views/sale_order_view.xml",
        "views/purchase_order_view.xml",
        # "views/stock_picking_view.xml"
    ],
    "installable": True,
}