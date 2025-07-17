import base64
import csv
import logging
from io import StringIO

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.energy_communities.config import DISPLAY_DATE_FORMAT

from ..config import DEFAULT_ENCODING

# Constants for CSV export
CSV_EXPORT_DELIMITER = ";"
CSV_EXPORT_ENCODING = DEFAULT_ENCODING
DEFAULT_EXPORT_FILENAME = "export_inscriptions.csv"
PRIVACY_ACCEPTANCE_VALUE = "yes"
TERMS_ACCEPTANCE_VALUE = "yes"

# CSV column headers (in English for internal processing)
CSV_HEADERS = [
    "DNI Socio",
    "Fecha efectiva",
    "CUPS",
    "Potencia máxima contratada",
    "Tarifa de acceso",
    "Calle 1",
    "Calle 2",
    "Ciudad",
    "Provincia",
    "Código postal",
    "Código ISO del país",
    "Referencia Catastral",
    "DNI Titular",
    "Nombre Titular",
    "Apellidos Titular",
    "Género Titular",
    "Fecha nacimiento Titular",
    "Teléfono Titular",
    "Idioma Titular",
    "Email Titular",
    "Situación vulnerabilidad Titular",
    "Acepta política privacidad Titular",
    "IBAN",
    "Fecha autorización cargo bancario del mandato",
    "Usa auto-consumo",
    "Uso consumo eléctrico anual",
    "Participación",
    "Acepta Términos",
]

logger = logging.getLogger(__name__)


