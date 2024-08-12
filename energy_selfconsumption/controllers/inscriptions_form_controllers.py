from odoo import _, http
from odoo.http import request

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
        return self.display_data_page(values, self.get_form_submit_url(values), "id")

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

    def get_model_name(self):
        return "energy_project.project"

    def data_validation_custom(self, values):
        return super().data_validation_custom(values)

    def get_data_main_fields(self):
        return {
            "company_name": _("Company Name"),
            "project_name": _("Energy Project Name"),
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
        return model_values

    def get_data_page_url(self, values):
        return "{base_url}/inscription-data?model_id={model_id}".format(
            base_url=request.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url"),
            model_id=values["model_id"],
        )

    def get_form_submit_url(self, values):
        return request.env.ref(
            "energy_selfconsumption.inscription_data_page"
        ).id

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

        return values




