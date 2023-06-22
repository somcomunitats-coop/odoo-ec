# -*- coding: utf-8 -*-
{
    "name": "Cooperator Account Banking Mandate",
    "version": "14.0.1.0.3",
    "license": "AGPL-3",
    "summary": """
        This module adds mandate selection to cooperator subscription request.""",
    "author": "Som IT Cooperatiu SCCL",
    "category": "Banking addons",
    "depends": ["cooperator", "cooperator_account_payment", "account_banking_mandate",
                "account_banking_sepa_direct_debit"],
    "data": [
        "views/subscription_request_views.xml",
    ],
    "installable": True,
}
