import setuptools

setuptools.setup(
    setup_requires=["setuptools-odoo"],
    odoo_addon={
        "depends_override": {
            "account_banking_mandate": "odoo-addon-account-banking-mandate>=15.0.2.1.4",
            "account_lock_date_update": "odoo-addon-account-lock-date-update==15.0.1.0.2",
            "account_multicompany_easy_creation": "odoo-addon-account-multicompany-easy-creation==15.0.1.0.0.5",
            "account_payment_order": "odoo-addon-account-payment-order==15.0.2.7.1.1",
            # "account_reconciliation_widget": "odoo14-addon-account-reconciliation-widget==14.0.2.0.2",
            "auth_api_key": "odoo-addon-auth-api-key==15.0.1.1.1.6",
            "auth_oidc": "odoo-addon-auth-oidc==15.0.1.1.0.3",
            "base_rest": "odoo-addon-base-rest==15.0.1.2.2.1",
            "base_technical_features": "odoo-addon-base-technical-features==15.0.1.1.0.3",
            "base_user_role": "odoo-addon-base-user-role==15.0.0.4.2",
            # "base_user_role_company": "odoo14-addon-base-user-role-company==14.0.2.0.2",
            # "community_maps": "odoo14-addon-community-maps==14.0.0.2.8",
            # "metadata": "odoo14-addon-metadata==14.0.0.0.1",
            "l10n_es_aeat_sii_oca": "odoo-addon-l10n-es-aeat-sii-oca==15.0.2.21.1",
            "mail_multicompany": "odoo-addon-mail-multicompany==15.0.0.1.0.3",
            "partner_firstname": "odoo-addon-partner-firstname>=15.0.1.1.0.4",
            "partner_multi_company": "odoo-addon-partner-multi-company==15.0.1.1.0.3",
            "queue_job": "odoo-addon-queue-job==15.0.2.3.10",
        },
    },
)
