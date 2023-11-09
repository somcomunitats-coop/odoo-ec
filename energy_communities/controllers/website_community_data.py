import base64
from datetime import datetime

from odoo import _, http
from odoo.http import request

from ..models.res_company import _LEGAL_FORM_VALUES

_COMMUNITY_DATA__FIELDS = {}
_COMMUNITY_DATA__GENERAL_FIELDS = {
    "ce_name": _("Energy Community Name"),
    "ce_fiscal_name": _("Fiscal Name"),
    "ce_description": _("Community short description"),
    "ce_long_description": _("Community long description"),
    "ce_address": _("Address (Street, number, appartment)"),
    "ce_zip": _("Postal Code"),
    "ce_city": _("City"),
    "ce_state": _("State"),
    "email_from": _("Community Email"),
    "contact_phone": _("Community Phone"),
    "current_lang": _(
        "Predefined language for the Community (communication will be used on this language.)"
    ),
    "ce_services": _("Community active services"),
    "ce_number_of_members": _("Number of members"),
    "ce_status": _("Is the community open to accept new members or already closed?"),
    "ce_why_become_cooperator": _("Why become cooperator"),
    "ce_become_cooperator_process": _("Become cooperator process"),
    "ce_type": _("Community type"),
    "ce_constitution_state": _("Constitution state"),
    "ce_constitution_state_other": _("Which one?"),
    "ce_legal_form": _("Community legal form"),
}
_COMMUNITY_DATA__FIELDS.update(_COMMUNITY_DATA__GENERAL_FIELDS)
_COMMUNITY_DATA__IMAGE_FIELDS = {
    "ce_primary_image_file": _("Primary Image"),
    "ce_secondary_image_file": _("Secondary Image"),
    "ce_logo_image_file": _("Community Logo"),
}
_COMMUNITY_DATA__FIELDS.update(_COMMUNITY_DATA__IMAGE_FIELDS)
_COMMUNITY_DATA__URL_PARAMS = {
    "lead_id": _("lead_id on website url"),
}
_COMMUNITY_DATA__FIELDS.update(_COMMUNITY_DATA__URL_PARAMS)
_COMMUNITY_STATUS_OPTIONS = [
    {"id": "open", "name": _("Open")},
    {"id": "closed", "name": _("Closed")},
]
_COMMUNITY_TYPE_OPTIONS = [
    {"id": "citizen", "name": _("Citizen")},
    {"id": "industrial", "name": _("Industrial")},
]
_COMMUNITY_CONSTITUTION_STATE_OPTIONS = [
    {"id": "constituted", "name": _("Legally constituted")},
    {"id": "in_progress", "name": _("Constitution in progress")},
    {"id": "in_definition", "name": _("Definition in progress")},
    {"id": "other", "name": _("Other")},
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
        # lead_id validation
        response = self._page_render_validation(kwargs)
        if response is not True:
            return response
        # prefill values
        lead_values = self._get_lead_values(kwargs["lead_id"])
        lead_values.update(kwargs)
        values = self._fill_values(lead_values)
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

        energy_services = self._get_energy_service_tag_ids()
        form_energy_services = []

        print("Processing values")
        print(kwargs)

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
            if field_name in energy_services:
                form_energy_services.append(field_name)

        # convert form_energy_services on meta string
        for i, form_energy_service in enumerate(form_energy_services):
            if i == 0:
                form_values["ce_services"] = form_energy_service
                values["ce_services"] = form_energy_service
            else:
                form_values["ce_services"] += form_energy_service
                values["ce_services"] += form_energy_service
            if i != len(form_energy_services) - 1:
                form_values["ce_services"] += ","
                values["ce_services"] += ","

        # avoid form resubmission by ctrl+r
        if form_values:
            # validation
            response = self._form_submit_validation(values)
            if response is not True:
                return response
            # metadata processing
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
            .mapped(lambda r: {"id": r.id, "name": r.name})
        )

    def _get_langs(self):
        return (
            request.env["res.lang"]
            .search([("active", "=", 1)])
            .mapped(lambda r: {"id": r.code, "name": r.name})
        )

    def _get_energy_service_tags(self):
        return (
            request.env["crm.tag"]
            .search([("tag_type", "=", "energy_service")])
            .mapped(
                lambda r: {
                    "id": r.tag_ext_id.replace("energy_communities.", ""),
                    "name": r.name,
                }
            )
        )

    def _get_energy_service_tag_ids(self):
        return (
            request.env["crm.tag"]
            .search([("tag_type", "=", "energy_service")])
            .mapped(lambda r: r.tag_ext_id.replace("energy_communities.", ""))
        )

    def _get_legal_forms(self):
        legal_forms = []
        for legal_form_id, legal_form_name in _LEGAL_FORM_VALUES:
            legal_forms.append({"id": legal_form_id, "name": legal_form_name})
        return legal_forms

    def _get_lead_values(self, lead_id):
        lead_values = {}
        lead = request.env["crm.lead"].sudo().search([("id", "=", lead_id)])[0]
        # TODO: When we know how to populate form fields need to move this to iterate trough _COMMUNITY_DATA__FORM_FIELDS
        for field_key in _COMMUNITY_DATA__GENERAL_FIELDS.keys():
            meta_line = lead.metadata_line_ids.filtered(
                lambda meta_data_line: meta_data_line.key == field_key
            )
            if meta_line:
                lead_values[field_key] = meta_line.value
        for field_key in _COMMUNITY_DATA__IMAGE_FIELDS.keys():
            meta_line = lead.metadata_line_ids.filtered(
                lambda meta_data_line: meta_data_line.key == field_key
            )
            if meta_line:
                attachment = (
                    request.env["ir.attachment"]
                    .sudo()
                    .search([("id", "=", meta_line.value)])
                )
                if attachment:
                    lead_values[
                        field_key
                    ] = "{base_url}/web/image/{attachment_id}".format(
                        base_url=request.env["ir.config_parameter"]
                        .sudo()
                        .get_param("web.base.url"),
                        attachment_id=attachment.id,
                    )
        return lead_values

    def _fill_values(self, values, display_success=False, display_form=True):
        # urls
        values["page_url"] = self._get_community_data_page_url(values)
        values["form_submit_url"] = "community-data/submit?lead_id={lead_id}".format(
            lead_id=values["lead_id"]
        )
        # form labels
        # form keys
        for field_key in _COMMUNITY_DATA__FIELDS.keys():
            values[field_key + "_label"] = _COMMUNITY_DATA__FIELDS[field_key]
            values[field_key + "_key"] = field_key
        # language selection
        values["lang_options"] = self._get_langs()
        if "current_lang" not in values.keys() or values["current_lang"] == "":
            values["current_lang"] = False
        # state selection
        values["state_options"] = self._get_states()
        if (
            "ce_state" not in values.keys()
            or values["ce_state"] == ""
            or not values["ce_state"].isnumeric()
        ):
            values["ce_state"] = False
        # energy_services selection
        values["energy_service_options"] = self._get_energy_service_tags()
        # community_status selection
        values["community_status_options"] = _COMMUNITY_STATUS_OPTIONS
        # community_type selection
        values["community_type_options"] = _COMMUNITY_TYPE_OPTIONS
        # community_constitution_state selection
        values[
            "community_constitution_state_options"
        ] = _COMMUNITY_CONSTITUTION_STATE_OPTIONS
        # community_legal_form selection
        values["community_legal_form_options"] = self._get_legal_forms()
        # form/messages visibility
        values["display_success"] = display_success
        values["display_form"] = display_form
        return values

    def _lead_id_validation(self, values):
        values["lead_id"] = values.get("lead_id", False)
        if not values["lead_id"]:
            values["error_msgs"] = [
                _("lead_id param must be defined on the url in order to use the form")
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
                    "public": True,
                }
            )
        )
