from odoo.tools.translate import _

COOP_SHARE_PRODUCT_CATEG_REF = "cooperator.product_category_company_share"
COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF = (
    "energy_communities_cooperator.product_category_company_voluntary_share"
)
PAYMENT_METHOD_SEPA = "account_banking_sepa_direct_debit.sepa_direct_debit"
PAYMENT_METHOD_TRANSFER = "account.account_payment_method_manual_in"

MAPPING__PAYMENT_METHOD = {
    "sepa": PAYMENT_METHOD_SEPA,
    "transfer": PAYMENT_METHOD_TRANSFER,
}

MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF = {
    "member": COOP_SHARE_PRODUCT_CATEG_REF,
    "company_member": COOP_SHARE_PRODUCT_CATEG_REF,
    "invited": COOP_SHARE_PRODUCT_CATEG_REF,
    "company_invited": COOP_SHARE_PRODUCT_CATEG_REF,
    "voluntary": COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF,
}
MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_TITLE = {
    "member": _("Become Cooperator of {company_name} ") + _("member_eu_ES"),
    "company_member": _("Become Cooperator of {company_name} ") + _("member_eu_ES"),
    "invited": _("Become Invited of {company_name} ") + _("invited_eu_ES"),
    "company_invited": _("Become Invited of {company_name} ") + _("invited_eu_ES"),
    "voluntary": _("Voluntary Share of {company_name} ") + _("vol_share_eu_es"),
}
MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE = {
    "member": "<p>"
    + _("This form allow you to request be member of the community: {company_name} ")
    + _("member_ccee_eu_ES")
    + ".</p>",
    "company_member": "<p>"
    + _("This form allow you to request be member of the community: {company_name} ")
    + _("member_ccee_eu_ES")
    + ".</p>",
    "invited": "<p>"
    + _("This form allow you to request be invited of the community: {company_name} ")
    + _("invited_ccee_eu_ES")
    + ".</p>",
    "company_invited": "<p>"
    + _("This form allow you to request be invited of the community: {company_name} ")
    + _("invited_ccee_eu_ES")
    + ".</p>",
    "voluntary": "<p>"
    + _("This form allow you to request be voluntary of the community: {company_name} ")
    + _("vol_share_eu_es")
    + ".</p>",
}
MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_TRANSFER = {
    "member": _(
        "<p id='transfer_text'>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>{product_price}</span>{currency_symbol} by follow the steps you will receive by email.</p>"
    ),
    "company_member": _(
        "<p id='transfer_text'>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>{product_price}</span>{currency_symbol} by follow the steps you will receive by email.</p>"
    ),
    "invited": _(
        "<p id='transfer_text'>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>{product_price}</span>{currency_symbol} by follow the steps you will receive by email.</p>"
    ),
    "company_invited": _(
        "<p id='transfer_text'>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>{product_price}</span>{currency_symbol} by follow the steps you will receive by email.</p>"
    ),
    "voluntary": _(
        "<p id='transfer_text'>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>{product_price}</span>{currency_symbol} by follow the steps you will receive by email.</p>"
    ),
}
MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_SEPA = {
    "member": _(
        "<p id='sepa_text'>To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span id='prodPrice'>{product_price}</span>{currency_symbol}</p>"
    ),
    "company_member": _(
        "<p id='sepa_text'>To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span id='prodPrice'>{product_price}</span>{currency_symbol}</p>"
    ),
    "invited": _(
        "<p id='sepa_text'>To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span id='prodPrice'>{product_price}</span>{currency_symbol}</p>"
    ),
    "company_invited": _(
        "<p id='sepa_text'>To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span id='prodPrice'>{product_price}</span>{currency_symbol}</p>"
    ),
    "voluntary": _(
        "<p id='sepa_text'>To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span id='prodPrice'>{product_price}</span>{currency_symbol}</p>"
    ),
}

SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT = (
    "<p>"
    + _(
        "Once you are a member you can enjoy the services available from the community and be part of a movement of social and energy model transformation."
    )
    + "</p>"
)

GENDER_OPTIONS = [
    {"id": "", "name": _("Select your gender")},
    {"id": "male", "name": _("Male")},
    {"id": "female", "name": _("Female")},
    {"id": "other", "name": _("Other")},
    {"id": "not_binary", "name": _("Not binary")},
    {"id": "not_share", "name": _("I prefer to not share it")},
]

