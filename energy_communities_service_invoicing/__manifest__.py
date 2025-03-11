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
    "version": "16.0.0.1.0",
    # any module necessary for this one to work correctly
    "depends": [
        "base",
        "contract",
        "sale",
        "sale_order_metadata",
        "sales_team",
        "purchase",
        "product",
        "product_contract",
        "contract_variable_quantity",
        "energy_communities",
        "energy_communities_cooperator",  # TODO: This dependency is needed for active members formula. Need to refactor this.
        "account_invoice_inter_company",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule_data.xml",
        "data/contract_cron.xml",
        "data/contract_line_qty_formula_data.xml",
        "data/product_data.xml",
        "report/report_invoice.xml",
        "views/account_move_views.xml",
        "views/contract_line_formula_views.xml",
        "views/contract_template_views.xml",
        "views/contract_views.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
        "views/service_invoicing_views.xml",
        "views/menus.xml",
        "wizards/service_invoicing_action.xml",
        "wizards/service_invoicing_action_create.xml",
    ],
    # only loaded in demonstration mode
    "demo": [],
}
