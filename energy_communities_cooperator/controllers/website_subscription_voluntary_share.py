import base64
import logging
from urllib.parse import urljoin

from odoo import http
from odoo.http import request
from odoo.tools.translate import _

from odoo.addons.cooperator_website.controllers import main as emyc_wsc

logger = logging.getLogger(__name__)
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
    @http.route(
        ["/page/voluntary_share", "/voluntary_share"],
        type="http",
        auth="public",
        website=True,
    )
    def display_voluntary_share_page(self, **kwargs):
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

        values = {}
        logged = False

        if request.env.user.login != "public":
            logged = True
        for field in _VOLUNTARY_SHARE_FORM_FIELD:
            if kwargs.get(field):
                values[field] = kwargs.pop(field)

        if request.env.user.login != "public":
            logged = True
        values = self.fill_values(values, True, logged, True)

        values.update(kwargs=kwargs.items())
        values.update({"company_id": target_odoo_company_id})
        company_id = request.env["res.company"].sudo().browse(target_odoo_company_id)
        values.update(
            {
                "company_id": target_odoo_company_id,
            }
        )
        if company_id.voluntary_share_id:
            values.update({"share_product_id": company_id.voluntary_share_id.id})
        else:
            raise UserWarning(
                _("This company doesn't have a voluntary product share selected.")
            )

        # redirect url to fall back on become cooperator in template redirection
        values["redirect_url"] = request.httprequest.url
        return request.render("energy_communities.voluntary_share", values)

    def voluntary_share_validation(  # noqa: C901 (method too complex)
        self, kwargs, logged, values, post_file
    ):
        company_id = request.env["res.company"].browse(int(kwargs.get("company_id")))

        user_obj = request.env["res.users"]
        sub_req_obj = request.env["subscription.request"]

        redirect = "energy_communities.voluntary_share"

        # url to use for "already have an account button" to go to become cooperator
        # rather than subscribe share after a failed validation
        # it is deleted at the end of the validation
        values["redirect_url"] = urljoin(
            request.httprequest.host_url, "voluntary_share"
        )

        email = kwargs.get("email")
        is_company = kwargs.get("is_company") == "on"

        # Check that required field from model subscription_request exists
        required_fields = sub_req_obj.sudo().get_required_field()
        """
        error = {field for field in required_fields if not values.get(field)}  # noqa

        if error:
            values = self.fill_values(values, is_company, logged)
            values["error_msg"] = _("Some mandatory fields have not been filled.")
            values = dict(values, error=error, kwargs=kwargs.items())
            return request.render(redirect, values)
        """

        if not logged and email:
            confirm_email = kwargs.get("confirm_email")
            if email != confirm_email:
                values = self.fill_values(values, is_company, logged)
                values.update(kwargs)
                values["error_msg"] = _(
                    "Email and confirmation email addresses don't match."
                )
                values.update({"share_product_id": company_id.voluntary_share_id.id})
                return request.render(redirect, values)

        # There's no issue with the email, so we can remember the confirmation email
        values["confirm_email"] = email

        """
        company = request.website.company_id
        if company.allow_id_card_upload:
            if not post_file:
                values = self.fill_values(values, is_company, logged)
                values.update(kwargs)
                values["error_msg"] = _("Please upload a scan of your ID card.")
                return request.render(redirect, values)
        """
        mandate_approved = kwargs.get("mandate_approved")
        if not mandate_approved:
            values = self.fill_values(values, is_company, logged)
            values["error_msg"] = _("You must check the SEPA transference.")
            values.update({"share_product_id": company_id.voluntary_share_id.id})
            return request.render(redirect, values)

        if "iban" in required_fields:
            iban = kwargs.get("iban")
            if iban.strip():
                valid = sub_req_obj.check_iban(iban)

                if not valid:
                    values = self.fill_values(values, is_company, logged)
                    values["error_msg"] = _("Provided IBAN is not valid.")
                    values.update(
                        {"share_product_id": company_id.voluntary_share_id.id}
                    )
                    return request.render(redirect, values)

        """
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
        """
        # total_amount = float(kwargs.get("total_parts"))

        """
        if max_amount > 0 and total_amount > max_amount:
            values = self.fill_values(values, is_company, logged)
            values["error_msg"] = _(
                "You can't subscribe for an amount that exceeds "
                "{amount}{currency_symbol}."
            ).format(amount=max_amount, currency_symbol=company.currency_id.symbol)
            return request.render(redirect, values)
        """
        # remove non-model attributes (used internally when re-rendering the
        # form in case of a validation error)
        del values["redirect_url"]
        del values["confirm_email"]

        return True

    @http.route(  # noqa: C901 (method too complex)
        ["/subscription/voluntary_share"],
        type="http",
        auth="public",
        website=True,
    )  # noqa: C901 (method too complex)
    def voluntary_share(self, **kwargs):  # noqa: C901 (method too complex)
        sub_req_obj = request.env["subscription.request"]
        attach_obj = request.env["ir.attachment"]

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

        ctx = dict(request.context)
        ctx.update({"target_odoo_company_id": target_odoo_company_id})
        request.context = ctx

        # List of file to add to ir_attachment once we have the ID
        post_file = []
        # Info to add after the message
        post_description = []
        values = {}

        for field_name, field_value in kwargs.items():
            if hasattr(field_value, "filename"):
                post_file.append(field_value)
            elif (
                field_name in sub_req_obj._fields
                and field_name not in emyc_wsc._BLACKLIST
            ):
                values[field_name] = field_value
            # allow to add some free fields or blacklisted field like ID
            elif field_name not in emyc_wsc._TECHNICAL:
                post_description.append("{}: {}".format(field_name, field_value))

        logged = kwargs.get("logged") == "on"
        is_company = kwargs.get("is_company") == "on"
        values["is_company"] = is_company

        response = self.voluntary_share_validation(kwargs, logged, values, post_file)
        if response is not True:
            return response

        values["source"] = "website"
        values["type"] = "increase"
        values["company_id"] = kwargs.get("company_id")
        already_coop = False
        values["vat"] = kwargs.get("vat")
        if values["vat"]:
            values["vat"] = values["vat"].strip().upper()
        partner = (
            request.env["res.partner"]
            .sudo()
            .get_cooperator_from_vat(values["vat"], values["company_id"])
        )
        if partner:
            values["partner_id"] = partner.id
            already_coop = partner.member
        elif kwargs.get("already_cooperator") == "on":
            already_coop = True

        values["already_cooperator"] = already_coop
        company = (
            request.env["res.company"]
            .sudo()
            .search([("id", "=", values["company_id"])])
        )

        if partner:
            values["email"] = partner.email or _("Email not found")
            values["phone"] = partner.phone
            values["lastname"] = partner.lastname or ""
            values["firstname"] = partner.firstname or partner.name
            values["address"] = partner.street or _("Address not found")
            values["city"] = partner.city or _("City not found")
            values["zip_code"] = partner.zip or _("ZIP code not found")
            values["country_id"] = (
                partner.country_id.id or company.default_country_id.id
            )
            values["lang"] = partner.lang or company.default_lang_id.id
            values["birthdate"] = partner.birthdate_date
        else:
            values["lastname"] = _("Partner not found")
            values["firstname"] = _("Partner not found")
            values["address"] = _("Partner not found")
            values["city"] = _("Partner not found")
            values["zip_code"] = _("Partner not found")
            values["country_id"] = company.default_country_id.id
            values["lang"] = company.default_lang_id.code

        if kwargs.get("data_policy_approved", "off") == "on":
            values["data_policy_approved"] = True
        if kwargs.get("internal_rules_approved", "off") == "on":
            values["internal_rules_approved"] = True
        if kwargs.get("financial_risk_approved", "off") == "on":
            values["financial_risk_approved"] = True
        if kwargs.get("generic_rules_approved", "off") == "on":
            values["generic_rules_approved"] = True

        values["share_product_id"] = self.get_selected_share(
            {"share_product_id": company.voluntary_share_id.id}
        ).id
        subscription_id = sub_req_obj.sudo().create(values)

        if partner:
            if partner.email != kwargs.get("email") or partner.phone != kwargs.get(
                "phone"
            ):
                subscription_id.message_post(
                    **{
                        "subject": "We found partner discrepancy in the form",
                        "body": """The contact information received from the form <b>was diferent</b> from the one saved in the partner:
                    <ul>
                        <li>Email: {} </li>
                        <li>Phone: {} </li>
                    </ul>""".format(
                            kwargs.get("email"), kwargs.get("phone"), kwargs.get("iban")
                        ),
                    }
                )
        if subscription_id:
            for field_value in post_file:
                attachment_value = {
                    "name": field_value.filename,
                    "res_model": "subscription.request",
                    "res_id": subscription_id,
                    "datas": base64.encodestring(field_value.read()),
                }
                attach_obj.sudo().create(attachment_value)

        return self.get_subscription_response(values, kwargs)
