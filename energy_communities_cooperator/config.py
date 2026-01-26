from odoo.tools.translate import _, _lt

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


def _get_subscription_mode_page_title_message(subscription_mode, company_name):
    MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_TITLE = {
        "member": _("Become a member of %(company_name)s ", company_name=company_name),
        "member_associations": _(
            "Become a member of %(company_name)s ", company_name=company_name
        ),
        "company_member": _(
            "Become a member of %(company_name)s ", company_name=company_name
        ),
        "invited": _(
            "Register to participate in the projects and initiatives of %(company_name)s ",
            company_name=company_name,
        ),
        "company_invited": _(
            "Register to participate in the projects and initiatives of %(company_name)s ",
            company_name=company_name,
        ),
        "voluntary": _(
            "Voluntary Share of %(company_name)s ", company_name=company_name
        ),
    }
    return MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_TITLE[subscription_mode]


SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT = _lt(
    "<p>Once you become a member, you will be able to use the services available to the energy community and,"
    + " at the same time, be part of a movement for social transformation and a new energy model</p>"
)


def _get_subscription_mode_headline_last_text_voluntary_message(external_id):
    SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT_VOLUNTARY = _(
        "<p>"
        + "Once your request has been received, you will receive a confirmation email with instructions to follow."
        + "</p>"
        + "<p>"
        + "Note: If you are not yet a member, please complete the following forms: "
        + "<a href='/subscription/member/%(external_id)s'>INDIVIDUAL MEMBERSHIP REGISTRATION</a>"
        + " and "
        + "<a href='/subscription/company_member/%(external_id)s'>LEGAL ENTITY MEMBERSHIP REGISTRATION</a>"
        + "</p>",
        external_id=external_id,
    )
    return SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT_VOLUNTARY


def _get_subscription_mode_headline_message(
    subscription_mode, company_name, external_id
):
    MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE = {
        "member": "<p>"
        + _(
            "This form allow you to request be member of the community: %(company_name)s ",
            company_name=company_name,
        )
        + ".</p>"
        + SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT,
        "member_associations": "<p>"
        + _(
            "This form allow you to request be member of the community: %(company_name)s ",
            company_name=company_name,
        )
        + ".</p>"
        + SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT,
        "company_member": "<p>"
        + _(
            "This form allow you to request be member of the community: %(company_name)s ",
            company_name=company_name,
        )
        + ".</p>"
        + SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT,
        "invited": "<p>"
        + _(
            "This is the form to register as a person/entity invited to participate in the Energy Community's projects and initiatives: %(company_name)s ",
            company_name=company_name,
        )
        + ".</p>"
        + SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT,
        "company_invited": "<p>"
        + _(
            "This is the form to register as a person/entity invited to participate in the Energy Community's projects and initiatives: %(company_name)s ",
            company_name=company_name,
        )
        + ".</p>"
        + SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT,
        "voluntary": "<p>"
        + _(
            "This is the form for members of %(company_name)s to make voluntary contributions to the share capital",
            company_name=company_name,
        )
        + ".</p>"
        + _get_subscription_mode_headline_last_text_voluntary_message(external_id),
    }
    return MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE[subscription_mode]


def _get_headline_fixed_transfer_message(
    subscription_mode, product_price, currency_symbol
):
    MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_TRANSFER = {
        "member": _(
            "<p id='transfer_text'>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>%(product_price)s</span>%(currency_symbol)s by follow the steps you will receive by email.</p>",
            product_price=product_price,
            currency_symbol=currency_symbol,
        ),
        "member_associations": _(
            "<p id='transfer_text'>To become a member, you must first fill out this questionnaire and then make the initial financial contribution of <span id='prodPrice'>%(product_price)s</span>%(currency_symbol)s by following the steps we will send you by email once we have received your request.</p>",
            product_price=product_price,
            currency_symbol=currency_symbol,
        ),
        "company_member": _(
            "<p id='transfer_text'>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>%(product_price)s</span>%(currency_symbol)s by follow the steps you will receive by email.</p>",
            product_price=product_price,
            currency_symbol=currency_symbol,
        ),
        "invited": _(
            "<p id='transfer_text'>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>%(product_price)s</span>%(currency_symbol)s by follow the steps you will receive by email.</p>",
            product_price=product_price,
            currency_symbol=currency_symbol,
        ),
        "company_invited": _(
            "<p id='transfer_text'>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>%(product_price)s</span>%(currency_symbol)s by follow the steps you will receive by email.</p>",
            product_price=product_price,
            currency_symbol=currency_symbol,
        ),
        "voluntary": _(
            "<p id='transfer_text'>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>%(product_price)s</span>%(currency_symbol)s by follow the steps you will receive by email.</p>",
            product_price=product_price,
            currency_symbol=currency_symbol,
        ),
    }
    return MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_TRANSFER[
        subscription_mode
    ]


