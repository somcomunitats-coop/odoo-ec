from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..config import DISTRIBUTION_STATE_ACTIVE

# Constants for coefficient validation
MIN_COEFFICIENT_VALUE = 0.0
MAX_COEFFICIENT_VALUE = 1.0
COEFFICIENT_PRECISION = (7, 6)


class SupplyPointAssignation(models.Model):
    """
    Supply Point Assignation Model

    This model manages the assignment of supply points to distribution tables
    with their corresponding distribution coefficients, including:
    - Supply point to distribution table relationships
    - Distribution coefficient management and validation
    - Energy shares calculation based on project power
    - Partner and owner information access
    - Validation of project membership and coefficient constraints
    """

    _name = "energy_selfconsumption.supply_point_assignation"
    _description = "Supply Point Assignation"

    # Core relationship fields
    distribution_table_id = fields.Many2one(
        "energy_selfconsumption.distribution_table",
        required=True,
        help="Distribution table this assignation belongs to",
    )
    supply_point_id = fields.Many2one(
        "energy_selfconsumption.supply_point",
        required=True,
        help="Supply point assigned to the distribution table",
    )

    # Related project information
    selfconsumption_project_id = fields.Many2one(
        related="distribution_table_id.selfconsumption_project_id",
        help="Self-consumption project associated with this assignation",
    )
    distribution_table_state = fields.Selection(
        related="distribution_table_id.state",
        help="Current state of the distribution table",
    )
    distribution_table_create_date = fields.Datetime(
        related="distribution_table_id.create_date",
        help="Creation date of the distribution table",
    )

    # Distribution coefficient and energy calculation
    coefficient = fields.Float(
        string="Distribution coefficient",
        digits=COEFFICIENT_PRECISION,
        required=True,
        help="Distribution coefficient for this supply point (must be between 0 and 1, sum of all coefficients must equal 1)",
    )
    energy_shares = fields.Float(
        string="Distribution coefficient in kWh",
        help="Distribution coefficient in kWh calculated from project power and coefficient",
        compute="_compute_energy_shares",
        store=True,
    )

    # Related partner and supply point information
    owner_id = fields.Many2one(
        "res.partner",
        related="supply_point_id.owner_id",
        help="Owner of the supply point",
    )
    partner_id = fields.Many2one(
        "res.partner",
        related="supply_point_id.partner_id",
        help="Cooperator partner associated with the supply point",
    )
    code = fields.Char(
        related="supply_point_id.code", help="CUPS code of the supply point"
    )

    # Validation and filtering fields
    table_coefficient_is_valid = fields.Boolean(
        related="distribution_table_id.coefficient_is_valid",
        help="Indicates if the distribution table coefficients are valid",
    )
    supply_point_filtered_ids = fields.One2many(
        "energy_selfconsumption.supply_point",
        compute="_compute_supply_point_filtered_ids",
        readonly=True,
        help="Available supply points for assignment (filtered to prevent duplicates)",
    )

    # System fields
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        readonly=True,
        help="Company that owns this assignation",
    )

    # Display fields for views (non-stored for performance)
    supply_point_code = fields.Char(
        related="supply_point_id.code",
        store=False,
        help="CUPS code for display purposes",
    )
    supply_point_address = fields.Char(
        related="supply_point_id.street",
        store=False,
        help="Supply point address for display purposes",
    )
    supply_point_postalcode = fields.Char(
        related="supply_point_id.zip",
        store=False,
        help="Supply point postal code for display purposes",
    )
    supply_point_town = fields.Char(
        related="supply_point_id.city",
        store=False,
        help="Supply point city for display purposes",
    )
    supply_point_state = fields.Char(
        related="supply_point_id.state_id.name",
        store=False,
        help="Supply point state for display purposes",
    )
    owner_name = fields.Char(
        related="owner_id.firstname",
        store=False,
        help="Owner first name for display purposes",
    )
    owner_surnames = fields.Char(
        related="owner_id.lastname",
        store=False,
        help="Owner last name for display purposes",
    )
    owner_vat = fields.Char(
        related="owner_id.vat",
        store=False,
        help="Owner VAT number for display purposes",
    )

    # Computed methods
    @api.depends("distribution_table_id")
    def _compute_supply_point_filtered_ids(self):
        """
        Compute available supply points for assignment

        Returns supply points of partners subscribed to the project that are not
        already assigned to the current distribution table to prevent duplicates.
        """
        for record in self:
            if not record.distribution_table_id:
                record.supply_point_filtered_ids = self.env[
                    "energy_selfconsumption.supply_point"
                ]
                continue

            # Get all supply points from project inscriptions
            project_supply_points = record.distribution_table_id.selfconsumption_project_id.inscription_ids.mapped(
                "partner_id.supply_ids"
            )

            # Get already assigned supply points in this distribution table
            assigned_supply_points = (
                record.distribution_table_id.supply_point_assignation_ids.mapped(
                    "supply_point_id"
                )
            )

            # Filter out already assigned supply points
            available_supply_points = project_supply_points.filtered(
                lambda sp: sp.id not in assigned_supply_points.ids
            )

            record.supply_point_filtered_ids = available_supply_points

    @api.depends("coefficient", "selfconsumption_project_id.power")
    def _compute_energy_shares(self):
        """
        Calculate energy shares based on project power and coefficient

        Energy shares = Project Power (kW) × Distribution Coefficient
        """
        for record in self:
            if (
                record.selfconsumption_project_id
                and record.selfconsumption_project_id.power
            ):
                record.energy_shares = (
                    record.selfconsumption_project_id.power * record.coefficient
                )
            else:
                record.energy_shares = 0.0

    # Display methods
    def name_get(self):
        """
        Generate display name for the assignation

        Format: ID-CUPS-VAT
        """
        return [
            (
                assignation.id,
                f"{assignation.id}-{assignation.code or 'N/A'}-{assignation.owner_vat or 'N/A'}",
            )
            for assignation in self
        ]

    # Validation constraints
    @api.constrains("coefficient")
    def _check_coefficient_range(self):
        """
        Validate coefficient is within acceptable range

        Raises:
            ValidationError: If coefficient is negative or greater than 1
        """
        for record in self:
            if record.coefficient < MIN_COEFFICIENT_VALUE:
                raise ValidationError(
                    _(
                        "Distribution coefficient cannot be negative. Current value: {coefficient}"
                    ).format(coefficient=record.coefficient)
                )
            if record.coefficient > MAX_COEFFICIENT_VALUE:
                raise ValidationError(
                    _(
                        "Distribution coefficient cannot be greater than 1. Current value: {coefficient}"
                    ).format(coefficient=record.coefficient)
                )

    @api.constrains("supply_point_id", "distribution_table_id")
    def _check_supply_point_project_membership(self):
        """
        Validate that the supply point partner is subscribed to the project

        Raises:
            ValidationError: If partner is not subscribed to the project
        """
        for record in self:
            if not record.supply_point_id or not record.distribution_table_id:
                continue

            # Get all supply points from project inscriptions
            project_inscriptions = self.env[
                "energy_selfconsumption.inscription_selfconsumption"
            ].search(
                [
                    (
                        "selfconsumption_project_id",
                        "=",
                        record.distribution_table_id.selfconsumption_project_id.id,
                    )
                ]
            )

            project_supply_points = project_inscriptions.mapped(
                "partner_id.supply_ids"
            ) + project_inscriptions.mapped("partner_id.owner_supply_ids")
            if record.supply_point_id not in project_supply_points:
                raise ValidationError(
                    _(
                        "The partner of supply point '{supply_point}' is not subscribed to project '{project}'"
                    ).format(
                        supply_point=record.supply_point_id.name
                        or record.supply_point_id.code,
                        project=record.distribution_table_id.selfconsumption_project_id.name,
                    )
                )

    @api.constrains("supply_point_id", "distribution_table_id")
    def _check_unique_supply_point_per_table(self):
        """
        Ensure supply point is not assigned multiple times to the same distribution table

        Raises:
            ValidationError: If supply point is already assigned to the table
        """
        for record in self:
            if not record.supply_point_id or not record.distribution_table_id:
                continue

            existing_assignation = self.search(
                [
                    ("id", "!=", record.id),
                    ("supply_point_id", "=", record.supply_point_id.id),
                    ("distribution_table_id", "=", record.distribution_table_id.id),
                ]
            )

            if existing_assignation:
                raise ValidationError(
                    _(
                        "Supply point '{supply_point}' is already assigned to this distribution table"
                    ).format(
                        supply_point=record.supply_point_id.name
                        or record.supply_point_id.code
                    )
                )

    # Onchange methods
    @api.onchange("coefficient")
    def _onchange_coefficient(self):
        """
        Auto-correct coefficient values to stay within valid range

        - Converts negative values to positive
        - Caps values at maximum of 1.0
        """
        if self.coefficient < MIN_COEFFICIENT_VALUE:
            self.coefficient = abs(self.coefficient)
        if self.coefficient > MAX_COEFFICIENT_VALUE:
            self.coefficient = MAX_COEFFICIENT_VALUE

    # Business logic methods
    def get_inscription(self):
        """
        Get the inscription record associated with this assignation

        Returns:
            inscription: The inscription record linking the partner and supply point to the project
        """
        self.ensure_one()
        return self.env["energy_selfconsumption.inscription_selfconsumption"].search(
            [
                (
                    "selfconsumption_project_id",
                    "=",
                    self.distribution_table_id.selfconsumption_project_id.id,
                ),
                ("supply_point_id", "=", self.supply_point_id.id),
            ],
            limit=1,
        )

    def is_active_assignation(self):
        """
        Check if this assignation belongs to an active distribution table

        Returns:
            bool: True if the distribution table is active, False otherwise
        """
        self.ensure_one()
        return self.distribution_table_state == DISTRIBUTION_STATE_ACTIVE

    def get_coefficient_percentage(self):
        """
        Get coefficient as percentage for display purposes

        Returns:
            float: Coefficient as percentage (0.25 -> 25.0)
        """
        self.ensure_one()
        return self.coefficient * 100

    def validate_coefficient_sum(self):
        """
        Validate that all coefficients in the distribution table sum to 1.0

        Returns:
            bool: True if sum is valid, False otherwise
        """
        self.ensure_one()
        if self.distribution_table_id.type == "fixed":
            return self.distribution_table_id.coefficient_is_valid
        return True  # Hourly tables don't need this validation

    def get_partner_display_name(self):
        """
        Get formatted partner display name for this assignation

        Returns:
            str: Formatted partner name with VAT
        """
        self.ensure_one()
        if self.partner_id:
            vat_info = f" ({self.partner_id.vat})" if self.partner_id.vat else ""
            return f"{self.partner_id.name}{vat_info}"
        return _("No Partner")

    def get_supply_point_display_info(self):
        """
        Get formatted supply point information for display

        Returns:
            dict: Dictionary with formatted supply point information
        """
        self.ensure_one()
        return {
            "code": self.supply_point_code or _("No CUPS"),
            "address": self.supply_point_address or _("No Address"),
            "city": f"{self.supply_point_postalcode or ''} {self.supply_point_town or ''}".strip(),
            "state": self.supply_point_state or _("No State"),
        }
