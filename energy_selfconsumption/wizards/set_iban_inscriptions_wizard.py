import logging

from stdnum.es import iban

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# Constants for IBAN wizard
IBAN_SPACE_CHAR = " "
DEFAULT_MANDATE_DATE_TODAY = True

logger = logging.getLogger(__name__)


class SetIbanInscriptionsWizard(models.TransientModel):
    """
    Set IBAN Inscriptions Wizard

    This wizard handles the configuration of IBAN and mandate information
    for inscriptions in a self-consumption project, including:
    - IBAN validation and formatting
    - Bank account creation and management
    - Mandate creation and assignment
    - Bulk processing of multiple inscriptions

    Features:
    - Spanish IBAN validation
    - Automatic bank account creation
    - Mandate management
    - Error handling and logging
    - Bulk operations support
    """

    _name = "energy_selfconsumption.set_iban_inscriptions_wizard"
    _description = "Set IBAN for inscriptions"

    # Line items for IBAN configuration
    set_iban_inscriptions_line_wizard_ids = fields.One2many(
        "energy_selfconsumption.set_iban_inscriptions_line_wizard",
        "set_iban_inscriptions_wizard_id",
        string="IBAN Configuration Lines",
        help="Lines for configuring IBAN and mandate information",
    )

    # Default value methods
    def get_default_inscriptions(self, default_fields):
        """
        Get default inscriptions from project context

        Args:
            default_fields: Dictionary of default field values

        Returns:
            dict: Updated default fields with inscription lines

        Raises:
            ValidationError: If no self-consumption project found
        """
        project_id = self.env.context.get("active_id")
        if not project_id:
            raise ValidationError(_("No self-consumption project selected"))

        selfconsumption = self.env["energy_selfconsumption.selfconsumption"].browse(
            project_id
        )
        if not selfconsumption.exists():
            raise ValidationError(_("Self-consumption project not found"))

        # Create lines for each inscription
        line_values = []
        for inscription in selfconsumption.inscription_ids:
            line_data = self._prepare_inscription_line_data(inscription)
            line_values.append((0, 0, line_data))

        default_fields["set_iban_inscriptions_line_wizard_ids"] = line_values
        return default_fields

    def _prepare_inscription_line_data(self, inscription):
        """
        Prepare line data for an inscription

        Args:
            inscription: Inscription record

        Returns:
            dict: Line data for wizard
        """
        # Get existing IBAN and mandate date
        existing_iban = ""
        existing_date = None

        if inscription.mandate_id and inscription.mandate_id.partner_bank_id:
            existing_iban = inscription.mandate_id.partner_bank_id.acc_number or ""
            existing_date = inscription.mandate_id.signature_date

        return {
            "inscription_id": inscription.id,
            "partner_id": inscription.partner_id.id,
            "iban": existing_iban,
            "date_mandate": existing_date,
        }

    @api.model
    def default_get(self, default_fields):
        """
        Set default values for wizard fields

        Args:
            default_fields: List of field names to get defaults for

        Returns:
            dict: Default values
        """
        defaults = super().default_get(default_fields)
        defaults = self.get_default_inscriptions(defaults)
        return defaults

    # Validation methods
    def _validate_wizard_data(self):
        """
        Validate wizard data before processing

        Raises:
            ValidationError: If validation fails
        """
        if not self.set_iban_inscriptions_line_wizard_ids:
            raise ValidationError(_("No inscriptions found to configure"))

    def _validate_iban_format(self, iban_number):
        """
        Validate IBAN format and checksum

        Args:
            iban_number: IBAN number to validate

        Raises:
            ValidationError: If IBAN is invalid
        """
        if not iban_number:
            return  # Empty IBAN is allowed

        try:
            iban.validate(iban_number)
        except Exception as e:
            raise ValidationError(
                _("Invalid IBAN '{iban}': {error}").format(
                    iban=iban_number, error=str(e)
                )
            )

    # Bank account and mandate methods
    def _get_or_create_bank_account(self, iban_number, partner, company):
        """
        Get existing bank account or create new one

        Args:
            iban_number: IBAN number
            partner: Partner record
            company: Company record

        Returns:
            res.partner.bank: Bank account record
        """
        # Search for existing bank account
        bank_account = (
            self.env["res.partner.bank"]
            .sudo()
            .search(
                [
                    ("acc_number", "=", iban_number),
                    ("partner_id", "=", partner.id),
                    ("company_id", "=", company.id),
                ],
                limit=1,
            )
        )

        if bank_account:
            return bank_account

        # Create new bank account
        return (
            self.env["res.partner.bank"]
            .sudo()
            .create(
                {
                    "acc_number": iban_number,
                    "partner_id": partner.id,
                    "company_id": company.id,
                }
            )
        )

    def _get_or_create_mandate(self, bank_account, partner, company, mandate_date):
        """
        Get existing mandate or create new one

        Args:
            bank_account: Bank account record
            partner: Partner record
            company: Company record
            mandate_date: Mandate signature date

        Returns:
            account.banking.mandate: Mandate record
        """
        # Search for existing mandate
        mandate = (
            self.env["account.banking.mandate"]
            .sudo()
            .search(
                [
                    ("partner_bank_id", "=", bank_account.id),
                    ("partner_id", "=", partner.id),
                    ("company_id", "=", company.id),
                ],
                limit=1,
            )
        )

        if mandate:
            # Update signature date if provided
            if mandate_date and mandate.signature_date != mandate_date:
                mandate.write({"signature_date": mandate_date})
            return mandate

        # Create new mandate
        return (
            self.env["account.banking.mandate"]
            .with_company(company.id)
            .sudo()
            .create(
                {
                    "partner_bank_id": bank_account.id,
                    "partner_id": partner.id,
                    "company_id": company.id,
                    "signature_date": mandate_date or fields.Date.today(),
                }
            )
        )

    def _process_inscription_line(self, line):
        """
        Process a single inscription line

        Args:
            line: Wizard line record

        Returns:
            tuple: (success, error_message)
        """
        try:
            # Skip if no IBAN provided
            if not line.iban:
                logger.warning(f"Empty IBAN for inscription {line.inscription_id.id}")
                return True, None

            # Clean and validate IBAN
            iban_number = line.iban.replace(IBAN_SPACE_CHAR, "")
            self._validate_iban_format(iban_number)

            # Set default mandate date if not provided
            mandate_date = line.date_mandate
            if not mandate_date:
                mandate_date = fields.Date.today()

            # Get partner and company
            partner = line.inscription_id.partner_id
            company = partner.company_id

            # Get or create bank account
            bank_account = self._get_or_create_bank_account(
                iban_number, partner, company
            )

            # Get or create mandate
            mandate = self._get_or_create_mandate(
                bank_account, partner, company, mandate_date
            )

            # Update inscription with mandate
            line.inscription_id.write({"mandate_id": mandate.id})

            return True, None

        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Error processing inscription {line.inscription_id.id}: {error_msg}"
            )
            return False, error_msg

    # Main action method
    def set_iban_inscriptions(self):
        """
        Set IBAN and mandate information for inscriptions

        Main method that processes all inscription lines and configures
        IBAN, bank accounts, and mandates.

        Returns:
            dict: Action to view inscriptions
        """
        self.ensure_one()

        # Validate wizard data
        self._validate_wizard_data()

        # Process each line
        success_count = 0
        error_messages = []

        for line in self.set_iban_inscriptions_line_wizard_ids:
            success, error_msg = self._process_inscription_line(line)

            if success:
                success_count += 1
            else:
                partner_name = line.inscription_id.partner_id.name
                error_messages.append(f"{partner_name}: {error_msg}")

        # Log results
        total_lines = len(self.set_iban_inscriptions_line_wizard_ids)
        logger.info(
            f"IBAN configuration completed: {success_count}/{total_lines} successful"
        )

        if error_messages:
            error_list = "\n".join(f"- {msg}" for msg in error_messages)
            raise ValidationError(
                _("Some IBAN configurations failed:\n{errors}").format(
                    errors=error_list
                )
            )

        # Return to inscriptions view
        project_id = self.env.context.get("active_id")
        if project_id:
            selfconsumption = self.env["energy_selfconsumption.selfconsumption"].browse(
                project_id
            )
            return selfconsumption.get_inscriptions_view()

        return {"type": "ir.actions.act_window_close"}

    # Utility methods
    def get_wizard_summary(self):
        """
        Get summary information about the wizard state

        Returns:
            dict: Summary information
        """
        self.ensure_one()

        total_lines = len(self.set_iban_inscriptions_line_wizard_ids)
        lines_with_iban = len(
            [line for line in self.set_iban_inscriptions_line_wizard_ids if line.iban]
        )

        return {
            "total_inscriptions": total_lines,
            "inscriptions_with_iban": lines_with_iban,
            "inscriptions_without_iban": total_lines - lines_with_iban,
        }

    def validate_all_ibans(self):
        """
        Validate all IBAN numbers without saving

        Returns:
            dict: Validation results
        """
        self.ensure_one()

        validation_results = []

        for line in self.set_iban_inscriptions_line_wizard_ids:
            if not line.iban:
                continue

            iban_number = line.iban.replace(IBAN_SPACE_CHAR, "")
            partner_name = line.inscription_id.partner_id.name

            try:
                self._validate_iban_format(iban_number)
                validation_results.append(
                    {
                        "partner_name": partner_name,
                        "iban": iban_number,
                        "valid": True,
                        "error": None,
                    }
                )
            except ValidationError as e:
                validation_results.append(
                    {
                        "partner_name": partner_name,
                        "iban": iban_number,
                        "valid": False,
                        "error": str(e),
                    }
                )

        return {
            "validation_results": validation_results,
            "total_validated": len(validation_results),
            "valid_count": len([r for r in validation_results if r["valid"]]),
            "invalid_count": len([r for r in validation_results if not r["valid"]]),
        }


