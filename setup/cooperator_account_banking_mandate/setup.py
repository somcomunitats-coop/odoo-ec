import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "cooperator_account_payment": "odoo14-addon-cooperator-account-payment==14.0.1.0.1",
        },
    }
)
