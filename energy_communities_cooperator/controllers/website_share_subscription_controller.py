import logging

from odoo import http
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
            "/subscription/<string:subscription_mode>/<string:company_ext_id>",
            "/subscription/<string:subscription_mode>/<string:company_ext_id>/<string:product_ext_id>",
        ],
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
    )
    def share_subscription_form(self, **kwargs):
        context_creation_params_dict = self._get_context_creation_params_dict(kwargs)
        try:
            ctx = WebsiteShareSubscriptionContext(**context_creation_params_dict)
        except Exception as e:
            _logger.error(f"Error validating request: {e}")
            return request.render(template="website.page_404", status=404)
        if request.httprequest.method == "GET":
            values = self._get_page_values(ctx)
            return self._render_page(values)
        self._process_form(values)
        return self._render_page(values)

    def _render_page(self, values):
        return request.render(
            "energy_communities_cooperator.template_subscription_page",
            values,
        )

    def _process_form(self, values):
        pass

    # getters
    def _get_context_creation_params_dict(self, kwargs):
        subscription_mode = kwargs.get("subscription_mode")
        query_product = self._get_model_from_ext_id(
            "product.template", "product_external_id", kwargs.get("product_ext_id")
        )
        company = self._get_model_from_ext_id(
            "res.company", "company_external_id", kwargs.get("company_ext_id")
        )
        product_categ = self._get_product_categ(subscription_mode)
        return {
            "membership_mode": MAPPING__SUBSCRIPTION_MODE__MEMBERSHIP_MODE.get(
                subscription_mode
            ),
            "membertype_mode": MAPPING__SUBSCRIPTION_MODE__MEMBERTYPE_MODE.get(
                subscription_mode
            ),
            "subscription_mode": subscription_mode,
            "formtype_mode": self._get_formtype_mode(kwargs),
            "company": company,
            "product_categ": product_categ,
        } | self._get_page_products_dict(company, product_categ, query_product)

    def _get_page_values(self, ctx):
        values = (
            ctx.model_dump()
            | self._get_page_base_values(ctx)
            | self._get_page_form_fields_values(ctx)
        )
        self._update_custom_options(values)
        self._update_custom_description(values)
        self._update_form_custom_fields(values)
        values["subscription_mode"] = ctx.subscription_mode.value
        return values

    def _get_page_base_values(self, ctx):
        return {
            "currency_symbol": ctx.company.currency_id.symbol,
            "page_title": self._get_page_title(ctx),
            "page_headline": self._get_page_headline(ctx),
            "page_headline_fixed_transfer": self._get_page_headline_fixed_transfer(ctx),
            "page_headline_fixed_sepa": self._get_page_headline_fixed_sepa(ctx),
        }

    def _get_page_products_dict(self, company, product_categ, query_product):
        if query_product:
            return {"products": query_product, "product": query_product}
        if product_categ and company:
            products = (
                request.env["product.template"]
                .sudo()
                .search(
                    [
                        ("categ_id", "=", product_categ.id),
                        ("company_id", "=", company.id),
                    ],
                    order="default_share_product desc",
                )
            )
            return {"products": products, "product": products[0]}
        return {"products": None, "product": None}

    def _get_formtype_mode(self, kwargs):
        if "product_external_id" in kwargs:
            return "single"
        return "global"

    def _get_model_from_ext_id(self, model_name, field_name, ext_id):
        if ext_id:
            return request.env[model_name].sudo().search([(field_name, "=", ext_id)])
        return False

    def _get_product_categ(self, subscription_mode):
        try:
            categ = request.env.ref(
                MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF.get(subscription_mode)
            )
        except:
            categ = None

        return categ

    def _get_page_form_fields_values(self, ctx):
        form_fields = MAPPING__SUBSCRIPTION_MODE__DEFAULT_FORM_FIELDS[
            ctx.subscription_mode
        ]
        values = {}
        for field in form_fields:
            values[field + "_key"] = field
            values[field + "_label"] = form_fields[field]["label"]
            values[field] = self._get_form_field_value(
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
        return values

    def _get_page_title(self, ctx):
        return MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_TITLE[
            ctx.subscription_mode
        ].format(company_name=ctx.company.comercial_name)

    def _get_page_headline(self, ctx):
        return MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE[
            ctx.subscription_mode
        ].format(company_name=ctx.company.comercial_name)

    def _get_page_headline_fixed_transfer(self, ctx):
        return MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_TRANSFER[
            ctx.subscription_mode
        ].format(
            product_price=str(ctx.product.list_price).replace(".", ","),
            currency_symbol=ctx.company.currency_id.symbol,
        )

    def _get_page_headline_fixed_sepa(self, ctx):
        return MAPPING__SUBSCRIPTION_MODE__DEFAULT_PAGE_HEADLINE_FIXED_SEPA[
            ctx.subscription_mode
        ].format(
            product_price=str(ctx.product.list_price).replace(".", ","),
            currency_symbol=ctx.company.currency_id.symbol,
        )

    def _get_form_field_value(self, data, path):
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

    # updaters
    # TODO: This method shouldn't be necessary if we control wich fields do we render on each subscription mode
    # We must used it to control share product selector behaviour
    def _update_form_custom_fields(self, values):
        if len(values["products"]) == 1:
            values["share_product_id_disabled"] = True
            # values["ordered_parts_disabled"] = True
        if values["subscription_mode"] == "voluntary":
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
