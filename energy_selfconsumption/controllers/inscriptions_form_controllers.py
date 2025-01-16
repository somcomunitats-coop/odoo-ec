import re

from odoo import _, http
from odoo.http import request

from odoo.addons.energy_communities.controllers.website_form_controllers import (
    WebsiteFormController,
)
from odoo.addons.energy_communities.utils import get_translation


class WebsiteInscriptionsFormController(WebsiteFormController):
    @http.route(
        ["/page/inscription-data", "/inscription-data"],
        type="http",
        auth="public",
        website=True,
    )
    def display_inscription_data_page(self, **kwargs):
        return self.display_data_page(kwargs, self.get_form_submit(kwargs), "id")

    @http.route(
        ["/inscription-data/submit"],
        type="http",
        auth="public",
        website=True,
    )
    def inscription_data_submit(self, **kwargs):
        return self.data_submit("id", kwargs)

    def get_model_name(self):
        return "energy_selfconsumption.selfconsumption"

    # Validation on view of from
    def data_validation_custom(self, model, values):
        if model.conf_state == "inactive":
            return {
                "error_msgs": [
                    _(
                        "The form is not open. For more information write to your Energy Community {email}".format(
                            email=model.company_id.email
                        )
                    )
                ],
                "global_error": True,
            }
        return super().data_validation_custom(model, values)

    # Validation on submit form
    def form_submit_validation(self, values):
        if values.get("supplypoint_owner_id_same", "yes") == "no":
            if values.get("inscription_project_privacy", "off") != "on":
                return {
                    "error_msgs": [_("Have to accept politic privacy.")],
                    "global_error": True,
                }
        project = (
            request.env["energy_selfconsumption.selfconsumption"]
            .sudo()
            .browse(int(values["model_id"]))
        )
        partner = (
            request.env["res.partner"]
            .sudo()
            .search([("vat", "=", values["inscription_partner_id_vat"]),
                     ("parent_id", "=", False), 
                     ("company_ids", "in", (project.company_id.id))])
        )
        if not partner:
            return {
                "error_msgs": [_("Partner does not exist.")],
                "global_error": True,
            }
        partner = partner.get_partner_with_type()
        cooperator = (
            request.env["cooperative.membership"]
            .sudo()
            .search(
                [
                    ("company_id", "=", project.company_id.id),
                    ("partner_id", "=", partner.id),
                    ("cooperator", "=", True),
                    ("member", "=", True),
                ]
            )
        )
        if not cooperator:
            return {
                "error_msgs": [_("Partner is not cooperator.")],
                "global_error": True,
            }
        inscription = (
            request.env["energy_selfconsumption.inscription_selfconsumption"]
            .sudo()
            .search(
                [
                    ("project_id", "=", int(values["model_id"])),
                    ("partner_id", "=", partner.id),
                ]
            )
        )
        if inscription:
            return {
                "error_msgs": [
                    _("You are already enrolled in this self-consumption project.")
                ],
                "global_error": True,
            }
        if (
            values["supplypoint_owner_id_email"]
            != values["supplypoint_owner_id_email_confirm"]
        ):
            return {
                "error_msgs": [_("The email is not the same.")],
                "global_error": True,
            }
        participation = (
            request.env["energy_project.participation"]
            .sudo()
            .search(
                [
                    (
                        "quantity",
                        "=",
                        float(values["inscriptionselfconsumption_participation"]),
                    )
                ]
            )
        )
        if not participation:
            return {
                "error_msgs": [_("Participation does not exist.")],
                "global_error": True,
            }
        if values["supplypoint_owner_id_same"] == "no":
            date_pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")
            if not date_pattern.match(values["supplypoint_owner_id_birthdate_date"]):
                return {
                    "error_msgs": [_("Error format date.")],
                    "global_error": True,
                }
            lang = (
                request.env["res.lang"]
                .sudo()
                .search(
                    [
                        "|",
                        "|",
                        ("name", "=", values["supplypoint_owner_id_lang"]),
                        ("code", "=", values["supplypoint_owner_id_lang"]),
                        ("iso_code", "=", values["supplypoint_owner_id_lang"]),
                    ]
                )
            )
            if not lang:
                return {
                    "error_msgs": [_("Language not found.")],
                    "global_error": True,
                }
        return values

    # All fields of form
    def get_data_main_fields(self):
        return {
            "company_name": _("Company Name"),
            "project_name": _("Energy Project Name"),
            "project_conf_used_in_selfconsumption": False,
            "project_conf_vulnerability_situation": False,
            "project_conf_bank_details": False,
            "project_header_description": _("Header description on website form"),
            "inscription_partner_id_vat": _("VAT of the partner"),
            "supplypoint_cups": _("CUPS"),
            "supplypoint_street": _("Address"),
            "supplypoint_city": _("City"),
            "supplypoint_zip": _("Zip"),
            "supplypoint_contracted_power": _("Maximum contracted power"),
            "supplypoint_cadastral_reference": _("Cadastral reference of the property"),
            "supplypoint_used_in_selfconsumption": _(
                "Do you currently have self-consumption?"
            ),
            "supplypoint_owner_id_same": _("Is the owner the same partner?"),
            "supplypoint_owner_id_name": _("Name"),
            "supplypoint_owner_id_lastname": _("Lastname"),
            "supplypoint_owner_id_gender": _("Gender"),
            "supplypoint_owner_id_birthdate_date": _("Birthdate"),
            "supplypoint_owner_id_phone": _("Phone"),
            "supplypoint_owner_id_lang": _("Lang"),
            "supplypoint_owner_id_vat": _("CIF/NIF"),
            "supplypoint_owner_id_email": _("E-mail"),
            "supplypoint_owner_id_email_confirm": _("Confirm E-mail"),
            "supplypoint_owner_id_vulnerability_situation": _(
                "Are you in a vulnerable situation?"
            ),
            "project_conf_policy_privacy_text": _("Privacy policy file text"),
            "inscription_project_privacy": _("I accept privacy policy"),
            "inscriptionselfconsumption_annual_electricity_use": _(
                "Annual electricity use?"
            ),
            "inscriptionselfconsumption_participation": _(
                "What participation would you like?"
            ),
            "inscription_acc_number": _("IBAN"),
            "inscriptionselfconsumption_accept": _(
                "I accept and authorize being able to issue payments to this bank account as part of participation in this shared self-consumption project of my energy community"
            ),
        }

    def get_extra_data_main_fields(self, model, model_values):
        model_values["company_name"] = model.company_id.name
        model_values["project_name"] = model.name
        model_values["model_id"] = model.id
        model_values["project_model_key"] = "model_id"
        model_values["project_header_description"] = model.conf_header_description
        model_values[
            "project_conf_used_in_selfconsumption"
        ] = model.conf_used_in_selfconsumption
        model_values[
            "project_conf_vulnerability_situation"
        ] = model.conf_vulnerability_situation
        model_values["project_conf_bank_details"] = model.conf_bank_details
        model_values[
            "project_conf_policy_privacy_text"
        ] = model.company_id.data_policy_approval_text
        return model_values

    def get_data_custom_submit(self, kwargs):
        values = kwargs
        return values

    def get_data_page_url(self, values):
        return "{base_url}/inscription-data?model_id={model_id}".format(
            base_url=request.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url"),
            model_id=values["model_id"],
        )

    def get_form_submit(self, values):
        return request.env.ref("energy_selfconsumption.inscription_data_page").id

    def get_form_submit_url(self, values):
        return "{base_url}/inscription-data/submit".format(
            base_url=request.env["ir.config_parameter"].sudo().get_param("web.base.url")
        )

    def get_translate_field_label(self, source):
        mods = "energy_communities_crm"
        lang = "en"
        if "lang" in request.env.context:
            lang = request.env.context["lang"][:-3]
        return get_translation(self.get_data_main_fields()[source], lang, mods)

    # Filling in extra values
    def get_fill_values_custom(self, values):
        values["supplypoint_used_in_selfconsumption_options"] = [
            {
                "id": "yes",
                "name": _("Yes"),
            },
            {
                "id": "no",
                "name": _("No"),
            },
        ]

        values["supplypoint_owner_id_same_options"] = [
            {
                "id": "yes",
                "name": _("Yes"),
            },
            {
                "id": "no",
                "name": _("No"),
            },
        ]

        values["supplypoint_owner_id_gender_options"] = [
            {"id": "male", "name": _("Male")},
            {"id": "female", "name": _("Female")},
            {"id": "other", "name": _("Other")},
            {"id": "not_binary", "name": _("Not binary")},
            {"id": "not_share", "name": _("I prefer to not share it")},
        ]

        values["supplypoint_owner_id_vulnerability_situation_options"] = [
            {
                "id": "yes",
                "name": _("Yes"),
            },
            {
                "id": "no",
                "name": _("No"),
            },
        ]

        participations = (
            request.env["energy_project.participation"]
            .sudo()
            .search([("project_id", "=", int(values["model_id"]))])
        )
        participation_options = []
        for participation in participations:
            participation_options.append(
                {
                    "id": participation.quantity,
                    "name": participation.name,
                }
            )
        values[
            "inscriptionselfconsumption_participation_options"
        ] = participation_options

        langs = request.env["res.lang"].sudo().search([])
        lang_options = []
        for lang in langs:
            lang_options.append(
                {
                    "id": lang.iso_code,
                    "name": lang.name,
                }
            )
        values["supplypoint_owner_id_lang_options"] = lang_options

        values["supplypoint_cups_title"] = _(
            "CUPS is the Unified Code of the Point of Supply. "
            "You can find it on electricity bills."
        )
        values["supplypoint_cadastral_reference_title"] = _(
            "Information necessary for the formalization of the distribution agreement."
            "You can find it at cadastro.es"
        )
        values["project_conf_used_in_selfconsumption_title"] = _(
            "There is already an individual photovoltaic self-consumption or "
            "collective at this supply point?"
        )
        values["project_conf_vulnerability_situation_title"] = _(
            "You have a recognized situation of vulnerability due to energy poverty or "
            "other type of social support need?"
        )
        values["inscriptionselfconsumption_annual_electricity_use_title"] = _(
            "You can find the annual electricity use on the electricity bill"
            "(Total annual consumption). Put it in kWh/year"
        )
        values["inscriptionselfconsumption_participation_title"] = _(
            "How much power of the collective PV installation you would like to "
            "purchase."
        )
        return values

    # Algorithm of the form
    def process_metadata(self, model, values):
        if model.conf_bank_details:
            if values["inscriptionselfconsumption_accept"] != "on":
                return {
                    "error_msgs": [
                        _(
                            "Have to accept and authorize being able to issue payments to this bank account as part of participation in this shared self-consumption project of my energy community."
                        )
                    ],
                    "global_error": True,
                }

        error, message = (
            request.env["energy_selfconsumption.create_inscription_selfconsumption"]
            .sudo()
            .create_inscription(values, model)
        )
        if error:
            return {
                "error_msgs": [message],
                "global_error": True,
            }
        partner = (
            request.env["res.partner"]
            .sudo()
            .search([
                ("vat", "=", values["inscription_partner_id_vat"]),
                ("parent_id", "=", False),
                ("company_ids", "in", (model.company_id.id))
            ])
        )
        self.send_email(model, partner)
        return values

    def send_email(self, model, partner):
        email_values = {"email_to": partner.email}
        template = request.env.ref(
            "energy_selfconsumption.selfconsumption_insciption_form"
        ).with_context(email_values)
        ctx = {"partner_name": partner.name}
        model.with_context(ctx).message_post_with_template(
            template.id, email_layout_xmlid="mail.mail_notification_layout"
        )