class SetIbanInscriptionsLineWizard(models.TransientModel):
    """
    Set IBAN Inscriptions Line Wizard

    Individual line for configuring IBAN and mandate information
    for a specific inscription.
    """

    _name = "energy_selfconsumption.set_iban_inscriptions_line_wizard"
    _description = "IBAN configuration line for inscription"

    # Parent wizard relationship
    set_iban_inscriptions_wizard_id = fields.Many2one(
        "energy_selfconsumption.set_iban_inscriptions_wizard",
        string="IBAN Wizard",
        required=True,
        ondelete="cascade",
        help="Parent wizard for IBAN configuration",
    )

    # Inscription and partner information
    inscription_id = fields.Many2one(
        "energy_selfconsumption.inscription_selfconsumption",
        string="Inscription",
        required=True,
        help="Inscription to configure IBAN for",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        required=True,
        help="Partner associated with the inscription",
    )

    # IBAN and mandate fields
    iban = fields.Char(
        string="IBAN", help="International Bank Account Number for the partner"
    )
    date_mandate = fields.Date(
        string="Mandate Date", help="Date when the mandate was signed"
    )

    # Validation constraints
    @api.constrains("iban")
    def _check_iban_format(self):
        """
        Validate IBAN format when entered

        Raises:
            ValidationError: If IBAN format is invalid
        """
        for record in self:
            if record.iban:
                iban_number = record.iban.replace(IBAN_SPACE_CHAR, "")
                try:
                    iban.validate(iban_number)
                except Exception as e:
                    raise ValidationError(
                        _("Invalid IBAN for partner '{partner}': {error}").format(
                            partner=record.partner_id.name, error=str(e)
                        )
                    )

    # Utility methods
    def get_line_summary(self):
        """
        Get summary information for this line

        Returns:
            dict: Line summary information
        """
        self.ensure_one()

        return {
            "partner_name": self.partner_id.name,
            "has_iban": bool(self.iban),
            "has_mandate_date": bool(self.date_mandate),
            "inscription_state": self.inscription_id.state
            if hasattr(self.inscription_id, "state")
            else None,
        }
