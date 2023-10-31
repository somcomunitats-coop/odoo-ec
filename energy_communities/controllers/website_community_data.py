import base64
from datetime import datetime

from odoo import http
from odoo.http import request
from odoo.tools.translate import _

_COMMUNITY_DATA__FIELDS = {}
_COMMUNITY_DATA__GENERAL_FIELDS = {
    "cd_community_name": _("Energy Community Name"),
    "cd_address": _("Address (Street, number, appartment number)"),
    "cd_zip": _("Postal Code"),
    "cd_state_id": _("State"),
    "cd_contact_email": _("Contact Email"),
}
_COMMUNITY_DATA__FIELDS.update(_COMMUNITY_DATA__GENERAL_FIELDS)
_COMMUNITY_DATA__IMAGE_FIELDS = {
    "cd_primary_image_file": _("Primary Image Field"),
    "cd_secondary_image_file": _("Secondary Image Field"),
}
_COMMUNITY_DATA__FIELDS.update(_COMMUNITY_DATA__IMAGE_FIELDS)
_COMMUNITY_DATA__URL_PARAMS = {
    "lead_id": _("lead_id on website url"),
}
_COMMUNITY_DATA__FIELDS.update(_COMMUNITY_DATA__URL_PARAMS)


class WebsiteCommunityData(http.Controller):
    @http.route(
        ["/page/community-data", "/community-data"],
        type="http",
        auth="public",
        website=True,
    )
    def display_community_data_page(self, **kwargs):
        values = {}
        # lead_id validation
        response = self._page_render_validation(kwargs)
        if response is not True:
            return response
        # prefill values
        values = self._fill_values(kwargs)
        return request.render("energy_communities.community_data_page", values)

    @http.route(
        ["/community-data/submit"],
        type="http",
        auth="public",
        website=True,
    )
    def community_data_submit(self, **kwargs):
        values = {}
        form_values = {}

        # data structures contruction
        for field_name, field_value in kwargs.items():
            if field_name in _COMMUNITY_DATA__URL_PARAMS.keys():
                values[field_name] = field_value
            if field_name in _COMMUNITY_DATA__GENERAL_FIELDS.keys():
                if field_value:
                    values[field_name] = field_value
                    form_values[field_name] = field_value
            if field_name in _COMMUNITY_DATA__IMAGE_FIELDS.keys():
                if field_value.filename:
                    values[field_name] = field_value
                    form_values[field_name] = field_value

        # avoid form resubmission by ctrl+r
        if form_values:
            # validation
            response = self._form_submit_validation(values)
            if response is not True:
                return response
            # TODO: process lead metadata here
            self._process_lead_metadata(values)
            # success
            return self._get_community_data_submit_response(values)
        else:
            return request.redirect(self._get_community_data_page_url(values))

        # values["birthdate"] = datetime.strptime(
        #     kwargs.get("birthdate"), "%Y-%m-%d"
        # ).date()

        # if is_company:
        #     if kwargs.get("company_register_number"):
        #         values["company_register_number"] = re.sub(
        #             "[^0-9a-zA-Z]+", "", kwargs.get("company_register_number")
        #         )

    def _get_community_data_submit_response(self, values):
        values = self._fill_values(values, True, False)
        return request.render("energy_communities.community_data_page", values)

    def _get_date_string(self, date_val):
        if date_val:
            return datetime.strftime(date_val, "%Y-%m-%d")
        return False

    def _get_community_data_page_url(self, values):
        return "{base_url}/community-data?lead_id={lead_id}".format(
            base_url=request.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url"),
            lead_id=values["lead_id"],
        )

    def _get_states(self):
        company = request.website.company_id
        return (
            request.env["res.country.state"]
            .sudo()
            .search([("country_id", "=", company.default_country_id.id)], order="name")
        )

    def _fill_values(self, values, display_success=False, display_form=True):
        # urls
        values["page_url"] = self._get_community_data_page_url(values)
        values["form_submit_url"] = "community-data/submit?lead_id={lead_id}".format(
            lead_id=values["lead_id"]
        )
        # form labels
        for field_key in _COMMUNITY_DATA__FIELDS.keys():
            values[field_key + "_label"] = _COMMUNITY_DATA__FIELDS[field_key]
        # state list
        values["states"] = self._get_states()
        # state_id initial
        if "cd_state_id" not in values.keys():
            values["cd_state_id"] = False
        elif values["cd_state_id"] == "":
            values["cd_state_id"] = False
        values["display_success"] = display_success
        values["display_form"] = display_form
        return values

    def _lead_id_validation(self, values):
        values["lead_id"] = values.get("lead_id", False)
        if not values["lead_id"]:
            values["error_msgs"] = [
                _("lead_id must be defined on the url in order to use the form")
            ]
            values = self._fill_values(values, False, False)
            return values
        try:
            values["lead_id"] = int(values["lead_id"])
        except ValueError:
            values["error_msgs"] = [
                _("lead_id must be defined on the url as a numeric value")
            ]
            values = self._fill_values(values, False, False)
            return values

        related_lead = (
            request.env["crm.lead"].sudo().search([("id", "=", values["lead_id"])])
        )
        if not related_lead:
            values["error_msgs"] = [
                _(
                    "Related Lead not found. The url is not correct. lead_id param invalid."
                )
            ]
            values = self._fill_values(values, False, False)
            return values
        return values

    def _page_render_validation(self, values):
        values = self._lead_id_validation(values)
        if "error_msgs" in values.keys():
            return request.render("energy_communities.community_data_page", values)
        return True

    def _form_submit_validation(self, values):
        error = []
        error_msgs = []

        # lead_id validation
        values = self._lead_id_validation(values)
        if "error_msgs" in values.keys():
            return request.render("energy_communities.community_data_page", values)

        # image validation
        for image_field_key in _COMMUNITY_DATA__IMAGE_FIELDS:
            if image_field_key in values.keys():
                if values[image_field_key].filename:
                    if "image" not in values[image_field_key].mimetype:
                        error.append(image_field_key)
                        error_msgs.append(
                            "{} must be of type image (jpg/jpeg/png)".format(
                                _COMMUNITY_DATA__IMAGE_FIELDS[image_field_key]
                            )
                        )
        if error_msgs:
            values["error"] = error
            values["error_msgs"] = error_msgs
            values = self._fill_values(values, False, True)
            return request.render("energy_communities.community_data_page", values)
        return True

    def _process_lead_metadata(self, values):
        print("PROCESS metadata")
        print(values)
        related_lead = (
            request.env["crm.lead"].sudo().search([("id", "=", values["lead_id"])])
        )
        for meta_key in _COMMUNITY_DATA__GENERAL_FIELDS.keys():
            if meta_key in values.keys():
                related_lead.create_update_metadata(meta_key, values[meta_key])
        for meta_key in _COMMUNITY_DATA__IMAGE_FIELDS.keys():
            if meta_key in values.keys():
                attachment = self._create_attachment(related_lead, values[meta_key])
                related_lead.create_update_metadata(meta_key, attachment.id)

    def _create_attachment(self, lead, value):
        return (
            request.env["ir.attachment"]
            .sudo()
            .create(
                {
                    "name": value.filename,
                    "res_model": "crm.lead",
                    "res_id": lead.id,
                    "datas": base64.encodestring(value.read()),
                }
            )
        )
