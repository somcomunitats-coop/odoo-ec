import setuptools

setuptools.setup(
    setup_requires=["setuptools-odoo"],
    odoo_addon={
        "depends_override": {
            # TODO: Missing v15 versions
            # "cooperator": "odoo14-addon-cooperator>=14.0.2.1.1",
            "account_banking_mandate": "odoo-addon-account-banking-mandate>=15.0.2.1.4",
        }
    },
)
