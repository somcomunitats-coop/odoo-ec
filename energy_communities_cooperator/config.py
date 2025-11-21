from odoo.tools.translate import _

COOP_SHARE_PRODUCT_CATEG_REF = "cooperator.product_category_company_share"
COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF = (
    "energy_communities_cooperator.product_category_company_voluntary_share"
)
MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF = {
    "member": "cooperator.product_category_company_share",
    "company_member": "cooperator.product_category_company_share",
    "invited": "cooperator.product_category_company_share",
    "company_invited": "cooperator.product_category_company_share",
    "voluntary": "cooperator.product_category_company_share",
    "company_voluntary": "cooperator.product_category_company_share",
}
MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_TITLE = {
    "member": _("Become Cooperator of {company_name}") + _("member_eu_ES"),
    "company_member": _("Become Cooperator of {company_name}") + _("member_eu_ES"),
    "invited": _("Become Invited of {company_name}") + _("invited_eu_ES"),
    "company_invited": _("Become Invited of {company_name}") + _("invited_eu_ES"),
    "voluntary": _("Voluntary Share of {company_name}") + _("vol_share_eu_es"),
    "company_voluntary": _("Voluntary Share of {company_name}") + _("vol_share_eu_es"),
}
MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE = {
    "member": _("Become Cooperator Headline"),
    "company_member": _("Become Company Cooperator Headline"),
    "invited": _("Become Invited Headline"),
    "company_invited": _("Become Company Invited Headline"),
    "voluntary": _("Become Voluntary Headline"),
    "company_voluntary": _("Become Company Voluntary Headline"),
}
MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_TRANSFER = {
    "member": _(
        "<p>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>{product_price}</span>€ by follow the steps you will receive by email.</p>"
    ),
    "company_member": _(
        "<p>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>{product_price}</span>€ by follow the steps you will receive by email.</p>"
    ),
    "invited": _(
        "<p>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>{product_price}</span>€ by follow the steps you will receive by email.</p>"
    ),
    "company_invited": _(
        "<p>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>{product_price}</span>€ by follow the steps you will receive by email.</p>"
    ),
    "voluntary": _(
        "<p>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>{product_price}</span>€ by follow the steps you will receive by email.</p>"
    ),
    "company_voluntary": _(
        "<p>To be a member you must fulfill this form and lateron proceed to pay the initial share of <span id='prodPrice'>{product_price}</span>€ by follow the steps you will receive by email.</p>"
    ),
}
MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_SEPA = {
    "member": _(
        "<p>To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span id=prodPrice'>{product_price}</span>€</p>"
    ),
    "company_member": _(
        "<p>To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span id=prodPrice'>{product_price}</span>€</p>"
    ),
    "invited": _(
        "<p>To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span id=prodPrice'>{product_price}</span>€</p>"
    ),
    "company_invited": _(
        "<p>To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span id=prodPrice'>{product_price}</span>€</p>"
    ),
    "voluntary": _(
        "<p>To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span id=prodPrice'>{product_price}</span>€</p>"
    ),
    "company_voluntary": _(
        "<p>To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span id=prodPrice'>{product_price}</span>€</p>"
    ),
}