def _get_headline_fixed_sepa_message(subscription_mode, product_price, currency_symbol):
    MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_SEPA = {
        "member": _(
            "<p id='sepa_text'>To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span id='prodPrice'>%(product_price)s</span>%(currency_symbol)s</p>",
            product_price=product_price,
            currency_symbol=currency_symbol,
        ),
        "member_associations": _(
            "<p id='sepa_text'>To become a member, you must first fill out this form, where we ask you for your bank account details and authorization to issue a direct debit to collect the initial contribution of <span id='prodPrice'>%(product_price)s</span>%(currency_symbol)s</p>",
            product_price=product_price,
            currency_symbol=currency_symbol,
        ),
        "company_member": _(
            "<p id='sepa_text'>To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span id='prodPrice'>%(product_price)s</span>%(currency_symbol)s</p>",
            product_price=product_price,
            currency_symbol=currency_symbol,
        ),
        "invited": _(
            "<p id='sepa_text'>To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span id='prodPrice'>%(product_price)s</span>%(currency_symbol)s</p>",
            product_price=product_price,
            currency_symbol=currency_symbol,
        ),
        "company_invited": _(
            "<p id='sepa_text'>To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span id='prodPrice'>%(product_price)s</span>%(currency_symbol)s</p>",
            product_price=product_price,
            currency_symbol=currency_symbol,
        ),
        "voluntary": _(
            "<p id='sepa_text'>To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span id='prodPrice'>%(product_price)s</span>%(currency_symbol)s</p>",
            product_price=product_price,
            currency_symbol=currency_symbol,
        ),
    }
    return MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_SEPA[
        subscription_mode
    ]


GENDER_OPTIONS = [
    {"id": "male", "name": _lt("Male")},
    {"id": "female", "name": _lt("Female")},
    {"id": "other", "name": _lt("Other")},
    {"id": "not_binary", "name": _lt("Not binary")},
    {"id": "not_share", "name": _lt("I prefer to not share it")},
]

MAPPING_FORM_SUCCESS = {
    "general": _lt(
        "Your subscription request has been submitted successfully. "
        "You will receive a confirmation email shortly."
    )
}

MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_COMPANY_CONTACT = {
    "company_name": {
        "class": "col-md-12",
        "type": "form_field_text",
        "value": "",
        "label": _lt("Company Name"),
        "required": True,
        "readonly": False,
    },
    "company_email": {
        "class": "col-md-12",
        "type": "form_field_email",
        "value": "",
        "label": _lt("Company Email"),
        "required": True,
        "readonly": False,
    },
    "company_email_confirmation": {
        "class": "col-md-12",
        "type": "form_field_email",
        "value": "",
        "label": _lt("CompanyEmail Confirmation"),
        "required": True,
        "readonly": False,
    },
}

MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PERSONAL_CONTACT = {
    "email": {
        "class": "col-md-12",
        "type": "form_field_email",
        "value": "",
        "label": _lt("Email"),
        "required": True,
        "readonly": False,
    },
    "email_confirmation": {
        "class": "col-md-12",
        "type": "form_field_email",
        "value": "",
        "label": _lt("Email Confirmation"),
        "required": True,
        "readonly": False,
    },
    "firstname": {
        "class": "col-md-6",
        "type": "form_field_text",
        "value": "",
        "label": _lt("Firstname"),
        "required": True,
        "readonly": False,
    },
    "lastname": {
        "class": "col-md-6",
        "type": "form_field_text",
        "value": "",
        "label": _lt("Lastname"),
        "required": True,
        "readonly": False,
    },
    "gender": {
        "class": "col-md-6",
        "type": "form_field_selection",
        "value": "",
        "label": _lt("Gender"),
        "required": True,
        "options": GENDER_OPTIONS,
        "readonly": False,
    },
    "birthdate": {
        "class": "col-md-6",
        "type": "form_field_date_past",
        "value": "",
        "label": _lt("Birthdate"),
        "required": True,
        "readonly": False,
    },
    "phone": {
        "class": "col-md-12",
        "type": "form_field_text",
        "value": "",
        "label": _lt("Phone"),
        "required": True,
        "readonly": False,
    },
    "lang": {
        "class": "col-md-12",
        "type": "form_field_selection",
        "value": "",
        "label": _lt("Language"),
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
        "label": _lt("VAT"),
        "required": True,
        "readonly": False,
    },
}
MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_ADDRESS = {
    "address": {
        "class": "col-md-12",
        "type": "form_field_text",
        "value": "",
        "label": _lt("Address"),
        "required": True,
        "readonly": False,
    },
    "city": {
        "class": "col-md-6",
        "type": "form_field_text",
        "value": "",
        "label": _lt("City"),
        "required": True,
        "readonly": False,
    },
    "zip_code": {
        "class": "col-md-6",
        "type": "form_field_text",
        "value": "",
        "label": _lt("Postal Code"),
        "required": True,
        "readonly": False,
    },
    "country_id": {
        "class": "col-md-12",
        "type": "form_field_selection",
        "value": "",
        "label": _lt("Country"),
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
        "label": _lt("Share Product"),
        "required": True,
        "readonly": False,
        "options": [],
    },
    "ordered_parts": {
        "class": "col-md-3",
        "type": "form_field_number",
        "value": "",
        "label": _lt("Ordered Parts"),
        "required": True,
        "readonly": False,
    },
    "total_price": {
        "class": "col-md-4",
        "type": "form_field_text",
        "value": "",
        "label": _lt("Total Price"),
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
            {"id": "sepa", "name": _lt("SEPA")},
            {"id": "transfer", "name": _lt("Transfer")},
        ],
    },
}

MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PAYMENT_METHOD = {
    "iban": {
        "class": "col-md-12",
        "type": "form_field_text",
        "value": "",
        "label": _lt("IBAN"),
        "required": True,
        "readonly": False,
    },
    "conditions_payment": {
        "class": "col-md-12",
        "type": "form_field_checkbox",
        "value": False,
        "label": _lt(
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
        "label": _lt("Financial Risk"),
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
        "label": _lt("Internal Rules"),
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
        "label": _lt("Generic Rules"),
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
        "label": _lt("Privacy Policy"),
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
        "label": _lt("Function"),
        "required": True,
        "readonly": False,
    },
}

MAPPING__MEMBER__DEFAULT_FORM_FIELDS = (
    MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PERSONAL_CONTACT
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_VAT
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_ADDRESS
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_SHARE_PRODUCT
    | {
        "h3_company_bank_details": {
            "key": "h3_company_bank_details",
            "class": "h3_company_bank_details col-md-12",
            "type": "form_h3",
            "description": _lt("Company bank details"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PAYMENT_METHOD
)
MAPPING__COMPANY_MEMBER__DEFAULT_FORM_FIELDS = (
    {
        "h3_company_information": {
            "key": "h3_company_information",
            "class": "col-md-12",
            "type": "form_h3",
            "description": _lt("Company Information"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_COMPANY_CONTACT
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_VAT
    | {
        "h3_main_address": {
            "key": "h3_main_address",
            "class": "col-md-12",
            "type": "form_h3",
            "description": _lt("Main Address"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_ADDRESS
    | {
        "h3_contact_person": {
            "key": "h3_contact_person",
            "class": "col-md-12",
            "type": "form_h3",
            "description": _lt("Contact Person"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PERSONAL_CONTACT
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_CONTACT_PERSON_FUNCTION
    | {
        "h3_share_selection": {
            "key": "h3_share_selection",
            "class": "col-md-12",
            "type": "form_h3",
            "description": _lt("Share Selection"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_SHARE_PRODUCT
    | {
        "h3_company_bank_details": {
            "key": "h3_company_bank_details",
            "class": "h3_company_bank_details col-md-12",
            "type": "form_h3",
            "description": _lt("Company bank details"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PAYMENT_METHOD
)
MAPPING__INVITED__DEFAULT_FORM_FIELDS = (
    MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PERSONAL_CONTACT
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_VAT
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_ADDRESS
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_SHARE_PRODUCT
    | {
        "h3_company_bank_details": {
            "key": "h3_company_bank_details",
            "class": "h3_company_bank_details col-md-12",
            "type": "form_h3",
            "description": _lt("Company bank details"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PAYMENT_METHOD
)
MAPPING__COMPANY_INVITED__DEFAULT_FORM_FIELDS = (
    {
        "h3_company_information": {
            "key": "h3_company_information",
            "class": "col-md-12",
            "type": "form_h3",
            "description": _lt("Company Information"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_COMPANY_CONTACT
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_VAT
    | {
        "h3_main_address": {
            "key": "h3_main_address",
            "class": "col-md-12",
            "type": "form_h3",
            "description": _lt("Main Address"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_ADDRESS
    | {
        "h3_contact_person": {
            "key": "h3_contact_person",
            "class": "col-md-12",
            "type": "form_h3",
            "description": _lt("Contact Person"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PERSONAL_CONTACT
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_CONTACT_PERSON_FUNCTION
    | {
        "h3_share_selection": {
            "key": "h3_share_selection",
            "class": "col-md-12",
            "type": "form_h3",
            "description": _lt("Share Selection"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_SHARE_PRODUCT
    | {
        "h3_company_bank_details": {
            "key": "h3_company_bank_details",
            "class": "h3_company_bank_details col-md-12",
            "type": "form_h3",
            "description": _lt("Company bank details"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PAYMENT_METHOD
)
MAPPING__VOLUNTARY__DEFAULT_FORM_FIELDS = (
    MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_VAT
    | {
        "email": {
            "class": "col-md-12",
            "type": "form_field_email",
            "value": "",
            "label": _lt("Email"),
            "required": True,
            "disabled": False,
        },
        "email_confirmation": {
            "class": "col-md-12",
            "type": "form_field_email",
            "value": "",
            "label": _lt("Email Confirmation"),
            "required": True,
            "disabled": False,
        },
        "phone": {
            "class": "col-md-12",
            "type": "form_field_text",
            "value": "",
            "label": _lt("Phone"),
            "required": True,
            "disabled": False,
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_SHARE_PRODUCT
    | {
        "h3_company_bank_details": {
            "key": "h3_company_bank_details",
            "class": "h3_company_bank_details col-md-12",
            "type": "form_h3",
            "description": _lt("Company bank details"),
        },
    }
    | MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PAYMENT_METHOD
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
    "general": _lt("There is a problem with the data you submitted")
}
MAPPING_SUBSCRIPTION_COMPONENT_ERROR_TITLE = {
    "general": _lt("There is a problem validating the creation of the request")
}
CONTEXT_VALIDATION_ERROR_TITLE = _lt("Form can't be loaded")
CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE = _lt(
    "There is a problem loading the form. Please contact your administrator for more details"
)
CONTEXT_VALIDATION_ERROR_UNAVAILABLE_MESSAGE = _lt(
    "The form is no longer available. Contact your coordinator for further information."
)
STATUS_CODE_NOT_FOUND_ERROR = 404
STATUS_CODE_CONSISTENCY_ERROR = 406  # not acceptable
STATUS_CODE_UNAVAILABLE_ERROR = 423  # locked
STATUS_CODE_SERVER_ERROR = 500
