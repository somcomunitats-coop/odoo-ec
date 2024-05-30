{
    "name": "energy_communities_demo",
    "summary": """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    "description": """
        Long description of module's purpose
    """,
    "author": "Som Comunitats",
    "website": "https://coopdevs.org",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Uncategorized",
    "version": "14.0.0.0.0",
    # any module necessary for this one to work correctly
    "depends": [
        "base",
        "energy_communities_cooperator",
        "energy_communities_mass_mailing",
        "energy_communities_crm",
    ],
    # always loaded
    "data": [
        # 'security/ir.model.access.csv',
        "views/views.xml",
        "views/templates.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
        "demo/res_lang_demo.xml",
        "demo/res_company_demo.xml",
        "demo/res_user_demo.xml",
        "demo/subscription_request_demo.xml",
        "demo/energy_selfconsumption_demo.xml",
    ],
}
