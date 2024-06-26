from urllib.parse import urljoin

from odoo import http
from odoo.http import request
from odoo.tools.translate import _

from odoo.addons.cooperator_website.controllers import main as emyc_wsc

_VOLUNTARY_SHARE_FORM_FIELD = [
    "email",
    "confirm_email",
    "iban",
    "share_product_id",
    "phone",
    "lang",
    "nb_parts",
    "total_parts",
    "error_msg",
]


class WebsiteSubscriptionCCEE(emyc_wsc.WebsiteSubscription):
    @http.route()
    def display_become_cooperator_page(self, **kwargs):
        target_odoo_company_id = False
        if kwargs.get("odoo_company_id", False):
            try:
                target_odoo_company_id = int(kwargs.get("odoo_company_id"))
            except:
                pass

        if ("odoo_company_id" in kwargs) and (
            not target_odoo_company_id
            or not request.env["res.company"]
            .sudo()
            .search([("id", "=", target_odoo_company_id)])
        ):
            return http.Response(
                _("Not valid parameter value [odoo_company_id]"), status=500
            )

        ctx = dict(request.context)
        ctx.update({"target_odoo_company_id": target_odoo_company_id})
        request.context = ctx

        res = super().display_become_cooperator_page(**kwargs)
        return res

    @http.route()
    def display_become_company_cooperator_page(self, **kwargs):
        target_odoo_company_id = False
        if kwargs.get("odoo_company_id", False):
            try:
                target_odoo_company_id = int(kwargs.get("odoo_company_id"))
            except:
                pass

        if ("odoo_company_id" in kwargs) and (
            not target_odoo_company_id
            or not request.env["res.company"]
            .sudo()
            .search([("id", "=", target_odoo_company_id)])
        ):
            return http.Response(
                _("Not valid parameter value [odoo_company_id]"), status=500
            )

        ctx = dict(request.context)
        ctx.update({"target_odoo_company_id": target_odoo_company_id})
        request.context = ctx

        res = super().display_become_company_cooperator_page(**kwargs)
        return res

    @http.route()  # noqa: C901 (method too complex)
    def share_subscription(self, **kwargs):
        target_odoo_company_id = False
        if kwargs.get("company_id", False):
            try:
                target_odoo_company_id = int(kwargs.get("company_id"))
            except:
                pass

        if ("odoo_company_id" in kwargs) and (
            not target_odoo_company_id
            or not request.env["res.company"]
            .sudo()
            .search([("id", "=", target_odoo_company_id)])
        ):
            return http.Response(
                _("Not valid parameter value [odoo_company_id]"), status=500
            )

        if "vat" in kwargs:
            kwargs["vat"] = kwargs["vat"].upper().strip()

        ctx = dict(request.context)
        ctx.update({"target_odoo_company_id": target_odoo_company_id})
        request.context = ctx

        res = super().share_subscription(**kwargs)
        return res

    def fill_values(self, values, is_company, logged, load_from_user=False):
        target_company_id = request.context.get("target_odoo_company_id", False)

        sub_req_obj = request.env["subscription.request"]
        if target_company_id:
            company = request.env["res.company"].sudo().browse(target_company_id)
        else:
            company = request.website.company_id
        products = self.get_products_share(is_company)

        if load_from_user:
            values = self.get_values_from_user(values, is_company)
        if is_company:
            values["is_company"] = "on"
        if logged:
            values["logged"] = "on"
        values["countries"] = self.get_countries()
        values["langs"] = self.get_langs()
        values["products"] = products
        fields_desc = sub_req_obj.sudo().fields_get(["company_type", "gender"])
        values["company_types"] = fields_desc["company_type"]["selection"]
        values["genders"] = fields_desc["gender"]["selection"]
        values["company"] = company
        values["share_payment_sepa_direct_debit"] = False

        if not values.get("share_product_id"):
            for product in products:
                if (
                    product.default_share_product is True
                    and product.id != company.voluntary_share_id.id
                ):
                    values["share_product_id"] = product.id
                    values["share_payment_sepa_direct_debit"] = (
                        product.payment_mode_id.payment_method_id.code
                        == "sepa_direct_debit"
                        or False
                    )
                    break
            if not values.get("share_product_id", False) and products:
                values["share_product_id"] = products[0].id
                values["share_payment_sepa_direct_debit"] = (
                    product[0].payment_mode_id.payment_method_id.code
                    == "sepa_direct_debit"
                    or False
                )
        if not values.get("country_id"):
            if company.default_country_id:
                values["country_id"] = company.default_country_id.id
            else:
                values["country_id"] = 68
        if not values.get("activities_country_id"):
            if company.default_country_id:
                values["activities_country_id"] = company.default_country_id.id
            else:
                values["activities_country_id"] = 68
        if not values.get("lang"):
            if company.default_lang_id:
                values["lang"] = company.default_lang_id.code

        values.update(
            {
                "display_data_policy": company.display_data_policy_approval,
                "data_policy_required": company.data_policy_approval_required,
                "data_policy_text": company.data_policy_approval_text,
                "display_internal_rules": company.display_internal_rules_approval,
                "internal_rules_required": company.internal_rules_approval_required,
                "internal_rules_text": company.internal_rules_approval_text,
                "display_financial_risk": company.display_financial_risk_approval,
                "financial_risk_required": company.financial_risk_approval_required,
                "financial_risk_text": company.financial_risk_approval_text,
                "display_generic_rules": company.display_generic_rules_approval,
                "generic_rules_required": company.generic_rules_approval_required,
                "generic_rules_text": company.generic_rules_approval_text,
            }
        )
        return values

    def validation(  # noqa: C901 (method too complex)
        self, kwargs, logged, values, post_file
    ):
        target_odoo_company_id = (
            kwargs.get("company_id") and int(kwargs.get("company_id")) or None
        )

        sub_req_obj = request.env["subscription.request"]

        redirect = "cooperator_website.becomecooperator"

        if target_odoo_company_id:
            company = request.env["res.company"].sudo().browse(target_odoo_company_id)
        else:
            company = request.website.company_id

        values["redirect_url"] = urljoin(
            request.httprequest.host_url,
            "/page/become_cooperator?odoo_company_id={}".format(company.id),
        )
        email = kwargs.get("email")
        is_company = kwargs.get("is_company") == "on"

        if is_company:
            is_company = True
            redirect = "cooperator_website.becomecompanycooperator"
            email = kwargs.get("company_email")

        # Check that required field from model subscription_request exists
        required_fields = sub_req_obj.sudo().get_required_field()
        error = {field for field in required_fields if not values.get(field)}  # noqa
        if error:
            values = self.fill_values(values, is_company, logged)
            values["error_msg"] = _("Some mandatory fields have not been filled.")
            values = dict(values, error=error, kwargs=kwargs.items())
            return request.render(redirect, values)

        # email match verification
        if not logged and email:
            confirm_email = kwargs.get("confirm_email")
            if email != confirm_email:
                values = self.fill_values(values, is_company, logged)
                values.update(kwargs)
                values["error_msg"] = _(
                    "Email and confirmation email addresses don't match."
                )
                return request.render(redirect, values)
        values["confirm_email"] = email

        # existing cooperator
        if "vat" in required_fields:
            vat = kwargs.get("vat")
            if vat:
                vat = vat.strip().upper()

            partner = request.env["res.partner"].sudo().search([("vat", "ilike", vat)])
            if partner:
                membership = partner._get_member_or_candidate_cooperative_membership(
                    company.id
                )
                if membership:
                    values = self.fill_values(values, is_company, logged)
                    values.update(kwargs)
                    values["error_msg"] = _(
                        "There is an existing account for this"
                        " vat number on this community. "
                        "Please contact with the community administrators."
                    )
                    return request.render(redirect, values)

        # upload id card image validation
        if company.allow_id_card_upload:
            if not post_file:
                values = self.fill_values(values, is_company, logged)
                values.update(kwargs)
                values["error_msg"] = _("Please upload a scan of your ID card.")
                return request.render(redirect, values)

        # iban validation
        if "iban" in required_fields:
            iban = kwargs.get("iban")
            if iban.strip():
                valid = sub_req_obj.check_iban(iban)

                if not valid:
                    values = self.fill_values(values, is_company, logged)
                    values["error_msg"] = _("Provided IBAN is not valid.")
                    return request.render(redirect, values)

        # check the subscription's amount
        max_amount = company.subscription_maximum_amount
        if logged:
            partner = request.env.user.partner_id
            if partner.member:
                max_amount = max_amount - partner.total_value
                if company.unmix_share_type:
                    share = self.get_selected_share(kwargs)
                    if partner.cooperator_type != share.default_code:
                        values = self.fill_values(values, is_company, logged)
                        values["error_msg"] = _(
                            "You can't subscribe to two different types of share."
                        )
                        return request.render(redirect, values)
        total_amount = float(kwargs.get("total_parts"))

        if max_amount > 0 and total_amount > max_amount:
            values = self.fill_values(values, is_company, logged)
            values["error_msg"] = _(
                "You can't subscribe for an amount that exceeds "
                "{amount}{currency_symbol}."
            ).format(amount=max_amount, currency_symbol=company.currency_id.symbol)
            return request.render(redirect, values)

        # remove non-model attributes (used internally when re-rendering the
        # form in case of a validation error)
        del values["redirect_url"]
        del values["confirm_email"]

        return True
