import pandas as pd

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..config import (
    DISTRIBUTION_STATE_ACTIVE,
    DISTRIBUTION_STATE_DEFAULT_VALUE,
    DISTRIBUTION_STATE_DRAFT,
    DISTRIBUTION_STATE_PROCESS,
    DISTRIBUTION_STATE_VALIDATED,
    DISTRIBUTION_STATE_VALUES,
    DISTRIBUTION_TYPE_DEFAULT_VALUE,
    DISTRIBUTION_TYPE_VALUES,
)

# Constants for coefficient validation
COEFFICIENT_PRECISION = 0.000001
VALID_COEFFICIENT_SUM = 1.000000


class DistributionTable(models.Model):
    """
    Distribution Table Model

    This model manages energy distribution tables for self-consumption projects,
    including:
    - Fixed and variable hourly distribution coefficients
    - Supply point assignments and validations
    - State management and lifecycle control
    - CSV file import for hourly coefficients
    - Coefficient validation and sum verification
    """

    _name = "energy_selfconsumption.distribution_table"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Distribution Table"

    # Basic identification and relationships
    name = fields.Char(help="Auto-generated name based on project and sequence")
    selfconsumption_project_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption",
        required=True,
        help="Self-consumption project this table belongs to",
    )
    selfconsumption_project_state = fields.Selection(
        related="selfconsumption_project_id.state",
        help="Current state of the associated self-consumption project",
    )

    # Configuration fields
    type = fields.Selection(
        DISTRIBUTION_TYPE_VALUES,
        default=DISTRIBUTION_TYPE_DEFAULT_VALUE,
        required=True,
        string="Modality",
        help="Distribution type: Fixed coefficients or Variable hourly coefficients",
    )
    state = fields.Selection(
        DISTRIBUTION_STATE_VALUES,
        default=DISTRIBUTION_STATE_DEFAULT_VALUE,
        required=True,
        help="Current state of the distribution table",
    )

    # Relationships
    supply_point_assignation_ids = fields.One2many(
        "energy_selfconsumption.supply_point_assignation",
        "distribution_table_id",
        help="Supply point assignments with their distribution coefficients",
    )

    # Validation and status fields
    coefficient_is_valid = fields.Boolean(
        compute="_compute_coefficient_is_valid",
        readonly=True,
        store=False,
        help="Indicates if the sum of coefficients equals 1.0 (for fixed type)",
    )

    # Date tracking
    date_start = fields.Date(
        string="Start date", help="Date when this distribution table becomes active"
    )
    date_end = fields.Date(
        string="End date", help="Date when this distribution table was deactivated"
    )

    # System fields
    active = fields.Boolean(
        default=True,
        help="If unchecked, this distribution table will be hidden from most views",
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        readonly=True,
        help="Company that owns this distribution table",
    )

    # Hourly coefficients import fields
    hourly_coefficients_imported_file = fields.Binary(
        string="Import File (*.csv)",
        help="CSV file containing hourly distribution coefficients",
    )
    hourly_coefficients_imported_filename = fields.Char(
        string="File Name", help="Name of the imported CSV file"
    )
    hourly_coefficients_imported_delimiter = fields.Char(
        default=",",
        required=True,
        string="File Delimiter",
        help="Delimiter used in the CSV file (usually comma or semicolon)",
    )
    hourly_coefficients_imported_quotechar = fields.Char(
        default='"',
        required=True,
        string="File Quotechar",
        help="Quote character used in the CSV file",
    )
    hourly_coefficients_imported_encoding = fields.Char(
        default="utf-8",
        required=True,
        string="File Encoding",
        help="Character encoding of the CSV file",
    )

    # Computed methods
    @api.depends("supply_point_assignation_ids.coefficient")
    def _compute_coefficient_is_valid(self):
        """
        Validate that coefficients sum to 1.0 for fixed distribution tables

        For fixed type tables, all coefficients must sum to exactly 1.0.
        For hourly type tables, validation is always considered valid
        as coefficients are managed per hour.
        """
        for record in self:
            if record.type == "fixed":
                coefficients = record.supply_point_assignation_ids.mapped("coefficient")
                sum_coefficients = sum(coefficients)
                record.coefficient_is_valid = not fields.Float.compare(
                    sum_coefficients,
                    VALID_COEFFICIENT_SUM,
                    precision_rounding=COEFFICIENT_PRECISION,
                )
            else:
                # Hourly tables are always considered valid
                record.coefficient_is_valid = True

    # Validation constraints
    @api.constrains("supply_point_assignation_ids")
    def _supply_point_constrain(self):
        """
        Prevent modification of supply points when table is in protected states

        Raises:
            ValidationError: If trying to modify supply points in protected states
        """
        for record in self:
            if record.state in (
                DISTRIBUTION_STATE_VALIDATED,
                DISTRIBUTION_STATE_PROCESS,
                DISTRIBUTION_STATE_ACTIVE,
            ):
                raise ValidationError(
                    _(
                        "Supply points cannot be removed because the distribution table state is '{table_state}'"
                    ).format(table_state=record.state)
                )

    # CRUD methods
    @api.model_create_multi
    def create(self, vals):
        """
        Create distribution table records with auto-generated names

        Args:
            vals (list): List of value dictionaries for creation

        Returns:
            recordset: Created distribution table records
        """
        for val in vals:
            if "selfconsumption_project_id" in val:
                project_id = val["selfconsumption_project_id"]
                count = (
                    self.search_count([("selfconsumption_project_id", "=", project_id)])
                    + 1
                )
                val["name"] = f"DT{str(count).zfill(3)}"
        return super().create(vals)

    def write(self, vals):
        """
        Update distribution table with type change validation

        Args:
            vals (dict): Values to update

        Returns:
            bool: True if successful

        Raises:
            ValidationError: If trying to change type with existing assignments
        """
        if "type" in vals and self.supply_point_assignation_ids:
            raise ValidationError(
                _(
                    """To change the type you must first delete the associated distribution points.

Hint: you can delete all the associated distribution points at once using an action."""
                )
            )
        return super().write(vals)

    def unlink(self):
        """
        Delete distribution table records
        """
        for record in self:
            if record.state != DISTRIBUTION_STATE_DRAFT:
                raise ValidationError(
                    _(
                        "You cannot delete a distribution table that is not in draft state."
                    )
                )
            record.supply_point_assignation_ids.unlink()
        return super().unlink()

    # State management methods
    def button_validate(self):
        """
        Validate and approve the distribution table

        Performs validation checks and sets state to 'validated' if all
        conditions are met.

        Raises:
            ValidationError: If validation fails or conflicts exist
        """
        for record in self:
            # Check coefficient validity for fixed tables
            if not record.coefficient_is_valid:
                raise ValidationError(
                    _(
                        "Coefficient distribution must sum to 1.0 for fixed distribution tables."
                    )
                )

            # Check for existing validated table
            existing_validated = record.selfconsumption_project_id.distribution_table_ids.filtered_domain(
                [("state", "=", DISTRIBUTION_STATE_VALIDATED)]
            )
            if existing_validated:
                raise ValidationError(
                    _(
                        "Self-consumption project already has a validated table: {table_name}"
                    ).format(table_name=existing_validated.name)
                )

            # Check for existing table in process
            existing_process = record.selfconsumption_project_id.distribution_table_ids.filtered_domain(
                [("state", "=", DISTRIBUTION_STATE_PROCESS)]
            )
            if existing_process:
                raise ValidationError(
                    _(
                        "Self-consumption project already has a table in process: {table_name}"
                    ).format(table_name=existing_process.name)
                )

            # Set state to validated
            record.write({"state": DISTRIBUTION_STATE_VALIDATED})

    def button_draft(self):
        """Set distribution table state back to draft"""
        for record in self:
            record.write({"state": DISTRIBUTION_STATE_DRAFT})

    # Action methods
    def action_distribution_table_import_wizard(self):
        """
        Open wizard for importing distribution table data

        Returns:
            dict: Action dictionary for opening the import wizard
        """
        self.ensure_one()
        return {
            "name": _("Import Distribution Table"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "energy_selfconsumption.distribution_table_import.wizard",
            "views": [(False, "form")],
            "view_id": False,
            "target": "new",
            "context": {"default_distribution_table_id": self.id},
        }

    def action_clean_supply_point_assignation_wizard(self):
        """
        Open wizard for cleaning supply point assignations

        Returns:
            dict: Action dictionary for opening the clean wizard
        """
        return {
            "name": _("Clean supply point assignation"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "clean.supply.point.assignation.wizard",
            "target": "new",
            "context": {"active_ids": self.env.context.get("active_ids", [])},
        }

    # Business logic methods
    def get_total_coefficient(self):
        """
        Get the total sum of all coefficients in this distribution table

        Returns:
            float: Sum of all coefficients
        """
        self.ensure_one()
        return sum(self.supply_point_assignation_ids.mapped("coefficient"))

    def get_supply_points_count(self):
        """
        Get the number of supply points assigned to this table

        Returns:
            int: Number of assigned supply points
        """
        self.ensure_one()
        return len(self.supply_point_assignation_ids)

    def is_editable(self):
        """
        Check if the distribution table can be edited

        Returns:
            bool: True if editable, False otherwise
        """
        self.ensure_one()
        return self.state == DISTRIBUTION_STATE_DRAFT

    def can_be_activated(self):
        """
        Check if the distribution table can be activated

        Returns:
            bool: True if can be activated, False otherwise
        """
        self.ensure_one()
        return (
            self.state == DISTRIBUTION_STATE_VALIDATED
            and self.coefficient_is_valid
            and self.supply_point_assignation_ids
        )

    def get_assignation_by_supply_point(self, supply_point):
        """
        Get the assignation record for a specific supply point

        Args:
            supply_point: Supply point record

        Returns:
            supply_point_assignation: Assignation record or False
        """
        self.ensure_one()
        return self.supply_point_assignation_ids.filtered(
            lambda a: a.supply_point_id == supply_point
        )

    def action_manager_authorization_report(self):
        self.ensure_one()
        return self.with_context(
            distribution_table_id=self.id
        ).selfconsumption_project_id.action_manager_authorization_report()

    def action_power_sharing_agreement_report(self):
        self.ensure_one()
        return self.with_context(
            distribution_table_id=self.id
        ).selfconsumption_project_id.action_power_sharing_agreement_report()

    def action_manager_partition_coefficient_report(self):
        self.ensure_one()
        return self.with_context(
            distribution_table_id=self.id
        ).selfconsumption_project_id.action_manager_partition_coefficient_report()
