import base64
import re
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
    "ce_creation_date": _("Constitution date"),
    "ce_constitution_status": _("Constitution status"),
    "ce_constitution_status_other": _("Which one?"),
    "ce_legal_form": _("Community legal form"),
    "ce_member_mandatory_contribution": _(
        "What amount of mandatory contribution to the social capital do you ask for when a new member joins?"
    ),
    "ce_registration_tool": _(
        "Describe which system is currently used by the Register of members (historical register of additions/dismissals and official list of members)"
    ),
    "ce_account_management": _(
        "Do you plan to use Odoo (management program) of the platform to keep the accounts of the Energy Community? or will an external management take it to you?"
    ),
    "ce_tax_management": _(
        "Do you plan to use the platform's Odoo (management program) to carry out tax management: generation of tax reports from the Treasury (303, 390,...) or will it be carried out by an external management company?"
    ),
    "ce_management_can_enter_platform": _(
        "Do you think that management could enter Odoo to generate the models from Odoo itself?"
    ),
    "ce_manager": _(
        "Who will do the day-to-day corporate management of the Energy Community? (person/s with user access to the Odoo corporate/accounting/tax management program of the Energy Community)"
    ),
    "ce_manager_firstname": _("Name"),
    "ce_manager_surname": _("Surnames"),
    "ce_manager_email": _("Email"),
    "ce_manager_phone": _("Phone"),
    "ce_payment_method": _(
        "Which payment method will you use to collect the mandatory contributions to the share capital (registration of new partners)?"
    ),
    "ce_iban_1": _("IBAN (bank account) used by the Energy Community"),
    "ce_iban_2": _(
        "IBAN 2 (bank account) used by the Energy Community (only if you use more than one)"
    ),
    "ce_extra_charges": _(
        "Are members charged any type of recurring fee? For what concepts? How are they charged? How often?"
    ),
    "ce_voluntary_contributions": _(
        "Do the members currently make voluntary contributions to the social capital of the Energy Community? How it works?"
    ),
    "ce_other_comments": _(
        "Do you want to comment on any other particular / important aspect of your corporate management?"
    ),
    "ce_web_url": _("Web url"),
    "ce_twitter_url": _("Twitter url"),
    "ce_instagram_url": _("Instagram url"),
    "ce_facebook_url": _("Facebook url"),
    "ce_telegram_url": _("Telegram url"),
}
_COMMUNITY_DATA__LEGAL_DOC_FIELDS = {
    "ce_vat": _("VAT"),
}
_COMMUNITY_DATA__GENERAL_FIELDS.update(_COMMUNITY_DATA__LEGAL_DOC_FIELDS)
_COMMUNITY_DATA__BOOLEAN_FIELDS = {
    "ce_privacy_policy": _("I have read and accept the privacy policy"),
}
_COMMUNITY_DATA__GENERAL_FIELDS.update(_COMMUNITY_DATA__BOOLEAN_FIELDS)
_COMMUNITY_DATA__PAST_DATE_FIELDS = {
    "ce_creation_date": _("Constitution date"),
}
_COMMUNITY_DATA__DATE_FIELDS = _COMMUNITY_DATA__PAST_DATE_FIELDS
_COMMUNITY_DATA__GENERAL_FIELDS.update(_COMMUNITY_DATA__DATE_FIELDS)
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
# OPTIONS
_COMMUNITY_STATUS_OPTIONS = [
    {"id": "open", "name": _("Open")},
    {"id": "closed", "name": _("Closed")},
]
_COMMUNITY_TYPE_OPTIONS = [
    {"id": "citizen", "name": _("Citizen")},
    {"id": "industrial", "name": _("Industrial")},
]
_COMMUNITY_CONSTITUTION_STATUS_OPTIONS = [
    {"id": "constituted", "name": _("Legally constituted")},
    {"id": "in_progress", "name": _("Constitution in progress")},
    {"id": "in_definition", "name": _("Definition in progress")},
    {"id": "other", "name": _("Other")},
]
_COMMUNITY_MANAGEMENT_OPTIONS = [
    {"id": "our_platform", "name": _("Our platform")},
    {"id": "external_management", "name": _("External management")},
]
_YES_NO_OPTIONS = [
    {"id": "yes", "name": _("Yes")},
    {"id": "no", "name": _("No")},
]
_COMMUNITY_MANAGER_OPTIONS = [
    {
        "id": "coordinator",
        "name": _(
            "It will be delegated to people from the Coordinating entity that supports the Energy Community on the Platform"
        ),
    },
    {
        "id": "member_admin",
        "name": _("One or more of a person linked to the Energy Community itself"),
    },
    {"id": "both", "name": _("Both of the above options")},
]
_COMMUNITY_PAYMENT_METHOD_OPTIONS = [
    {
        "id": "transfer",
        "name": _("Transfer of the candidate to partner to the entity's account"),
    },
    {
        "id": "sepa",
        "name": _("Bank transfer to the account of the candidate for membership"),
    },
]


