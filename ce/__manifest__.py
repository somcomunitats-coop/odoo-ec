{
    'name': "Comunitats Energètiques customizations",
    'version': '12.0.0.0.3',
    'depends': [
        'auth_keycloak',
        'contacts',
        'easy_my_coop_website',
    ],
    'author': "Coopdevs Treball SCCL & Som Energia SCCL",
    'website': 'https://somenergia.coop',
    'category': "Cooperative management",
    'description': """
    Odoo Comunitats Energètiques customizations.
    """,
    "license": "AGPL-3",
    'demo': [
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


