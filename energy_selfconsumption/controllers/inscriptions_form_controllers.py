from odoo import _, http
from odoo.http import request
from datetime import datetime
import re
import base64

from odoo.addons.energy_communities.controllers.website_form_controllers import WebsiteFormController

class WebsiteInscriptionsFormController(WebsiteFormController):

    @http.route(
        ["/page/inscription-data", "/inscription-data"],
        type="http",
        auth="public",
        website=True,
    )
    def display_inscription_data_page(self, **kwargs):
        values = kwargs
        values["model_name"] = "energy_selfconsumption.selfconsumption"
        return self.display_data_page(values, self.get_form_submit(values), "id")

    @http.route(
        ["/inscription-data/submit"],
        type="http",
        auth="public",
        website=True,
    )
    def inscription_data_submit(self, **kwargs):
        values = kwargs
        values["model_name"] = "energy_selfconsumption.selfconsumption"
        return self.data_submit("id", kwargs)

    @http.route('/inscription-data/privacy_policy_file/<int:record_id>', type='http',
                auth='public', csrf=False)
    def download_privacy_policy_file(self, record_id, **kwargs):
        record = request.env['energy_selfconsumption.selfconsumption'].sudo().browse(record_id)
        if not record or not record.conf_policy_privacy_import_file:
            return request.not_found()

        file_content = base64.b64decode(record.conf_policy_privacy_import_file)
        file_name = record.conf_policy_privacy_fname

        return request.make_response(
            file_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'attachment; filename=%s;' % file_name),
                ('Content-Length', len(file_content)),
            ]
        )

    def get_model_name(self):
        return "energy_project.project"

    def data_validation_custom(self, model, values):
        if model.state != "inscription":
            return {
                "error_msgs": [
                    _(
                        "You cannot display the form if the project is not in inscription status."
                    )
                ],
                "global_error": True,
            }
        if not model.conf_policy_privacy_import_file:
            return {
                "error_msgs": [
                    _(
                        "You need to add the privacy policy file to display the form."
                    )
                ],
                "global_error": True,
            }
        return super().data_validation_custom(model, values)

    def form_submit_validation(self, values):
        partner = request.env["res.partner"].sudo().search([
            ("vat", "=", values["inscription_partner_id_vat"])]
        )
        if not partner:
            return {
                "error_msgs": [
                    _(
                        "Partner is not exist."
                    )
                ],
                "global_error": True,
            }
        inscription = request.env["energy_selfconsumption.inscription_selfconsumption"].sudo().search(
            [
                ("project_id", "=", int(values["model_id"])),
                ("partner_id", "=", partner.id)
            ]
        )
        if inscription:
            return {
                "error_msgs": [
                    _(
                        "You are already enrolled in this self-consumption project."
                    )
                ],
                "global_error": True,
            }
        if values["supplypoint_owner_id_email"] != values["supplypoint_owner_id_email_confirm"]:
            return {
                "error_msgs": [
                    _(
                        "The email is not the same."
                    )
                ],
                "global_error": True,
            }
        if not values["inscription_project_privacy"]:
            return {
                "error_msgs": [
                    _(
                        "Have to accept politic privacy."
                    )
                ],
                "global_error": True,
            }
        participation = request.env["energy_project.participation"].sudo().search([
            (
            "quantity", "=", float(values["inscriptionselfconsumption_participation"]))]
        )
        if not participation:
            return {
                "error_msgs": [
                    _(
                        "Participation no exit."
                    )
                ],
                "global_error": True,
            }
        if values["supplypoint_owner_id_same"] == "no":
            date_pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")
            if not date_pattern.match(values["supplypoint_owner_id_birthdate_date"]):
                return {
                    "error_msgs": [
                        _(
                            "Error format date."
                        )
                    ],
                    "global_error": True,
                }
            lang = request.env["res.lang"].sudo().search([
                '|',
                '|',
                ("name", "=", values["supplypoint_owner_id_lang"]),
                ("code", "=", values["supplypoint_owner_id_lang"]),
                ("iso_code", "=", values["supplypoint_owner_id_lang"])
            ])
            if not lang:
                return {
                    "error_msgs": [
                        _(
                            "Language not found."
                        )
                    ],
                    "global_error": True,
                }
        return values

    def get_data_main_fields(self):
        return {
            "company_name": _("Company Name"),
            "project_name": _("Energy Project Name"),
            "project_conf_used_in_selfconsumption": False,
            "project_conf_vulnerability_situation": False,
            "project_conf_bank_details": False,
            "project_header_description": _("Header description on website form"),
            "inscription_partner_id_vat": _("CIF/NIF of the partner"),
            "supplypoint_cups": _("CUPS"),
            "supplypoint_street": _("Address"),
            "supplypoint_city": _("City"),
            "supplypoint_zip": _("Zip"),
            "supplypoint_contracted_power": _("Maximum contracted power"),
            "supplypoint_cadastral_reference": _("Cadastral reference del inmueble"),
            "supplypoint_used_in_selfconsumption": _("Do you currently have self-consumption?"),
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
            "supplypoint_owner_id_vulnerability_situation": _("Are you in a vulnerable situation?"),
            "project_privacy_policy_file": _("Privacy policy"),
            "project_privacy_policy_name": _("Privacy policy file name"),
            "inscription_project_privacy": _("I accept privacy policy"),
            "inscriptionselfconsumption_annual_electricity_use": _("Annual electricity use?"),
            "inscriptionselfconsumption_participation": _("What participation would you like?"),
            "inscription_acc_number": _("IBAN"),
            "inscriptionselfconsumption_accept": _("I accept and authorize being able to issue payments to this bank account as part of participation in this shared self-consumption project of my energy community")
        }

    def get_extra_data_main_fields(self, model, model_values):
        model_values["company_name"] = model.company_id.name
        model_values["project_name"] = model.name
        model_values["model_id"] = model.id
        model_values["project_model_key"] = "model_id"
        model_values["project_header_description"] = model.conf_header_description
        model_values["project_conf_used_in_selfconsumption"] = model.conf_used_in_selfconsumption
        model_values["project_conf_vulnerability_situation"] = model.conf_vulnerability_situation
        model_values["project_conf_bank_details"] = model.conf_bank_details
        model_values["project_conf_policy_privacy_import_file_url"] = "{base_url}/inscription-data/privacy_policy_file/{record_id}".format(
            base_url=request.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url"),
            record_id=model.id,
        )
        model_values["project_conf_policy_privacy_fname"] = model.conf_policy_privacy_fname
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
        return request.env.ref(
            "energy_selfconsumption.inscription_data_page"
        ).id

    def get_form_submit_url(self, values):
        return "{base_url}/inscription-data/submit".format(
            base_url=request.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url")
        )

    def get_translate_field_label(self, data_fields, values, field_key):
        return request.env["ir.translation"]._get_source(
                    name="addons/energy_selfconsumption/controllers/inscriptions_form_controllers.py",
                    types="code",
                    lang=request.env.context["lang"],
                    source=self.get_data_main_fields()[field_key],
                )

    def get_fill_values_custom(self, values):
        values["supplypoint_used_in_selfconsumption_options"] = [
            {
                "id": "yes",
                "name": _("Yes"),
            },
            {
                "id": "no",
                "name": _("No"),
            }
        ]

        values["supplypoint_owner_id_same_options"] = [
            {
                "id": "yes",
                "name": _("Yes"),
            },
            {
                "id": "no",
                "name": _("No"),
            }
        ]

        values["supplypoint_owner_id_gender_options"] = [
            {
                "id": "male",
                "name": _("Male")
            },
            {
                "id": "female",
                "name": _("Female")
            },
        ]

        values["supplypoint_owner_id_vulnerability_situation_options"] = [
            {
                "id": "yes",
                "name": _("Yes"),
            },
            {
                "id": "no",
                "name": _("No"),
            }
        ]

        participations = request.env["energy_project.participation"].sudo().search([
            ("project_id", "=", int(values["model_id"]))]
        )
        participation_options = []
        for participation in participations:
            participation_options.append({
                "id": participation.quantity,
                "name": participation.name,
            })
        values[
            "inscriptionselfconsumption_participation_options"
        ] = participation_options

        return values

    def process_metadata(self, model, values):
        partner = request.env["res.partner"].sudo().search([
            ("vat", "=", values["inscription_partner_id_vat"])]
        )
        if model.conf_bank_details:
            bank_accounts = request.env["res.partner.bank"].sudo().search(
                [("acc_number","=",values["inscription_acc_number"])]
            )
            if not bank_accounts:
                bank_account = request.env["res.partner.bank"].sudo().create(
                    {
                        "acc_number": values["inscription_acc_number"],
                        "partner_id": partner.id,
                        "company_id": model.company_id.id,
                    }
                )
            else:
                bank_account = bank_accounts[0]
            mandates = request.env["account.banking.mandate"].sudo().search(
                [("partner_bank_id", "=", bank_account.id)]
            )
            if mandates:
                mandate = mandates[0]
            else:
                mandate = request.env["account.banking.mandate"].sudo().create(
                    {
                        "format": "sepa",
                        "type": "recurrent",
                        "state": "valid",
                        "signature_date": datetime.now().strftime("%Y-%m-%d"),
                        "partner_bank_id": bank_account.id,
                        "partner_id": partner.id,
                        "company_id": model.company_id.id,
                    }
                )
        else:
            mandates = request.env["account.banking.mandate"].sudo().search([
                ("partner_id", "=", partner.id)]
            )
            mandate = False
            if mandates:
                mandate = mandates[0].id
        participation = request.env["energy_project.participation"].sudo().search([
            ("quantity", "=", float(values["inscriptionselfconsumption_participation"]))]
        )
        request.env["energy_selfconsumption.inscription_selfconsumption"].sudo().create(
            {
                "project_id": model.id,
                "partner_id": partner.id,
                "effective_date": datetime.now().strftime("%Y-%m-%d"),
                "mandate_id": mandate.id,
                "participation" : participation[0].id,
                "annual_electricity_use": values[
                    "inscriptionselfconsumption_annual_electricity_use"
                ],
                "accept": True,
            }
        )
        if values["supplypoint_owner_id_same"] == "yes":
            owner_id = partner.id
            state_id = partner.state_id.id
            country_id = partner.country_id.id
        else:
            vulnerability_situation = "no"
            if model.conf_vulnerability_situation:
                vulnerability_situation = values["supplypoint_owner_id_vulnerability_situation"]
            lang = request.env["res.lang"].sudo().search([
                '|',
                '|',
                ("name", "=", values["supplypoint_owner_id_lang"]),
                ("code", "=", values["supplypoint_owner_id_lang"]),
                ("iso_code", "=", values["supplypoint_owner_id_lang"])
            ])
            birthdate_obj = datetime.strptime(values["supplypoint_owner_id_birthdate_date"], "%d/%m/%Y")
            formatted_birthdate = birthdate_obj.strftime("%Y-%m-%d")
            owner = request.env["res.partner"].sudo().search([
                ("vat", "=", values["supplypoint_owner_id_vat"]),
            ])
            if not owner:
                owner = request.env["res.partner"].sudo().create(
                    {
                        "name": values["supplypoint_owner_id_name"],
                        "lastname": values["supplypoint_owner_id_lastname"],
                        "gender": values["supplypoint_owner_id_gender"],
                        "vulnerability_situation": vulnerability_situation,
                        "birthdate_date": formatted_birthdate,
                        "phone": values["supplypoint_owner_id_phone"],
                        "lang": lang[0].code,
                        "email": values["supplypoint_owner_id_email"],
                        "vat": values["supplypoint_owner_id_vat"],
                        "type": "contact",
                        "company_id": model.company_id.id,
                        "company_type": "person",
                        "cooperative_membership_id": model.company_id.partner_id.id,
                        "country_id": model.company_id.partner_id.country_id.id,
                        "state_id": model.company_id.partner_id.state_id.id,
                        "street": values["supplypoint_street"],
                        "city": values["supplypoint_city"],
                        "zip": values["supplypoint_zip"],
                    }
                )
            owner_id = owner.id
            state_id = owner.state_id.id
            country_id = owner.country_id.id

        if float(values["supplypoint_contracted_power"]) <= 15:
            tariff = "2.0TD"
        elif float(values["supplypoint_contracted_power"]) <= 50:
            tariff = "3.0TD"
        else:
            tariff = "6.1TD"

        used_in_selfconsumption = "no"
        if model.conf_used_in_selfconsumption:
            used_in_selfconsumption = values["supplypoint_used_in_selfconsumption"]
        supply_point = request.env["energy_selfconsumption.supply_point"].sudo().search(
            [("code","=",values["supplypoint_cups"])]
        )
        if not supply_point:
            request.env["energy_selfconsumption.supply_point"].sudo().create(
                {
                    "code": values["supplypoint_cups"],
                    "name": values["inscription_partner_id_vat"],
                    "street": values["supplypoint_street"],
                    "city": values["supplypoint_city"],
                    "zip": values["supplypoint_zip"],
                    "state_id": state_id,
                    "country_id": country_id,
                    "owner_id": owner_id,
                    "partner_id": partner.id,
                    "contracted_power": float(values["supplypoint_contracted_power"]),
                    "cadastral_reference": values["supplypoint_cadastral_reference"],
                    "tariff": tariff,
                    "used_in_selfconsumption": used_in_selfconsumption,
                }
            )
