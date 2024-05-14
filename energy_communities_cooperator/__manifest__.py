{
    "name": "energy_communities_cooperator",
    "summary": """
        Energy communities cooperative membership management
    """,
    "description": """
        Energy communities cooperative membership management
    """,
    "author": "Som Comunitats SCCL",
    "website": "https://coopdevs.org",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Cooperative management",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": ["base", "cooperator", "l10n_es_cooperator", "energy_communities"],
    # always loaded
    "data": [
        # 'security/ir.model.access.csv',
        "views/account_move_views.xml",
        "views/cooperative_membership_views.xml",
        "views/operation_request_views.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "views/subscription_request_view.xml",
        "data/mail_template_update_data.xml",
        "data/ir_config_parameter_data.xml",
    ],
    # only loaded in demonstration mode
    "demo": [],
}
