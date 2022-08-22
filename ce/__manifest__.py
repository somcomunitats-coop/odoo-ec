{
    'name': "Comunitats Energètiques customizations",
    'version': '12.0.0.0.4',
    'depends': [
        'base_rest_base_structure',
        'cooperator_website',
        'auth_keycloak',
        'contacts',
        'base_user_role',
        'auth_api_key',
        'crm',
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
        'views/res_config_settings.xml',
        'views/auth_oauth_provider_views.xml',
        'views/res_company_views.xml',
        'views/website_subscription_template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}


