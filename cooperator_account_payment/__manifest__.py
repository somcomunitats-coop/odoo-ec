{
    "name": "Cooperator Account Payment",
    "version": "16.0.0.0.1",
    "license": "AGPL-3",
    "summary": """
        This module adds support for payment mode to cooperator.""",
    "author": "Som IT Cooperatiu SCCL",
    "category": "Banking addons",
    "website": "https://coopdevs.org",
    "depends": ["cooperator", "account_payment_partner"],
    "data": [
        "views/product_template_views.xml",
        "views/subscription_request_views.xml",
    ],
    "installable": True,
}
