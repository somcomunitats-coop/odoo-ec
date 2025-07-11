import csv
from io import StringIO

from odoo import models

from ..config import CSV_DELIMITER, CSV_QUOTE_CHAR

DEFAULT_ENERGY_VALUE = "0,02"  # Default energy value in kWh
DATE_FORMAT = "%d/%m/%Y"


class ContractCSVReport(models.AbstractModel):
    """
    Contract CSV Report Generator

    This abstract model provides CSV report generation functionality
    for contracts in self-consumption projects, including:
    - Contract billing information export
    - Period date formatting
    - CUPS and CAU code extraction
    - Energy billing data preparation
    """

    _name = "report.contract_contract.csv"
    _description = "Report contract"
    _inherit = "report.report_csv.abstract"

    def create_csv_report(self, docids, data):
        """
        Create CSV report for contracts

        Main entry point for contract CSV report generation.
        Exports contract billing information including CUPS codes,
        energy amounts, CAU codes, and billing periods.

        Args:
            docids (list): Contract IDs to generate report for
            data (dict): Additional report data

        Returns:
            tuple: (csv_content, file_extension)
        """
        # Get contract objects
        objs = self._get_objs_for_report(docids, data)
        contracts = objs

        if not contracts:
            return "", "csv"

        # Generate CSV content
        file_data = StringIO()
        file = csv.DictWriter(file_data, **self.csv_report_options())
        self.generate_csv_report(file, data, contracts)
        file_data.seek(0)

        return file_data.read(), "csv"

    def generate_csv_report(self, writer, data, contracts):
        """
        Generate the actual CSV content for contracts

        Creates CSV rows with contract billing information including:
        - CUPS code from supply point
        - Energy to bill (default or calculated)
        - CAU code from self-consumption project
        - Billing period start and end dates

        Args:
            writer: CSV DictWriter instance
            data (dict): Report data
            contracts: Contract recordset
        """
        writer.writeheader()

        # Write contract data rows
        for contract in contracts:
            contract_data = self._get_contract_billing_data(contract)
            writer.writerow(contract_data)

    def _get_contract_billing_data(self, contract):
        """
        Extract billing data from contract

        Gets all necessary billing information from the contract including
        CUPS code, energy amount, CAU code, and billing period dates.

        Args:
            contract: Contract record

        Returns:
            dict: Contract billing data for CSV row
        """
        # Get main line or first line for period dates
        main_line = contract.get_main_line()
        reference_line = (
            main_line
            if main_line
            else contract.contract_line_ids[0]
            if contract.contract_line_ids
            else None
        )

        # Extract period dates
        next_period_date_start = None
        next_period_date_end = None

        if reference_line:
            next_period_date_start = reference_line.next_period_date_start
            next_period_date_end = reference_line.next_period_date_end

        # Get CUPS code from supply point assignation
        cups_code = ""
        if (
            contract.supply_point_assignation_id
            and contract.supply_point_assignation_id.supply_point_id
        ):
            cups_code = contract.supply_point_assignation_id.supply_point_id.code or ""

        # Get CAU code from self-consumption project
        cau_code = ""
        if contract.project_id and contract.project_id.selfconsumption_id:
            selfconsumption = (
                contract.project_id.selfconsumption_id[0]
                if contract.project_id.selfconsumption_id
                else None
            )
            if selfconsumption:
                cau_code = selfconsumption.code or ""

        # Format dates
        period_start_formatted = ""
        period_end_formatted = ""

        if next_period_date_start:
            period_start_formatted = next_period_date_start.strftime(DATE_FORMAT)

        if next_period_date_end:
            period_end_formatted = next_period_date_end.strftime(DATE_FORMAT)

        return {
            "CUPS": cups_code,
            "Energia a facturar (kWh)": DEFAULT_ENERGY_VALUE,
            "CAU": cau_code,
            "Periode facturat start (dd/mm/aaaa)": period_start_formatted,
            "Periode facturat end (dd/mm/aaaa)": period_end_formatted,
        }

    def csv_report_options(self):
        """
        Get CSV writer configuration options

        Configures CSV writer with field names and formatting options
        for contract billing reports.

        Returns:
            dict: CSV writer configuration options
        """
        options = super().csv_report_options()

        # Define field names for contract billing report
        options["fieldnames"] = [
            "CUPS",
            "Energia a facturar (kWh)",
            "CAU",
            "Periode facturat start (dd/mm/aaaa)",
            "Periode facturat end (dd/mm/aaaa)",
        ]

        # Set CSV formatting options
        options["delimiter"] = CSV_DELIMITER
        options["quotechar"] = CSV_QUOTE_CHAR

        return options

    def validate_contracts_for_report(self, contracts):
        """
        Validate contracts before generating report

        Args:
            contracts: Contract recordset

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        errors = []

        for contract in contracts:
            # Check if contract has supply point assignation
            if not contract.supply_point_assignation_id:
                errors.append(
                    f"Contract {contract.name} has no supply point assignation"
                )

            # Check if contract has project
            if not contract.project_id:
                errors.append(f"Contract {contract.name} has no associated project")

            # Check if contract has lines
            if not contract.contract_line_ids:
                errors.append(f"Contract {contract.name} has no contract lines")

        if errors:
            from odoo.exceptions import ValidationError

            raise ValidationError("\n".join(errors))

        return True

    def get_report_summary(self, contracts):
        """
        Get summary information about the contracts in the report

        Args:
            contracts: Contract recordset

        Returns:
            dict: Report summary information
        """
        return {
            "contract_count": len(contracts),
            "contracts_with_supply_points": len(
                contracts.filtered("supply_point_assignation_id")
            ),
            "contracts_with_projects": len(contracts.filtered("project_id")),
            "unique_projects": len(contracts.mapped("project_id")),
            "unique_supply_points": len(
                contracts.mapped("supply_point_assignation_id.supply_point_id")
            ),
        }
