import base64
import logging
from io import StringIO

import chardet
import pandas as pd

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.energy_communities.config import DISPLAY_DATE_FORMAT

from ..config import (
    CSV_DELIMITER,
    CSV_FILE_EXTENSION,
    CSV_QUOTE_CHAR,
    DEFAULT_ENCODING,
    MIN_POWER_VALUE,
    SELFCONSUMPTION_INVOICING_MODE_ENERGY_CUSTOM,
    SELFCONSUMPTION_INVOICING_MODE_ENERGY_DELIVERED,
    SELFCONSUMPTION_INVOICING_MODE_VALUES,
)

# Constants for invoicing wizard
VALID_INVOICING_MODES = [
    SELFCONSUMPTION_INVOICING_MODE_ENERGY_DELIVERED,
    SELFCONSUMPTION_INVOICING_MODE_ENERGY_CUSTOM,
]
ENERGY_DELIVERED_TEMPLATE = "Energy Delivered Custom: {energy_delivered} kWh"

logger = logging.getLogger(__name__)


class InvoicingWizard(models.TransientModel):
    """
    Invoicing Wizard for Self-consumption Projects

    This wizard handles invoice generation for self-consumption energy projects,
    supporting different invoicing modes:
    - Energy delivered: Fixed energy amount for all contracts
    - Energy custom: Individual energy amounts from CSV file

    Features:
    - Contract validation and grouping
    - CSV file import and processing
    - Period validation
    - Bulk invoice generation
    """

    _name = "energy_selfconsumption.invoicing.wizard"
    _description = "Service to generate type invoicing"

    # Energy and contract fields
    power = fields.Float(
        string="Total Energy Generated (kWh)",
        help="Total energy generated for energy delivered mode",
    )
    contract_ids = fields.Many2many(
        "contract.contract",
        readonly=True,
        help="Contracts selected for invoice generation",
    )

    # Period fields (computed)
    next_period_date_start = fields.Date(
        string="Start",
        compute="_compute_next_period_date_start_and_end",
        readonly=True,
        help="Start date of the invoicing period",
    )
    next_period_date_end = fields.Date(
        string="End",
        compute="_compute_next_period_date_start_and_end",
        readonly=True,
        help="End date of the invoicing period",
    )

    # Contract count and mode
    num_contracts = fields.Integer(
        string="Selected contracts",
        default=lambda self: len(self.env.context.get("active_ids", [])),
        help="Number of contracts selected for invoicing",
    )
    invoicing_mode = fields.Selection(
        SELFCONSUMPTION_INVOICING_MODE_VALUES,
        string="Invoicing Mode",
        default="_get_invoicing_mode",
        help="Invoicing mode of the selected contracts",
    )

    # CSV import fields
    import_file = fields.Binary(
        string="Import File (*.csv)",
        help="CSV file with custom energy amounts per contract",
    )
    fname = fields.Char(string="File Name", help="Name of the imported file")
    delimiter = fields.Char(
        default=CSV_DELIMITER,
        string="File Delimiter",
        help="Delimiter in import CSV file",
    )
    quotechar = fields.Char(
        default=CSV_QUOTE_CHAR,
        string="File Quotechar",
        help="Quote character in import CSV file",
    )
    encoding = fields.Char(
        default=DEFAULT_ENCODING,
        string="File Encoding",
        help="Encoding format in import CSV file",
    )

    # Default methods
    def _get_invoicing_mode(self):
        """
        Get invoicing mode from selected contracts

        Returns:
            str: Invoicing mode or None if no contracts selected
        """
        active_ids = self.env.context.get("active_ids", [])
        if not active_ids:
            return False

        contracts = self.env["contract.contract"].search([("id", "in", active_ids)])
        if contracts:
            return contracts[0].project_id.selfconsumption_id.invoicing_mode
        return False

    # Computed methods
    @api.depends("contract_ids")
    def _compute_next_period_date_start_and_end(self):
        """
        Compute period dates from contract lines

        Gets the period dates from the main line or first line
        of the first contract.
        """
        for record in self:
            record.next_period_date_start = False
            record.next_period_date_end = False

            if not record.contract_ids:
                continue

            first_contract = record.contract_ids[0]
            if not first_contract.contract_line_ids:
                continue

            # Get main line or first line
            main_line = first_contract.get_main_line()
            reference_line = (
                main_line if main_line else first_contract.contract_line_ids[0]
            )

            record.next_period_date_start = reference_line.next_period_date_start
            record.next_period_date_end = reference_line.next_period_date_end

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

    @api.constrains("contract_ids")
    def _check_contract_consistency(self):
        """
        Validate contract consistency for invoicing

        Checks:
        - All contracts belong to the same project
        - All contracts have valid invoicing mode
        - All contracts have the same invoicing period

        Raises:
            ValidationError: If validation fails
        """
        for record in self:
            if not record.contract_ids:
                continue

            contract_list = record.contract_ids
            first_contract = contract_list[0]

            # Check same project
            if not self._validate_same_project(contract_list, first_contract):
                return

            # Check valid invoicing mode
            if not self._validate_invoicing_mode(contract_list):
                return

            # Check same period
            if not self._validate_same_period(contract_list, first_contract):
                return

    def _validate_same_project(self, contract_list, first_contract):
        """
        Validate all contracts belong to the same project

        Args:
            contract_list: List of contracts to validate
            first_contract: Reference contract

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If contracts from different projects
        """
        all_same_project = all(
            contract.project_id == first_contract.project_id
            for contract in contract_list
        )

        if not all_same_project:
            project_name = first_contract.project_id.selfconsumption_id.name
            raise ValidationError(
                _(
                    "Some contracts are not from the same self-consumption project. "
                    "Please ensure all contracts belong to project '{project_name}'."
                ).format(project_name=project_name)
            )
        return True

    def _validate_invoicing_mode(self, contract_list):
        """
        Validate contracts have valid invoicing mode

        Args:
            contract_list: List of contracts to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If invalid invoicing mode
        """
        all_valid_mode = all(
            contract.project_id.selfconsumption_id.invoicing_mode
            in VALID_INVOICING_MODES
            for contract in contract_list
        )

        if not all_valid_mode:
            raise ValidationError(
                _(
                    "Some contracts are not configured for energy delivered invoicing. "
                    "Please ensure all contracts have valid invoicing mode."
                )
            )
        return True

    def _validate_same_period(self, contract_list, first_contract):
        """
        Validate all contracts have the same invoicing period

        Args:
            contract_list: List of contracts to validate
            first_contract: Reference contract

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If different periods
        """
        first_start = first_contract.next_period_date_start
        first_end = first_contract.next_period_date_end

        all_same_period = all(
            contract.next_period_date_start == first_start
            and contract.next_period_date_end == first_end
            for contract in contract_list
        )

        if not all_same_period:
            raise ValidationError(
                _(
                    "Selected contracts have different invoicing periods. "
                    "Please select contracts with the same period: {start} to {end}"
                ).format(
                    start=first_start.strftime(DISPLAY_DATE_FORMAT)
                    if first_start
                    else "N/A",
                    end=first_end.strftime(DISPLAY_DATE_FORMAT) if first_end else "N/A",
                )
            )
        return True

    @api.constrains("power")
    def _check_power_value(self):
        """
        Validate power value is positive

        Raises:
            ValidationError: If power is not positive
        """
        for record in self:
            if record.power is not False and record.power <= MIN_POWER_VALUE:
                raise ValidationError(
                    _(
                        "The energy generated must be greater than {min_value} kWh"
                    ).format(min_value=MIN_POWER_VALUE)
                )

    # Main action methods
    def generate_invoices(self):
        """
        Generate invoices for selected contracts

        Main method that orchestrates invoice generation based on
        the invoicing mode (energy delivered or energy custom).

        Returns:
            list: List of generated invoice records
        """
        self.ensure_one()

        if not self.contract_ids:
            raise ValidationError(_("No contracts selected for invoicing"))

        # Parse CSV file if needed
        df, csv_loaded = self._parse_csv_if_needed()

        # Generate invoices
        generated_invoices = []
        for contract in self.contract_ids:
            invoicing_mode = contract.project_id.selfconsumption_id.invoicing_mode

            if invoicing_mode == SELFCONSUMPTION_INVOICING_MODE_ENERGY_DELIVERED:
                invoice = self._process_energy_delivered_contract(contract)
                invoice.write({"energy_delivered": self.power})
                generated_invoices.append(invoice)

            elif invoicing_mode == SELFCONSUMPTION_INVOICING_MODE_ENERGY_CUSTOM:
                if not csv_loaded:
                    raise ValidationError(
                        _("CSV file is required for energy custom mode")
                    )
                invoice = self._process_energy_custom_contract(df, contract)
                invoice.write({"energy_delivered": contract_data["energy"]})
                generated_invoices.append(invoice)

        return generated_invoices

    def _parse_csv_if_needed(self):
        """
        Parse CSV file if energy custom mode is used

        Returns:
            tuple: (DataFrame, success_flag)
        """
        # Check if any contract uses energy custom mode
        uses_custom_mode = any(
            contract.project_id.selfconsumption_id.invoicing_mode
            == SELFCONSUMPTION_INVOICING_MODE_ENERGY_CUSTOM
            for contract in self.contract_ids
        )

        if uses_custom_mode:
            return self.parse_csv_file()
        return None, True

    def _process_energy_delivered_contract(self, contract):
        """
        Process contract with energy delivered mode

        Args:
            contract: Contract record to process

        Returns:
            account.move: Generated invoice
        """
        return contract.with_context(
            {"energy_delivered": self.power}
        )._recurring_create_invoice()

    def _process_energy_custom_contract(self, df, contract):
        """
        Process contract with energy custom mode

        Args:
            df: DataFrame with CSV data
            contract: Contract record to process

        Returns:
            account.move: Generated invoice
        """
        # Validate CSV data count
        if len(self.contract_ids) != df.shape[0]:
            raise ValidationError(
                _(
                    "Number of selected contracts ({selected}) does not match "
                    "number of contracts in CSV ({csv_count})"
                ).format(selected=len(self.contract_ids), csv_count=df.shape[0])
            )

        # Get contract data
        contract_data = self._extract_contract_data_from_csv(df, contract)

        # Update contract lines with custom energy
        self._update_contract_lines_with_custom_energy(contract, contract_data)

        # Generate invoice
        return contract.with_context(
            {"energy_delivered": contract_data["energy"]}
        )._recurring_create_invoice()

    def _extract_contract_data_from_csv(self, df, contract):
        """
        Extract contract-specific data from CSV

        Args:
            df: DataFrame with CSV data
            contract: Contract record

        Returns:
            dict: Contract data with CUPS, energy, and period info
        """
        # Get contract identifiers
        cups_code = contract.supply_point_assignation_id.supply_point_id.code
        cau_code = contract.project_id.selfconsumption_id.code

        # Get period dates
        main_line = contract.get_main_line()
        reference_line = main_line if main_line else contract.contract_line_ids[0]

        period_start = reference_line.next_period_date_start.strftime(
            DISPLAY_DATE_FORMAT
        )
        period_end = reference_line.next_period_date_end.strftime(DISPLAY_DATE_FORMAT)

        # Find matching row in CSV
        matching_rows = df[
            (df["CUPS"] == cups_code)
            & (df["CAU"] == cau_code)
            & (df["Periode facturat start (dd/mm/aaaa)"] == period_start)
            & (df["Periode facturat end (dd/mm/aaaa)"] == period_end)
        ]

        if matching_rows.empty:
            raise ValidationError(
                _(
                    "No data found in CSV for:\n"
                    "Project (CAU): {cau}\n"
                    "CUPS: {cups}\n"
                    "Period: {start} - {end}"
                ).format(
                    cau=cau_code, cups=cups_code, start=period_start, end=period_end
                )
            )

        # Extract energy value
        row_index = matching_rows.index[0]
        energy_str = matching_rows.loc[row_index, "Energia a facturar (kWh)"]
        energy_value = round(float(str(energy_str).replace(",", ".")), 2)

        if energy_value <= MIN_POWER_VALUE:
            raise ValidationError(
                _(
                    "Energy value must be greater than {min_value} kWh. "
                    "Found: {energy} kWh for CUPS {cups}"
                ).format(min_value=MIN_POWER_VALUE, energy=energy_value, cups=cups_code)
            )

        return {
            "cups": cups_code,
            "energy": energy_value,
            "period_start": period_start,
            "period_end": period_end,
        }

    def _update_contract_lines_with_custom_energy(self, contract, contract_data):
        """
        Update contract lines with custom energy data

        Args:
            contract: Contract record
            contract_data: Dictionary with contract data
        """
        if not contract.contract_line_ids:
            raise ValidationError(
                _("Contract {contract_name} has no lines to update").format(
                    contract_name=contract.name or contract.display_name
                )
            )

        # Get template name
        template_name = contract.contract_template_id.contract_line_ids[0].name
        template_name += " " + ENERGY_DELIVERED_TEMPLATE

        # Update all contract lines
        for line in contract.contract_line_ids:
            line.write(
                {
                    "name": template_name.format(
                        energy_delivered=contract_data["energy"],
                        code=contract_data["cups"],
                        owner_id=contract.supply_point_assignation_id.supply_point_id.owner_id.display_name,
                    ),
                    "quantity": contract_data["energy"],
                }
            )

    # CSV processing methods
    def parse_csv_file(self):
        """
        Parse uploaded CSV file

        Returns:
            tuple: (DataFrame, success_flag)
        """
        if not self.import_file:
            return None, False

        try:
            file_data = base64.b64decode(self.import_file)
            return self._parse_file_data(file_data)
        except Exception as e:
            logger.error(f"Error parsing CSV file: {e}")
            return None, False

    def _parse_file_data(self, file_data):
        """
        Parse file data into DataFrame

        Args:
            file_data: Binary file data

        Returns:
            tuple: (DataFrame, success_flag)
        """
        try:
            # Try to decode with specified encoding
            try:
                decoded_file = file_data.decode(self.encoding)
            except UnicodeDecodeError:
                # Auto-detect encoding if specified encoding fails
                detected_encoding = chardet.detect(file_data).get("encoding")
                if not detected_encoding:
                    logger.warning("No valid encoding detected for file")
                    return None, False
                decoded_file = file_data.decode(detected_encoding)

            # Parse CSV
            df = pd.read_csv(
                StringIO(decoded_file),
                delimiter=self.delimiter,
                quotechar=self.quotechar,
            )

            # Validate CSV structure
            if not self._validate_csv_structure(df):
                return None, False

            return df, True

        except Exception as e:
            logger.error(f"Error parsing file data: {e}")
            return None, False

    def _validate_csv_structure(self, df):
        """
        Validate CSV file structure

        Args:
            df: DataFrame to validate

        Returns:
            bool: True if valid structure
        """
        required_columns = [
            "CUPS",
            "CAU",
            "Energia a facturar (kWh)",
            "Periode facturat start (dd/mm/aaaa)",
            "Periode facturat end (dd/mm/aaaa)",
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValidationError(
                _("CSV file is missing required columns: {columns}").format(
                    columns=", ".join(missing_columns)
                )
            )

        if df.empty:
            raise ValidationError(_("CSV file is empty"))

        return True

    # Utility methods
    def download_template_button(self):
        """
        Download CSV template for energy custom mode

        Returns:
            dict: Report action for template download
        """
        self.ensure_one()

        if not self.contract_ids:
            raise ValidationError(_("No contracts selected for template generation"))

        return self.env.ref(
            "energy_selfconsumption.contract_contract_csv_report"
        ).report_action(docids=self.contract_ids.ids)

    def get_wizard_summary(self):
        """
        Get summary information about the wizard state

        Returns:
            dict: Summary information
        """
        self.ensure_one()

        return {
            "contract_count": len(self.contract_ids),
            "invoicing_mode": self.invoicing_mode,
            "has_csv_file": bool(self.import_file),
            "period_start": self.next_period_date_start,
            "period_end": self.next_period_date_end,
            "total_energy": self.power,
        }
