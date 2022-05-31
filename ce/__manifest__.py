{
    'name': "Comunitats Energètiques customizations",
    'version': '12.0.0.0.1',
    'depends': [
        'auth_keycloak',
        'contacts',
    ],
    'author': "Coopdevs Treball SCCL & Som Energia SCCL",
    'website': 'https://coopdevs.org, https://somenergia.coop',
    'category': "Cooperative management",
    'description': """
    Odoo Comunitats Energètiques customizations.
    """,
    "license": "AGPL-3",
    'demo': [
    ],
    'data': [
        'security/ir_rules_data.xml',
        'data/auth_keycloak_data.xml',
        'data/res_company_data.xml',
        'data/res_groups_data.xml',
        'views/auth_oauth_provider_views.xml',
        'views/res_company_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}


