import setuptools

setuptools.setup(
    setup_requires=["setuptools-odoo"],
    odoo_addon={
        "depends_override": {
            "account_banking_mandate": "odoo14-addon-account-banking-mandate>=14.0.1.2.0",
            "account_lock_date_update": "odoo14-addon-account-lock-date-update==14.0.2.0.1.dev10",
            "account_multicompany_easy_creation": "odoo14-addon-account-multicompany-easy-creation==14.0.1.0.1.dev2",
            "account_payment_order": "odoo14-addon-account-payment-order==14.0.1.11.0",
            "account_reconciliation_widget": "odoo14-addon-account-reconciliation-widget==14.0.2.0.2",
            "auth_api_key": "odoo14-addon-auth-api-key==14.0.2.2.1",
            "auth_oidc": "odoo14-addon-auth-oidc==14.0.1.0.3.dev1",
            "base_rest": "odoo14-addon-base-rest==14.0.4.8.1",
            "base_technical_features": "odoo14-addon-base-technical-features==14.0.1.1.2.dev1",
            "base_user_role": "odoo14-addon-base-user-role==14.0.2.5.1",
            "base_user_role_company": "odoo14-addon-base-user-role-company==14.0.2.0.2",
            "community_maps": "odoo14-addon-community-maps==14.0.0.2.8",
            "l10n_es_aeat_sii_oca": "odoo14-addon-l10n-es-aeat-sii-oca==14.0.2.10.2",
            "mail_multicompany": "odoo14-addon-mail-multicompany==14.0.0.1.1.dev2",
            "metadata": "odoo14-addon-metadata==14.0.0.0.1",
            "partner_firstname": "odoo14-addon-partner-firstname>=14.0.1.1.1.dev4",
            "partner_multi_company": "odoo14-addon-partner-multi-company==14.0.1.0.1.dev4",
            "queue_job": "odoo14-addon-queue-job==14.0.3.1.5",
        },
    },
)
