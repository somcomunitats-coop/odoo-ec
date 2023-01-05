{
    'name': "Energy Communities integration with authoidc",
    'version': '14.0.0.0.0',
    'depends': [
        'auth_oauth',
        'auth_oidc'
    ],
    'author': "Coopdevs Treball SCCL & Som Energia SCCL",
    'website': 'https://somenergia.coop',
    'category': "Cooperative management",
    'description': """
    Energy Communities integration with authoidc.
    """,
    "license": "AGPL-3",
    'demo': [

    ],
    'data': [
        'views/auth_oauth_views.xml',
        'data/auth_oauth_provider_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}


