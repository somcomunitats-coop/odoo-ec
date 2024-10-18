{
    "name": "Cooperator Account Banking Mandate",
    "version": "16.0.0.0.1",
    "license": "AGPL-3",
    "summary": """
        This module adds mandate selection to cooperator subscription request.""",
    "author": "Som IT Cooperatiu SCCL",
    "category": "Banking addons",
    "website": "https://coopdevs.org",
    "depends": [
        "cooperator",
        "account_banking_mandate",
        "account_banking_sepa_direct_debit",
    ],
    "data": [
        "views/subscription_request_views.xml",
    ],
    "installable": True,
}
