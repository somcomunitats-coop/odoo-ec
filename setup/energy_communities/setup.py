import setuptools

setuptools.setup(
    setup_requires=["setuptools-odoo"],
    odoo_addon={
        "depends_override": {
            "account_banking_mandate": "odoo-addon-account-banking-mandate==16.0.1.3.3",
            "account_lock_date_update": "odoo-addon-account-lock-date-update==16.0.1.0.1.12",
            "account_multicompany_easy_creation": "odoo-addon-account-multicompany-easy-creation==16.0.1.0.0.8",
            "account_payment_order": "odoo-addon-account-payment-order==16.0.1.12.3",
            # "account_reconciliation_widget": "odoo14-addon-account-reconciliation-widget==14.0.2.0.2",
            "auth_api_key": "odoo-addon-auth-api-key==16.0.1.0.0.7",
            "auth_oidc": "odoo-addon-auth-oidc==16.0.1.2.1",
            "base_rest": "odoo-addon-base-rest==16.0.1.0.2.2",
            "base_technical_features": "odoo-addon-base-technical-features==16.0.1.0.0.10",
            "base_user_role": "odoo-addon-base-user-role==16.0.1.4.1.1",
            "base_user_role_company": "odoo-addon-base-user-role-company==16.0.1.2.0",
            "community_maps": "odoo-addon-community-maps==16.0.1.0.0",
            # TODO: Related aeat installation problems
            "l10n_es_aeat_sii_oca": "odoo-addon-l10n-es-aeat-sii-oca==16.0.2.0.1",
            "mail_multicompany": "odoo-addon-mail-multicompany==16.0.2.0.0.2",
            "metadata": "odoo-addon-metadata==16.0.1.0.0",
            "partner_firstname": "odoo-addon-partner-firstname==16.0.1.0.3.1",
            "partner_multi_company": "odoo-addon-partner-multi-company==16.0.1.1.0.4",
            "queue_job": "odoo-addon-queue-job>=16.0.2.6.8",
        },
    },
)
