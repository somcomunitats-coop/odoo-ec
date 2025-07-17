import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..config import DISTRIBUTION_TYPE_FIXED, MIN_POWER_VALUE

# Constants for distribution table wizard
DISTRIBUTE_EXCESS_YES = "yes"
DISTRIBUTE_EXCESS_NO = "no"
DISTRIBUTE_TYPE_PROPORTIONAL = "proportional"
DISTRIBUTE_TYPE_LINEAR = "linear"
PERCENTAGE_MULTIPLIER = 100

# Selection values
TYPE_VALUES = [
    (DISTRIBUTION_TYPE_FIXED, _("Fixed")),
    # (DISTRIBUTION_TYPE_HOURLY, _("Variable hourly"))  # Future implementation
]

DISTRIBUTE_EXCESS_VALUES = [
    (DISTRIBUTE_EXCESS_YES, _("Yes")),
    (DISTRIBUTE_EXCESS_NO, _("No")),
]

TYPE_DISTRIBUTE_EXCESS_VALUES = [
    (DISTRIBUTE_TYPE_PROPORTIONAL, _("Proportional")),
    (DISTRIBUTE_TYPE_LINEAR, _("Linear")),
]

logger = logging.getLogger(__name__)


class CreateDistributionTableWizard(models.TransientModel):
    """
    Create Distribution Table Wizard

    This wizard handles the creation of distribution tables for self-consumption
    projects, including:
    - Power distribution calculation and validation
    - Coefficient calculation for participants
    - Excess power distribution strategies
    - Supply point assignation creation
    - Integration with inscription data

    Features:
    - Fixed and hourly distribution types
    - Proportional and linear excess distribution
    - Automatic coefficient calculation
    - Validation of power limits
    - Bulk assignation creation
    """

    _name = "energy_selfconsumption.create_distribution_table.wizard"
    _description = "Service to generate distribution table"

    # Power distribution fields
    percentage_of_distributed_power = fields.Float(
        string="Percentage of distributed power",
        readonly=True,
        help="Percentage of project power that will be distributed",
    )
    distributed_power = fields.Float(
        string="Distributed power",
        readonly=True,
        help="Total power to be distributed among participants (kW)",
    )
    max_distributed_power = fields.Float(
        string="Max distributed power",
        readonly=True,
        help="Maximum power available for distribution (kW)",
    )

    # Distribution configuration fields
    type = fields.Selection(
        TYPE_VALUES,
        default=DISTRIBUTION_TYPE_FIXED,
        required=True,
        string="Modality",
        help="Type of distribution table to create",
    )
    distribute_excess = fields.Selection(
        DISTRIBUTE_EXCESS_VALUES,
        default=DISTRIBUTE_EXCESS_NO,
        required=True,
        string="Distribute excess",
        help="Whether to distribute excess power among participants",
    )
    type_distribute_excess = fields.Selection(
        TYPE_DISTRIBUTE_EXCESS_VALUES,
        default=DISTRIBUTE_TYPE_PROPORTIONAL,
        required=True,
        string="Type distribute excess",
        help="Method for distributing excess power",
    )

    # Onchange methods
    @api.onchange("distributed_power")
    def _onchange_distributed_power(self):
        """
        Auto-enable excess distribution when power exceeds limits

        Automatically sets distribute_excess to 'yes' when the distributed
        power exceeds the maximum or is invalid.
        """
        if (
            self.distributed_power > self.max_distributed_power
            or self.distributed_power <= MIN_POWER_VALUE
        ):
            self.distribute_excess = DISTRIBUTE_EXCESS_YES

    # Default value methods
    @api.model
    def default_get(self, default_fields):
        """
        Set default values based on selected inscriptions

        Calculates power distribution values from the selected inscriptions
        and validates the project configuration.

        Args:
            default_fields: List of field names to get defaults for

        Returns:
            dict: Default values

        Raises:
            ValidationError: If no inscriptions selected or invalid project
        """
        defaults = super().default_get(default_fields)

        # Validate selection
        active_ids = self.env.context.get("active_ids", [])
        if not active_ids:
            raise ValidationError(_("You must select at least one inscription"))

        # Get inscriptions and project
        inscriptions = self.env[
            "energy_selfconsumption.inscription_selfconsumption"
        ].browse(active_ids)
        project = self._get_project_from_inscriptions(inscriptions)

        # Validate project power
        if project.power <= MIN_POWER_VALUE:
            raise ValidationError(
                _(
                    "Project '{project}' must have power greater than {min_power} kW"
                ).format(project=project.name, min_power=MIN_POWER_VALUE)
            )

        # Calculate power distribution
        defaults.update(self._calculate_power_distribution(inscriptions, project))

        return defaults

    def _get_project_from_inscriptions(self, inscriptions):
        """
        Get self-consumption project from inscriptions

        Args:
            inscriptions: Inscription recordset

        Returns:
            selfconsumption: Self-consumption project

        Raises:
            ValidationError: If project not found
        """
        if not inscriptions:
            raise ValidationError(_("No inscriptions provided"))

        first_inscription = inscriptions[0]
        project = (
            self.env["energy_selfconsumption.selfconsumption"]
            .sudo()
            .search([("project_id", "=", first_inscription.project_id.id)], limit=1)
        )

        if not project:
            raise ValidationError(
                _(
                    "Self-consumption project not found for inscription project '{project}'"
                ).format(project=first_inscription.project_id.name)
            )

        return project

    def _calculate_power_distribution(self, inscriptions, project):
        """
        Calculate power distribution values

        Args:
            inscriptions: Inscription recordset
            project: Self-consumption project

        Returns:
            dict: Power distribution values
        """
        max_power = project.power
        distributed_power = sum(
            inscription.participation_real_quantity
            if inscription.state == "active"
            else inscription.participation_assigned_quantity
            for inscription in inscriptions
        )

        percentage = (
            (distributed_power / max_power * PERCENTAGE_MULTIPLIER)
            if max_power > 0
            else 0
        )

        return {
            "max_distributed_power": max_power,
            "distributed_power": distributed_power,
            "percentage_of_distributed_power": percentage,
        }

    # Validation methods
    def _validate_wizard_data(self):
        """
        Validate wizard data before creating distribution table

        Raises:
            ValidationError: If validation fails
        """
        if self.max_distributed_power <= MIN_POWER_VALUE:
            raise ValidationError(
                _(
                    "Maximum distributed power must be greater than {min_power} kW"
                ).format(min_power=MIN_POWER_VALUE)
            )

        if self.distributed_power < MIN_POWER_VALUE:
            raise ValidationError(
                _("Distributed power must be greater than {min_power} kW").format(
                    min_power=MIN_POWER_VALUE
                )
            )

    def _validate_inscriptions(self, inscriptions):
        """
        Validate inscriptions for distribution table creation

        Args:
            inscriptions: Inscription recordset

        Raises:
            ValidationError: If validation fails
        """
        if not inscriptions:
            raise ValidationError(_("No inscriptions selected"))

        # Check all inscriptions belong to same project
        projects = inscriptions.mapped("project_id")
        if len(projects) > 1:
            raise ValidationError(_("All inscriptions must belong to the same project"))

        # Check inscriptions have supply points
        missing_supply_points = inscriptions.filtered(lambda i: not i.supply_point_id)
        if missing_supply_points:
            partner_names = missing_supply_points.mapped("partner_id.name")
            raise ValidationError(
                _(
                    "The following inscriptions are missing supply points:\n{partners}"
                ).format(partners="\n".join(f"- {name}" for name in partner_names))
            )

    # Main action method
    def create_distribution_table(self):
        """
        Create distribution table with supply point assignations

        Main method that creates the distribution table and all associated
        supply point assignations with calculated coefficients.

        Returns:
            dict: Action to view created distribution tables
        """
        self.ensure_one()

        # Validate wizard data
        self._validate_wizard_data()

        # Get inscriptions and validate
        active_ids = self.env.context.get("active_ids", [])
        inscriptions = self.env[
            "energy_selfconsumption.inscription_selfconsumption"
        ].browse(active_ids)
        self._validate_inscriptions(inscriptions)

        # Get project
        project = self._get_project_from_inscriptions(inscriptions)

        # Create distribution table
        distribution_table = self._create_distribution_table(project)

        # Create supply point assignations
        self._create_supply_point_assignations(inscriptions, distribution_table)

        # Return view action
        return project.get_distribution_tables_view()

    def _create_distribution_table(self, project):
        """
        Create the distribution table record

        Args:
            project: Self-consumption project

        Returns:
            distribution_table: Created distribution table
        """
        return self.env["energy_selfconsumption.distribution_table"].create(
            {
                "selfconsumption_project_id": project.id,
                "type": self.type,
            }
        )

    def _create_supply_point_assignations(self, inscriptions, distribution_table):
        """
        Create supply point assignations for all inscriptions

        Args:
            inscriptions: Inscription recordset
            distribution_table: Distribution table record
        """
        assignation_values = []
        inscription_count = len(inscriptions)

        for inscription in inscriptions:
            values = self._get_supply_point_assignation_values(
                inscription, distribution_table, inscription_count
            )
            assignation_values.append(values)

        # Use bulk creation service
        # self.env[
        #     "energy_selfconsumption.create_distribution_table"
        # ].create_energy_selfconsumption_supply_point_assignation_sql(
        #     assignation_values, distribution_table
        # )
        self.env[
            "energy_selfconsumption.create_distribution_table"
        ].create_energy_selfconsumption_supply_point_assignation(
            assignation_values, distribution_table
        )

    def _get_supply_point_assignation_values(
        self, inscription, distribution_table, inscription_count
    ):
        """
        Calculate supply point assignation values for an inscription

        Calculates the coefficient and energy shares for a specific inscription
        based on the distribution configuration and excess handling.

        Args:
            inscription: Inscription record
            distribution_table: Distribution table record
            inscription_count: Total number of inscriptions

        Returns:
            dict: Supply point assignation values
        """
        # Get base coefficient
        base_coefficient = self._get_base_coefficient(inscription)

        # Apply excess distribution if enabled
        final_coefficient = self._apply_excess_distribution(
            base_coefficient, inscription, inscription_count
        )

        # Normalize coefficient
        normalized_coefficient = final_coefficient / self.max_distributed_power

        # Calculate energy shares
        energy_shares = (
            distribution_table.selfconsumption_project_id.power * normalized_coefficient
        )

        return {
            "distribution_table_id": distribution_table.id,
            "supply_point_id": inscription.supply_point_id.id,
            "coefficient": normalized_coefficient,
            "energy_shares": energy_shares,
            "company_id": distribution_table.company_id.id,
        }

    def _get_base_coefficient(self, inscription):
        """
        Get base coefficient for an inscription

        Args:
            inscription: Inscription record

        Returns:
            float: Base coefficient value
        """
        if inscription.state == "active":
            return inscription.participation_real_quantity
        else:
            return inscription.participation_assigned_quantity

    def _apply_excess_distribution(
        self, base_coefficient, inscription, inscription_count
    ):
        """
        Apply excess distribution to coefficient

        Args:
            base_coefficient: Base coefficient value
            inscription: Inscription record
            inscription_count: Total number of inscriptions

        Returns:
            float: Adjusted coefficient
        """
        if self.distribute_excess != DISTRIBUTE_EXCESS_YES:
            return base_coefficient

        excess_amount = abs(self.max_distributed_power - self.distributed_power)

        if self.distributed_power < self.max_distributed_power:
            # Distribute positive excess
            return base_coefficient + self._calculate_excess_share(
                excess_amount, inscription, inscription_count, positive=True
            )
        elif self.distributed_power > self.max_distributed_power:
            # Distribute negative excess (reduction)
            return base_coefficient - self._calculate_excess_share(
                excess_amount, inscription, inscription_count, positive=False
            )
        else:
            return base_coefficient

    def _calculate_excess_share(
        self, excess_amount, inscription, inscription_count, positive=True
    ):
        """
        Calculate excess share for an inscription

        Args:
            excess_amount: Amount of excess to distribute
            inscription: Inscription record
            inscription_count: Total number of inscriptions
            positive: Whether this is positive excess (True) or reduction (False)

        Returns:
            float: Excess share for this inscription
        """
        if self.type_distribute_excess == DISTRIBUTE_TYPE_PROPORTIONAL:
            # Proportional distribution based on participation
            inscription_participation = self._get_base_coefficient(inscription)
            return excess_amount * (inscription_participation / self.distributed_power)
        else:
            # Linear distribution (equal shares)
            return excess_amount / inscription_count

    # Utility methods
    def get_wizard_summary(self):
        """
        Get summary information about the wizard configuration

        Returns:
            dict: Summary information
        """
        self.ensure_one()

        active_ids = self.env.context.get("active_ids", [])

        return {
            "inscription_count": len(active_ids),
            "distribution_type": self.type,
            "max_power": self.max_distributed_power,
            "distributed_power": self.distributed_power,
            "power_percentage": self.percentage_of_distributed_power,
            "has_excess": self.distributed_power != self.max_distributed_power,
            "distribute_excess": self.distribute_excess == DISTRIBUTE_EXCESS_YES,
            "excess_type": self.type_distribute_excess,
        }

    def preview_distribution(self):
        """
        Preview distribution without creating the table

        Returns:
            dict: Distribution preview information
        """
        self.ensure_one()

        try:
            self._validate_wizard_data()

            active_ids = self.env.context.get("active_ids", [])
            inscriptions = self.env[
                "energy_selfconsumption.inscription_selfconsumption"
            ].browse(active_ids)
            self._validate_inscriptions(inscriptions)

            # Calculate preview data
            preview_data = []
            inscription_count = len(inscriptions)

            for inscription in inscriptions:
                base_coeff = self._get_base_coefficient(inscription)
                final_coeff = self._apply_excess_distribution(
                    base_coeff, inscription, inscription_count
                )
                normalized_coeff = final_coeff / self.max_distributed_power

                preview_data.append(
                    {
                        "partner_name": inscription.partner_id.name,
                        "supply_point_code": inscription.supply_point_id.code,
                        "base_participation": base_coeff,
                        "final_participation": final_coeff,
                        "coefficient": normalized_coeff,
                        "energy_share_percentage": normalized_coeff
                        * PERCENTAGE_MULTIPLIER,
                    }
                )

            return {
                "valid_preview": True,
                "participants": preview_data,
                "total_coefficient": sum(p["coefficient"] for p in preview_data),
            }

        except ValidationError as e:
            return {
                "valid_preview": False,
                "error_message": str(e),
            }
