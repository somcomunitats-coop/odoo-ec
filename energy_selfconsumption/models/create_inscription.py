from datetime import datetime

from stdnum.es import iban

from odoo import _, models


class CreateInscription(models.AbstractModel):
    """
    Service to create inscriptions for self-consumption projects

    This abstract model provides methods to handle the creation of inscriptions
    for self-consumption energy projects, including:
    - Partner validation and verification
    - Supply point creation and management
    - Bank mandate creation
    - Participation assignment
    """

    _name = "energy_selfconsumption.create_inscription_selfconsumption"
    _description = "Service to create inscriptions for a self-consumption"

    # Constants for tariff determination
    TARIFF_2_0TD_LIMIT = 15  # kW
    TARIFF_3_0TD_LIMIT = 300  # kW
    DEFAULT_TARIFF_LOW = "2.0TD"
    DEFAULT_TARIFF_MEDIUM = "3.0TD"
    DEFAULT_TARIFF_HIGH = "6.1TD"

    def _determine_tariff(self, contracted_power, values):
        """
        Determine the appropriate tariff based on contracted power

        Args:
            contracted_power (float): Contracted power in kW
            values (dict): Form values that may contain tariff override

        Returns:
            str: Tariff code (2.0TD, 3.0TD, or 6.1TD)
        """
        # Return explicit tariff if provided
        if values.get("tariff"):
            return values["tariff"]

        # Determine tariff based on power thresholds
        if contracted_power <= self.TARIFF_2_0TD_LIMIT:
            return self.DEFAULT_TARIFF_LOW
        elif contracted_power <= self.TARIFF_3_0TD_LIMIT:
            return self.DEFAULT_TARIFF_MEDIUM
        else:
            return self.DEFAULT_TARIFF_HIGH

    def _build_supply_point_address(self, values):
        """
        Build complete address string for supply point

        Args:
            values (dict): Form values containing address information

        Returns:
            str: Complete address string
        """
        street = values["supplypoint_street"]
        if values.get("street2"):
            street += " " + values["street2"]
        return street

    def _prepare_supply_point_values(
        self, values, project, partner, owner, tariff, country, state
    ):
        """
        Prepare values dictionary for supply point creation/update

        Args:
            values (dict): Form values
            project: Self-consumption project record
            partner: Partner record
            owner: Owner partner record
            tariff (str): Tariff code
            country: Country record
            state: State record

        Returns:
            dict: Values for supply point creation/update
        """
        street = self._build_supply_point_address(values)
        contracted_power = float(
            str(values.get("supplypoint_contracted_power", "0")).replace(",", ".")
        )

        vals = {
            "owner_id": owner.id,
            "contracted_power": contracted_power,
            "tariff": tariff,
            "partner_id": partner.id,
            "company_id": project.company_id.id,
            "street": street,
            "city": values["supplypoint_city"],
            "country_id": country.id,
            "state_id": state.id,
            "zip": values["supplypoint_zip"],
            "cadastral_reference": values["supplypoint_cadastral_reference"],
        }

        # Add self-consumption usage if configured
        if project.conf_used_in_selfconsumption:
            usage_value = values.get("supplypoint_used_in_selfconsumption")
            if usage_value and usage_value != "":
                vals["used_in_selfconsumption"] = usage_value

        return vals

    def _create_new_supply_point(self, values, project, partner, owner, tariff):
        """
        Create a new supply point record

        Args:
            values (dict): Form values
            project: Self-consumption project record
            partner: Partner record
            owner: Owner partner record
            tariff (str): Tariff code

        Returns:
            tuple: (error_flag, supply_point_or_error_message)
        """
        try:
            country = self._get_country(values, project)
            state = self._get_state(values, project, country)

            vals = self._prepare_supply_point_values(
                values, project, partner, owner, tariff, country, state
            )
            vals["code"] = values["supplypoint_cups"]

            supply_point = (
                self.env["energy_selfconsumption.supply_point"].sudo().create(vals)
            )
            return False, supply_point

        except Exception as e:
            return True, _(str(e))

    def _update_existing_supply_point(
        self, supply_point, values, project, partner, owner, tariff
    ):
        """
        Update an existing supply point record

        Args:
            supply_point: Existing supply point record
            values (dict): Form values
            project: Self-consumption project record
            partner: Partner record
            owner: Owner partner record
            tariff (str): Tariff code

        Returns:
            tuple: (error_flag, supply_point_or_error_message)
        """
        try:
            country = self._get_country(values, project)
            state = self._get_state(values, project, country)

            vals = self._prepare_supply_point_values(
                values, project, partner, owner, tariff, country, state
            )
            vals["active"] = True

            supply_point.sudo().write(vals)
            return False, supply_point

        except Exception as e:
            return True, _(str(e))

    def _create_supply_point(self, values, project, partner, owner, tariff):
        """
        Create or update supply point based on CUPS code

        Args:
            values (dict): Form values
            project: Self-consumption project record
            partner: Partner record
            owner: Owner partner record
            tariff (str): Tariff code

        Returns:
            tuple: (error_flag, success_message_or_error)
        """
        # Get partner with proper type context
        partner = partner.sudo().get_partner_with_type()

        # Search for existing supply point
        supply_point = (
            self.env["energy_selfconsumption.supply_point"]
            .sudo()
            .search([("code", "=", values["supplypoint_cups"])])
        )

        # Create or update supply point
        if not supply_point:
            error, supply_point = self._create_new_supply_point(
                values, project, partner, owner, tariff
            )
        else:
            error, supply_point = self._update_existing_supply_point(
                supply_point, values, project, partner, owner, tariff
            )

        if error:
            return True, supply_point  # supply_point contains error message

        # Validate participation
        participation = self._get_participation(values, project)
        if not participation:
            return True, _("No participation found for this project.")

        # Create bank mandate
        error, mandate = self._create_bank_mandate(values, partner, project)
        if error:
            return True, mandate  # mandate contains error message

        # Get additional data
        effective_date = self._get_effective_date(values)
        annual_electricity_use = values.get(
            "inscriptionselfconsumption_annual_electricity_use", False
        )

        # Create inscription record
        self._create_inscription_record(
            project,
            partner,
            effective_date,
            mandate,
            participation,
            annual_electricity_use,
            supply_point,
        )

        return False, _("You have successfully registered.")

    def create_inscription(self, values, project):
        """
        Main method to create an inscription for self-consumption project

        Args:
            values (dict): Form values containing all inscription data
            project: Self-consumption project record

        Returns:
            tuple: (error_flag, message)
        """
        # Validate partner existence
        partner = self._get_partner(
            values["inscription_partner_id_vat"], project.company_id.id
        )
        if not partner:
            return True, _("Partner with VAT:<b>{vat}</b> was not found.").format(
                vat=values["inscription_partner_id_vat"]
            )

        # Validate cooperator status
        if not self._is_cooperator(partner, project):
            return True, _("Partner with VAT:<b>{vat}</b> is not a cooperator.").format(
                vat=values["inscription_partner_id_vat"]
            )

        # Set default date format if not provided
        values.setdefault("date_format", "%Y-%m-%d")

        # Check for duplicate registration
        if self._is_partner_already_registered(
            project, partner, values["supplypoint_cups"]
        ):
            return True, _(
                "Partner with VAT {vat} is already registered in project {code}"
            ).format(vat=partner.vat, code=project.code)

        # Get or create owner
        owner = self._get_owner(values, project, partner)
        if not owner:
            return True, _("Owner could not be created or found.")

        # Determine tariff based on contracted power
        contracted_power = float(
            str(values.get("supplypoint_contracted_power", "0")).replace(",", ".")
        )
        tariff = self._determine_tariff(contracted_power, values)

        # Create supply point and complete inscription
        return self._create_supply_point(values, project, partner, owner, tariff)

    def _get_partner(self, vat, company_id):
        """
        Search for a partner based on VAT number

        Args:
            vat (str): VAT number to search for
            company_id (int): Company ID for multi-company context

        Returns:
            res.partner: Partner record or False if not found
        """
        return (
            self.env["res.partner"]
            .sudo()
            .search(
                [
                    ("vat", "=", vat),
                    ("parent_id", "=", False),
                    ("company_ids", "in", (company_id)),
                ],
                limit=1,
            )
        )

    def _is_cooperator(self, partner, project):
        """
        Verify if partner is a cooperative member or authorized for energy actions

        Args:
            partner: Partner record to verify
            project: Project record for company context

        Returns:
            bool: True if partner is authorized, False otherwise
        """
        # Check if partner is authorized for energy actions without membership
        if partner.with_company(
            project.company_id.id
        ).no_member_autorized_in_energy_actions:
            return True

        # Check cooperative membership
        return bool(
            self.env["cooperative.membership"]
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

    def _create_bank_mandate(self, values, partner, project):
        if not project.conf_bank_details:
            return False, None
        """Creates a bank mandate."""
        iban_number = values.get("inscription_acc_number", False)
        if not iban_number:
            return True, _("The IBAN field cannot be empty.")

        try:
            iban.validate(iban_number)
        except Exception as e:
            return True, _("Invalid IBAN: {error}").format(error=e)

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
        mandate_obj = (
            self.env["account.banking.mandate"]
            .with_company(project.company_id)
            .sudo()
            .search(
                [
                    ("partner_bank_id", "=", bank_account.id),
                    ("partner_id", "=", partner.id),
                    ("company_id", "=", project.company_id.id),
                ],
                limit=1,
            )
        )
        if mandate_obj:
            return False, mandate_obj
        return False, (
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
        """Obtains the date of authorization of the mandate."""
        date_format = values.get("date_format", "%Y-%m-%d")
        mandate_auth_date = values.get(
            "mandate_auth_date", datetime.now().strftime(date_format)
        )
        return datetime.strptime(mandate_auth_date, date_format).date()

    def _is_partner_already_registered(self, project, partner, code):
        """Check if the partner is already enrolled in the project."""
        return project.inscription_ids.filtered_domain(
            [("partner_id", "=", partner.id), ("code", "=", code)]
        )

    def _get_participation(self, values, project):
        """Seeks participation in the project."""
        domain = [("project_id", "=", project.id)]
        if "inscriptionselfconsumption_participation" in values:
            domain.append(
                (
                    "quantity",
                    "=",
                    float(values["inscriptionselfconsumption_participation"]),
                )
            )
        return (
            self.env["energy_selfconsumptions.participation"]
            .sudo()
            .search(domain, limit=1)
        )

    def _get_effective_date(self, values):
        """Gets the effective date."""
        date_format = values.get("date_format", "%Y-%m-%d")
        effective_date = values.get(
            "effective_date", datetime.now().strftime(date_format)
        )
        return datetime.strptime(effective_date, date_format).date()

    def _create_inscription_record(
        self,
        project,
        partner,
        effective_date,
        mandate,
        participation,
        annual_electricity_use,
        supply_point,
    ):
        # partner = partner.sudo().get_partner_with_type()
        """Creates the registration record."""
        self.env["energy_selfconsumption.inscription_selfconsumption"].sudo().create(
            {
                "project_id": project.project_id.id,
                "selfconsumption_project_id": project.id,
                "partner_id": partner.id,
                "effective_date": effective_date,
                "mandate_id": mandate.id if mandate else False,
                "participation_id": participation.id,
                "participation_assigned_quantity": participation.quantity,
                "participation_real_quantity": participation.quantity,
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
    ):
        # Check if the owner is the same as the partner
        if values.get("inscription_partner_id_vat") == values.get(
            "supplypoint_owner_id_vat", False
        ):
            values["supplypoint_owner_id_same"] = "yes"

        """Obtains or creates the owner of the supply."""
        if values.get("supplypoint_owner_id_same", "no") == "yes":
            if project.conf_vulnerability_situation:
                if (
                    values.get("supplypoint_owner_id_vulnerability_situation", False)
                    and values.get(
                        "supplypoint_owner_id_vulnerability_situation", False
                    )
                    != ""
                ):
                    partner.sudo().write(
                        {
                            "vulnerability_situation": values.get(
                                "supplypoint_owner_id_vulnerability_situation", None
                            )
                        }
                    )
            return partner

        country = self._get_country(values, project)
        state = self._get_state(values, project, country)
        lang = self._get_language(values)
        formatted_birthdate = self._get_formatted_birthdate(values)
        owner = self._get_existing_contact_owner(values, project)

        if not owner:
            return self._create_new_owner(
                values,
                project,
                country,
                state,
                lang,
                formatted_birthdate,
            )

        return self._update_owner_address(project, owner, values, country, state)

    def _get_country(self, values, project):
        """Obtains the country based on the project or values."""
        if not values.get("country", False):
            return project.company_id.partner_id.country_id
        return (
            self.env["res.country"]
            .sudo()
            .search([("code", "=", values.get("country"))])
        )

    def _get_state(self, values, project, country):
        """Gets the state based on values and country."""
        if not values.get("state", False):
            return project.company_id.partner_id.state_id
        return (
            self.env["res.country.state"]
            .sudo()
            .search(
                [("code", "=", values.get("state")), ("country_id", "=", country.id)]
            )
        )

    def _get_language(self, values):
        """Gets the language based on values."""
        lang_code = values.get("supplypoint_owner_id_lang")
        return (
            self.env["res.lang"].sudo().search([("iso_code", "=", lang_code)])
            if lang_code
            else None
        )

    def _get_formatted_birthdate(self, values):
        """Gets the formatted date of birth."""
        if (
            "supplypoint_owner_id_birthdate_date" in values
            and values["supplypoint_owner_id_birthdate_date"] != ""
        ):
            birthdate_obj = datetime.strptime(
                values["supplypoint_owner_id_birthdate_date"], "%d/%m/%Y"
            )
            return birthdate_obj.strftime("%Y-%m-%d")
        return None

    def _get_existing_contact_owner(self, values, project):
        """Search for an existing VAT-based owner."""
        return (
            self.env["res.partner"]
            .sudo()
            .search(
                [
                    ("company_ids", "in", (project.company_id.id)),
                    ("vat", "=", values["supplypoint_owner_id_vat"]),
                    ("type", "=", "contact"),
                ],
                limit=1,
            )
        )

    def _get_existing_owner_self_consumption_owner(self, values, project):
        """Search for an existing VAT-based owner."""
        return (
            self.env["res.partner"]
            .sudo()
            .search(
                [
                    ("vat", "=", values["supplypoint_owner_id_vat"]),
                    ("type", "=", "owner_self-consumption"),
                    ("company_ids", "in", (project.company_id.id)),
                ],
                limit=1,
            )
        )

    def _create_new_owner(
        self,
        values,
        project,
        country,
        state,
        lang,
        formatted_birthdate,
    ):
        """Creates a new owner."""
        vals = {
            "firstname": values["supplypoint_owner_id_name"],
            "lastname": values["supplypoint_owner_id_lastname"],
            "gender": values.get("supplypoint_owner_id_gender"),
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
        if project.conf_vulnerability_situation:
            if (
                values.get("supplypoint_owner_id_vulnerability_situation", False)
                and values.get("supplypoint_owner_id_vulnerability_situation", False)
                != ""
            ):
                vals["vulnerability_situation"] = values.get(
                    "supplypoint_owner_id_vulnerability_situation", None
                )
        return self.env["res.partner"].sudo().create(vals)

    def _update_owner_address(self, project, owner, values, country, state):
        """Update the address of an existing owner."""
        exists = self._get_existing_owner_self_consumption_owner(values, project)
        if exists:
            vals = {
                "type": "owner_self-consumption",
                "company_id": project.company_id.id,
                "company_type": "person",
                "parent_id": owner.id,
                "country_id": country.id,
                "state_id": state.id,
            }
            if (
                values.get("supplypoint_owner_id_name", False)
                and values.get("supplypoint_owner_id_name", False) != ""
            ):
                vals["firstname"] = values["supplypoint_owner_id_name"]
            if (
                values.get("supplypoint_owner_id_lastname", False)
                and values.get("supplypoint_owner_id_lastname", False) != ""
            ):
                vals["lastname"] = values["supplypoint_owner_id_lastname"]
            if (
                values.get("supplypoint_owner_id_gender", False)
                and values.get("supplypoint_owner_id_gender", False) != ""
            ):
                vals["gender"] = values.get("supplypoint_owner_id_gender")
            if (
                values.get("supplypoint_owner_id_birthdate_date", False)
                and values.get("supplypoint_owner_id_birthdate_date", False) != ""
            ):
                vals["birthdate_date"] = self._get_formatted_birthdate(values)
            if (
                values.get("supplypoint_owner_id_phone", False)
                and values.get("supplypoint_owner_id_phone", False) != ""
            ):
                vals["phone"] = values.get("supplypoint_owner_id_phone")
            if (
                values.get("supplypoint_owner_id_lang", False)
                and values.get("supplypoint_owner_id_lang", False) != ""
            ):
                vals["lang"] = self._get_language(values).code
            if (
                values.get("supplypoint_owner_id_email", False)
                and values.get("supplypoint_owner_id_email", False) != ""
            ):
                vals["email"] = values.get("supplypoint_owner_id_email")
            if (
                values.get("supplypoint_owner_id_vat", False)
                and values.get("supplypoint_owner_id_vat", False) != ""
            ):
                vals["vat"] = values.get("supplypoint_owner_id_vat")
            if (
                values.get("supplypoint_street", False)
                and values.get("supplypoint_street", False) != ""
            ):
                vals["street"] = values.get("supplypoint_street")
            if (
                values.get("supplypoint_city", False)
                and values.get("supplypoint_city", False) != ""
            ):
                vals["city"] = values.get("supplypoint_city")
            if (
                values.get("supplypoint_zip", False)
                and values.get("supplypoint_zip", False) != ""
            ):
                vals["zip"] = values.get("supplypoint_zip")

            if project.conf_vulnerability_situation:
                if (
                    values.get("supplypoint_owner_id_vulnerability_situation", False)
                    and values.get(
                        "supplypoint_owner_id_vulnerability_situation", False
                    )
                    != ""
                ):
                    vals["vulnerability_situation"] = values.get(
                        "supplypoint_owner_id_vulnerability_situation", None
                    )
            exists.sudo().write(vals)
            return exists

        vals = {
            "firstname": values["supplypoint_owner_id_name"],
            "lastname": values["supplypoint_owner_id_lastname"],
            "gender": values.get("supplypoint_owner_id_gender"),
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
        if project.conf_vulnerability_situation:
            if (
                values.get("supplypoint_owner_id_vulnerability_situation", False)
                and values.get("supplypoint_owner_id_vulnerability_situation", False)
                != ""
            ):
                vals["vulnerability_situation"] = values.get(
                    "supplypoint_owner_id_vulnerability_situation", None
                )
        return self.env["res.partner"].sudo().create(vals)
