import base64
import logging
from csv import DictReader
from io import StringIO

import chardet
from markupsafe import Markup, escape

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from odoo.addons.energy_communities.config import (
    DISPLAY_DATE_FORMAT,
    PLATFORM_ADMIN,
)

from ..config import (
    CSV_FILE_EXTENSION,
    CSV_QUOTE_CHAR,
    DEFAULT_ENCODING,
    TARIFF_2_0TD,
)

# Constants for import wizard
EXPECTED_CSV_COLUMNS = 28
INSCRIPTION_IMPORT_DELIMITER = ";"
SPANISH_COUNTRY_CODE = "ES"
SPANISH_NIF_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
CUPS_ALPHABET = "TRWAGMYFPDXBNJZSQVHLCKE"
CUPS_DISTRIBUTOR_CODE = "1234"
CUPS_SUPPLY_NUMBER_LENGTH = 12
CUPS_CONTROL_MODULO = 529
CUPS_CONTROL_DIVISOR = 23
SAMPLE_PARTNER_REF_PREFIX = "sample-inscription-"
SAMPLE_VAT_BASE = 90000000
SAMPLE_COUNT_DEFAULT = 5
SAMPLE_COUNT_MAX = 50
SAMPLE_CONTRACTED_POWER = 3.0
HIDDEN_INSCRIPTION_FORM_FIELDS = (
    "conf_show_contracted_power",
    "conf_show_access_tariff",
    "conf_used_in_selfconsumption",
    "conf_vulnerability_situation",
    "conf_bank_details",
    "conf_cadastral_reference_readonly",
    "conf_show_annual_consumption",
    "conf_show_participation",
)

logger = logging.getLogger(__name__)


