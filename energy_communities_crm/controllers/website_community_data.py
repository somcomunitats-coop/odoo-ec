import base64
import re
from datetime import datetime

from odoo import _, http
from odoo.http import request

from odoo.addons.energy_communities.models.res_company import (
    _LEGAL_FORM_VALUES_WEBSITE,
)
from odoo.addons.energy_communities.utils import get_translation
from odoo.addons.web.controllers.webclient import WebClient

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
    "ce_current_lang": _("Default language of the Energy Community"),
    "known_coordinator": _("Do you know the coordinator of the Energy Community?"),
    "coordinator_id": _("Select a Coordinator"),
    "ce_services": _("Community active services"),
    "ce_number_of_members": _("Number of members"),
    "ce_status": _("Is the Community open to accepting new members?"),
    "ce_why_become_cooperator": _("Why become cooperator"),
    "ce_become_cooperator_process": _("Process for becoming a member"),
    "ce_type": _("Community type"),
    "ce_creation_date": _("Constitution date"),
    "ce_constitution_status": _("Constitution status"),
    "ce_constitution_status_other": _("Which one?"),
    "ce_legal_form": _("Community legal form"),
    "ce_legal_form_other": _("Which one?"),
    "ce_member_recurrent_contribution_date": _(
        "(Associations) Fixed day of the year on which the annual membership fee is charged to members."
    ),
    "ce_member_mandatory_contribution": _(
        "Amount of the mandatory initial contribution/fee required of new members"
    ),
    "ce_management_can_enter_platform": _(
        "Do you think that management could enter Odoo to generate the models from Odoo itself?"
    ),
    "ce_date_fixed": _(
        "(Associations) Fixed day of the year for collecting membership fees from members"
    ),
    "ce_member_recurrent_contribution": _(
        "(Associations) Amount of the fixed annual membership fee for members"
    ),
    "ce_manager_firstname": _("Name"),
    "ce_manager_surname": _("Surnames"),
    "ce_manager_email": _("Email"),
    "ce_manager_phone": _("Phone"),
    "ce_payment_method": _(
        "Payment method to be used for collecting membership fees or contributions from members"
    ),
    "ce_iban_1": _("IBAN (bank account) used by the Energy Community"),
    "ce_web_url": _("Web url"),
    "ce_twitter_url": _("Twitter url"),
    "ce_instagram_url": _("Instagram url"),
    "ce_facebook_url": _("Facebook url"),
    "ce_telegram_url": _("Telegram url"),
    "ce_mastodon_url": _("Mastodon url"),
    "ce_bluesky_url": _("Bluesky url"),
    "comments": _("Comments"),
}
_COMMUNITY_DATA__LEGAL_DOC_FIELDS = {
    "ce_vat": _("VAT"),
}
_COMMUNITY_DATA__GENERAL_FIELDS.update(_COMMUNITY_DATA__LEGAL_DOC_FIELDS)
_COMMUNITY_DATA__BOOLEAN_FIELDS = {
    "terms_conditions": _("I have read and accept the privacy policy"),
}
_COMMUNITY_DATA__GENERAL_FIELDS.update(_COMMUNITY_DATA__BOOLEAN_FIELDS)
_COMMUNITY_DATA__PAST_DATE_FIELDS = {
    "ce_creation_date": _("Constitution date"),
}
_COMMUNITY_DATA__DATE_FIELDS = _COMMUNITY_DATA__PAST_DATE_FIELDS
_COMMUNITY_DATA__GENERAL_FIELDS.update(_COMMUNITY_DATA__DATE_FIELDS)
_COMMUNITY_DATA__FIELDS.update(_COMMUNITY_DATA__GENERAL_FIELDS)
_COMMUNITY_DATA__FIELDS.update()
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
_COMMUNITY_DATA__STATIC_TEXTS = {}
# H3 TEXTS
_COMMUNITY_DATA__H3_TEXTS = {
    "general_data_h3": _("General data"),
    "coordinator_h3": _("Coordinator"),
    "status_h3": _("Status"),
    "activity_h3": _("Activity"),
    "corporate_and_administrative_management_h3": _(
        "Corporate and administrative management"
    ),
    "website_data_and_map_h3": _("Website data and map"),
    "social_media_h3": _("Social media"),
    "comments_h3": _("Comments"),
}
_COMMUNITY_DATA__STATIC_TEXTS.update(_COMMUNITY_DATA__H3_TEXTS)
# HELPS TEXTS
_COMMUNITY_DATA__HELPS_TEXTS = {
    "known_coordinator_help_html": _(
        "The Som Comunitats Platform requests that every Energy Community be supported by a Coordinating Entity. <a href='https://somcomunitats.coop/es/que-son-las-coordinadoras/' target='_blank'>Here</a> we explain what they are, and <a href='https://somcomunitats.coop/es/que-son-las-coordinadoras/#ce-coordinadores-members' target='_blank'>here</a> is a list of available Coordinators."
    ),
    "coordinator_id_help_html": _(
        "Select which <a href='https://somcomunitats.coop/es/que-son-las-coordinadoras/#ce-coordinadores-members' target='_blank'>coordinating entity</a> you would like to accompany and support you."
    ),
    "comments_help": _(
        "Please indicate if there is anything else you think we should consider."
    ),
    "ce_member_recurrent_contribution_date_help": _(
        "Select it for the current year. Example: if it is 2025 and the annual fee is charged on March 1, select 03/01/2025."
    ),
    "ce_description_help_html": _(
        "Use a maximum of 1000 characters to write a summary of your Energy Community. It will be published as a description of the Community at its <a href='https://somcomunitats.coop/es/#encuentra-tu-comunidad' target='_blank'>map</a> location and at the top of its <a href='https://somcomunitats.coop/wp-content/uploads/2025/09/landing-prova-es.png' target='_blank'>own web page</a> on the Platform."
    ),
    "ce_long_description_help_html": _(
        "Use a maximum of 1500 characters to explain your Energy Community. It will be published in the ‘About us’ section of <a href='https://somcomunitats.coop/wp-content/uploads/2025/09/landing-prova-es.png' target='_blank'>your own page</a> on the Platform."
    ),
    "ce_become_cooperator_process_help_html": _(
        "Use a maximum of 500 characters to explain the process for joining the Community. If completed, it will be published in the ‘Registration Process’ section of <a href='https://somcomunitats.coop/wp-content/uploads/2025/09/landing-prova-es.png' target='_blank'>your own website</a> on the Platform."
    ),
    "ce_number_of_members_help": _(
        "Current participants in the Energy Community. If it has not yet been established, indicate the number of people interested in joining or those who make up the group promoting/driving the initiative (enter a value greater than or equal to 1)."
    ),
    "ce_status_help_html": _(
        "If ‘Open’ is selected, buttons will be displayed that provide access to public forms for receiving applications from new members of the Community at your <a href='https://somcomunitats.coop/es/#encuentra-tu-comunidad' target='_blank'>map</a> location and at the top of your <a href='https://somcomunitats.coop/wp-content/uploads/2025/09/landing-prova-es.png' target='_blank'>own website</a> on the Platform. Otherwise, these buttons will be hidden and only a generic Contact the Community button will be displayed."
    ),
    "ce_why_become_cooperator_help_html": _(
        "Use a maximum of 500 characters to explain the advantages of joining the Community. If filled in, it will be published in the ‘Why become a member’ section of your <a href='https://somcomunitats.coop/wp-content/uploads/2025/09/landing-prova-es.png' target='_blank'>own web page</a> on the Platform."
    ),
    "ce_current_lang_help": _(
        "All communications from the Energy Community will be made in this language by default."
    ),
    "ce_legal_form_help": _(
        "Indicate the legal form that the Community already has or that you know it will have. If you do not know yet, you can select: ‘To be defined’."
    ),
    "ce_primary_image_file_help_html": _(
        "Preferably a group photo of the Energy Community. It will be published at the top of your <a href='https://somcomunitats.coop/wp-content/uploads/2025/09/landing-prova-es.png' target='_blank'>own web page</a> on the Platform."
    ),
    "ce_secondary_image_file_help_html": _(
        "It will be published in the Contact section of <a href='https://somcomunitats.coop/wp-content/uploads/2025/09/landing-prova-es.png' target='_blank'>your own web page</a> on the Platform."
    ),
    "ce_web_url_help": _(
        "Link to the Energy Community website. Example: https://somcomunitats.coop"
    ),
    "ce_twitter_url_help": _(
        "Link to the Energy Community's social network profile. Example: https://x.com/SomComunitats"
    ),
    "ce_instagram_url_help": _(
        "Link to the Energy Community's social network profile. Example: https://www.instagram.com/SomComunitats/"
    ),
    "ce_facebook_url_help": _(
        "Link to the Energy Community's social network profile. Example: https://www.facebook.com/SomComunitats/"
    ),
    "ce_telegram_url_help": _(
        "Link to the Energy Community's social network profile. Example: https://t.me/SomComunitats"
    ),
    "ce_mastodon_url_help": _(
        "Link to the Energy Community's social network profile. Example: https://mastodon.social/@SomComunitats"
    ),
    "ce_bluesky_url_help": _(
        "Link to the Energy Community's social network profile. Example: https://bsky.app/profile/somcomunitats.coop"
    ),
}
_COMMUNITY_DATA__STATIC_TEXTS.update(_COMMUNITY_DATA__HELPS_TEXTS)
# OPTIONS
_COMMUNITY_KNOWN_COORDINATOR_OPTIONS = [
    {"id": "yes", "name": _("Yes")},
    {"id": "not_yet", "name": _("No yet")},
]
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
        return request.render("energy_communities_crm.community_data_page", values)

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

        energy_services = self._get_energy_action_tag_ids()
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
                    lead_meta = related_lead.get_metadata_line(field_name)
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
    def _get_translation(self, source, lang="en", mods="energy_communities_crm"):
        if "lang" in request.env.context:
            lang = request.env.context["lang"]
        return get_translation(source, lang, mods)

    def _get_localized_options(self, original_options):
        localized_options = []
        for option in original_options:
            localized_options.append(
                {
                    "id": option["id"],
                    "name": self._get_translation(option["name"]),
                }
            )
        return localized_options

    def _get_community_data_submit_response(self, values):
        values = self._fill_values(values, True, False)
        return request.render("energy_communities_crm.community_data_page", values)

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

    def _get_coordinators(self):
        result = (
            request.env["res.company"]
            .sudo()
            .search(
                [
                    ("hierarchy_level", "=", "coordinator"),
                    ("name", "not ilike", "%[ON-HOLD]%"),
                    ("name", "not ilike", "%[TO-DELETE]%"),
                ]
            )
            .mapped(lambda r: {"id": r.id, "name": r.name})
        )
        return result

    def _get_energy_actions(self):
        return (
            request.env["energy.action"]
            .sudo()
            .search([])
            .mapped(
                lambda r: {
                    "id": r.xml_id.replace("energy_communities.", ""),
                    "name": r.name,
                }
            )
        )

    def _get_energy_action_tag_ids(self):
        return (
            request.env["energy.action"]
            .sudo()
            .search([])
            .mapped(lambda r: r.xml_id.replace("energy_communities.", ""))
        )

    def _get_legal_forms(self):
        legal_forms = []
        for legal_form_id, legal_form_name in _LEGAL_FORM_VALUES_WEBSITE:
            legal_forms.append(
                {
                    "id": legal_form_id,
                    "name": self._get_translation(
                        legal_form_name, lang="en", mods="energy_communities"
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
            for field_key in _COMMUNITY_DATA__STATIC_TEXTS.keys():
                lead_values[field_key] = self._get_translation(
                    _COMMUNITY_DATA__STATIC_TEXTS[field_key]
                )
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
        # date format
        for date_field_key in _COMMUNITY_DATA__DATE_FIELDS.keys():
            if date_field_key in values.keys():
                values[date_field_key] = self._format_date(values[date_field_key])
        # form labels
        # form keys
        for field_key in _COMMUNITY_DATA__FIELDS.keys():
            values[field_key + "_label"] = self._get_translation(
                _COMMUNITY_DATA__FIELDS[field_key]
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
        values["energy_service_options"] = self._get_energy_actions()
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
        # community_known_coordinator selection
        values["community_known_coordinator_options"] = self._get_localized_options(
            _COMMUNITY_KNOWN_COORDINATOR_OPTIONS
        )
        # coordinator_name selection
        values["coordinator_name_options"] = self._get_coordinators()
        if "coordinator_id" not in values.keys() or values["coordinator_id"] == "":
            values["coordinator_id"] = False
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

    def _validate_past_date(self, date_string):
        form_date = datetime.strptime(date_string, "%d/%m/%Y").strftime("%Y-%m-%d")
        now = datetime.today().strftime("%Y-%m-%d")
        return form_date <= now

    def _page_render_validation(self, values):
        values = self._lead_id_validation(values)
        if "error_msgs" in values.keys():
            return request.render("energy_communities_crm.community_data_page", values)
        return True

    def _check_url_validation(self, url):
        if not url:
            return True
        if not url.startswith("https://"):
            return False
        return True

    def _form_submit_validation(self, values):
        error = []
        error_msgs = []

        # lead_id validation
        values = self._lead_id_validation(values)
        if "error_msgs" in values.keys():
            return request.render("energy_communities_crm.community_data_page", values)

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
                if not self._valid_es_date_format(values[date_field_key]):
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
        if "ce_web_url" in values.keys():
            if not self._check_url_validation(values["ce_web_url"]):
                error.append("ce_web_url")
                error_msgs.append(
                    _("{} field must begin with https://").format(
                        self._get_translation(_COMMUNITY_DATA__FIELDS["ce_web_url"])
                    )
                )
        if "ce_twitter_url" in values.keys():
            if not self._check_url_validation(values["ce_twitter_url"]):
                error.append("ce_twitter_url")
                error_msgs.append(
                    _("{} field must begin with https://").format(
                        self._get_translation(_COMMUNITY_DATA__FIELDS["ce_twitter_url"])
                    )
                )
        if "ce_telegram_url" in values.keys():
            if not self._check_url_validation(values["ce_telegram_url"]):
                error.append("ce_telegram_url")
                error_msgs.append(
                    _("{} field must begin with https://").format(
                        self._get_translation(
                            _COMMUNITY_DATA__FIELDS["ce_telegram_url"]
                        )
                    )
                )
        if "ce_instagram_url" in values.keys():
            if not self._check_url_validation(values["ce_instagram_url"]):
                error.append("ce_instagram_url")
                error_msgs.append(
                    _("{} field must begin with https://").format(
                        self._get_translation(
                            _COMMUNITY_DATA__FIELDS["ce_instagram_url"]
                        )
                    )
                )
        if "ce_facebook_url" in values.keys():
            if not self._check_url_validation(values["ce_facebook_url"]):
                error.append("ce_facebook_url")
                error_msgs.append(
                    _("{} field must begin with https://").format(
                        self._get_translation(
                            _COMMUNITY_DATA__FIELDS["ce_facebook_url"]
                        )
                    )
                )
        if "ce_mastodon_url" in values.keys():
            if not self._check_url_validation(values["ce_mastodon_url"]):
                error.append("ce_mastodon_url")
                error_msgs.append(
                    _("{} field must begin with https://").format(
                        self._get_translation(
                            _COMMUNITY_DATA__FIELDS["ce_mastodon_url"]
                        )
                    )
                )
        if "ce_bluesky_url" in values.keys():
            if not self._check_url_validation(values["ce_bluesky_url"]):
                error.append("ce_bluesky_url")
                error_msgs.append(
                    _("{} field must begin with https://").format(
                        self._get_translation(_COMMUNITY_DATA__FIELDS["ce_bluesky_url"])
                    )
                )

        if error_msgs:
            values["error"] = error
            values["error_msgs"] = error_msgs
            values = self._fill_values(values, False, True)
            return request.render("energy_communities_crm.community_data_page", values)
        return True

    def _valid_es_date_format(self, date_value):
        regex = re.compile(
            r"(((0[1-9])|([12][0-9])|(3[01]))\/((0[0-9])|(1[012]))\/((20[012]\d|19\d\d)|(1\d|2[0123])))"
        )
        match = regex.match(str(date_value))
        return bool(match)

    #
    # DATA PROCESSING
    #
    def _format_date(self, date_value):
        if not self._valid_es_date_format(date_value):
            # Use try because date_value might not contain a dated format text
            try:
                date_value = datetime.strptime(date_value, "%Y-%m-%d").strftime(
                    "%d/%m/%Y"
                )
            except Exception as e:
                pass
        return date_value

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
                    "datas": base64.encodebytes(value.read()),
                    "public": True,
                }
            )
        )
