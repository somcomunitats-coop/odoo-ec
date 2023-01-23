{
    'name': "Comunitats Energètiques customizations",
    'version': '12.0.0.0.16',
    'depends': [
        'base_rest_base_structure',
        'l10n_es_cooperator',
        'auth_keycloak',
        'contacts',
        'base_rest',
        'base_user_role',
        'auth_api_key',
        'crm',
        'community_maps',
    ],
    'author': "Coopdevs Treball SCCL & Som Energia SCCL",
    'website': 'https://somenergia.coop',
    'category': "Cooperative management",
    'description': """
    Odoo Comunitats Energètiques customizations.
    """,
    "license": "AGPL-3",
    'demo': [
        'demo/demo_data.xml',
    ],
    'data': [
        'security/ir_rules_data.xml',
        'data/res_groups_data.xml',
        'data/auth_keycloak_data.xml',
        'data/ir_config_parameter_data.xml',
        'data/res_company_data.xml',
        'data/utm_data.xml',
        'data/crm_lead_tag.xml',
        'data/crm_maps_data.xml',
        'views/res_config_settings.xml',
        'views/crm_lead_views.xml',
        'views/auth_oauth_provider_views.xml',
        'views/res_company_views.xml',
        'views/website_subscription_template.xml',
        'views/ce_views.xml',
        'views/utm_views.xml',
        'views/menus.xml',
        'views/res_users.xml',
        'views/cm_place.xml',
        'data/mail_template_data.xml',
        'data/mail_template_update_data.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}