class WebsiteCommunityData(http.Controller):
    #
    # ROUTER
    #
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
        # lead_id validation
        response = self._page_render_validation(kwargs)
        if response is not True:
            return response

        values = {}
        form_values = {}

        related_lead = (
            request.env["crm.lead"]
            .sudo()
            .search([("external_id", "=", kwargs["lead_id"])])
        )

        energy_services = self._get_energy_service_tag_ids()
        form_energy_services = []

        # data structures contruction
        for field_name, field_value in kwargs.items():
            if field_name in _COMMUNITY_DATA__URL_PARAMS.keys():
                values[field_name] = field_value
            if field_name in _COMMUNITY_DATA__GENERAL_FIELDS.keys():
                if field_value:
                    values[field_name] = field_value
                    form_values[field_name] = field_value
                else:
                    lead_meta = related_lead.get_metadata(field_name)
                    if lead_meta:
                        lead_meta.unlink()

            if field_name in _COMMUNITY_DATA__IMAGE_FIELDS.keys():
                if field_value.filename:
                    values[field_name] = field_value
                    form_values[field_name] = field_value
            if field_name in energy_services:
                form_energy_services.append(field_name)

        # enter boolean if not set
        for boolean_key in _COMMUNITY_DATA__BOOLEAN_FIELDS.keys():
            if boolean_key not in kwargs.keys():
                values[boolean_key] = "off"

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

        # avoid form resubmission by accessing /submit url
        if form_values:
            # validation
            response = self._form_submit_validation(values)
            if response is not True:
                return response
            # metadata processing
            self._process_lead_metadata(related_lead, values)
            # success
            return self._get_community_data_submit_response(values)
        else:
            return request.redirect(self._get_community_data_page_url(values))

    #
    # GETTERS
    #
    def _get_translation(self, source):
        return request.env["ir.translation"]._get_source(
            name="addons/energy_communities/controllers/website_community_data.py",
            types="code",
            lang=request.env.context["lang"],
            source=source,
        )

    def _get_localized_options(self, original_options):
        localized_options = []
        for option in original_options:
            localized_options.append(
                {
                    "id": option["id"],
                    "name": request.env["ir.translation"]._get_source(
                        name="addons/energy_communities/controllers/website_community_data.py",
                        types="code",
                        lang=request.env.context["lang"],
                        source=option["name"],
                    ),
                }
            )
        return localized_options

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
            .sudo()
            .search([("active", "=", 1)])
            .mapped(lambda r: {"id": r.code, "name": r.name})
        )

    def _get_energy_service_tags(self):
        return (
            request.env["crm.tag"]
            .sudo()
            .search([("tag_type", "=", "energy_service")])
            .mapped(
                lambda r: {
                    "id": r.tag_ext_id.replace("energy_communities.", ""),
                    "name": r.name,
                }
            )
        )

    def _is_lead_pack(self, lead_id, pack_tag_ext_id):
        leads = request.env["crm.lead"].sudo().search([("external_id", "=", lead_id)])
        if leads:
            lead = leads[0]
            pack_tag = lead.tag_ids.filtered(
                lambda tag: tag.tag_ext_id == "energy_communities." + pack_tag_ext_id
            )
            return bool(pack_tag)

    def _get_energy_service_tag_ids(self):
        return (
            request.env["crm.tag"]
            .sudo()
            .search([("tag_type", "=", "energy_service")])
            .mapped(lambda r: r.tag_ext_id.replace("energy_communities.", ""))
        )

    def _get_legal_forms(self):
        legal_forms = []
        for legal_form_id, legal_form_name in _LEGAL_FORM_VALUES:
            legal_forms.append(
                {
                    "id": legal_form_id,
                    "name": request.env["ir.translation"]._get_source(
                        name="addons/energy_communities/models/res_company.py",
                        types="code",
                        lang=request.env.context["lang"],
                        source=legal_form_name,
                    ),
                }
            )
        return legal_forms

    def _get_lead_values(self, lead_id):
        leads = request.env["crm.lead"].sudo().search([("external_id", "=", lead_id)])
        lead_values = {"closed_lead": False}
        if leads:
            lead = leads[0]
            if lead.probability >= 100 or lead.stage_id.is_won:
                lead_values["closed_lead"] = True

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

    #
    # UTILS
    #
    def _fill_values(self, values, display_success=False, display_form=True):
        # urls
        values["page_url"] = self._get_community_data_page_url(values)
        values["form_submit_url"] = "/community-data/submit?lead_id={lead_id}".format(
            lead_id=values["lead_id"]
        )
        # packs
        values["pack_1"] = self._is_lead_pack(values["lead_id"], "pack_1")
        values["pack_2"] = self._is_lead_pack(values["lead_id"], "pack_2")
        # form labels
        # form keys
        for field_key in _COMMUNITY_DATA__FIELDS.keys():
            # values[field_key + "_label"] = _COMMUNITY_DATA__FIELDS[field_key]
            values[field_key + "_label"] = request.env["ir.translation"]._get_source(
                name="addons/energy_communities/controllers/website_community_data.py",
                types="code",
                lang=request.env.context["lang"],
                source=_COMMUNITY_DATA__FIELDS[field_key],
            )
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
        if "ce_services" not in values.keys() or values["ce_services"] == "":
            values["ce_services"] = []
        values["energy_service_options"] = self._get_energy_service_tags()
        # yes_no selection
        values["yes_no_options"] = self._get_localized_options(_YES_NO_OPTIONS)
        # community_status selection
        values["community_status_options"] = self._get_localized_options(
            _COMMUNITY_STATUS_OPTIONS
        )
        # community_type selection
        values["community_type_options"] = self._get_localized_options(
            _COMMUNITY_TYPE_OPTIONS
        )
        # community_management selection
        values["community_management_options"] = self._get_localized_options(
            _COMMUNITY_MANAGEMENT_OPTIONS
        )
        # community_manager selection
        values["community_manager_options"] = self._get_localized_options(
            _COMMUNITY_MANAGER_OPTIONS
        )
        # community_payment_method_options
        values["community_payment_method_options"] = self._get_localized_options(
            _COMMUNITY_PAYMENT_METHOD_OPTIONS
        )
        # community_constitution_status selection
        values["community_constitution_status_options"] = self._get_localized_options(
            _COMMUNITY_CONSTITUTION_STATUS_OPTIONS
        )
        # community_legal_form selection
        values["community_legal_form_options"] = self._get_legal_forms()
        # image preselection from db (if necessary)
        for image_field_key in _COMMUNITY_DATA__IMAGE_FIELDS.keys():
            if image_field_key not in values.keys():
                lead_values = self._get_lead_values(values["lead_id"])
                if image_field_key in lead_values:
                    values[image_field_key] = lead_values[image_field_key]
        # form/messages visibility
        values["display_success"] = display_success
        values["display_form"] = display_form
        values["closed_form"] = False
        # if lead is won close form
        if "closed_lead" in values.keys():
            values["closed_form"] = values["closed_lead"]
        return values

    #
    # VALIDATION
    #
    def _lead_id_validation(self, values):
        # lead_id not defined
        values["lead_id"] = values.get("lead_id", False)
        if not values["lead_id"]:
            return {
                "error_msgs": [
                    _(
                        "lead_id param must be defined on the url in order to use the form"
                    )
                ],
                "global_error": True,
            }
        # lead_id not lost
        related_lead = (
            request.env["crm.lead"]
            .sudo()
            .search([("active", "=", False), ("external_id", "=", values["lead_id"])])
        )
        if related_lead:
            return {
                "error_msgs": [_("Related Lead closed.")],
                "ce_name": related_lead.name,
                "display_success": False,
                "display_form": False,
                "closed_form": True,
            }
        # lead_id not found
        related_lead = (
            request.env["crm.lead"]
            .sudo()
            .search([("external_id", "=", values["lead_id"])])
        )
        if not related_lead:
            return {
                "error_msgs": [
                    _(
                        "Related Lead not found. The url is not correct. lead_id param invalid."
                    )
                ],
                "global_error": True,
            }
        return values

    def _validate_regex(self, value, regex_string):
        regex = re.compile(regex_string)
        match = regex.match(str(value))
        return bool(match)

    def _validate_past_date(self, date_string):
        form_date = datetime.strptime(date_string, "%d/%m/%Y").strftime("%Y-%m-%d")
        now = datetime.today().strftime("%Y-%m-%d")
        return form_date <= now

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

        # ce_services validation
        if "ce_services" not in values.keys():
            error.append("ce_services")
            error_msgs.append(
                _(
                    "Please select at least one Energy service in order to submit the form"
                )
            )

        # image validation
        for image_field_key in _COMMUNITY_DATA__IMAGE_FIELDS.keys():
            if image_field_key in values.keys():
                if values[image_field_key].filename:
                    if "image" not in values[image_field_key].mimetype:
                        error.append(image_field_key)
                        error_msgs.append(
                            _("{} must be of type image (jpg/jpeg/png)").format(
                                self._get_translation(
                                    _COMMUNITY_DATA__IMAGE_FIELDS[image_field_key]
                                )
                            )
                        )

        # date validation
        for date_field_key in _COMMUNITY_DATA__DATE_FIELDS.keys():
            if date_field_key in values.keys():
                if not self._validate_regex(
                    values[date_field_key],
                    r"(((0[1-9])|([12][0-9])|(3[01]))\/((0[0-9])|(1[012]))\/((20[012]\d|19\d\d)|(1\d|2[0123])))",
                ):
                    error.append(date_field_key)
                    error_msgs.append(
                        _("{} field must have date format (dd/mm/yyyy)").format(
                            self._get_translation(
                                _COMMUNITY_DATA__DATE_FIELDS[date_field_key]
                            )
                        )
                    )
                elif date_field_key in _COMMUNITY_DATA__PAST_DATE_FIELDS:
                    if not self._validate_past_date(values[date_field_key]):
                        error.append(date_field_key)
                        error_msgs.append(
                            _("{} field must be a past date").format(
                                self._get_translation(
                                    _COMMUNITY_DATA__DATE_FIELDS[date_field_key]
                                )
                            )
                        )

        # TODO: legal docs validation
        # TODO: iban validator
        # TODO: url validator

        if error_msgs:
            values["error"] = error
            values["error_msgs"] = error_msgs
            values = self._fill_values(values, False, True)
            return request.render("energy_communities.community_data_page", values)
        return True

    #
    # DATA PROCESSING
    #
    def _process_lead_metadata(self, related_lead, values):
        changed_data = []
        for meta_key in _COMMUNITY_DATA__GENERAL_FIELDS.keys():
            if meta_key in values.keys():
                changed = related_lead.create_update_metadata(
                    meta_key, values[meta_key]
                )
                if changed:
                    changed_data.append(meta_key)
        for meta_key in _COMMUNITY_DATA__IMAGE_FIELDS.keys():
            if meta_key in values.keys():
                attachment = self._create_attachment(related_lead, values[meta_key])
                changed = related_lead.create_update_metadata(meta_key, attachment.id)
                if changed:
                    changed_data.append(meta_key)
        # notification message
        if bool(changed_data):
            changed_data_msg_body = "<h6>{}</h6><ul>".format(
                _("Public community data changed:")
            )
            for meta_key in changed_data:
                changed_data_msg_body += "<li>{label}: {value}</li>".format(
                    label=_COMMUNITY_DATA__FIELDS[meta_key], value=values[meta_key]
                )
            changed_data_msg_body += "</ul>"
            related_lead.sudo().message_post(
                subject="{} public form submission".format(related_lead.name),
                body=changed_data_msg_body,
                subtype_id=None,
                message_type="notification",
                subtype_xmlid="mail.mt_comment",
            )

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
