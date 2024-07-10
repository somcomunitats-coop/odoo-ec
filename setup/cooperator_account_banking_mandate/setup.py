import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "cooperator": "odoo14-addon-cooperator>=14.0.2.1.1",
            "account_banking_mandate": "odoo14-addon-account-banking-mandate==14.0.1.2.0",
            "account_banking_sepa_direct_debit": "odoo14-addon-account-banking-sepa-direct-debit==14.0.1.3.3",
        },
    }
)
