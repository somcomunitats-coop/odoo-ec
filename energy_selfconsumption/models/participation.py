from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..config import DEFAULT_PARTICIPATIONS, MAX_POWER_VALUE, MIN_POWER_VALUE


class Participation(models.Model):
    """
    Participation Model for Self-consumption Projects

    This model manages participation options for self-consumption energy projects,
    including:
    - Participation quantity definitions
    - Project-specific participation options
    - Validation of participation values
    - Display and selection functionality
    """

    _name = "energy_selfconsumptions.participation"
    _description = "Participation inscription"
    _order = "quantity asc, name"

    # Basic fields
    name = fields.Char(
        string="Description",
        required=True,
        help="Description of the participation option (e.g., '1.0 kW', '2.5 kW')",
    )
    quantity = fields.Float(
        string="Quantity",
        required=True,
        digits=(10, 3),
        help="Participation quantity in kW",
    )

    # Project relationship
    project_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption",
        required=True,
        ondelete="cascade",
        help="Self-consumption project this participation belongs to",
    )

    # Additional information fields
    active = fields.Boolean(
        default=True,
        help="If unchecked, this participation option will be hidden from selection",
    )
    sequence = fields.Integer(
        default=10, help="Sequence for ordering participation options"
    )

    # Computed fields
    inscription_count = fields.Integer(
        compute="_compute_inscription_count",
        help="Number of inscriptions using this participation",
    )

    # SQL constraints
    _sql_constraints = [
        (
            "unique_name_project",
            "unique(name, project_id)",
            _("Participation name must be unique per project."),
        ),
        (
            "positive_quantity",
            "check(quantity > 0)",
            _("Participation quantity must be positive."),
        ),
    ]

    # Computed methods
    @api.depends("project_id.inscription_ids.participation_id")
    def _compute_inscription_count(self):
        """
        Calculate number of inscriptions using this participation
        """
        for record in self:
            record.inscription_count = len(
                record.project_id.inscription_ids.filtered(
                    lambda i: i.participation_id == record
                )
            )

    # Validation constraints
    @api.constrains("quantity")
    def _check_quantity_range(self):
        """
        Validate participation quantity is within acceptable range

        Raises:
            ValidationError: If quantity is outside valid range
        """
        for record in self:
            if record.quantity < MIN_POWER_VALUE:
                raise ValidationError(
                    _(
                        "Participation quantity cannot be less than {min_value} kW"
                    ).format(min_value=MIN_POWER_VALUE)
                )
            if record.quantity > MAX_POWER_VALUE:
                raise ValidationError(
                    _("Participation quantity cannot exceed {max_value} kW").format(
                        max_value=MAX_POWER_VALUE
                    )
                )

    @api.constrains("name")
    def _check_name_not_empty(self):
        """
        Validate participation name is not empty

        Raises:
            ValidationError: If name is empty or only whitespace
        """
        for record in self:
            if not record.name or not record.name.strip():
                raise ValidationError(_("Participation description cannot be empty"))

    # Display methods
    def name_get(self):
        """
        Generate display name for participation

        Format: "Description (Quantity kW)"
        """
        return [
            (participation.id, f"{participation.name} ({participation.quantity} kW)")
            for participation in self
        ]

    # Business logic methods
    def is_available_for_inscription(self):
        """
        Check if participation is available for new inscriptions

        Returns:
            bool: True if available, False otherwise
        """
        self.ensure_one()
        return self.active and self.project_id.state in (
            "inscription",
            "activation",
            "active",
        )

    def get_total_assigned_power(self):
        """
        Get total power assigned through inscriptions using this participation

        Returns:
            float: Total assigned power in kW
        """
        self.ensure_one()
        inscriptions = self.project_id.inscription_ids.filtered(
            lambda i: i.participation_id == self and i.is_active()
        )
        return sum(inscriptions.mapped("participation_real_quantity"))

    def get_available_quantity(self):
        """
        Get available quantity for new inscriptions

        Calculates how much of this participation type is still available
        based on project capacity and current assignments.

        Returns:
            float: Available quantity in kW
        """
        self.ensure_one()

        if not self.project_id.power:
            return 0.0

        total_assigned = self.get_total_assigned_power()
        project_capacity = self.project_id.power

        # Calculate remaining capacity
        remaining_capacity = project_capacity - total_assigned

        # Return the minimum between remaining capacity and this participation quantity
        return min(remaining_capacity, self.quantity) if remaining_capacity > 0 else 0.0

    def can_be_deleted(self):
        """
        Check if participation can be safely deleted

        Returns:
            bool: True if can be deleted, False otherwise
        """
        self.ensure_one()
        return self.inscription_count == 0

    def get_usage_statistics(self):
        """
        Get usage statistics for this participation

        Returns:
            dict: Statistics about participation usage
        """
        self.ensure_one()

        inscriptions = self.project_id.inscription_ids.filtered(
            lambda i: i.participation_id == self
        )

        active_inscriptions = inscriptions.filtered(lambda i: i.is_active())

        return {
            "total_inscriptions": len(inscriptions),
            "active_inscriptions": len(active_inscriptions),
            "total_assigned_power": self.get_total_assigned_power(),
            "available_quantity": self.get_available_quantity(),
            "utilization_percentage": (
                (self.get_total_assigned_power() / self.quantity * 100)
                if self.quantity > 0
                else 0
            ),
        }

    # CRUD methods
    def unlink(self):
        """
        Override unlink to prevent deletion if participation is in use

        Returns:
            bool: True if successful

        Raises:
            ValidationError: If participation is in use
        """
        for record in self:
            if not record.can_be_deleted():
                raise ValidationError(
                    _(
                        "Cannot delete participation '{name}' because it is used by {count} inscriptions"
                    ).format(name=record.name, count=record.inscription_count)
                )
        return super().unlink()

    # Utility methods
    @api.model
    def create_default_participations(self, project_id, participation_list=None):
        """
        Create default participation options for a project

        Args:
            project_id (int): Project ID to create participations for
            participation_list (list): List of participation dictionaries

        Returns:
            recordset: Created participation records
        """
        if not participation_list:
            participation_list = DEFAULT_PARTICIPATIONS

        participations = []
        for participation_data in participation_list:
            participations.append(
                {
                    "name": participation_data["name"],
                    "quantity": participation_data["quantity"],
                    "project_id": project_id,
                }
            )

        return self.create(participations)

    def toggle_active(self):
        """
        Toggle active state of participation
        """
        for record in self:
            record.active = not record.active
