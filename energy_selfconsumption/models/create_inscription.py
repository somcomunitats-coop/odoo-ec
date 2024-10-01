from datetime import datetime

from stdnum.es import iban

from odoo import _, api, models


class CreateInscription(models.AbstractModel):
    _name = "energy_selfconsumption.create_inscription_selfconsumption"
    _description = "Service to create inscriptions for a self-consumption"

    def _determine_tariff(self, contracted_power, values):
        """Determina la tarifa en función de la potencia contratada."""
        return values.get("tariff") or (
            "2.0TD"
            if contracted_power <= 15
            else ("3.0TD" if contracted_power <= 300 else "6.1TD")
        )

    def _create_supply_point(
        self,
        values,
        project,
        partner,
        owner,
        tariff,
        used_in_selfconsumption,
        create_bank,
    ):
        """Crea el punto de suministro si no existe ya."""
        supply_point = (
            self.env["energy_selfconsumption.supply_point"]
            .sudo()
            .search([("code", "=", values["supplypoint_cups"])])
        )
        # if supply_point:
        #    return False, _("The supply point {code} already exists").format(code=supply_point.code)
        if not supply_point:
            try:
                supply_point = (
                    self.env["energy_selfconsumption.supply_point"]
                    .sudo()
                    .create(
                        {
                            "supply_point_id": supply_point.id,
                            "name": values["supplypoint_owner_id_name"],
                            "owner_id": owner.id,
                            "contracted_power": float(
                                values.get("supplypoint_contracted_power", 0)
                            ),
                            "tariff": tariff,
                            "used_in_selfconsumption": used_in_selfconsumption,
                            "project_id": project.id,
                            "company_id": project.company_id.id,
                            "active": True,
                            "street": values["supplypoint_street"],
                            "city": values["supplypoint_city"],
                            "zip": values["supplypoint_zip"],
                        }
                    )
                )

            except Exception as e:
                return True, _(str(e))

        participation = self._get_participation(values, project)
        if not participation:
            return True, _("No participation found for this project.")
        mandate = (
            self._create_bank_mandate(values, partner, project) if create_bank else None
        )
        effective_date = self._get_effective_date(values)
        annual_electricity_use = values.get(
            "inscriptionselfconsumption_annual_electricity_use", False
        )

        self._create_inscription_record(
            values,
            project,
            partner,
            effective_date,
            mandate,
            participation,
            annual_electricity_use,
            supply_point,
        )

        return False, _("You have successfully registered.")

    def create_inscription(
        self,
        values,
        project,
        create_bank=True,
        supplypoint_owner_id_same=True,
        conf_vulnerability_situation=False,
        conf_used_in_selfconsumption=False,
    ):
        """Crea una inscripción para auto-consumo en un proyecto específico."""
        partner = self._get_partner(values["inscription_partner_id_vat"])
        if not partner:
            return True, _("Partner with VAT:<b>{vat}</b> was not found.").format(
                vat=values["inscription_partner_id_vat"]
            )

        if not self._is_cooperator(partner, project):
            return True, _("Partner with VAT:<b>{vat}</b> is not a cooperator.").format(
                vat=values["inscription_partner_id_vat"]
            )

        values.setdefault("date_format", "%Y-%m-%d")

        if self._is_partner_already_registered(project, partner):
            return True, _(
                "Partner with VAT {vat} is already registered in project {code}"
            ).format(vat=partner.vat, code=project.code)

        owner = self._get_owner(
            values,
            project,
            partner,
            supplypoint_owner_id_same,
            conf_vulnerability_situation,
        )
        if not owner:
            return True, _("Owner could not be created or found.")

        contracted_power = float(values.get("supplypoint_contracted_power", 0))
        tariff = self._determine_tariff(contracted_power, values)

        used_in_selfconsumption = (
            "yes"
            if conf_used_in_selfconsumption
            and values.get("supplypoint_used_in_selfconsumption") == "yes"
            else "no"
        )

        return self._create_supply_point(
            values,
            project,
            partner,
            owner,
            tariff,
            used_in_selfconsumption,
            create_bank,
        )

    def _get_partner(self, vat):
        """Busca un partner basado en el VAT proporcionado."""
        return (
            self.env["res.partner"]
            .sudo()
            .search(
                [
                    "|",
                    ("vat", "=", vat),
                    ("vat", "=ilike", vat),
                ],
                limit=1,
            )
        )

    def _is_cooperator(self, partner, project):
        """Verifica si el partner es un cooperativista."""
        return bool(
            self.env["cooperative.membership"]
            .sudo()
            .search(
                [
                    ("company_id", "=", project.company_id.id),
                    ("partner_id", "=", partner.id),
                    ("cooperator", "=", True),
                ]
            )
        )

    def _create_bank_mandate(self, values, partner, project):
        """Crea un mandato bancario."""
        iban_number = values.get("inscription_acc_number")
        if not iban_number:
            raise ValueError(_("The IBAN field cannot be empty."))

        try:
            iban.validate(iban_number)
        except Exception as e:
            raise ValueError(_("Invalid IBAN: {error}").format(error=e))

        bank_account = (
            self.env["res.partner.bank"]
            .sudo()
            .search(
                [
                    ("acc_number", "=", iban_number),
                    ("partner_id", "=", partner.id),
                    ("company_id", "=", project.company_id.id),
                ]
            )
        )

        if not bank_account:
            bank_account = (
                self.env["res.partner.bank"]
                .sudo()
                .create(
                    {
                        "acc_number": iban_number,
                        "partner_id": partner.id,
                        "company_id": project.company_id.id,
                    }
                )
            )

        mandate_auth_date = self._get_mandate_auth_date(values)
        return (
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

    def _get_mandate_auth_date(self, values):
        """Obtiene la fecha de autorización del mandato."""
        date_format = values.get("date_format", "%Y-%m-%d")
        mandate_auth_date = values.get(
            "mandate_auth_date", datetime.now().strftime(date_format)
        )
        return datetime.strptime(mandate_auth_date, date_format).date()

    def _is_partner_already_registered(self, project, partner):
        """Verifica si el partner ya está inscrito en el proyecto."""
        return project.inscription_ids.filtered_domain(
            [("partner_id", "=", partner.id)]
        )

    def _get_participation(self, values, project):
        """Busca la participación en el proyecto."""
        domain = [("project_id", "=", project.id)]
        if "inscriptionselfconsumption_participation" in values:
            domain.append(
                (
                    "quantity",
                    "=",
                    float(values["inscriptionselfconsumption_participation"]),
                )
            )
        return self.env["energy_project.participation"].sudo().search(domain, limit=1)

    def _get_effective_date(self, values):
        """Obtiene la fecha efectiva."""
        date_format = values.get("date_format", "%Y-%m-%d")
        effective_date = values.get(
            "effective_date", datetime.now().strftime(date_format)
        )
        return datetime.strptime(effective_date, date_format).date()

    def _create_inscription_record(
        self,
        values,
        project,
        partner,
        effective_date,
        mandate,
        participation,
        annual_electricity_use,
        supply_point,
    ):
        """Crea el registro de inscripción."""
        self.env["energy_selfconsumption.inscription_selfconsumption"].sudo().create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "effective_date": effective_date,
                "mandate_id": mandate.id if mandate else False,
                "participation": participation.id,
                "annual_electricity_use": annual_electricity_use,
                "accept": True,
                "member": True,
                "supply_point_id": supply_point.id,
            }
        )

    def _get_owner(
        self,
        values,
        project,
        partner,
        supplypoint_owner_id_same,
        conf_vulnerability_situation,
    ):
        """Obtiene o crea el propietario del suministro."""
        if supplypoint_owner_id_same:
            return partner

        country = self._get_country(values, project)
        state = self._get_state(values, country)

        vulnerability_situation = (
            values.get("supplypoint_owner_id_vulnerability_situation", "no")
            if conf_vulnerability_situation
            else "no"
        )
        lang = self._get_language(values)

        formatted_birthdate = self._get_formatted_birthdate(values)
        owner = self._get_existing_contact_owner(values)

        if not owner:
            return self._create_new_owner(
                values,
                project,
                country,
                state,
                lang,
                vulnerability_situation,
                formatted_birthdate,
            )

        return self._update_owner_address(project, owner, values, country, state)

    def _get_country(self, values, project):
        """Obtiene el país basado en el proyecto o en los valores."""
        return (
            self.env["res.country"]
            .sudo()
            .search(
                [
                    (
                        "code",
                        "=",
                        values.get(
                            "country", project.company_id.partner_id.country_id.code
                        ),
                    )
                ]
            )
        )

    def _get_state(self, values, country):
        """Obtiene el estado basado en los valores y el país."""
        return (
            self.env["res.country.state"]
            .sudo()
            .search(
                [("code", "=", values.get("state")), ("country_id", "=", country.id)]
            )
        )

    def _get_language(self, values):
        """Obtiene el idioma basado en los valores."""
        lang_code = values.get("supplypoint_owner_id_lang")
        return (
            self.env["res.lang"].sudo().search([("iso_code", "=", lang_code)])
            if lang_code
            else None
        )

    def _get_formatted_birthdate(self, values):
        """Obtiene la fecha de nacimiento formateada."""
        if "supplypoint_owner_id_birthdate_date" in values:
            birthdate_obj = datetime.strptime(
                values["supplypoint_owner_id_birthdate_date"], "%d/%m/%Y"
            )
            return birthdate_obj.strftime("%Y-%m-%d")
        return None

    def _get_existing_contact_owner(self, values):
        """Busca un propietario existente basado en el VAT."""
        return (
            self.env["res.partner"]
            .sudo()
            .search(
                [
                    ("vat", "=", values["supplypoint_owner_id_vat"]),
                    ("type", "=", "contact"),
                ]
            )
        )

    def _get_existing_owner_self_consumption_owner(self, values):
        """Busca un propietario existente basado en el VAT."""
        return (
            self.env["res.partner"]
            .sudo()
            .search(
                [
                    ("vat", "=", values["supplypoint_owner_id_vat"]),
                    ("type", "=", "owner_self-consumption"),
                ]
            )
        )

    def _create_new_owner(
        self,
        values,
        project,
        country,
        state,
        lang,
        vulnerability_situation,
        formatted_birthdate,
    ):
        """Crea un nuevo propietario."""
        return (
            self.env["res.partner"]
            .sudo()
            .create(
                {
                    "name": values["supplypoint_owner_id_name"],
                    "lastname": values["supplypoint_owner_id_lastname"],
                    "gender": values.get("supplypoint_owner_id_gender"),
                    "vulnerability_situation": vulnerability_situation,
                    "birthdate_date": formatted_birthdate,
                    "phone": values.get("supplypoint_owner_id_phone"),
                    "lang": lang.code if lang else lang,
                    "email": values.get("supplypoint_owner_id_email"),
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

    def _update_owner_address(self, project, owner, values, country, state):
        """Actualiza la dirección de un propietario existente."""
        exists = self._get_existing_owner_self_consumption_owner(values)
        if exists:
            exists.sudo().write(
                {
                    "name": values["supplypoint_owner_id_name"],
                    "lastname": values["supplypoint_owner_id_lastname"],
                    "gender": values.get("supplypoint_owner_id_gender"),
                    "vulnerability_situation": values.get(
                        "supplypoint_owner_id_vulnerability_situation", "no"
                    ),
                    "birthdate_date": self._get_formatted_birthdate(values),
                    "phone": values.get("supplypoint_owner_id_phone"),
                    "lang": self._get_language(values).code
                    if self._get_language(values)
                    else None,
                    "email": values.get("supplypoint_owner_id_email"),
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
            return exists

        return (
            self.env["res.partner"]
            .sudo()
            .create(
                {
                    "name": values["supplypoint_owner_id_name"],
                    "lastname": values["supplypoint_owner_id_lastname"],
                    "gender": values.get("supplypoint_owner_id_gender"),
                    "vulnerability_situation": values.get(
                        "supplypoint_owner_id_vulnerability_situation", "no"
                    ),
                    "birthdate_date": self._get_formatted_birthdate(values),
                    "phone": values.get("supplypoint_owner_id_phone"),
                    "lang": self._get_language(values).code
                    if self._get_language(values)
                    else None,
                    "email": values.get("supplypoint_owner_id_email"),
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
