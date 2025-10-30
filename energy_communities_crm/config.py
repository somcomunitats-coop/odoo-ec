COMPANY_CREATION_WIZARD_DEFAULT_TAXES = {
    "general": {
        "default_sale_tax_id": "l10n_es.account_tax_template_s_iva21s",
        "default_purchase_tax_id": "l10n_es.account_tax_template_p_iva21_sc",
    },
    "canary": {
        "default_sale_tax_id": "l10n_es_igic.account_tax_template_igic_r_7",
        "default_purchase_tax_id": "l10n_es_igic.account_tax_template_igic_sop_7",
    },
}
_MAP__LEAD_METADATA__COMPANY_CREATION_WIZARD = {
    "ce_name": "name",
    "ce_fiscal_name": "legal_name",
    "ce_description": "landing_short_description",
    "ce_long_description": "landing_long_description",
    "ce_address": "street",
    "ce_zip": "zip_code",
    "ce_city": "city",
    "ce_state": "state_id",
    "email_from": "email",
    "contact_phone": "phone",
    "current_lang": "default_lang_id",
    "ce_services": "energy_action_mids",
    "ce_number_of_members": "ce_number_of_members",
    "ce_status": "ce_member_status",
    "ce_constitution_status": "ce_status",
    "ce_why_become_cooperator": "landing_why_become_cooperator",
    "ce_become_cooperator_process": "landing_become_cooperator_process",
    "ce_primary_image_file": "landing_primary_image_file",
    "ce_secondary_image_file": "landing_secondary_image_file",
    "ce_logo_image_file": "landing_logo_file",
    "ce_type": "landing_community_type",
    "ce_legal_form": "legal_form",
    "ce_creation_date": "foundation_date",
    "ce_vat": "vat",
    "ce_web_url": "website",
    "ce_twitter_url": "ce_twitter_url",
    "ce_instagram_url": "ce_instagram_url",
    "ce_facebook_url": "ce_facebook_url",
    "ce_telegram_url": "ce_telegram_url",
    "ce_mastodon_url": "ce_mastodon_url",
    "ce_bluesky_url": "ce_bluesky_url",
    "comments": "comments",
    "coordinator_id": "coordinator_id",
    "coordinator_name": "coordinator_name",
    "ce_iban_1": "ce_iban_1",
    "ce_member_recurrent_contribution_date": "ce_member_recurrent_contribution_date",
}
_LEAD_METADATA__DATE_FIELDS = [
    "ce_creation_date",
    "ce_member_recurrent_contribution_date",
]
_LEAD_METADATA__ENERGY_TAGS_FIELDS = ["ce_services"]
_LEAD_METADATA__LANG_FIELDS = ["current_lang"]
_LEAD_METADATA__EXTID_FIELDS = [
    "ce_state",
    "ce_primary_image_file",
    "ce_secondary_image_file",
    "ce_logo_image_file",
]
_LEAD_METADATA__IMAGE_FIELDS = [
    "ce_primary_image_file",
    "ce_secondary_image_file",
    "ce_logo_image_file",
]
