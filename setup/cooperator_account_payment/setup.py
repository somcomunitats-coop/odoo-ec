import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "cooperator": "odoo14-addon-cooperator>=14.0.2.1.1",
            "account_payment_partner": "odoo14-addon-account-payment-partner==14.0.1.7.0",
        }
    }
)
