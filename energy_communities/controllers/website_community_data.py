from datetime import datetime

from odoo import http
from odoo.http import request
from odoo.tools.translate import _

# Only use for behavior, don't stock it
# Used to filter the session dict to keep only the form fields
_TECHNICAL = ["view_from", "view_callback"]
# Allow in description
_BLACKLIST = [
    "id",
    "create_uid",
    "create_date",
    "write_uid",
    "write_date",
    "user_id",
    "active",
]

_COMMUNITY_DATA__FORM_FIELD = [
    "firstname",
    "lastname",
    "gender",
    "phone",
    "address",
    "city",
    "zip_code",
    "country_id",
    "error_msg",
]


class WebsiteCommunityData(http.Controller):
    @http.route(
        ["/page/community-data", "/community-data"],
        type="http",
        auth="public",
        website=True,
    )
    def display_community_data_page(self, **kwargs):
        values = {}
        logged = False
        if request.env.user.login != "public":
            logged = True
            partner = request.env.user.partner_id
        # prefill values
        values = self._fill_values()
        # for field in _COMMUNITY_DATA__FORM_FIELD:
        #     if kwargs.get(field):
        #         values[field] = kwargs.pop(field)
        values.update(kwargs=kwargs.items())
        # redirect url to fall back on community data in template redirection
        values["redirect_url"] = request.httprequest.url
        values["firstname"] = "populate name"
        return request.render("energy_communities.community_data_form", values)

    def _fill_values(self):
        return {"lead": False}

    def pre_render_thanks(self, values, kwargs):
        """
        Allows to modify values passed to the "thanks" template by overriding
        this method.
        """
        return {"_values": values, "_kwargs": kwargs}

    def get_community_data_submit_response(self, values, kwargs):
        values = self.pre_render_thanks(values, kwargs)
        return request.render("energy_communities.community_data_confirmation", values)

    def get_date_string(self, date_val):
        if date_val:
            return datetime.strftime(date_val, "%Y-%m-%d")
        return False

    # def _additional_validate(self, kwargs, logged, values, post_file):
    #     """
    #     Validation hook that can be reimplemented in dependent modules.

    #     This should return a boolean value indicating whether the validation
    #     succeeded or not. If it did not succeed, an error message should be
    #     assigned to values["error_msg"].
    #     """
    #     return True

    # def validation(
    #     self, kwargs, logged, values, post_file
    # ):
    #     user_obj = request.env["res.users"]
    #     sub_req_obj = request.env["subscription.request"]

    #     redirect = "cooperator_website.becomecooperator"

    #     # url to use for "already have an account button" to go to become cooperator
    #     # rather than subscribe share after a failed validation
    #     # it is deleted at the end of the validation
    #     values["redirect_url"] = urljoin(
    #         request.httprequest.host_url, "become_cooperator"
    #     )

    #     email = kwargs.get("email")
    #     is_company = kwargs.get("is_company") == "on"

    #     if is_company:
    #         is_company = True
    #         redirect = "cooperator_website.becomecompanycooperator"
    #         email = kwargs.get("company_email")
    #     # Check that required field from model subscription_request exists
    #     required_fields = sub_req_obj.sudo().get_required_field()
    #     error = {field for field in required_fields if not values.get(field)}  # noqa

    #     if error:
    #         values = self.fill_values(values, is_company, logged)
    #         values["error_msg"] = _("Some mandatory fields have not been filled.")
    #         values = dict(values, error=error, kwargs=kwargs.items())
    #         return request.render(redirect, values)

    #     if not logged and email:
    #         user = user_obj.sudo().search([("login", "=", email)])
    #         if user:
    #             values = self.fill_values(values, is_company, logged)
    #             values.update(kwargs)
    #             values["error_msg"] = _(
    #                 "An account already exists for this email address. "
    #                 "Please log in before filling in the form."
    #             )

    #             return request.render(redirect, values)
    #         else:
    #             confirm_email = kwargs.get("confirm_email")
    #             if email != confirm_email:
    #                 values = self.fill_values(values, is_company, logged)
    #                 values.update(kwargs)
    #                 values["error_msg"] = _(
    #                     "Email and confirmation email addresses don't match."
    #                 )
    #                 return request.render(redirect, values)

    #     # There's no issue with the email, so we can remember the confirmation email
    #     values["confirm_email"] = email

    #     company = request.website.company_id
    #     if company.allow_id_card_upload:
    #         if not post_file:
    #             values = self.fill_values(values, is_company, logged)
    #             values.update(kwargs)
    #             values["error_msg"] = _("Please upload a scan of your ID card.")
    #             return request.render(redirect, values)

    #     if "iban" in required_fields:
    #         iban = kwargs.get("iban")
    #         if iban.strip():
    #             valid = sub_req_obj.check_iban(iban)

    #             if not valid:
    #                 values = self.fill_values(values, is_company, logged)
    #                 values["error_msg"] = _("Provided IBAN is not valid.")
    #                 return request.render(redirect, values)

    #     # check the subscription's amount
    #     max_amount = company.subscription_maximum_amount
    #     if logged:
    #         partner = request.env.user.partner_id
    #         if partner.member:
    #             max_amount = max_amount - partner.total_value
    #             if company.unmix_share_type:
    #                 share = self.get_selected_share(kwargs)
    #                 if partner.cooperator_type != share.default_code:
    #                     values = self.fill_values(values, is_company, logged)
    #                     values["error_msg"] = _(
    #                         "You can't subscribe to two different types of share."
    #                     )
    #                     return request.render(redirect, values)
    #     total_amount = float(kwargs.get("total_parts"))

    #     if max_amount > 0 and total_amount > max_amount:
    #         values = self.fill_values(values, is_company, logged)
    #         values["error_msg"] = _(
    #             "You can't subscribe for an amount that exceeds "
    #             "{amount}{currency_symbol}."
    #         ).format(amount=max_amount, currency_symbol=company.currency_id.symbol)
    #         return request.render(redirect, values)

    #     if not self._additional_validate(kwargs, logged, values, post_file):
    #         values = self.fill_values(values, is_company, logged)
    #         return request.render(redirect, values)

    #     # remove non-model attributes (used internally when re-rendering the
    #     # form in case of a validation error)
    #     del values["redirect_url"]
    #     del values["confirm_email"]

    #     return True

    @http.route(
        ["/community-data/submit"],
        type="http",
        auth="public",
        website=True,
    )
    def community_data_submit(self, **kwargs):
        crm_lead_obj = request.env["subscription.request"]

        # List of file to add to ir_attachment once we have the ID
        post_file = []
        # Info to add after the message
        post_description = []
        values = {}

        for field_name, field_value in kwargs.items():
            if hasattr(field_value, "filename"):
                post_file.append(field_value)
            elif field_name in crm_lead_obj._fields and field_name not in _BLACKLIST:
                values[field_name] = field_value
            # allow to add some free fields or blacklisted field like ID
            elif field_name not in _TECHNICAL:
                post_description.append("{}: {}".format(field_name, field_value))

        logged = kwargs.get("logged") == "on"
        is_company = kwargs.get("is_company") == "on"

        # response = self.validation(kwargs, logged, values, post_file)
        # if response is not True:
        #     return response

        lastname = kwargs.get("lastname")
        firstname = kwargs.get("firstname")
        values["lastname"] = lastname
        values["firstname"] = firstname

        # values["birthdate"] = datetime.strptime(
        #     kwargs.get("birthdate"), "%Y-%m-%d"
        # ).date()

        # if is_company:
        #     if kwargs.get("company_register_number"):
        #         values["company_register_number"] = re.sub(
        #             "[^0-9a-zA-Z]+", "", kwargs.get("company_register_number")
        #         )

        # crm_lead_obj.sudo().write(values)

        # attachments
        # for field_value in post_file:
        #     attachment_value = {
        #         "name": field_value.filename,
        #         "res_model": "subscription.request",
        #         "res_id": subscription_id,
        #         "datas": base64.encodestring(field_value.read()),
        #     }
        #     request.env["ir.attachment"].sudo().create(attachment_value)

        return self.get_community_data_submit_response(values, kwargs)
