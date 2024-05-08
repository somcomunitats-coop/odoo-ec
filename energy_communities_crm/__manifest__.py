{
    "name": "energy_communities_crm",
    "summary": """
        Use CRM for coordinators and energy communities
    """,
    "description": """
        Use CRM for coordinators and energy communities
    """,
    "author": "Som Comunitats",
    "website": "https://coopdevs.org",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Sales/CRM",
    "version": "14.0.1.0.1",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "base",
        "crm",
        "crm_metadata",
        "crm_metadata_rest_api",
        "crm_rest_api",
        "sales_team",
        "energy_communities",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule_data.xml",
        "data/mail_template_data.xml",
        "views/crm_lead_metadata_mapping_views.xml",
        "views/crm_lead_views.xml",
        "views/crm_stage_views.xml",
        "views/crm_tag_views.xml",
        "views/crm_team_views.xml",
        "views/energy_communities_crm_lead_views.xml",
        "views/menus.xml",
        "views/website_community_data_template.xml",
        "wizards/assign_crm_to_coordinator_company.xml",
    ],
    "post_init_hook": "post_setup_multicompany_crm",
    # only loaded in demonstration mode
    "demo": [],
}
