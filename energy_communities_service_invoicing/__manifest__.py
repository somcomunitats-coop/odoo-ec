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
    "depends": ["base", "product_contract", "energy_communities"],
    # always loaded
    "data": [
        # 'security/ir.model.access.csv',
        "views/menus.xml",
        "views/contract_views.xml",
        "views/sale_order_views.xml",
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    "demo": [],
}
