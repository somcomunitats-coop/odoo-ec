import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    install_requires=[
        "odoo14-addon-account-payment-cooperator @ git+https://git.coopdevs.org/coopdevs/comunitats-energetiques/odoo-ce@v14.0.1.1.3#egg=odoo14-addon-account-payment-cooperator&subdirectory=setup/account_payment_cooperator",
        "odoo14-addon-account-banking-mandate-cooperator @ git+https://git.coopdevs.org/coopdevs/comunitats-energetiques/odoo-ce@v14.0.1.1.3#egg=odoo14-addon-account-banking-mandate-cooperator&subdirectory=setup/account_banking_mandate_cooperator",
    ],
    odoo_addon={
        "depends_override": {
            "account_banking_mandate_cooperator": "odoo14-addon-account-banking-mandate-cooperator",
            "account_lock_date_update": "odoo14-addon-account-lock-date-update==14.0.2.0.1.dev10",
            "account_payment_cooperator": "odoo14-addon-account-payment-cooperator",
            "account_reconciliation_widget": "odoo14-addon-account-reconciliation-widget==14.0.2.0.2",
            "community_maps": "odoo14-addon-community-maps==14.0.0.1.2",
            "crm_metadata": "odoo14-addon-crm-metadata==14.0.1.0.0",
            "crm_metadata_rest_api": "odoo14-addon-crm-metadata-rest-api==14.0.1.0.0",
            "crm_rest_api": "odoo14-addon-crm-rest-api==14.0.1.0.1.dev1",
            "mail_multicompany": "odoo14-addon-mail-multicompany==14.0.0.1.1.dev2",
            "metadata": "odoo14-addon-metadata==14.0.0.0.1",
            "partner_multi_company": "odoo14-addon-partner-multi-company==14.0.1.0.1.dev4",
        },
    }
)
