{
    'name': "Comunitats Energètiques customizations",
    'version': '12.0.0.0.0',
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
        'data/auth_keycloak_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}


