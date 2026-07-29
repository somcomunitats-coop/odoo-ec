{
    "name": "energy_communities_l10n_es_ticketbai",
    "version": "16.0.0.1.0",
    "author": "Som IT SCCL & Som Energia SCCL",
    "website": "https://git.coopdevs.org/coopdevs/comunitats-energetiques/odoo-ce",
    "category": "TicketBAI management",
    "description": """
    Energy Communities adjustments for the compatibility of TicketBAI.
    """,
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "auto_install": False,
    "depends": [
        "energy_communities",
        "l10n_es_ticketbai",
        "l10n_es_ticketbai_api_batuz",
    ],
    "data": [
        "views/ticketbai_menu_views.xml",
    ],
}
