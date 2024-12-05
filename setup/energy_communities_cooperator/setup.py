import setuptools

setuptools.setup(
    setup_requires=["setuptools-odoo"],
    odoo_addon={
        "depends_override": {
            "account_multicompany_easy_creation": "odoo-addon-account-multicompany-easy-creation==16.0.1.0.0.8",
            "cooperator": "odoo-addon-cooperator==16.0.1.1.0.4",
            "cooperator_account_payment": "odoo-addon-cooperator-account-payment==16.0.0.1.0",
            "cooperator_account_banking_mandate": "odoo-addon-cooperator-account-banking-mandate==16.0.0.1.1",
            "l10n_es_cooperator": "odoo-addon-l10n-es-cooperator==16.0.1.0.0.4",
            "energy_communities": "odoo14-addon-energy-communities>=16.0.0.0.1",
        },
    },
)
