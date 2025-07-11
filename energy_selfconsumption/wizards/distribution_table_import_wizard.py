import base64
import logging
from io import StringIO

import chardet
import pandas as pd

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..config import (
    CSV_DELIMITER,
    CSV_FILE_EXTENSION,
    CSV_QUOTE_CHAR,
    DEFAULT_ENCODING,
    DISTRIBUTION_TYPE_FIXED,
    DISTRIBUTION_TYPE_HOURLY,
)

# Constants for distribution table import
COEFFICIENT_SUM_TOLERANCE = 1e-6
EXPECTED_COEFFICIENT_SUM = 1.0
HOURLY_COLUMNS_START_INDEX = 1
CUPS_COLUMN_NAME = "CUPS"
COEFFICIENT_COLUMN_NAME = "Coefficient"

logger = logging.getLogger(__name__)


class DistributionTableImportWizard(models.TransientModel):
    """
    Distribution Table Import Wizard

    This wizard handles the import of distribution table data from CSV files,
    supporting both fixed and hourly distribution types:
    - Fixed distribution: Single coefficient per supply point
    - Hourly distribution: Hourly coefficients for each supply point

    Features:
    - CSV file parsing with encoding detection
    - Data validation and coefficient verification
    - Bulk supply point assignation creation
    - Template download functionality
    - Error handling and logging
    """

    _name = "energy_selfconsumption.distribution_table_import.wizard"
    _description = "Service to import distribution table"

    # File import fields
    import_file = fields.Binary(
        string="Import File (*.csv)", help="CSV file containing distribution table data"
    )
    fname = fields.Char(string="File Name", help="Name of the imported file")

    # CSV format configuration
    delimiter = fields.Char(
        default=CSV_DELIMITER,
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

    # Processing options
    clean = fields.Boolean(
        string="Clean existing data",
        default=True,
        help="Remove existing supply point assignations before import",
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
        Import distribution table data from CSV file

        Main method that processes the uploaded CSV file and imports
        all distribution data into the distribution table.

        Returns:
            bool: True if import completed successfully
        """
        self.ensure_one()

        # Get distribution table from context
        distribution_table = self._get_distribution_table_from_context()

        # Parse and import CSV file
        self.parse_csv_file(distribution_table)

        return True

    def _get_distribution_table_from_context(self):
        """
        Get distribution table from active context

        Returns:
            distribution_table: Distribution table record

        Raises:
            ValidationError: If distribution table not found
        """
        active_id = self.env.context.get("active_id")
        if not active_id:
            raise ValidationError(_("No distribution table selected"))

        distribution_table = self.env[
            "energy_selfconsumption.distribution_table"
        ].browse(active_id)
        if not distribution_table.exists():
            raise ValidationError(_("Distribution table not found"))

        return distribution_table

    def parse_csv_file(self, distribution_table):
        """
        Parse CSV file and import data

        Args:
            distribution_table: Distribution table record to import data into
        """
        logger.info("Starting CSV file parsing for distribution table import")

        try:
            # Decode and parse file
            file_data = base64.b64decode(self.import_file)
            df, parsing_success = self._parse_file(file_data)

            if not parsing_success:
                return

            # Validate data
            if not self.check_data_validity(df, distribution_table):
                return

            # Clean existing data if requested
            if self.clean:
                self.clean_lines(distribution_table)

            # Import all lines
            self.import_all_lines(df, distribution_table)

            # Update distribution table with import metadata for hourly type
            if distribution_table.type == DISTRIBUTION_TYPE_HOURLY:
                self._update_distribution_table_metadata(distribution_table)

            logger.info("CSV file parsing completed successfully")

        except Exception as e:
            logger.error(f"Error parsing CSV file: {e}")
            self._notify_error(
                distribution_table,
                _("Error parsing CSV file: {error}").format(error=str(e)),
            )

    def _update_distribution_table_metadata(self, distribution_table):
        """
        Update distribution table with import metadata

        Args:
            distribution_table: Distribution table record
        """
        distribution_table.write(
            {
                "hourly_coefficients_imported_file": self.import_file,
                "hourly_coefficients_imported_filename": self.fname,
                "hourly_coefficients_imported_delimiter": self.delimiter,
                "hourly_coefficients_imported_quotechar": self.quotechar,
                "hourly_coefficients_imported_encoding": self.encoding,
            }
        )

    # File parsing methods
    def _parse_file(self, data_file):
        """
        Parse CSV file data into DataFrame

        Args:
            data_file: Binary file data

        Returns:
            tuple: (DataFrame, success_flag)
        """
        logger.info("Parsing CSV file data")
        self.ensure_one()

        try:
            # Decode file with proper encoding
            decoded_file = self._decode_file_data(data_file)
            if not decoded_file:
                return None, False

            # Parse CSV into DataFrame
            df = pd.read_csv(
                StringIO(decoded_file),
                delimiter=self.delimiter,
                quotechar=self.quotechar,
            )

            logger.info(
                f"Successfully parsed CSV with {len(df)} rows and {len(df.columns)} columns"
            )
            return df, True

        except Exception as e:
            logger.error(f"Error parsing CSV file: {e}")
            self._notify_error(
                None, _("Error parsing the file: {error}").format(error=str(e))
            )
            return None, False

    def _decode_file_data(self, data_file):
        """
        Decode file data with proper encoding

        Args:
            data_file: Binary file data

        Returns:
            str: Decoded file content or None if failed
        """
        try:
            # Try specified encoding first
            return data_file.decode(self.encoding)
        except UnicodeDecodeError:
            # Auto-detect encoding if specified encoding fails
            detected_encoding = chardet.detect(data_file).get("encoding")
            if not detected_encoding:
                self._notify_error(None, _("No valid encoding detected for the file"))
                return None

            try:
                return data_file.decode(detected_encoding)
            except UnicodeDecodeError:
                self._notify_error(
                    None, _("Failed to decode file with detected encoding")
                )
                return None

    # Data validation methods
    def check_data_validity(self, df, distribution_table):
        """
        Validate CSV data based on distribution table type

        Args:
            df: DataFrame with CSV data
            distribution_table: Distribution table record

        Returns:
            bool: True if data is valid
        """
        if distribution_table.type == DISTRIBUTION_TYPE_HOURLY:
            return self._validate_hourly_data(df, distribution_table)
        elif distribution_table.type == DISTRIBUTION_TYPE_FIXED:
            return self._validate_fixed_data(df, distribution_table)
        else:
            self._notify_error(
                distribution_table,
                _("Unknown distribution table type: {type}").format(
                    type=distribution_table.type
                ),
            )
            return False

    def _validate_hourly_data(self, df, distribution_table):
        """
        Validate hourly distribution data

        Args:
            df: DataFrame with CSV data
            distribution_table: Distribution table record

        Returns:
            bool: True if data is valid
        """
        # Group by first column (hour) and check coefficient sums
        grouped = df.groupby(df.columns[0]).sum()
        coefficient_sums = grouped.sum(axis=1)

        # Check for hours where coefficients don't sum to 1
        invalid_hours = grouped[
            abs(coefficient_sums - EXPECTED_COEFFICIENT_SUM) > COEFFICIENT_SUM_TOLERANCE
        ]

        if not invalid_hours.empty:
            invalid_hours_list = invalid_hours.index.tolist()
            self._notify_error(
                distribution_table,
                _(
                    "The sum of coefficients for the following hours is not equal to 1: {hours}"
                ).format(hours=", ".join(map(str, invalid_hours_list))),
            )
            return False

        return True

    def _validate_fixed_data(self, df, distribution_table):
        """
        Validate fixed distribution data

        Args:
            df: DataFrame with CSV data
            distribution_table: Distribution table record

        Returns:
            bool: True if data is valid
        """
        # Check if coefficient column exists
        if COEFFICIENT_COLUMN_NAME not in df.columns:
            self._notify_error(
                distribution_table,
                _("Required column '{column}' not found in CSV file").format(
                    column=COEFFICIENT_COLUMN_NAME
                ),
            )
            return False

        # Check coefficient sum
        coefficient_sum = df[COEFFICIENT_COLUMN_NAME].sum()
        if abs(coefficient_sum - EXPECTED_COEFFICIENT_SUM) > COEFFICIENT_SUM_TOLERANCE:
            self._notify_error(
                distribution_table,
                _("The sum of coefficients is not equal to 1: {sum}").format(
                    sum=round(coefficient_sum, 6)
                ),
            )
            return False

        return True

    # Data import methods
    def clean_lines(self, distribution_table):
        """
        Remove existing supply point assignations

        Args:
            distribution_table: Distribution table record
        """
        logger.info("Cleaning existing supply point assignations")
        distribution_table.supply_point_assignation_ids.unlink()

    def import_all_lines(self, df, distribution_table):
        """
        Import all lines from DataFrame

        Args:
            df: DataFrame with CSV data
            distribution_table: Distribution table record
        """
        logger.info(
            f"Importing {len(df)} lines for distribution table type: {distribution_table.type}"
        )

        if distribution_table.type == DISTRIBUTION_TYPE_FIXED:
            values_list = self.prepare_fixed_csv_values(df, distribution_table)
        elif distribution_table.type == DISTRIBUTION_TYPE_HOURLY:
            values_list = self.prepare_hourly_csv_values(df, distribution_table)
        else:
            raise ValidationError(
                _("Unsupported distribution table type: {type}").format(
                    type=distribution_table.type
                )
            )

        # Create supply point assignations using bulk service
        self.env[
            "energy_selfconsumption.create_distribution_table"
        ].create_energy_selfconsumption_supply_point_assignation_sql(
            values_list, distribution_table
        )

    def prepare_fixed_csv_values(self, df, distribution_table):
        """
        Prepare values for fixed distribution import

        Args:
            df: DataFrame with CSV data
            distribution_table: Distribution table record

        Returns:
            list: List of values for supply point assignations
        """
        logger.info("Preparing fixed distribution values")
        values_list = []

        for index, row in df.iterrows():
            try:
                values = self.get_supply_point_assignation_values(
                    row, None, distribution_table
                )
                if values:  # Only add if values are valid
                    values_list.append(values)
            except Exception as e:
                logger.error(f"Error processing row {index}: {e}")
                continue

        return values_list

    def prepare_hourly_csv_values(self, df, distribution_table):
        """
        Prepare values for hourly distribution import

        Args:
            df: DataFrame with CSV data
            distribution_table: Distribution table record

        Returns:
            list: List of values for supply point assignations
        """
        logger.info("Preparing hourly distribution values")
        values_list = []

        # Process only first row for hourly (contains all CUPS columns)
        if not df.empty:
            row = df.iloc[0]
            for column in df.columns[HOURLY_COLUMNS_START_INDEX:]:
                try:
                    cups_code = column
                    values = self.get_supply_point_assignation_values(
                        row, cups_code, distribution_table
                    )
                    if values:  # Only add if values are valid
                        values_list.append(values)
                except Exception as e:
                    logger.error(f"Error processing CUPS {column}: {e}")
                    continue

        return values_list

    def get_supply_point_assignation_values(self, row, cups_code, distribution_table):
        """
        Get supply point assignation values for a row

        Args:
            row: DataFrame row
            cups_code: CUPS code (for hourly) or None (for fixed)
            distribution_table: Distribution table record

        Returns:
            dict: Supply point assignation values or None if invalid
        """
        try:
            # Determine CUPS code and coefficient based on distribution type
            if cups_code:
                # Hourly distribution
                supply_point_id = self.get_supply_point_id(
                    cups_code, distribution_table
                )
                coefficient = 0  # Will be set later for hourly
            else:
                # Fixed distribution
                if CUPS_COLUMN_NAME not in row or COEFFICIENT_COLUMN_NAME not in row:
                    return None

                supply_point_id = self.get_supply_point_id(
                    row[CUPS_COLUMN_NAME], distribution_table
                )
                coefficient = self.get_coefficient(row[COEFFICIENT_COLUMN_NAME])

            if supply_point_id == "null":
                return None  # Invalid supply point

            # Calculate energy shares
            energy_shares = (
                distribution_table.selfconsumption_project_id.power * coefficient
            )

            return {
                "distribution_table_id": distribution_table.id,
                "supply_point_id": supply_point_id,
                "coefficient": coefficient,
                "energy_shares": energy_shares,
                "company_id": distribution_table.company_id.id,
            }

        except Exception as e:
            logger.error(f"Error creating assignation values: {e}")
            return None

    def get_supply_point_id(self, code, distribution_table):
        """
        Get supply point ID by CUPS code

        Args:
            code: CUPS code
            distribution_table: Distribution table record

        Returns:
            int: Supply point ID or "null" if not found
        """
        if not code:
            return "null"

        supply_point = self.env["energy_selfconsumption.supply_point"].search(
            [("code", "=", code)], limit=1
        )

        if not supply_point:
            self._notify_error(
                distribution_table,
                _("Supply point not found for CUPS code: {code}").format(code=code),
            )
            return "null"

        return supply_point.id

    def get_coefficient(self, coefficient_value):
        """
        Convert coefficient value to float

        Args:
            coefficient_value: Raw coefficient value

        Returns:
            float: Converted coefficient value
        """
        try:
            return float(coefficient_value) if coefficient_value is not None else 0.0
        except (ValueError, TypeError):
            logger.warning(f"Invalid coefficient value: {coefficient_value}")
            return 0.0

    # Template and utility methods
    def download_template_button(self):
        """
        Download CSV template for distribution table import

        Returns:
            dict: Report action for template download
        """
        logger.info("Downloading distribution table template")

        doc_ids = self.env.context.get("active_ids", [])
        if not doc_ids:
            raise ValidationError(
                _("No distribution table selected for template download")
            )

        return self.env.ref(
            "energy_selfconsumption.distribution_table_hourly_csv_report"
        ).report_action(docids=doc_ids)

    def _notify_error(self, distribution_table, message):
        """
        Send error notification

        Args:
            distribution_table: Distribution table record (can be None)
            message: Error message
        """
        if distribution_table:
            self.env["energy_selfconsumption.create_distribution_table"].notification(
                distribution_table, "Error", message
            )
        else:
            # Log error if no distribution table available
            logger.error(f"Distribution table import error: {message}")

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
            "quote_char": self.quotechar,
            "clean_existing": self.clean,
        }

    def preview_import_data(self):
        """
        Preview import data without actually importing

        Returns:
            dict: Preview information
        """
        self.ensure_one()

        if not self.import_file:
            return {
                "valid_preview": False,
                "error_message": _("No file selected for preview"),
            }

        try:
            # Parse file
            file_data = base64.b64decode(self.import_file)
            df, parsing_success = self._parse_file(file_data)

            if not parsing_success:
                return {
                    "valid_preview": False,
                    "error_message": _("Failed to parse CSV file"),
                }

            # Get distribution table
            distribution_table = self._get_distribution_table_from_context()

            # Validate data
            is_valid = self.check_data_validity(df, distribution_table)

            return {
                "valid_preview": is_valid,
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "distribution_type": distribution_table.type,
                "sample_data": df.head(5).to_dict("records") if len(df) > 0 else [],
            }

        except Exception as e:
            return {
                "valid_preview": False,
                "error_message": str(e),
            }
