import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "energy_communities": "odoo14-addon-energy-communities>=14.0.9.0.0",
            "cooperator": "odoo14-addon-cooperator==14.0.2.1.1",
            "cooperator_account_payment": "odoo14-addon-cooperator-account-payment==14.0.1.1.0",
            "cooperator_account_banking_mandate": "odoo14-addon-cooperator-account-banking-mandate==14.0.1.1.1",
        },
    },
)