class ExportCsvInscriptionsWizard(models.TransientModel):
    """
    Export CSV Inscriptions Wizard

    This wizard handles the export of inscription data to CSV format,
    including:
    - Partner and supply point information
    - Mandate and banking details
    - Participation and consumption data
    - Owner information when different from partner

    Features:
    - Comprehensive data export
    - Proper CSV formatting
    - Error handling and validation
    - Configurable output format
    """

    _name = "export.csv.inscritions.wizard"
    _description = "Assistant to export CSV inscriptions"

    # Export result fields
    file_data = fields.Binary(
        string="CSV File",
        readonly=True,
        help="Generated CSV file with inscription data",
    )
    file_name = fields.Char(
        string="File Name", readonly=True, help="Name of the generated CSV file"
    )

    # Validation methods
    def _validate_export_context(self):
        """
        Validate export context and data availability

        Returns:
            selfconsumption: Self-consumption project record

        Raises:
            ValidationError: If validation fails
        """
        project_id = self.env.context.get("active_id")
        if not project_id:
            raise ValidationError(_("No self-consumption project selected for export"))

        selfconsumption = self.env["energy_selfconsumption.selfconsumption"].browse(
            project_id
        )
        if not selfconsumption.exists():
            raise ValidationError(_("Self-consumption project not found"))

        if not selfconsumption.inscription_ids:
            raise ValidationError(
                _("No inscriptions found in project '{project}'").format(
                    project=selfconsumption.name
                )
            )

        return selfconsumption

    # Data extraction methods
    def _get_safe_field_value(self, record, field_path, default=""):
        """
        Safely get field value from record with nested field support

        Args:
            record: Record to extract value from
            field_path: Dot-separated field path (e.g., 'supply_point_id.code')
            default: Default value if field is empty or record is False

        Returns:
            str: Field value or default
        """
        if not record:
            return default

        try:
            current_record = record
            for field_name in field_path.split("."):
                if not current_record:
                    return default
                current_record = getattr(current_record, field_name, None)

            return str(current_record) if current_record is not False else default
        except Exception:
            return default

    def _format_date_field(self, date_value):
        """
        Format date field for CSV export

        Args:
            date_value: Date value to format

        Returns:
            str: Formatted date string or empty string
        """
        if not date_value:
            return ""

        try:
            return date_value.strftime(DISPLAY_DATE_FORMAT)
        except Exception:
            return ""

    def _extract_inscription_row_data(self, inscription):
        """
        Extract all data for a single inscription row

        Args:
            inscription: Inscription record

        Returns:
            list: List of values for CSV row
        """
        supply_point = inscription.supply_point_id
        owner = inscription.owner_id
        mandate = inscription.mandate_id

        return [
            # Partner information
            self._get_safe_field_value(inscription.partner_id, "vat"),
            self._format_date_field(inscription.effective_date),
            # Supply point information
            self._get_safe_field_value(supply_point, "code"),
            self._get_safe_field_value(supply_point, "contracted_power"),
            self._get_safe_field_value(supply_point, "tariff"),
            self._get_safe_field_value(supply_point, "street"),
            "",  # Street 2 (not used)
            self._get_safe_field_value(supply_point, "city"),
            self._get_safe_field_value(supply_point, "state_id.name"),
            self._get_safe_field_value(supply_point, "zip"),
            self._get_safe_field_value(supply_point, "country_id.code"),
            self._get_safe_field_value(supply_point, "cadastral_reference"),
            # Owner information (when different from partner)
            self._get_safe_field_value(owner, "vat"),
            self._get_safe_field_value(owner, "name"),
            self._get_safe_field_value(owner, "lastname"),
            self._get_safe_field_value(owner, "gender"),
            self._format_date_field(
                getattr(owner, "birthdate_date", None) if owner else None
            ),
            self._get_safe_field_value(owner, "phone"),
            self._get_safe_field_value(owner, "lang"),
            self._get_safe_field_value(owner, "email"),
            self._get_safe_field_value(owner, "vulnerability_situation"),
            # Privacy and terms
            PRIVACY_ACCEPTANCE_VALUE,
            # Banking information
            self._get_safe_field_value(inscription, "acc_number"),
            self._format_date_field(
                getattr(mandate, "signature_date", None) if mandate else None
            ),
            # Self-consumption information
            self._get_safe_field_value(supply_point, "used_in_selfconsumption"),
            self._get_safe_field_value(inscription, "annual_electricity_use"),
            self._get_safe_field_value(inscription, "participation_quantity"),
            TERMS_ACCEPTANCE_VALUE,
        ]

    # CSV generation methods
    def _generate_csv_content(self, inscriptions):
        """
        Generate CSV content from inscriptions

        Args:
            inscriptions: Inscription recordset

        Returns:
            bytes: CSV content as bytes
        """
        output = StringIO()
        writer = csv.writer(output, delimiter=CSV_EXPORT_DELIMITER)

        # Write headers
        writer.writerow(CSV_HEADERS)

        # Write data rows
        for inscription in inscriptions:
            try:
                row_data = self._extract_inscription_row_data(inscription)
                writer.writerow(row_data)
            except Exception as e:
                logger.error(f"Error processing inscription {inscription.id}: {e}")
                # Continue with other inscriptions
                continue

        csv_content = output.getvalue()
        output.close()

        return csv_content.encode(CSV_EXPORT_ENCODING)

    # Main export method
    def exportar_csv(self):
        """
        Export inscriptions to CSV file

        Main method that validates data, generates CSV content,
        and prepares the file for download.

        Returns:
            dict: Action to display the wizard with generated file
        """
        self.ensure_one()

        # Validate context and get data
        selfconsumption = self._validate_export_context()
        inscriptions = selfconsumption.inscription_ids

        logger.info(f"Exporting {len(inscriptions)} inscriptions to CSV")

        try:
            # Generate CSV content
            csv_data = self._generate_csv_content(inscriptions)

            # Update wizard with file data
            self.write(
                {
                    "file_data": base64.b64encode(csv_data),
                    "file_name": _(DEFAULT_EXPORT_FILENAME),
                }
            )

            logger.info("CSV export completed successfully")

        except Exception as e:
            logger.error(f"Error generating CSV export: {e}")
            raise ValidationError(
                _("Error generating CSV file: {error}").format(error=str(e))
            )

        # Return action to show wizard with download link
        return {
            "type": "ir.actions.act_window",
            "res_model": "export.csv.inscritions.wizard",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
            "context": {"dialog_size": "medium"},
        }

    # Utility methods
    def get_export_summary(self):
        """
        Get summary information about the export

        Returns:
            dict: Export summary information
        """
        self.ensure_one()

        try:
            selfconsumption = self._validate_export_context()
            return {
                "project_name": selfconsumption.name,
                "inscription_count": len(selfconsumption.inscription_ids),
                "has_file": bool(self.file_data),
                "file_name": self.file_name,
            }
        except ValidationError:
            return {
                "project_name": None,
                "inscription_count": 0,
                "has_file": False,
                "file_name": None,
            }

    def preview_export_data(self):
        """
        Preview export data without generating the file

        Returns:
            dict: Preview information
        """
        self.ensure_one()

        try:
            selfconsumption = self._validate_export_context()
            inscriptions = selfconsumption.inscription_ids

            # Get sample data (first 5 inscriptions)
            sample_inscriptions = inscriptions[:5]
            sample_data = []

            for inscription in sample_inscriptions:
                sample_data.append(
                    {
                        "partner_name": inscription.partner_id.name,
                        "cups_code": self._get_safe_field_value(
                            inscription.supply_point_id, "code"
                        ),
                        "participation": self._get_safe_field_value(
                            inscription, "participation_quantity"
                        ),
                        "has_mandate": bool(inscription.mandate_id),
                    }
                )

            return {
                "valid_preview": True,
                "total_inscriptions": len(inscriptions),
                "sample_data": sample_data,
                "headers": CSV_HEADERS,
            }

        except ValidationError as e:
            return {
                "valid_preview": False,
                "error_message": str(e),
            }
