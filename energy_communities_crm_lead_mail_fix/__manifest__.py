{
    "name": "Energy communities CRM Lead Mail Body Fix",
    "version": "16.0.0.1.0",
    "category": "Sales/CRM",
    "summary": "Fix missing email body in CRM leads created from emails without existing partners",
    "description": """
This module fixes the issue where email body content is lost when creating CRM leads from incoming emails when no matching partner exists in the database.

Features:
- Automatically creates a partner when processing emails without existing contacts
- Marks auto-created partners with a special tag for identification
- Ensures email body and attachments are properly saved in lead chatter
- Maintains compatibility with existing lead creation workflows
    """,
    "author": "SOM Comunitats",
    "website": "https://git.coopdevs.org/coopdevs/comunitats-energetiques/odoo-ce",
    "depends": ["crm", "mail", "mass_mailing"],
    "data": [
        "data/partner_tags.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
