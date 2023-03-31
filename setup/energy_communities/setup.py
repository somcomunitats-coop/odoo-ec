import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "mail_multicompany": "odoo14-addon-mail-multicompany==14.0.0.1.1.dev2",
            "partner_multi_company": "odoo14-addon-partner-multi-company==14.0.1.0.1.dev4",
            },
    },
)