class SelfconsumptionImportWizard(models.TransientModel):
    """
    Self-consumption Import Wizard

    This wizard handles the import of self-consumption project data from CSV files,
    including:
    - Partner and supply point data import
    - Inscription creation and validation
    - Bank account and mandate management
    - Auto-generation of test data
    - Template and documentation downloads

    Features:
    - CSV file parsing with encoding detection
    - Comprehensive data validation
    - Error reporting and logging
    - Bulk data import processing
    - Test data generation utilities
    """

    _name = "energy_selfconsumption.selfconsumption_import.wizard"
    _description = "Service to import project selfconsumption"

    # File import fields
    import_file = fields.Binary(
        string="Import File (*.csv)",
        help="CSV file containing self-consumption project data",
    )
    fname = fields.Char(string="File Name", help="Name of the imported file")

    # CSV format configuration
    delimiter = fields.Char(
        default=INSCRIPTION_IMPORT_DELIMITER,
        required=True,
        string="File Delimiter",
        help="Delimiter character used in the CSV file",
    )
    quotechar = fields.Char(
        default=CSV_QUOTE_CHAR,
        required=True,
        string="File Quotechar",
        help="Quote character used in the CSV file",
    )
    encoding = fields.Char(
        default=DEFAULT_ENCODING,
        required=True,
        string="File Encoding",
        help="Character encoding format of the CSV file",
    )
    date_format = fields.Char(
        default=DISPLAY_DATE_FORMAT,
        required=True,
        string="Date Format",
        help="Date format used for effective dates in the CSV file",
    )

    # Configuration fields
    user_current_role = fields.Char(
        help="Current role of the user performing the import"
    )
    conf_bank_details = fields.Boolean(
        help="Configuration flag for bank details handling"
    )
    project_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption",
        string="Self-consumption project",
    )
    hidden_fields_alert = fields.Html(
        compute="_compute_hidden_fields_alert",
        help="Warning listing inscription form fields that are not requested",
    )
    sample_count = fields.Integer(
        string="Sample count",
        default=SAMPLE_COUNT_DEFAULT,
        help="How many numbered sample inscriptions to ensure on this project",
    )

    # Default value methods
    @api.model
    def default_get(self, fields_list):
        """
        Set default values for wizard fields

        Gets default values from user context and project configuration.

        Args:
            fields_list: List of field names to get defaults for

        Returns:
            dict: Default values
        """
        defaults = super().default_get(fields_list)

        # Set user role
        defaults["user_current_role"] = self.env.user.user_current_role

        # Get project configuration
        project_id = self.env.context.get("active_id")
        if project_id:
            project = self.env["energy_selfconsumption.selfconsumption"].browse(
                project_id
            )
            if project.exists():
                defaults["project_id"] = project.id
                defaults["conf_bank_details"] = project.conf_bank_details

        return defaults

    @api.depends("project_id")
    def _compute_hidden_fields_alert(self):
        """List form fields that this project does not request."""
        for wizard in self:
            project = wizard.project_id
            wizard.hidden_fields_alert = (
                wizard._hidden_fields_alert_html(project) if project else False
            )

    def _hidden_fields_alert_html(self, project):
        """Build the alert shown above the template download.

        Cadastral reference is included when it is not mandatory. Import still
        keeps that column, because the flag controls obligation, not visibility.
        """
        labels = self._hidden_form_field_labels(project)
        if not labels:
            return False
        items = Markup("").join(
            Markup("<li>{}</li>").format(escape(label)) for label in labels
        )
        return Markup("<p>{}</p><ul>{}</ul>").format(
            escape(
                _(
                    "ALERT: On the 'Inscription form configuration' tab of this "
                    "project, the fields listed below are set not to be shown on "
                    "the form (and therefore they are not requested). You do not "
                    "need to fill in the corresponding columns of the template, "
                    "because they will not be considered or imported. If you want "
                    "to import values in bulk for any of these fields, change the "
                    "form configuration so that they are shown (requested):"
                )
            ),
            items,
        )

    def _hidden_form_field_labels(self, project):
        """Return 'No <translated field name>' for every hidden form flag."""
        descriptions = project.fields_get(list(HIDDEN_INSCRIPTION_FORM_FIELDS))
        labels = []
        for field_name in HIDDEN_INSCRIPTION_FORM_FIELDS:
            if project[field_name]:
                continue
            label = descriptions[field_name]["string"]
            labels.append(_("No %s") % label)
        return labels

    @api.constrains("sample_count")
    def _check_sample_count(self):
        """Keep the sample batch small enough to identify by index."""
        for wizard in self:
            if wizard.sample_count and not 1 <= wizard.sample_count <= SAMPLE_COUNT_MAX:
                raise ValidationError(
                    _("Sample count must be between 1 and {maximum}.").format(
                        maximum=SAMPLE_COUNT_MAX
                    )
                )

    # Validation constraints
    @api.constrains("import_file", "fname")
    def _check_import_file_format(self):
        """
        Validate imported file format

        Raises:
            ValidationError: If file format is not CSV
        """
        for record in self:
            if record.fname:
                file_extension = record.fname.split(".")[-1].lower()
                if file_extension != CSV_FILE_EXTENSION:
                    raise ValidationError(
                        _(
                            "Only CSV format files are accepted. Current file: {filename}"
                        ).format(filename=record.fname)
                    )

    # Main import methods
    def import_file_button(self):
        """
        Import data from uploaded CSV file

        Main method that processes the CSV file and imports all data,
        handling errors and providing feedback through project messages.

        Returns:
            bool: True if import completed (with or without errors)
        """
        self.ensure_one()
        self.flush()

        if not self.import_file:
            raise ValidationError(_("Please select a file to import"))

        # Get project context
        project_id = self.env.context.get("active_id")
        if not project_id:
            raise ValidationError(_("No project context found"))

        project = self.env["energy_selfconsumption.selfconsumption"].browse(project_id)
        if not project.exists():
            raise ValidationError(_("Project not found"))

        # Parse CSV file
        try:
            file_data = base64.b64decode(self.import_file)
            parsing_data = self._parse_file(file_data)
        except Exception as e:
            raise ValidationError(
                _("Error parsing CSV file: {error}").format(error=str(e))
            )

        # Process each line
        error_messages = []
        success_count = 0

        for line_index, line_data in enumerate(parsing_data, start=1):
            try:
                # Parse line data
                parse_error, import_dict = self._get_line_dict(line_data)
                if parse_error:
                    error_messages.append(
                        _("Line {line}: Parse error - {error}").format(
                            line=line_index, error=import_dict
                        )
                    )
                    continue

                # Import line data
                import_error, error_message = self._import_line(import_dict, project)
                if import_error:
                    error_messages.append(
                        _("Line {line}: Import error - {error}").format(
                            line=line_index, error=error_message
                        )
                    )
                else:
                    success_count += 1

            except Exception as e:
                error_messages.append(
                    _("Line {line}: Unexpected error - {error}").format(
                        line=line_index, error=str(e)
                    )
                )

        # Post import summary
        self._post_import_summary(project, success_count, error_messages)

        return True

    def _post_import_summary(self, project, success_count, error_messages):
        """
        Post import summary message to project

        Args:
            project: Project record
            success_count: Number of successfully imported lines
            error_messages: List of error messages
        """
        if error_messages:
            error_list = (
                "<ul>" + "".join(f"<li>{msg}</li>" for msg in error_messages) + "</ul>"
            )
            project.message_post(
                subject=_("Import Results"),
                body=_(
                    "Import completed with {success} successful imports and {errors} errors:\n{error_list}"
                ).format(
                    success=success_count,
                    errors=len(error_messages),
                    error_list=error_list,
                ),
            )
        else:
            project.message_post(
                subject=_("Import Successful"),
                body=_(
                    "Import completed successfully. {count} records imported."
                ).format(count=success_count),
            )

    # Template and documentation methods
    def download_template_button(self):
        """
        Download CSV template for import

        Returns:
            dict: Action to download template file
        """
        self.ensure_one()
        template_attachment = self.env[
            "res.config.settings"
        ]._inscription_import_template_attachment()
        if not template_attachment:
            raise ValidationError(_("Template file not found"))
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{template_attachment.id}/?download=true",
            "target": "new",
        }

    # Data parsing and processing methods
    def _get_state_code(self, state_name):
        """
        Get state code from state name

        Args:
            state_name (str): Name of the state

        Returns:
            str: State code or False if not found
        """
        if not state_name:
            return False

        state = (
            self.env["res.country.state"]
            .sudo()
            .search([("name", "=", state_name)], limit=1)
        )

        return state.code if state else False

    def _get_line_dict(self, line_data):
        """
        Parse CSV line data into dictionary

        Converts a CSV line into a structured dictionary with all
        required fields for inscription creation.

        Args:
            line_data (dict): Raw CSV line data

        Returns:
            tuple: (error_flag, parsed_dict_or_error_message)
        """
        try:
            headers = list(line_data.keys())

            # Validate column count
            if len(headers) != EXPECTED_CSV_COLUMNS:
                return True, _(
                    "Expected {expected} columns, found {actual} columns"
                ).format(expected=EXPECTED_CSV_COLUMNS, actual=len(headers))

            # Determine if supply point owner is the same as inscription partner
            owner_same = self._determine_owner_same_flag(line_data, headers)

            # Parse and structure data
            parsed_data = {
                "inscription_partner_id_vat": line_data.get(headers[0], False),
                "effective_date": line_data.get(headers[1], False),
                "supplypoint_cups": line_data.get(headers[2], False),
                "supplypoint_contracted_power": self._blank_or_float(
                    line_data.get(headers[3])
                ),
                "tariff": (line_data.get(headers[4]) or "").strip() or False,
                "supplypoint_street": line_data.get(headers[5], False),
                "street2": line_data.get(headers[6], False),
                "supplypoint_city": line_data.get(headers[7], False),
                "state": self._get_state_code(line_data.get(headers[8], "")),
                "supplypoint_zip": line_data.get(headers[9], False),
                "country": line_data.get(headers[10], False),
                "supplypoint_cadastral_reference": line_data.get(headers[11], False),
                "supplypoint_owner_id_vat": line_data.get(headers[12], False),
                "supplypoint_owner_id_name": line_data.get(headers[13], False),
                "supplypoint_owner_id_lastname": line_data.get(headers[14], False),
                "supplypoint_owner_id_gender": line_data.get(headers[15], False),
                "supplypoint_owner_id_birthdate_date": line_data.get(
                    headers[16], False
                ),
                "supplypoint_owner_id_phone": line_data.get(headers[17], False),
                "supplypoint_owner_id_lang": line_data.get(headers[18], False),
                "supplypoint_owner_id_email": line_data.get(headers[19], False),
                "supplypoint_owner_id_vulnerability_situation": line_data.get(
                    headers[20], False
                ),
                "inscription_project_privacy": line_data.get(headers[21], False),
                "inscription_acc_number": line_data.get(headers[22], False),
                "mandate_auth_date": line_data.get(headers[23], False),
                "date_format": self.date_format,
                "supplypoint_owner_id_same": owner_same,
                "supplypoint_used_in_selfconsumption": line_data.get(
                    headers[24], False
                ),
                "inscriptionselfconsumption_annual_electricity_use": self._blank_or_float(
                    line_data.get(headers[25])
                ),
                "inscriptionselfconsumption_participation": self._blank_or_float(
                    line_data.get(headers[26])
                ),
                "inscriptionselfconsumption_accept": line_data.get(headers[27], False),
            }

            return False, parsed_data

        except Exception as e:
            return True, str(e)

    def _determine_owner_same_flag(self, line_data, headers):
        """
        Determine if supply point owner is the same as inscription partner

        Args:
            line_data (dict): CSV line data
            headers (list): Column headers

        Returns:
            str: "yes" if same, "no" if different
        """
        # Check if owner fields are empty (indicating same as partner)
        owner_fields = [headers[12], headers[13], headers[14]]  # VAT, name, lastname

        for field in owner_fields:
            if line_data.get(field, False):
                return "no"

        return "yes"

    def _blank_or_float(self, value_str):
        """Keep an empty CSV cell empty so hidden fields can be ignored."""
        if value_str is None or str(value_str).strip() == "":
            return False
        return self._parse_float_value(value_str)

    def _parse_float_value(self, value_str):
        """
        Parse string value to float

        Args:
            value_str (str): String value to parse

        Returns:
            float: Parsed float value
        """
        if not value_str or value_str == "":
            return 0.0

        try:
            # Replace comma with dot for decimal separator
            clean_value = str(value_str).replace(",", ".")
            return float(clean_value)
        except (ValueError, TypeError):
            return 0.0

    def _parse_file(self, file_data):
        """
        Parse CSV file data

        Args:
            file_data (bytes): Binary file data

        Returns:
            list: List of dictionaries with CSV data

        Raises:
            UserError: If parsing fails
        """
        self.ensure_one()

        try:
            # Configure CSV options
            csv_options = {
                "delimiter": self.delimiter,
                "quotechar": self.quotechar,
            }

            # Decode file with proper encoding
            try:
                decoded_file = file_data.decode(self.encoding)
            except UnicodeDecodeError:
                # Auto-detect encoding if specified encoding fails
                detected_encoding = chardet.detect(file_data).get("encoding")
                if not detected_encoding:
                    raise UserError(_("No valid encoding detected for the file"))
                decoded_file = file_data.decode(detected_encoding)

            # Parse CSV
            csv_file = StringIO(decoded_file)
            csv_reader = DictReader(csv_file, **csv_options)

            return list(csv_reader)

        except Exception as e:
            logger.error(f"Error parsing CSV file: {e}")
            raise UserError(
                _("Error parsing the CSV file: {error}").format(error=str(e))
            )

    def _import_line(self, line_dict, project):
        """
        Import a single line of data

        Args:
            line_dict (dict): Parsed line data
            project: Project record

        Returns:
            tuple: (error_flag, error_message)
        """
        try:
            return (
                self.env["energy_selfconsumption.create_inscription_selfconsumption"]
                .sudo()
                .create_inscription(line_dict, project)
            )
        except Exception as e:
            logger.error(f"Error importing line: {e}")
            return True, str(e)

    # Sample inscription generation
    def action_generate_sample_inscriptions(self):
        """Create missing numbered sample inscriptions for this project.

        Indexes that already exist are left untouched, so running the action
        again does not duplicate test data.
        """
        self.ensure_one()
        self._check_platform_admin()
        project = self._import_project()
        if not 1 <= self.sample_count <= SAMPLE_COUNT_MAX:
            raise ValidationError(
                _("Sample count must be between 1 and {maximum}.").format(
                    maximum=SAMPLE_COUNT_MAX
                )
            )
        participation = self._sample_participation(project)
        created = 0
        existing = 0
        for index in range(1, self.sample_count + 1):
            if self._ensure_sample_inscription(project, participation, index):
                created += 1
            else:
                existing += 1
        return self._sample_notification(
            _(
                "Created {created} sample inscriptions. {existing} already existed."
            ).format(created=created, existing=existing)
        )

    def action_delete_sample_inscriptions(self):
        """Remove every sample inscription generated by this wizard."""
        self.ensure_one()
        self._check_platform_admin()
        deleted = self._delete_sample_inscriptions()
        return self._sample_notification(
            _("Deleted {count} sample inscriptions.").format(count=deleted)
        )

    def _check_platform_admin(self):
        """Restrict sample data actions to the active platform administrator role."""
        if self.env.user.get_current_role() != PLATFORM_ADMIN:
            raise AccessError(
                _("Only a platform administrator can manage sample inscriptions.")
            )

    def _import_project(self):
        """Return the self-consumption project that opened the wizard."""
        self.ensure_one()
        project = self.project_id
        if not project:
            project = (
                self.env["energy_selfconsumption.selfconsumption"]
                .browse(self.env.context.get("active_id"))
                .exists()
            )
        if not project:
            raise UserError(_("No project context found"))
        return project

    def _sample_participation(self, project):
        """Use the first participation of the project as the sample value."""
        participation = self.env["energy_selfconsumptions.participation"].search(
            [("project_id", "=", project.id)],
            order="quantity asc, id asc",
            limit=1,
        )
        if not participation:
            raise UserError(_("No participations found for this project"))
        return participation

    def _sample_partner_ref(self, index):
        """Stable reference used to find a sample partner again."""
        return f"{SAMPLE_PARTNER_REF_PREFIX}{index:04d}"

    def _sample_partner_name(self, index):
        """Stable name that shows the sample index."""
        return f"Sample Inscription {index:04d}"

    def _sample_vat(self, index):
        """Build a valid Spanish VAT that stays the same for this index."""
        number = f"{SAMPLE_VAT_BASE + index:08d}"
        letter = SPANISH_NIF_LETTERS[int(number) % 23]
        return f"{SPANISH_COUNTRY_CODE}{number}{letter}"

    def _sample_cups(self, index):
        """Build a valid CUPS that stays the same for this index."""
        supply_number = str(index).zfill(CUPS_SUPPLY_NUMBER_LENGTH)
        numeric_part = f"{CUPS_DISTRIBUTOR_CODE}{supply_number}"
        remainder = int(numeric_part) % CUPS_CONTROL_MODULO
        control = (
            CUPS_ALPHABET[remainder // CUPS_CONTROL_DIVISOR]
            + CUPS_ALPHABET[remainder % CUPS_CONTROL_DIVISOR]
        )
        return f"{SPANISH_COUNTRY_CODE}{numeric_part}{control}"

    def _ensure_sample_inscription(self, project, participation, index):
        """Create the sample records for one index when they are missing.

        Returns True when a new inscription was created.
        """
        partner = self._ensure_sample_partner(project, index)
        supply_point = self._ensure_sample_supply_point(project, partner, index)
        inscription = (
            self.env["energy_selfconsumption.inscription_selfconsumption"]
            .sudo()
            .search(
                [
                    ("selfconsumption_project_id", "=", project.id),
                    ("partner_id", "=", partner.id),
                    ("supply_point_id", "=", supply_point.id),
                ],
                limit=1,
            )
        )
        if inscription:
            return False
        self.env["energy_selfconsumption.inscription_selfconsumption"].with_company(
            project.company_id
        ).sudo().create(
            {
                "project_id": project.project_id.id,
                "selfconsumption_project_id": project.id,
                "partner_id": partner.id,
                "supply_point_id": supply_point.id,
                "participation_id": participation.id,
                "participation_assigned_quantity": participation.quantity,
                "participation_real_quantity": participation.quantity,
                "annual_electricity_use": 0.0,
                "effective_date": fields.Date.context_today(self),
                "accept": True,
                "member": True,
            }
        )
        return True

    def _ensure_sample_partner(self, project, index):
        """Return the sample partner for this index, creating it once."""
        ref = self._sample_partner_ref(index)
        partner = self.env["res.partner"].sudo().search([("ref", "=", ref)], limit=1)
        if partner:
            return partner
        vat = self._sample_vat(index)
        taken = self.env["res.partner"].sudo().search([("vat", "=", vat)], limit=1)
        if taken:
            raise UserError(
                _(
                    "VAT {vat} already belongs to {name}, so sample index "
                    "{index} cannot be created."
                ).format(vat=vat, name=taken.display_name, index=index)
            )
        return (
            self.env["res.partner"]
            .with_company(project.company_id)
            .sudo()
            .create(
                {
                    "name": self._sample_partner_name(index),
                    "ref": ref,
                    "vat": vat,
                    "company_id": project.company_id.id,
                    "street": project.street,
                    "city": project.city,
                    "zip": project.zip,
                    "state_id": project.state_id.id,
                    "country_id": project.country_id.id,
                    "company_type": "person",
                }
            )
        )

    def _ensure_sample_supply_point(self, project, partner, index):
        """Return the sample supply point for this index, creating it once."""
        code = self._sample_cups(index)
        supply_point = (
            self.env["energy_selfconsumption.supply_point"]
            .sudo()
            .search(
                [("code", "=", code), ("company_id", "=", project.company_id.id)],
                limit=1,
            )
        )
        if supply_point:
            if supply_point.partner_id != partner:
                raise UserError(
                    _(
                        "CUPS {cups} already belongs to another partner, so "
                        "sample index {index} cannot be created."
                    ).format(cups=code, index=index)
                )
            return supply_point
        return (
            self.env["energy_selfconsumption.supply_point"]
            .with_company(project.company_id)
            .sudo()
            .create(
                {
                    "code": code,
                    "partner_id": partner.id,
                    "owner_id": partner.id,
                    "street": project.street,
                    "city": project.city,
                    "zip": project.zip,
                    "state_id": project.state_id.id,
                    "country_id": project.country_id.id,
                    "company_id": project.company_id.id,
                    "contracted_power": SAMPLE_CONTRACTED_POWER,
                    "tariff": TARIFF_2_0TD,
                }
            )
        )

    def _sample_partners(self):
        """All partners created by the sample inscription action."""
        return (
            self.env["res.partner"]
            .sudo()
            .search([("ref", "=like", f"{SAMPLE_PARTNER_REF_PREFIX}%")])
        )

    def _delete_sample_inscriptions(self):
        """Delete sample partners together with their supply points and inscriptions."""
        partners = self._sample_partners()
        if not partners:
            return 0
        inscriptions = (
            self.env["energy_selfconsumption.inscription_selfconsumption"]
            .sudo()
            .search([("partner_id", "in", partners.ids)])
        )
        deleted = len(inscriptions)
        parent_inscriptions = inscriptions.mapped("inscription_id")
        supply_points = (
            self.env["energy_selfconsumption.supply_point"]
            .sudo()
            .search(
                [
                    "|",
                    ("partner_id", "in", partners.ids),
                    ("owner_id", "in", partners.ids),
                ]
            )
        )
        inscriptions.unlink()
        if parent_inscriptions:
            parent_inscriptions.exists().unlink()
        supply_points.exists().unlink()
        partners.exists().unlink()
        return deleted

    def _sample_notification(self, message):
        """Show the result without closing the import wizard."""
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Sample inscriptions"),
                "message": message,
                "type": "success",
                "sticky": False,
            },
        }

    # Utility methods
    def get_wizard_summary(self):
        """
        Get summary information about the wizard state

        Returns:
            dict: Summary information
        """
        self.ensure_one()

        return {
            "has_file": bool(self.import_file),
            "file_name": self.fname,
            "encoding": self.encoding,
            "delimiter": self.delimiter,
            "date_format": self.date_format,
            "user_role": self.user_current_role,
            "bank_details_config": self.conf_bank_details,
        }
