import csv
import random
from io import StringIO

from odoo import models

from ..config import (
    CSV_DELIMITER,
    CSV_QUOTE_CHAR,
    DISTRIBUTION_TYPE_FIXED,
    DISTRIBUTION_TYPE_HOURLY,
)

# Constants for CSV report generation
COEFFICIENT_DECIMAL_PLACES = 6
HOURS_PER_YEAR = 8760
COEFFICIENT_TOLERANCE = 0.000001


class DistributionTableCSV(models.AbstractModel):
    """
    Distribution Table CSV Report Generator

    This abstract model provides CSV report generation functionality
    for distribution tables in self-consumption projects, including:
    - Fixed coefficient CSV reports
    - Hourly coefficient CSV reports
    - Coefficient normalization and adjustment
    - Proper CSV formatting and structure
    """

    _name = "report.energy_selfconsumption.distribution_table.csv"
    _description = "Report distribution table"
    _inherit = "report.report_csv.abstract"

    def create_csv_report(self, docids, data):
        """
        Create CSV report for distribution table

        Main entry point for CSV report generation. Handles both fixed
        and hourly distribution table types.

        Args:
            docids (list): Document IDs to generate report for
            data (dict): Additional report data

        Returns:
            tuple: (csv_content, file_extension)
        """
        # Get distribution table objects
        objs = self._get_objs_for_report(docids, data)

        if not objs:
            return "", "csv"

        distribution_table = objs[0]

        # Get CUPS codes from project inscriptions
        list_cups = self._get_cups_list(distribution_table)

        if not list_cups:
            return "", "csv"

        # Generate CSV content
        file_data = StringIO()
        file = csv.DictWriter(
            file_data, **self.csv_report_options(list_cups, distribution_table.type)
        )

        self.generate_csv_report(file, data, list_cups, distribution_table)
        file_data.seek(0)

        return file_data.read(), "csv"

    def generate_csv_report(self, writer, data, list_cups, distribution_table):
        """
        Generate the actual CSV content

        Creates the CSV content based on distribution table type:
        - Fixed: Single row per CUPS with coefficient
        - Hourly: One row per hour (8760 rows) with coefficients for all CUPS

        Args:
            writer: CSV DictWriter instance
            data (dict): Report data
            list_cups (list): List of CUPS codes
            distribution_table: Distribution table record
        """
        writer.writeheader()

        if distribution_table.type == DISTRIBUTION_TYPE_FIXED:
            self._generate_fixed_csv_report(writer, list_cups)
        else:
            self._generate_hourly_csv_report(writer, list_cups)

    def _generate_fixed_csv_report(self, writer, list_cups):
        """
        Generate CSV report for fixed distribution table

        Creates one row per CUPS with a normalized coefficient.

        Args:
            writer: CSV DictWriter instance
            list_cups (list): List of CUPS codes
        """
        # Generate random coefficients for demonstration
        # In production, this should use actual distribution data
        coefficients = {code: random.random() for code in list_cups}
        coefficients = self._normalize_and_adjust_coefficients(coefficients)

        # Write rows
        for cups_code, coefficient_value in coefficients.items():
            writer.writerow(
                {
                    "CUPS": cups_code,
                    "Coefficient": self._format_coefficient(coefficient_value),
                }
            )

    def _generate_hourly_csv_report(self, writer, list_cups):
        """
        Generate CSV report for hourly distribution table

        Creates 8760 rows (one per hour) with coefficients for all CUPS.

        Args:
            writer: CSV DictWriter instance
            list_cups (list): List of CUPS codes
        """
        for hour in range(1, HOURS_PER_YEAR + 1):
            # Generate random coefficients for this hour
            # In production, this should use actual hourly distribution data
            coefficients = {code: random.random() for code in list_cups}
            coefficients = self._normalize_and_adjust_coefficients(coefficients)

            # Create row with hour and all CUPS coefficients
            row = {"hour": hour}
            row.update(
                {
                    cups_code: self._format_coefficient(coefficient_value)
                    for cups_code, coefficient_value in coefficients.items()
                }
            )

            writer.writerow(row)

    def _normalize_and_adjust_coefficients(self, coefficients):
        """
        Normalize coefficients to sum to 1.0 and adjust for rounding

        Ensures that all coefficients sum exactly to 1.0 by:
        1. Normalizing all coefficients by their sum
        2. Rounding to specified decimal places
        3. Adjusting the last coefficient to compensate for rounding errors

        Args:
            coefficients (dict): Dictionary of CUPS -> coefficient

        Returns:
            dict: Normalized and adjusted coefficients
        """
        if not coefficients:
            return coefficients

        # Normalize coefficients to sum to 1.0
        total_sum = sum(coefficients.values())
        if total_sum > 0:
            for key in coefficients:
                coefficients[key] = coefficients[key] / total_sum

        # Round to specified decimal places
        rounded_coefficients = {
            key: round(coefficients[key], COEFFICIENT_DECIMAL_PLACES)
            for key in coefficients
        }

        # Adjust the last coefficient to ensure sum equals 1.0
        sum_rounded = sum(rounded_coefficients.values())
        if rounded_coefficients:
            last_key = list(rounded_coefficients.keys())[-1]
            adjustment = round(1.0 - sum_rounded, COEFFICIENT_DECIMAL_PLACES)
            rounded_coefficients[last_key] += adjustment

        return rounded_coefficients

    def _format_coefficient(self, coefficient_value):
        """
        Format coefficient value for CSV output

        Args:
            coefficient_value (float): Coefficient to format

        Returns:
            str: Formatted coefficient string
        """
        return f"{coefficient_value:.{COEFFICIENT_DECIMAL_PLACES}f}"

    def _get_cups_list(self, distribution_table):
        """
        Get list of CUPS codes from distribution table project

        Args:
            distribution_table: Distribution table record

        Returns:
            list: List of CUPS codes from project inscriptions
        """
        if not distribution_table.selfconsumption_project_id:
            return []

        return distribution_table.selfconsumption_project_id.inscription_ids.mapped(
            "code"
        )

    def csv_report_options(self, list_cups, report_type):
        """
        Get CSV writer options based on report type

        Configures CSV writer with appropriate field names and formatting
        options based on whether it's a fixed or hourly report.

        Args:
            list_cups (list): List of CUPS codes
            report_type (str): Type of report ('fixed' or 'hourly')

        Returns:
            dict: CSV writer configuration options
        """
        # Get base options from parent class
        options = super().csv_report_options()

        # Configure field names based on report type
        if report_type == DISTRIBUTION_TYPE_FIXED:
            options["fieldnames"] = ["CUPS", "Coefficient"]
        else:
            # Hourly report: hour column + one column per CUPS
            options["fieldnames"] = ["hour"] + list_cups

        # Set CSV formatting options
        options["delimiter"] = CSV_DELIMITER
        options["quotechar"] = CSV_QUOTE_CHAR

        return options

    def validate_distribution_table(self, distribution_table):
        """
        Validate distribution table before generating report

        Args:
            distribution_table: Distribution table record

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        errors = []

        if not distribution_table:
            errors.append("Distribution table is required")

        if not distribution_table.selfconsumption_project_id:
            errors.append("Distribution table must be associated with a project")

        cups_list = self._get_cups_list(distribution_table)
        if not cups_list:
            errors.append("Project must have inscriptions with CUPS codes")

        if distribution_table.type not in (
            DISTRIBUTION_TYPE_FIXED,
            DISTRIBUTION_TYPE_HOURLY,
        ):
            errors.append(f"Invalid distribution table type: {distribution_table.type}")

        if errors:
            from odoo.exceptions import ValidationError

            raise ValidationError("\n".join(errors))

        return True

    def get_report_metadata(self, distribution_table):
        """
        Get metadata about the report being generated

        Args:
            distribution_table: Distribution table record

        Returns:
            dict: Report metadata
        """
        cups_list = self._get_cups_list(distribution_table)

        metadata = {
            "project_name": distribution_table.selfconsumption_project_id.name,
            "table_type": distribution_table.type,
            "cups_count": len(cups_list),
            "cups_codes": cups_list,
        }

        if distribution_table.type == DISTRIBUTION_TYPE_FIXED:
            metadata["row_count"] = len(cups_list)
        else:
            metadata["row_count"] = HOURS_PER_YEAR
            metadata["column_count"] = len(cups_list) + 1  # +1 for hour column

        return metadata
