from odoo import models, _, api
from stdnum.es import iban
from datetime import datetime

class CreateInscription(models.AbstractModel):
    _name = "energy_selfconsumption.create_inscription_selfconsumption"
    _description = "Service to create inscriptions for a self-consumption"

    def create_inscription(
           self,
           values,
           project,
           create_bank=True,
           supplypoint_owner_id_same=True,
           conf_vulnerability_situation=False,
           conf_used_in_selfconsumption=False
        ):

        partner = self.env["res.partner"].sudo().search(
            [
                "|",
                ("vat", "=", values["inscription_partner_id_vat"]),
                ("vat", "=ilike", values["inscription_partner_id_vat"]),
            ],
            limit=1,
        )

        if not partner:
            return False, _("Partner with VAT:<b>{vat}</b> was not found.").format(
                vat=values["inscription_partner_id_vat"]
            )

        cooperator = (
            self.env["cooperative.membership"]
            .sudo()
            .search(
                [
                    ("company_id", '=', project.company_id.id),
                    ("partner_id", '=', partner.id),
                    ("cooperator", '=', True),
                ]
            )
        )

        if not cooperator:
            return False, _("Partner with VAT:<b>{vat}</b> not is cooperator.").format(
                vat=values["inscription_partner_id_vat"]
            )

        if "date_format" not in values:
            values["date_format"] = "%Y-%m-%d"

        mandate = False
        if create_bank:
            if not values["inscription_acc_number"]:
                return False, _("The IBAN field cannot be empty.")

            try:
                iban.validate(values["inscription_acc_number"])
            except Exception as e:
                error_message = _("Invalid IBAN: {error}").format(error=e)
                return False, error_message


            bank_account = (
                self.env["res.partner.bank"]
                .sudo()
                .search(
                    [
                        ("acc_number", "=", values["inscription_acc_number"]),
                        ("partner_id", "=", partner.id),
                        ("company_id", "=", project.company_id.id),
                    ]
                )
            )

            if not bank_account:
                bank_account = self.env["res.partner.bank"].sudo().create(
                    {
                        "acc_number": values["inscription_acc_number"],
                        "partner_id": partner.id,
                        "company_id": project.company_id.id,
                    }
                )

            mandate_auth_date = datetime.now().strftime(values["date_format"])
            if "mandate_auth_date" in values:
                mandate_auth_date = datetime.strptime(
                    values["mandate_auth_date"], values["date_format"]
                ).date()

            try:
                mandate = (
                    self.env["account.banking.mandate"]
                    .with_company(project.company_id)
                    .sudo()
                    .create(
                        {
                            "recurrent_sequence_type": "first",
                            "scheme": "CORE",
                            "format": "sepa",
                            "type": "recurrent",
                            "state": "valid",
                            "signature_date": mandate_auth_date,
                            "partner_bank_id": bank_account.id,
                            "partner_id": partner.id,
                            "company_id": project.company_id.id,
                        }
                    )
                )
            except Exception as e:
                return False, _("Could not create mandate for {vat}. {error}").format(
                    vat=partner.vat, error=e
                )

        if project.inscription_ids.filtered_domain(
                [("partner_id", "=", partner.id)]
        ):
            return False, _("Partner with VAT {vat} is on project {code}").format(
                vat=partner.vat, code=project.code
            )

        domain = [
            (
                "project_id",
                "=",
                project.id,
            )
        ]
        if "inscriptionselfconsumption_participation" in values:
            domain.append(
                (
                    "quantity",
                    "=",
                    float(values["inscriptionselfconsumption_participation"]),
                )
            )

        participation = (
            self.env["energy_project.participation"]
            .sudo()
            .search(
                domain, limit=1
            )
        )

        if not participation:
            return False, _("Dont exit participation for this project.")

        effective_date = datetime.now().strftime(values["date_format"])

        if "effective_date" in values:
            effective_date = datetime.strptime(
                values["effective_date"], values["date_format"]
            ).date()
        annual_electricity_use = False
        if "inscriptionselfconsumption_annual_electricity_use" in values:
            annual_electricity_use = values[
                "inscriptionselfconsumption_annual_electricity_use"
            ]

        self.env["energy_selfconsumption.inscription_selfconsumption"].sudo().create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "effective_date": effective_date,
                "mandate_id": mandate.id if mandate else mandate,
                "participation": participation.id,
                "annual_electricity_use": annual_electricity_use,
                "accept": True,
                "member": True,
                "code": values["supplypoint_cups"]
            }
        )

        state = partner.state_id
        country = partner.country_id
        owner = partner

        if not supplypoint_owner_id_same:
            country = project.company_id.partner_id.country_id
            if "country" in values:
                country = self.env["res.country"].sudo().search(
                    [("code", "=", values["country"])])
                if not country:
                    return False, _("Country code was not found: {country}").format(
                        country=values["country"]
                    )
            state = project.company_id.partner_id.state_id
            if "state" in values:
                state = self.env["res.country.state"].sudo().search(
                    [("code", "=", values["state"]), ("country_id", "=", country.id)]
                )
                if not state:
                    return False, _("State code was not found: {state}").format(
                        state=values["state"]
                    )

            vulnerability_situation = "no"
            if conf_vulnerability_situation:
                vulnerability_situation = values[
                    "supplypoint_owner_id_vulnerability_situation"
                ]

            lang = False
            if "supplypoint_owner_id_lang" in values:
                lang = (
                    self.env["res.lang"]
                    .sudo()
                    .search([("iso_code", "=", values["supplypoint_owner_id_lang"])])
                )

            formatted_birthdate = False
            if "supplypoint_owner_id_birthdate_date" in values:
                birthdate_obj = datetime.strptime(
                    values["supplypoint_owner_id_birthdate_date"], "%d/%m/%Y"
                )
                formatted_birthdate = birthdate_obj.strftime("%Y-%m-%d")

            owner = (
                self.env["res.partner"]
                .sudo()
                .search(
                    [
                        ("vat", "=", values["supplypoint_owner_id_vat"]),
                    ]
                )
            )
            gender = False
            if "supplypoint_owner_id_gender" in values:
                gender = values["supplypoint_owner_id_gender"]

            phone = False
            if "supplypoint_owner_id_phone" in values:
                phone = values["supplypoint_owner_id_phone"]

            email = False
            if "supplypoint_owner_id_email" in values:
                email = values["supplypoint_owner_id_email"] 

            if not owner:
                owner = (
                    self.env["res.partner"]
                    .sudo()
                    .create(
                        {
                            "name": values["supplypoint_owner_id_name"],
                            "lastname": values["supplypoint_owner_id_lastname"],
                            "gender": gender,
                            "vulnerability_situation": vulnerability_situation,
                            "birthdate_date": formatted_birthdate,
                            "phone": phone,
                            "lang": lang.code if lang else lang,
                            "email": email,
                            "vat": values["supplypoint_owner_id_vat"],
                            "type": "contact",
                            "company_id": project.company_id.id,
                            "company_type": "person",
                            "country_id": country.id,
                            "state_id": state.id,
                            "street": values["supplypoint_street"],
                            "city": values["supplypoint_city"],
                            "zip": values["supplypoint_zip"],
                        }
                    )
                )
            else:
                owner = (
                    self.env["res.partner"]
                    .sudo()
                    .create(
                        {
                            "name": values["supplypoint_owner_id_name"],
                            "lastname": values["supplypoint_owner_id_lastname"],
                            "gender": gender,
                            "vulnerability_situation": vulnerability_situation,
                            "birthdate_date": formatted_birthdate,
                            "phone": phone,
                            "lang": lang.code if lang else lang,
                            "email": email,
                            "vat": values["supplypoint_owner_id_vat"],
                            "type": "owner_self-consumption",
                            "company_id": project.company_id.id,
                            "company_type": "person",
                            "parent_id": owner.id,
                            "country_id": country.id,
                            "state_id": state.id,
                            "street": values["supplypoint_street"],
                            "city": values["supplypoint_city"],
                            "zip": values["supplypoint_zip"],
                        }
                    )
                )

        tariff = "6.1TD"
        if "supplypoint_contracted_power" in values:
            if float(values["supplypoint_contracted_power"]) <= 15:
                tariff = "2.0TD"
            elif float(values["supplypoint_contracted_power"]) <= 300:
                tariff = "3.0TD"
            else:
                tariff = "6.1TD"

        if "tariff" in values:
            tariff = values["tariff"]

        used_in_selfconsumption = "no"
        if conf_used_in_selfconsumption:
            if "supplypoint_used_in_selfconsumption" in values:
                used_in_selfconsumption = values["supplypoint_used_in_selfconsumption"]

        supply_point = (
            self.env["energy_selfconsumption.supply_point"]
            .sudo()
            .search([("code", "=", values["supplypoint_cups"])])
        )
        if not supply_point:
            street2 = False
            if "street2" in values:
                street2 = values["street2"] 
            try:
                self.env["energy_selfconsumption.supply_point"].sudo().create(
                    {
                        "code": values["supplypoint_cups"],
                        "name": values["inscription_partner_id_vat"],
                        "street": values["supplypoint_street"],
                        "street2": street2,
                        "city": values["supplypoint_city"],
                        "zip": values["supplypoint_zip"],
                        "state_id": state.id,
                        "country_id": country.id,
                        "owner_id": owner.id,
                        "partner_id": partner.id,
                        "contracted_power": float(values["supplypoint_contracted_power"]),
                        "cadastral_reference": values["supplypoint_cadastral_reference"],
                        "tariff": tariff,
                        "used_in_selfconsumption": used_in_selfconsumption,
                    }
                )
            except Exception as e:
                return False, _(e)
        else:
            return False, _("The supply point {code} is exist".format(
                code=supply_point.code
            ))

        return True, _("Ok")
