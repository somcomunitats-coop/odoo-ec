import logging

from odoo import http
from odoo.exceptions import MissingError
from odoo.http import request
from odoo.tools.translate import _

from ..config import (
    MAPPING__PAYMENT_METHOD,
    MAPPING__SUBSCRIPTION_MODE__DEFAULT_FORM_FIELDS,
    MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE,
    MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_SEPA,
    MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_TRANSFER,
    MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_TITLE,
    MAPPING__SUBSCRIPTION_MODE__MEMBERSHIP_MODE,
    MAPPING__SUBSCRIPTION_MODE__MEMBERTYPE_MODE,
    MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF,
    SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT,
)
from ..schemas.website_share_subscription_schemas import (
    WebsiteShareSubscriptionContext,
)

_logger = logging.getLogger(__name__)


# http://odoo-ce.local:8069/es/subscription/member/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/invited/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/voluntary/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/company_invited/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
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
        methods=["GET", "POST"],
    )
    def share_subscription_form(self, **kwargs):
        try:
            context = self._validate_request(kwargs)
        except Exception as e:
            _logger.error(f"Error validating request: {e}")
            return request.render(template="website.page_404", status=404)
        else:
            values = context.model_dump()
        if request.httprequest.method == "GET":
            values = self._update_base_values(values)
            if values.get("global_error", False):
                return self._render_page(values)
            self._update_page_values(values)
            self._update_form_fields(values)
            self._update_custom_options(values)
            self._update_custom_description(values)
            self._update_form_custom_fields(values)
            return self._render_page(values)
        self._process_form(values)
        return self._render_page(values)

    def _update_base_values(self, values):
        values["currency_symbol"] = values["company"].currency_id.symbol
        if values.get("product_ext_id"):
            values["products"] = [values["product"]]
        else:
            values["products"] = self._get_products_from_category_and_company(
                values["product_categ"].id, values["company"].id
            )
            if len(values["products"]) > 0:
                values["product"] = values["products"][0]
        return values

    def _get_formtype_mode(self, kwargs):
        if "product_external_id" in kwargs:
            return "single"
        return "global"

    def _validate_request(self, kwargs):
        mode = kwargs.get("mode", "")
        return WebsiteShareSubscriptionContext(
            membership_mode=MAPPING__SUBSCRIPTION_MODE__MEMBERSHIP_MODE.get(mode),
            membertype_mode=MAPPING__SUBSCRIPTION_MODE__MEMBERTYPE_MODE.get(mode),
            formtype_mode=self._get_formtype_mode(kwargs),
            company=request.env["res.company"]
            .sudo()
            .search([("company_external_id", "=", kwargs.get("company_ext_id"))]),
            product_categ=request.env.ref(
                MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF.get(mode)
            ),
            product=request.env["product.template"]
            .sudo()
            .search(
                [
                    ("product_external_id", "=", kwargs.get("product_ext_id")),
                    (
                        "categ_id",
                        "=",
                        request.env.ref(
                            MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF.get(mode)
                        ).id,
                    ),
                ]
            ),
            product_ext_id=kwargs.get("product_ext_id"),
        )

    def _render_page(self, values):
        return request.render(
            "energy_communities_cooperator.template_subscription_page",
            values,
        )

    def _process_form(self, values):
        pass

    # updaters
    def _update_form_fields(self, values):
        form_fields = MAPPING__SUBSCRIPTION_MODE__DEFAULT_FORM_FIELDS[values["mode"]]
        for field in form_fields:
            values[field + "_key"] = field
            values[field + "_label"] = form_fields[field]["label"]
            values[field] = self._get_form_fields_values(
                values, form_fields[field]["value"]
            )
            if "required" in form_fields[field]:
                values[field + "_required"] = form_fields[field]["required"]
            else:
                values[field + "_required"] = False
            if "disabled" in form_fields[field]:
                values[field + "_disabled"] = form_fields[field]["disabled"]
            else:
                values[field + "_disabled"] = False
            if "options" in form_fields[field]:
                values[field + "_options"] = form_fields[field]["options"]
            if "description" in form_fields[field]:
                values[field + "_description"] = form_fields[field]["description"]

    def _update_form_custom_fields(self, values):
        if len(values["products"]) == 1:
            values["share_product_id_disabled"] = True
            # values["ordered_parts_disabled"] = True
        if values["mode"] == "voluntary":
            values["address_disabled"] = True
            values["phone_disabled"] = True
            values["birthdate_disabled"] = True
            # values["gender_disabled"] = True
            values["email_disabled"] = True
            values["firstname_disabled"] = True
            values["lastname_disabled"] = True
            # values["vat_disabled"] = True
            values["city_disabled"] = True
            values["zip_code_disabled"] = True
            # values["country_id_disabled"] = True

    def _update_custom_options(self, values):
        if "country_id_options" in values:
            values["country_id_options"] = self._get_country_options()
        if "share_product_id_options" in values:
            values["share_product_id_options"] = self._get_share_product_options(values)
        if "lang_options" in values:
            values["lang_options"] = self._get_lang_options()

    def _update_custom_description(self, values):
        if values["company"].display_data_policy_approval:
            values["privacy_policy_description"] = values[
                "company"
            ].data_policy_approval_text
        else:
            values["privacy_policy_description"] = ""

    def _update_page_values(self, values):
        values.update(
            {
                "page_title": self._get_page_title(values),
                "page_headline": self._get_page_headline(values),
                "page_headline_fixed_transfer": self._get_page_headline_fixed_transfer(
                    values
                ),
                "page_headline_fixed_sepa": self._get_page_headline_fixed_sepa(values),
                "page_headline_custom": self._get_page_headline_custom(values),
                "page_headline_last_text": SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_LAST_TEXT,
                "activate_form_specific_products": values[
                    "product"
                ].activate_form_specific_products,
            }
        )

    # getters
    def _get_products_from_category_and_company(self, product_categ_id, company_id):
        return (
            request.env["product.template"]
            .sudo()
            .search(
                [
                    ("categ_id", "=", product_categ_id),
                    ("default_share_product", "=", True),
                    ("company_id", "=", company_id),
                ]
            )
        )

    def _get_page_title(self, values):
        return MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_TITLE[values["mode"]].format(
            company_name=values["company"].comercial_name
        )

    def _get_page_headline(self, values):
        return MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE[values["mode"]].format(
            company_name=values["company"].comercial_name
        )

    def _get_page_headline_fixed_transfer(self, values):
        return MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_TRANSFER[
            values["mode"]
        ].format(
            product_price=str(values["product"].list_price).replace(".", ","),
            currency_symbol=values["currency_symbol"],
        )

    def _get_page_headline_fixed_sepa(self, values):
        return MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_SEPA[
            values["mode"]
        ].format(
            product_price=str(values["product"].list_price).replace(".", ","),
            currency_symbol=values["currency_symbol"],
        )

    def _get_page_headline_custom(self, values):
        text_custom = (
            values["product"].html_specific_products
            if values["product"].activate_form_specific_products
            else values["company"].cooperator_share_form_header_text
        )
        if not text_custom:
            return ""
        return text_custom

    def _get_form_fields_values(self, data, path):
        if isinstance(path, bool):
            return path
        keys = path.split(".")
        current = data
        for key in keys:
            if not isinstance(current, dict):
                try:
                    current = current.read()[0]  # Convert the record to a dictionary
                except:
                    return ""  # Return an empty string if the record cannot be converted to a dictionary
            if key not in current:
                return ""  # Return an empty string if the field is not found
            current = current[key]
        return current

    def _get_country_options(self):
        return [{"id": "", "name": _("Select your country")}] + request.env[
            "res.country"
        ].sudo().search([], order="name").mapped(lambda x: {"id": x.id, "name": x.name})

    def _get_lang_options(self):
        return [{"id": "", "name": _("Select your language")}] + request.env[
            "res.lang"
        ].sudo().search([("active", "=", True)], order="name").mapped(
            lambda x: {"id": x.id, "name": x.name}
        )

    def _get_share_product_options(self, values):
        options = []
        for product in values["products"]:
            payment_method = "transfer"
            if (
                product.payment_mode_id
                and product.payment_mode_id.payment_method_id
                and product.payment_mode_id.payment_method_id.id
                == request.env.ref(MAPPING__PAYMENT_METHOD["sepa"]).id
            ):
                payment_method = "sepa"
            elif (
                product.payment_mode_id
                and product.payment_mode_id.payment_method_id
                and product.payment_mode_id.payment_method_id.id
                == request.env.ref(MAPPING__PAYMENT_METHOD["transfer"]).id
            ):
                payment_method = "transfer"
            options.append(
                {
                    "id": product.id,
                    "name": product.name,
                    "extra": product.list_price,
                    "extra_2": payment_method,
                }
            )
        return options
