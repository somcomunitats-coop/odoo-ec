from odoo import http
from odoo.http import request
from odoo.tools.translate import _

from ..config import (
    MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE,
    MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_SEPA,
    MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_TRANSFER,
    MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_TITLE,
    MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF,
)


# http://odoo-ce.local:8069/es/subscription/member/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/invited/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/voluntary/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/company_invited/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/company_voluntary/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/company_member/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
class WebsiteShareSubscriptionController(http.Controller):
    @http.route(
        [
            "/subscription/<string:mode>/<string:company_ext_id>",
            "/subscription/<string:mode>/<string:company_ext_id>/<string:product_ext_id>",
        ],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def subscription_page(self, **kwargs):
        values = self._get_base_values(kwargs)
        # Validate the request
        self._validate_request(values)
        if not "global_error" in values.keys():
            self._get_page_values(values)
        # Render the page
        return self._render_page(values)

    @http.route(
        [
            "/subscription/<string:mode>/<string:company_ext_id>",
            "/subscription/<string:mode>/<string:company_ext_id>/<string:product_ext_id>",
        ],
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
    )
    def subscription_submission(self, **kwargs):
        values = self._get_base_values(kwargs)
        return self._render_page(values)

    def _get_base_values(self, kwargs):
        mode = kwargs.get("mode")
        values = {
            "mode": mode,
            "company": self._get_model_from_ext_id(
                "res.company", "company_external_id", kwargs.get("company_ext_id")
            ),
            "product_categ": request.env.ref(
                MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF[mode]
            ),
        }
        if "product_ext_id" in kwargs.keys():
            values["product_ext_id"] = kwargs.get("product_ext_id")
            # Get the product from the external ID
            values["product"] = self._get_model_from_ext_id(
                "product.template", "product_external_id", values["product_ext_id"]
            )
        else:
            values["product_ext_id"] = False
            values["product"] = (
                request.env["product.template"]
                .sudo()
                .search(
                    [
                        ("categ_id", "=", values["product_categ"].id),
                        ("default_share_product", "=", True),
                        ("company_id", "=", values["company"].id),
                    ],
                    limit=1,
                )
            )
        return values

    def _validate_request(self, values):
        if not values["company"]:
            values.update(
                {"global_error": True, "error_msgs": [_("Company not found")]}
            )
        if not values["mode"]:
            values.update({"global_error": True, "error_msgs": [_("Mode not found")]})
        if values["product_ext_id"] and not values["product"]:
            self.values.update(
                {"global_error": True, "error_msgs": [_("Product not found")]}
            )

    def _get_page_values(self, values):
        values.update(
            {
                "page_title": self._get_page_title(values),
                "page_headline": self._get_page_headline(values),
                "page_headline_fixed_transfer": self._get_page_headline_fixed_transfer(
                    values
                ),
                "page_headline_fixed_sepa": self._get_page_headline_fixed_sepa(values),
            }
        )

    def _render_page(self, values):
        return request.render(
            "energy_communities_cooperator.template_subscription_page",
            values,
        )

    # getters
    def _get_model_from_ext_id(self, model_name, field_name, ext_id):
        if ext_id:
            return request.env[model_name].sudo().search([(field_name, "=", ext_id)])
        return False

    def _get_page_title(self, values):
        return MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_TITLE[values["mode"]].format(
            company_name=values["company"].comercial_name
        )

    def _get_page_headline(self, values):
        return MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE[values["mode"]].format(
            product_price=str(values["product"].list_price).replace(".", ",")
        )

    def _get_page_headline_fixed_transfer(self, values):
        return MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_TRANSFER[
            values["mode"]
        ].format(product_price=str(values["product"].list_price).replace(".", ","))

    def _get_page_headline_fixed_sepa(self, values):
        return MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_SEPA[
            values["mode"]
        ].format(product_price=str(values["product"].list_price).replace(".", ","))
