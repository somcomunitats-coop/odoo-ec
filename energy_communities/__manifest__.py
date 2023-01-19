{
    'name': "Energy Community",
    'version': '14.0.1.0.0',
    'depends': [
        'account',
        'cooperator',
        'base_user_role',
        'base_user_role_company',
        'l10n_es_cooperator',
        'auth_oidc',
        'contacts',
        'base_rest',
        'auth_api_key',
        'crm',
    ],
    'author': "Coopdevs Treball SCCL & Som Energia SCCL",
    'website': 'https://somenergia.coop',
    'category': "Cooperative management",
    'description': """
    Energy Communities customizations.
    """,
    "license": "AGPL-3",
    'demo': [
        'demo/demo_data.xml',
    ],
    'data': [
        'security/ir_rules_data.xml',
        'security/res_users_role_data.xml',
        'data/utm_data.xml',
        'data/crm_lead_tag.xml',
        'views/crm_lead_views.xml',
        'views/res_company_views.xml',
        'views/website_subscription_template.xml',
        'views/ce_views.xml',
        'views/utm_views.xml',
        'views/menus.xml',
        'data/mail_template_data.xml',
        'data/mail_template_update_data.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}


