{
    "name": "Mass mailing - Energy Communities",
    "summary": """
        Use mass_mailing on a energy communities setup
    """,
    "description": """
        Use mass_mailing on a energy communities setup
    """,
    "author": "Som Comunitats",
    "website": "https://coopdevs.org",
    "category": "Marketing",
    "version": "16.0.0.1.1",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "sale",
        "energy_communities",
        "mass_mailing",
        "mass_mailing_partner",
        "mass_mailing_list_dynamic",
    ],
    # always loaded
    "data": [
        "security/ir_rule_data.xml",
        "security/res_users_role_data.xml",
        "views/mailing_mailing_views_menus.xml",
        "views/mailing_mailing_views.xml",
        "views/mailing_list_views.xml",
        "views/mailing_contact_views.xml",
        "views/utm_views.xml",
        "wizards/mail_compose_message_views.xml",
        "wizards/partner_mail_list_wizard.xml",
    ],
}
