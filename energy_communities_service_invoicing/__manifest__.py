{
    "name": "energy_communities_service_invoicing",
    "summary": """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    "description": """
        Long description of module's purpose
    """,
    "author": "Som comunitats",
    "website": "https://git.coopdevs.org/coopdevs/comunitats-energetiques/odoo-ce",
    "category": "Contract Management",
    "version": "16.0.0.5.7",
    # any module necessary for this one to work correctly
    "depends": [
        "base",
        "contract",
        "sale",
        "sale_order_metadata",
        "sales_team",
        "purchase",
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
        "views/contract_line_views.xml",
        "views/contract_template_line_views.xml",
        "views/contract_template_views.xml",
        "views/contract_views.xml",
        "views/cooperative_membership_views.xml",
        "views/product_category_views.xml",
        "views/product_template_views.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
        "views/service_invoicing_views.xml",
        "views/service_invoicing_views.xml",
        "views/subscription_request_views.xml",
        "wizards/assign_pack_to_partner.xml",
        "wizards/pack_product_creator.xml",
        "wizards/service_invoicing_action.xml",
        "wizards/service_invoicing_action_create.xml",
        "views/menus.xml",
    ],
    "post_init_hook": "post_setup_intercompany_invoicing_config",
    # only loaded in demonstration mode
    "demo": [
        "demo/product_template_demo.xml",
        # "demo/subscription_request_demo.xml"
    ],
}
