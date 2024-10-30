import setuptools

setuptools.setup(
    setup_requires=["setuptools-odoo"],
    odoo_addon={
        "depends_override": {
            "cooperator": "odoo-addon-cooperator>=15.0.0.0.1",
            "account_banking_mandate": "odoo-addon-account-banking-mandate==15.0.2.1.4",
            "account_banking_sepa_direct_debit": "odoo-addon-account-banking-sepa-direct-debit==15.0.2.3.1",
        },
    },
)
