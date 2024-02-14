import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "account_lock_date_update": "odoo14-addon-account-lock-date-update==14.0.2.0.1.dev10",
            "account_reconciliation_widget": "odoo14-addon-account-reconciliation-widget==14.0.2.0.2",
            "community_maps": "odoo14-addon-community-maps==14.0.0.2.1",
            "cooperator_account_payment": "odoo14-addon-cooperator-account-payment==14.0.1.1.0",
            "cooperator_account_banking_mandate": "odoo14-addon-cooperator-account-banking-mandate==14.0.1.1.1",
            "energy_selfconsumption": "odoo14-addon-energy-selfconsumption==14.0.3.6.0",
            "crm_metadata": "odoo14-addon-crm-metadata==14.0.1.0.0",
            "crm_metadata_rest_api": "odoo14-addon-crm-metadata-rest-api==14.0.1.0.2",
            "crm_rest_api": "odoo14-addon-crm-rest-api==14.0.1.0.2",
            "l10n_es_aeat_sii_oca": "odoo14-addon-l10n-es-aeat-sii-oca==14.0.2.8.1",
            "mail_multicompany": "odoo14-addon-mail-multicompany==14.0.0.1.1.dev2",
            "metadata": "odoo14-addon-metadata==14.0.0.0.1",
            "partner_multi_company": "odoo14-addon-partner-multi-company==14.0.1.0.1.dev4",
            "queue_job": "odoo14-addon-queue-job==14.0.3.1.5",
        },
    }
)
