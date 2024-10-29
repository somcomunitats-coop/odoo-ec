import setuptools

setuptools.setup(
    setup_requires=["setuptools-odoo"],
    odoo_addon={
        "depends_override": {
            "cooperator": "odoo-addon-cooperator>=15.0.0.0.1",
            "account_payment_partner": "odoo-addon-account-payment-partner==15.0.1.3.2",
        }
    },
)
