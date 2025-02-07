{
    "name": "energy_communities_service_invoicing",
    "summary": """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    "description": """
        Long description of module's purpose
    """,
    "author": "Som comunitats",
    "website": "https://coopdevs.org",
    "category": "Contract Management",
    "version": "16.0.0.1.1",
    # any module necessary for this one to work correctly
    "depends": [
        "base",
        "contract",
        "sale",
        "product_contract",
        "contract_variable_quantity",
        "energy_communities",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "data/contract_cron.xml",
        "data/contract_line_qty_formula_data.xml",
        "data/product_data.xml",
        "views/contract_views.xml",
        "views/sale_order_views.xml",
        "views/service_invoicing_views.xml",
        "views/menus.xml",
        "wizards/service_invoicing_action.xml",
        "wizards/service_invoicing_action_create.xml",
    ],
    # only loaded in demonstration mode
    "demo": [],
}
