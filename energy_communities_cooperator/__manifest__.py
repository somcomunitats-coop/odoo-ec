{
    "name": "energy_communities_cooperator",
    "summary": """
        Energy communities cooperative membership management
    """,
    "description": """
        Energy communities cooperative membership management
    """,
    "author": "Som Comunitats SCCL",
    "website": "https://git.coopdevs.org/coopdevs/comunitats-energetiques/odoo-ce",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Cooperative management",
    "version": "16.0.0.5.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "base",
        "account_multicompany_easy_creation",
        "contract_variable_quantity",
        "cooperator",
        "cooperator_account_payment",
        "cooperator_account_banking_mandate",
        "l10n_es_cooperator",
        "energy_communities",
        "energy_communities_crm",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule_data.xml",
        "report/reports.xml",
        "report/voluntary_share_interest_return_report.xml",
        "data/product_data.xml",
        "security/res_users_role_data.xml",
        "data/mail_template_data.xml",
        "data/mail_template_update_data.xml",
        "data/ir_config_parameter_data.xml",
        "views/menus.xml",
        "views/account_move_views.xml",
        "views/share_line_views.xml",
        "views/cooperative_membership_views.xml",
        "views/operation_request_views.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "views/res_company_views.xml",
        "views/voluntary_share_interest_return_views.xml",
        "views/subscription_request_view.xml",
        "views/website_subscription_template.xml",
        "views/res_config_settings_view.xml",
        "wizards/multicompany_easy_creation.xml",
        "wizards/voluntary_share_interest_return.xml",
    ],
    # only loaded in demonstration mode
    "demo": ["demo/res_company_demo.xml"],
    "assets": {
        "web.assets_common": [
            "energy_communities_cooperator/static/src/js/cooperator.js",
        ]
    },
}
# "demo/account_payment_mode_demo.xml",
