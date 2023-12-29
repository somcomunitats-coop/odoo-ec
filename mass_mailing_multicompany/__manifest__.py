{
    "name": "Mass mailing multicompany",
    "summary": """
        Use mass_mailing on a multicompany odoo setup
    """,
    "description": """
        Use mass_mailing on a multicompany odoo setup
    """,
    "author": "Som Comunitats",
    "website": "https://coopdevs.org",
    "category": "Marketing",
    "version": "14.0.0.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "base",
        "mass_mailing",
        # 'utm',
    ],
    # always loaded
    "data": [
        # 'security/ir_rule_data.xml',
        # 'views/mailing_mailing_views.xml',
        # 'views/mailing_list_views.xml',
        # 'views/mailing_contact_views.xml',
        # 'views/utm_views.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