MAPPING__BASE__DEFAULT_FORM_FIELDS = {
    "email": {
        "value": "",
        "key": "email",
        "label": _("Email"),
        "required": True,
        "disabled": False,
    },
    "firstname": {
        "value": "",
        "label": _("Firstname"),
        "required": True,
        "disabled": False,
    },
    "lastname": {
        "value": "",
        "label": _("Lastname"),
        "required": True,
        "disabled": False,
    },
    "gender": {
        "value": "",
        "label": _("Gender"),
        "required": True,
        "options": GENDER_OPTIONS,
        "disabled": False,
    },
    "birthdate": {
        "value": "",
        "label": _("Birthdate"),
        "required": True,
        "disabled": False,
    },
    "phone": {
        "value": "",
        "label": _("Phone"),
        "required": True,
        "disabled": False,
    },
    "lang": {
        "value": "",
        "label": _("Language"),
        "required": True,
        "disabled": False,
        "options": [],
    },
    "vat": {
        "value": "",
        "label": _("VAT"),
        "required": True,
        "disabled": False,
    },
    "address": {
        "value": "",
        "label": _("Address"),
        "required": True,
        "disabled": False,
    },
    "city": {
        "value": "",
        "label": _("City"),
        "required": True,
        "disabled": False,
    },
    "zip_code": {
        "value": "",
        "label": _("Postal Code"),
        "required": True,
        "disabled": False,
    },
    "country_id": {
        "value": "",
        "label": _("Country"),
        "required": True,
        "disabled": False,
        "options": [],
    },
    "share_product_id": {
        "value": "product.id",
        "label": _("Share Product"),
        "required": True,
        "disabled": False,
        "options": [],
    },
    "ordered_parts": {
        "value": "",
        "label": _("Ordered Parts"),
        "required": True,
        "disabled": False,
    },
    "total_price": {
        "value": "",
        "label": _("Total Price"),
        "required": True,
        "disabled": True,
    },
    "privacy_policy": {
        "value": False,
        "label": _("Privacy Policy"),
        "required": True,
        "disabled": False,
        "description": "",
    },
    "payment_method": {
        "value": "",
        "label": _("Payment Method"),
        "required": True,
        "disabled": True,
        "options": [
            {"id": "sepa", "name": _("SEPA")},
            {"id": "transfer", "name": _("Transfer")},
        ],
    },
    "iban": {
        "value": "",
        "label": _("IBAN"),
        "required": True,
        "disabled": False,
    },
    "conditions_payment": {
        "value": False,
        "label": _("Conditions Payment"),
        "required": True,
        "disabled": False,
        "description": _(
            "I confirm that the holder of the bank account, whether myself or another person, authorizes the direct debit of the bills."
        ),
    },
}

MAPPING__MEMBER__DEFAULT_FORM_FIELDS = MAPPING__BASE__DEFAULT_FORM_FIELDS
MAPPING__COMPANY_MEMBER__DEFAULT_FORM_FIELDS = MAPPING__BASE__DEFAULT_FORM_FIELDS
MAPPING__INVITED__DEFAULT_FORM_FIELDS = MAPPING__BASE__DEFAULT_FORM_FIELDS
MAPPING__COMPANY_INVITED__DEFAULT_FORM_FIELDS = MAPPING__BASE__DEFAULT_FORM_FIELDS
MAPPING__VOLUNTARY__DEFAULT_FORM_FIELDS = MAPPING__BASE__DEFAULT_FORM_FIELDS

MAPPING__SUBSCRIPTION_MODE__DEFAULT_FORM_FIELDS = {
    "member": MAPPING__MEMBER__DEFAULT_FORM_FIELDS,
    "company_member": MAPPING__COMPANY_MEMBER__DEFAULT_FORM_FIELDS,
    "invited": MAPPING__INVITED__DEFAULT_FORM_FIELDS,
    "company_invited": MAPPING__COMPANY_INVITED__DEFAULT_FORM_FIELDS,
    "voluntary": MAPPING__VOLUNTARY__DEFAULT_FORM_FIELDS,
}
MAPPING__SUBSCRIPTION_MODE__MEMBERSHIP_MODE = {
    "member": "cooperator",
    "company_member": "cooperator",
    "invited": "invited",
    "company_invited": "invited",
    "voluntary": "voluntary",
}
MAPPING__SUBSCRIPTION_MODE__MEMBERTYPE_MODE = {
    "member": "individual",
    "company_member": "company",
    "invited": "individual",
    "company_invited": "company",
    "voluntary": "individual_company",
}
