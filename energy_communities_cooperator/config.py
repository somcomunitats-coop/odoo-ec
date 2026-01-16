from odoo.tools.translate import _

COOP_SHARE_PRODUCT_CATEG_REF = "cooperator.product_category_company_share"
COOP_SHARE_PRODUCT_CATEG_REF_ASSOCIATIONS = (
    "energy_communities.product_category_share_recurring_fee_pack"
)
COOP_SHARE_INVITED_PRODUCT_CATEG_REF = (
    "energy_communities_cooperator.product_category_company_invited_share"
)
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
    "member_associations": COOP_SHARE_PRODUCT_CATEG_REF_ASSOCIATIONS,
    "company_member": COOP_SHARE_PRODUCT_CATEG_REF,
    "invited": COOP_SHARE_INVITED_PRODUCT_CATEG_REF,
    "company_invited": COOP_SHARE_INVITED_PRODUCT_CATEG_REF,
    "voluntary": COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF,
}

MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_TITLE = {
    "member": _("Become a member of {company_name} ") + _("member_eu_ES"),
    "member_associations": _("Become a member of {company_name} ") + _("member_eu_ES"),
    "company_member": _("Become a member of {company_name} ") + _("member_eu_ES"),
    "invited": _(
        "Register to participate in the projects and initiatives of {company_name} "
    )
    + _("invited_eu_ES"),
    "company_invited": _(
        "Register to participate in the projects and initiatives of {company_name} "
    )
    + _("invited_eu_ES"),
    "voluntary": _("Voluntary Share of {company_name} ") + _("vol_share_eu_es"),
}
SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT = (
    "<p>"
    + _(
        "Once you become a member, you will be able to use the services available to the energy community and, at the same time, be part of a movement for social transformation and a new energy model"
    )
    + "</p>"
)
SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT_VOLUNTARY = (
    "<p>"
    + _(
        "Once your request has been received, you will receive a confirmation email with instructions to follow."
    )
    + "</p>"
    + "<p>"
    + _("Note: If you are not yet a member, please complete the following forms:")
    + "<a href='/subscription/member/{external_id}'>"
    + _("INDIVIDUAL MEMBERSHIP REGISTRATION")
    + "</a>"
    + _(" and ")
    + "<a href='/subscription/company_member/{external_id}'>"
    + _("LEGAL ENTITY MEMBERSHIP REGISTRATION")
    + "</a>"
    + "</p>"
)
MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE = {
    "member": "<p>"
    + _("This form allow you to request be member of the community: {company_name} ")
    + _("member_ccee_eu_ES")
    + ".</p>"
    + SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT,
    "member_associations": "<p>"
    + _("This form allow you to request be member of the community: {company_name} ")
    + _("member_ccee_eu_ES")
    + ".</p>"
    + SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT,
    "company_member": "<p>"
    + _("This form allow you to request be member of the community: {company_name} ")
    + _("member_ccee_eu_ES")
    + ".</p>"
    + SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT,
    "invited": "<p>"
    + _(
        "This is the form to register as a person/entity invited to participate in the Energy Community's projects and initiatives: {company_name} "
    )
    + _("invited_ccee_eu_ES")
    + ".</p>"
    + SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT,
    "company_invited": "<p>"
    + _(
        "This is the form to register as a person/entity invited to participate in the Energy Community's projects and initiatives: {company_name} "
    )
    + _("invited_ccee_eu_ES")
    + ".</p>"
    + SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT,
    "voluntary": "<p>"
    + _(
        "This is the form for members of {company_name} to make voluntary contributions to the share capital"
    )
    + ".</p>"
    + SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT_VOLUNTARY,
}
MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_TRANSFER = {
    "member": _(
        "<p id='transfer_text'>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>{product_price}</span>{currency_symbol} by follow the steps you will receive by email.</p>"
    ),
    "member_associations": _(
        "<p id='transfer_text'>To become a member, you must first fill out this questionnaire and then make the initial financial contribution of <span id='prodPrice'>{product_price}</span>{currency_symbol} by following the steps we will send you by email once we have received your request.</p>"
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
    "member_associations": _(
        "<p id='sepa_text'>To become a member, you must first fill out this form, where we ask you for your bank account details and authorization to issue a direct debit to collect the initial contribution of <span id='prodPrice'>{product_price}</span>{currency_symbol}</p>"
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


GENDER_OPTIONS = [
    {"id": "male", "name": _("Male")},
    {"id": "female", "name": _("Female")},
    {"id": "other", "name": _("Other")},
    {"id": "not_binary", "name": _("Not binary")},
    {"id": "not_share", "name": _("I prefer to not share it")},
]

MAPPING_FORM_SUCCESS = {
    "general": _(
        "Your subscription request has been submitted successfully. "
        "You will receive a confirmation email shortly."
    )
}

MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_COMPANY_CONTACT = {
    "company_name": {
        "class": "col-md-12",
        "type": "form_field_text",
        "value": "",
        "label": _("Company Name"),
        "required": True,
        "readonly": False,
    },
    "company_email": {
        "class": "col-md-12",
        "type": "form_field_email",
        "value": "",
        "label": _("Company Email"),
        "required": True,
        "readonly": False,
    },
    "company_email_confirmation": {
        "class": "col-md-12",
        "type": "form_field_email",
        "value": "",
        "label": _("CompanyEmail Confirmation"),
        "required": True,
        "readonly": False,
    },
}

MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PERSONAL_CONTACT = {
    "email": {
        "class": "col-md-12",
        "type": "form_field_email",
        "value": "",
        "label": _("Email"),
        "required": True,
        "readonly": False,
    },
    "email_confirmation": {
        "class": "col-md-12",
        "type": "form_field_email",
        "value": "",
        "label": _("Email Confirmation"),
        "required": True,
        "readonly": False,
    },
    "firstname": {
        "class": "col-md-6",
        "type": "form_field_text",
        "value": "",
        "label": _("Firstname"),
        "required": True,
        "readonly": False,
    },
    "lastname": {
        "class": "col-md-6",
        "type": "form_field_text",
        "value": "",
        "label": _("Lastname"),
        "required": True,
        "readonly": False,
    },
    "gender": {
        "class": "col-md-6",
        "type": "form_field_selection",
        "value": "",
        "label": _("Gender"),
        "required": True,
        "options": GENDER_OPTIONS,
        "readonly": False,
    },
    "birthdate": {
        "class": "col-md-6",
        "type": "form_field_date_past",
        "value": "",
        "label": _("Birthdate"),
        "required": True,
        "readonly": False,
    },
    "phone": {
        "class": "col-md-12",
        "type": "form_field_text",
        "value": "",
        "label": _("Phone"),
        "required": True,
        "readonly": False,
    },
    "lang": {
        "class": "col-md-12",
        "type": "form_field_selection",
        "value": "",
        "label": _("Language"),
        "required": True,
        "readonly": False,
        "options": [],
    },
}

MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_VAT = {
    "vat": {
        "class": "col-md-12",
        "type": "form_field_text",
        "value": "",
        "label": _("VAT"),
        "required": True,
        "readonly": False,
    },
}
MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_ADDRESS = {
    "address": {
        "class": "col-md-12",
        "type": "form_field_text",
        "value": "",
        "label": _("Address"),
        "required": True,
        "readonly": False,
    },
    "city": {
        "class": "col-md-6",
        "type": "form_field_text",
        "value": "",
        "label": _("City"),
        "required": True,
        "readonly": False,
    },
    "zip_code": {
        "class": "col-md-6",
        "type": "form_field_text",
        "value": "",
        "label": _("Postal Code"),
        "required": True,
        "readonly": False,
    },
    "country_id": {
        "class": "col-md-12",
        "type": "form_field_selection",
        "value": "",
        "label": _("Country"),
        "required": True,
        "readonly": False,
        "options": [],
    },
}

MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_SHARE_PRODUCT = {
    "share_product_id": {
        "class": "col-md-4",
        "type": "form_field_selection",
        "value": "product.id",
        "label": _("Share Product"),
        "required": True,
        "readonly": False,
        "options": [],
    },
    "ordered_parts": {
        "class": "col-md-3",
        "type": "form_field_number",
        "value": "",
        "label": _("Ordered Parts"),
        "required": True,
        "readonly": False,
    },
    "total_price": {
        "class": "col-md-4",
        "type": "form_field_text",
        "value": "",
        "label": _("Total Price"),
        "required": True,
        "readonly": True,
    },
    "currency_symbol": {
        "class": "col-md-1",
        "type": "form_field_text",
        "value": "company.currency_id.symbol",
        "label": "",
        "required": False,
        "readonly": True,
    },
    "payment_method": {
        "class": "col-md-12 d-none",
        "type": "form_field_selection",
        "value": "",
        "label": _("Payment Method"),
        "required": True,
        "readonly": True,
        "options": [
            {"id": "sepa", "name": _("SEPA")},
            {"id": "transfer", "name": _("Transfer")},
        ],
    },
    "iban": {
        "class": "col-md-12",
        "type": "form_field_text",
        "value": "",
        "label": _("IBAN"),
        "required": True,
        "readonly": False,
    },
    "conditions_payment": {
        "class": "col-md-12",
        "type": "form_field_checkbox",
        "value": False,
        "label": _(
            "I confirm that the holder of the bank account, whether myself or another person, authorizes the direct debit of the bills."
        ),
        "required": True,
        "readonly": False,
        "description": "",
    },
}

MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_FINANCIAL_RISK = {
    "financial_risk": {
        "class": "col-md-12",
        "type": "form_field_checkbox",
        "value": False,
        "label": _("Financial Risk"),
        "required": False,
        "readonly": False,
        "description": "",
    },
}

MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_INTERNAL_RULES = {
    "internal_rules": {
        "class": "col-md-12",
        "type": "form_field_checkbox",
        "value": "",
        "label": _("Internal Rules"),
        "required": False,
        "readonly": False,
        "description": "",
    },
}

MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_GENERIC_RULES = {
    "generic_rules": {
        "class": "col-md-12",
        "type": "form_field_checkbox",
        "value": False,
        "label": _("Generic Rules"),
        "required": False,
        "readonly": False,
        "description": "",
    },
}

MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PRIVACY_POLICY = {
    "privacy_policy": {
        "class": "col-md-12",
        "type": "form_field_checkbox",
        "value": False,
        "label": _("Privacy Policy"),
        "required": False,
        "readonly": False,
        "description": "",
    },
}

MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_CONTACT_PERSON_FUNCTION = {
    "contact_person_function": {
        "class": "col-md-12",
        "type": "form_field_text",
        "value": "",
        "label": _("Function"),
        "required": True,
        "readonly": False,
    },
}

MAPPING__MEMBER__DEFAULT_FORM_FIELDS = (
    MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PERSONAL_CONTACT
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_VAT
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_ADDRESS
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_SHARE_PRODUCT
)
MAPPING__COMPANY_MEMBER__DEFAULT_FORM_FIELDS = (
    {
        "h3_company_information": {
            "key": "h3_company_information",
            "class": "col-md-12",
            "type": "form_h3",
            "description": _("Company Information"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_COMPANY_CONTACT
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_VAT
    | {
        "h3_main_address": {
            "key": "h3_main_address",
            "class": "col-md-12",
            "type": "form_h3",
            "description": _("Main Address"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_ADDRESS
    | {
        "h3_contact_person": {
            "key": "h3_contact_person",
            "class": "col-md-12",
            "type": "form_h3",
            "description": _("Contact Person"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PERSONAL_CONTACT
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_CONTACT_PERSON_FUNCTION
    | {
        "h3_share_selection": {
            "key": "h3_share_selection",
            "class": "col-md-12",
            "type": "form_h3",
            "description": _("Share Selection"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_SHARE_PRODUCT
)
MAPPING__INVITED__DEFAULT_FORM_FIELDS = (
    MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PERSONAL_CONTACT
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_VAT
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_ADDRESS
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_SHARE_PRODUCT
)
MAPPING__COMPANY_INVITED__DEFAULT_FORM_FIELDS = (
    {
        "h3_company_information": {
            "key": "h3_company_information",
            "class": "col-md-12",
            "type": "form_h3",
            "description": _("Company Information"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_COMPANY_CONTACT
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_VAT
    | {
        "h3_main_address": {
            "key": "h3_main_address",
            "class": "col-md-12",
            "type": "form_h3",
            "description": _("Main Address"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_ADDRESS
    | {
        "h3_contact_person": {
            "key": "h3_contact_person",
            "class": "col-md-12",
            "type": "form_h3",
            "description": _("Contact Person"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PERSONAL_CONTACT
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_CONTACT_PERSON_FUNCTION
    | {
        "h3_share_selection": {
            "key": "h3_share_selection",
            "class": "col-md-12",
            "type": "form_h3",
            "description": _("Share Selection"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_SHARE_PRODUCT
)
MAPPING__VOLUNTARY__DEFAULT_FORM_FIELDS = (
    MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_VAT
    | {
        "email": {
            "class": "col-md-12",
            "type": "form_field_email",
            "value": "",
            "label": _("Email"),
            "required": True,
            "disabled": False,
        },
        "email_confirmation": {
            "class": "col-md-12",
            "type": "form_field_email",
            "value": "",
            "label": _("Email Confirmation"),
            "required": True,
            "disabled": False,
        },
        "phone": {
            "class": "col-md-12",
            "type": "form_field_text",
            "value": "",
            "label": _("Phone"),
            "required": True,
            "disabled": False,
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_SHARE_PRODUCT
)

MAPPING__SUBSCRIPTION_MODE__DEFAULT_FORM_FIELDS = {
    "member": MAPPING__MEMBER__DEFAULT_FORM_FIELDS,
    "member_associations": MAPPING__MEMBER__DEFAULT_FORM_FIELDS,
    "company_member": MAPPING__COMPANY_MEMBER__DEFAULT_FORM_FIELDS,
    "invited": MAPPING__INVITED__DEFAULT_FORM_FIELDS,
    "company_invited": MAPPING__COMPANY_INVITED__DEFAULT_FORM_FIELDS,
    "voluntary": MAPPING__VOLUNTARY__DEFAULT_FORM_FIELDS,
}
MAPPING__SUBSCRIPTION_MODE__MEMBERSHIP_MODE = {
    "member": "member",
    "member_associations": "member",
    "company_member": "member",
    "invited": "invited",
    "company_invited": "invited",
    "voluntary": "voluntary",
}
MAPPING__SUBSCRIPTION_MODE__MEMBERTYPE_MODE = {
    "member": "individual",
    "member_associations": "individual",
    "company_member": "company",
    "invited": "individual",
    "company_invited": "company",
    "voluntary": "individual_company",
}
MAPPING_FORM_ERROR_TITLE = {
    "general": _("There is a problem with the data you submitted")
}
MAPPING_SUBSCRIPTION_COMPONENT_ERROR_TITLE = {
    "general": _("There is a problem validating the creation of the request")
}
CONTEXT_VALIDATION_ERROR_TITLE = _("Form can't be loaded")
CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE = _(
    "There is a problem loading the form. Please contact your administrator for more details"
)
CONTEXT_VALIDATION_ERROR_UNAVAILABLE_MESSAGE = _(
    "The form is no longer available. Contact your coordinator for further information."
)
STATUS_CODE_NOT_FOUND_ERROR = 404
STATUS_CODE_CONSISTENCY_ERROR = 406  # not acceptable
STATUS_CODE_UNAVAILABLE_ERROR = 423  # locked
STATUS_CODE_SERVER_ERROR = 500
