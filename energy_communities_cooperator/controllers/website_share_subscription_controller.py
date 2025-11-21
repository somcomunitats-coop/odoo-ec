from odoo import http
from odoo.http import request
from odoo.tools.translate import _

from ..config import (
    MAPPING__SUBSCRIPTION_MODE__PAGE_TITLE,
    MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF,
)


# http://odoo-ce.local:8069/es/subscription/member/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/invited/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/voluntary/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/company_invited/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/company_voluntary/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/company_member/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
class WebsiteShareSubscriptionController(http.Controller):
    mode = None
    company = None
    product_categ = None
    product_ext_id = None
    product = None
    values = {}

    @http.route(
        [
            "/subscription/<string:mode>/<string:company_ext_id>",
            "/subscription/<string:mode>/<string:company_ext_id>/<string:product_ext_id>",
        ],
        type="http",
        auth="public",
        website=True,
    )
    def subsctiption_page(self, **kwargs):
        """
        This function is used to render the subscription page. It is called when the user visits the subscription page.
        It validates the request and renders the page.
        Args:
            mode: The mode of the subscription page.
            company_ext_id: The external ID of the company.
            product_ext_id: The external ID of the product.
        Returns:
            The rendered page.
        """
        self._setup_class_defaults(kwargs)
        self._get_base_values()
        # Validate the request
        self._validate_request()
        if not "global_error" in self.values.keys():
            self._get_extended_values()
        # Render the page
        return self._render_page()

    def _setup_class_defaults(self, kwargs):
        self.mode = kwargs.get("mode")
        # Get the company and product from the external ID
        self.company = self._get_model_from_ext_id(
            "res.company", "company_external_id", kwargs.get("company_ext_id")
        )
        if "product_ext_id" in kwargs.keys():
            self.product_ext_id = kwargs.get("product_ext_id")
        # Get the product from the external ID
        self.product = self._get_model_from_ext_id(
            "product.template", "product_external_id", self.product_ext_id
        )
        self.product_categ = request.env.ref(
            MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF[self.mode]
        )

    def _get_base_values(self):
        self.values.update(
            {
                "form_submit_url": self._get_form_submit_url(),
                "page_title": self._get_page_title(),
                "headline_text_1": self._get_headline_text_1(),
                "headline_text_3": self._get_headline_text_3(),
                "footer_text": self._get_footer_text(),
                "mode": self.mode,
            }
        )

    def _validate_request(self):
        if not self.company:
            self.values.update(
                {"global_error": True, "error_msgs": [_("Company not found")]}
            )
        if not self.mode:
            self.values.update(
                {"global_error": True, "error_msgs": [_("Mode not found")]}
            )
        if self.product_ext_id and not self.product:
            self.values.update(
                {"global_error": True, "error_msgs": [_("Product not found")]}
            )

    def _get_extended_values(self):
        self.values.update(
            {
                "company_name": self.company.name,
                "currency_symbol": self.company.currency_id.symbol,
                "product_price": self.product.list_price,
                "headline_text_2": self._get_headline_text_2(),
            }
        )

    def _render_page(self):
        return request.render(
            "energy_communities_cooperator.template_subscription_page",
            self.values,
        )

    # getters
    def _get_model_from_ext_id(self, model_name, field_name, ext_id):
        if ext_id:
            return request.env[model_name].sudo().search([(field_name, "=", ext_id)])
        return False

    def _get_form_submit_url(self):
        return f"send/subscription/{self.mode}"

    def _get_page_title(self):
        return _(MAPPING__SUBSCRIPTION_MODE__PAGE_TITLE[self.mode])

    def _get_headline_text_1(self):
        return _(
            f"This form allow you to request be member of the community: {self.company.name}."
        )

    def _get_headline_text_2(self):
        if self.product.list_price:
            if self.values.get(
                "share_payment_sepa_direct_debit", False
            ):  # TODO: check if this is correct. This can be for product category share.
                return _(
                    f"To join, you must first fill out this form where we ask for a bank account and authorization to issue a bank receipt to collect the initial mandatory financial contribution of <span>{self.product.list_price}</span>{self.company.currency_id.symbol}."
                )
            else:
                return _(
                    f"To be a member you must fulfill this form and lateron proceed to pay the initial share of <span>{self.product.list_price}</span>{self.company.currency_id.symbol} by follow the steps you will receive by email."
                )
        return _("")

    def _get_headline_text_3(self):
        return _(
            "Once you are a member you can enjoy the services available from the community and be part of a movement of social and energy model transformation."
        )

    def _get_footer_text(self):
        return _(
            "Thank you for your interest in becoming a cooperator. We will review your application and get back to you soon."
        )
