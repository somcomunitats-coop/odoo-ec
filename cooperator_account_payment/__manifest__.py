# -*- coding: utf-8 -*-
{
    "name": "Cooperator Account Payment",
    "version": "14.0.1.0.2",
    "license": "AGPL-3",
    "summary": """
        This module adds support for payment mode to cooperator.""",
    "author": "Som IT Cooperatiu SCCL",
    "category": "Banking addons",
    "depends": ["cooperator", "account_payment_partner"],
    "data": [
        "views/product_template_views.xml",
        "views/subscription_request_views.xml",
    ],
    "installable": True,
}
