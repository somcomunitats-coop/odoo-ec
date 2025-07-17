from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..config import (
    INSCRIPTION_STATE_ACTIVE,
    INSCRIPTION_STATE_CANCELLED,
    INSCRIPTION_STATE_CHANGE,
    INSCRIPTION_STATE_DEFAULT_VALUE,
    INSCRIPTION_STATE_INACTIVE,
    INSCRIPTION_STATE_VALUES,
)


class Inscription(models.Model):
    """
    Self-consumption Project Inscription Model

    This model manages inscriptions for self-consumption energy projects,
    including:
    - Partner registration and participation management
    - Supply point association and validation
    - Participation quantity tracking (requested, assigned, actual)
    - State management for inscription lifecycle
    - Integration with energy project base functionality
    - Mandate and acceptance tracking
    """

    _name = "energy_selfconsumption.inscription_selfconsumption"
    _inherits = {
        "energy_project.inscription": "inscription_id",
    }
    _description = "Inscriptions for a self-consumption"

    # Core relationship fields
    inscription_id = fields.Many2one(
        "energy_project.inscription",
        required=True,
        ondelete="cascade",
        help="Base inscription record from energy project module",
    )
    selfconsumption_project_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption",
        required=True,
        ondelete="restrict",
        string="Self-consumption Energy Project",
        check_company=True,
        help="Self-consumption project this inscription belongs to",
    )
    supply_point_id = fields.Many2one(
        "energy_selfconsumption.supply_point",
        required=True,
        help="Supply point associated with this inscription",
    )

    # Participation management
    participation_id = fields.Many2one(
        comodel_name="energy_selfconsumptions.participation",
        string="Participation",
        help="Participation option selected for this inscription",
    )
    participation_quantity = fields.Float(
        string="Requested participation",
        related="participation_id.quantity",
        help="Originally requested participation quantity",
    )
    participation_assigned_quantity = fields.Float(
        string="Agreed participation",
        default=lambda self: self.participation_id.quantity
        if self.participation_id
        else 0.0,
        help="Participation quantity agreed upon during registration",
    )
    participation_real_quantity = fields.Float(
        string="Actual participation",
        default=lambda self: self.participation_id.quantity
        if self.participation_id
        else 0.0,
        help="Current actual participation quantity in the project",
    )

    # Energy consumption tracking
    annual_electricity_use = fields.Float(
        string="Annual electricity use",
        help="Estimated annual electricity consumption in kWh",
    )

    # State and status management
    state = fields.Selection(
        string="Status",
        selection=INSCRIPTION_STATE_VALUES,
        default=INSCRIPTION_STATE_DEFAULT_VALUE,
        help="Current status of the inscription",
    )
    accept = fields.Boolean(string="I accept bank wire transfer")
    member = fields.Boolean(string="Member/Non-Member")

    # Related information fields (for easy access and display)
    owner_id = fields.Many2one(
        related="supply_point_id.owner_id",
        string="Owner",
        help="Owner of the supply point",
    )
    code = fields.Char(
        string="CUPS",
        related="supply_point_id.code",
        help="CUPS code of the associated supply point",
    )
    used_in_selfconsumption = fields.Selection(
        string="Used in selfconsumption",
        related="supply_point_id.used_in_selfconsumption",
        help="Indicates if the supply point is used in self-consumption",
    )
    vulnerability_situation = fields.Selection(
        string="Vulnerability situation",
        related="supply_point_id.owner_id.vulnerability_situation",
        help="Vulnerability situation of the supply point owner",
    )

    # Onchange methods
    @api.onchange("participation_assigned_quantity")
    def _onchange_participation_assigned_quantity(self):
        """
        Handle changes in assigned participation quantity

        When the assigned quantity differs from the original quantity
        and the inscription is active, mark it as requiring change.
        """
        if (
            self.participation_assigned_quantity != self.participation_quantity
            and self.state == INSCRIPTION_STATE_ACTIVE
        ):
            self.state = INSCRIPTION_STATE_CHANGE

    # Validation constraints
    @api.constrains("project_id", "partner_id", "supply_point_id")
    def _check_unique_partner_supply_point(self):
        """
        Ensure unique combination of partner and supply point per project

        Raises:
            ValidationError: If partner is already registered with the same supply point
        """
        for record in self:
            existing_inscription = self.search(
                [
                    ("id", "!=", record.id),
                    ("project_id", "=", record.project_id.id),
                    ("partner_id", "=", record.partner_id.id),
                    ("supply_point_id", "=", record.supply_point_id.id),
                ]
            )

            if existing_inscription:
                raise ValidationError(
                    _(
                        "Partner '{partner}' is already registered in project '{project}' with supply point '{cups}'"
                    ).format(
                        partner=record.partner_id.name,
                        project=record.project_id.name,
                        cups=record.supply_point_id.code or record.supply_point_id.name,
                    )
                )

    @api.constrains("participation_assigned_quantity", "participation_real_quantity")
    def _check_participation_quantities(self):
        """
        Validate participation quantities are positive

        Raises:
            ValidationError: If quantities are negative
        """
        for record in self:
            if record.participation_assigned_quantity < 0:
                raise ValidationError(
                    _(
                        "Assigned participation quantity cannot be negative: {quantity}"
                    ).format(quantity=record.participation_assigned_quantity)
                )
            if record.participation_real_quantity < 0:
                raise ValidationError(
                    _(
                        "Real participation quantity cannot be negative: {quantity}"
                    ).format(quantity=record.participation_real_quantity)
                )

    @api.constrains("annual_electricity_use")
    def _check_annual_electricity_use(self):
        """
        Validate annual electricity use is reasonable

        Raises:
            ValidationError: If value is negative
        """
        for record in self:
            if record.annual_electricity_use and record.annual_electricity_use < 0:
                raise ValidationError(
                    _("Annual electricity use cannot be negative: {value} kWh").format(
                        value=record.annual_electricity_use
                    )
                )

    # Action methods
    def create_participant_table(self):
        """
        Open wizard to create distribution table for participants

        Returns:
            dict: Action dictionary for opening the wizard
        """
        ctx = self.env.context.copy()
        action = self.env.ref(
            "energy_selfconsumption.create_distribution_table_wizard_action"
        ).read()[0]
        action["context"] = ctx
        return action

    def change_state_inscription(self):
        """
        Open wizard to change inscription state

        Returns:
            dict: Action dictionary for opening the wizard
        """
        ctx = self.env.context.copy()
        action = self.env.ref(
            "energy_selfconsumption.change_state_inscription_wizard_action"
        ).read()[0]
        action["context"] = ctx
        return action

    # CRUD methods
    def unlink(self):
        """
        Delete inscription records and their base inscription

        Returns:
            bool: True if successful
        """
        for inscription in self:
            inscription.inscription_id.unlink()
        return super().unlink()

    # Business logic methods
    def activate_inscription(self):
        """
        Activate the inscription and update participation quantities

        Sets the inscription to active state and ensures participation
        quantities are properly synchronized.
        """
        self.ensure_one()
        self.write(
            {
                "state": INSCRIPTION_STATE_ACTIVE,
                "participation_real_quantity": self.participation_assigned_quantity,
            }
        )

    def deactivate_inscription(self):
        """
        Deactivate the inscription

        Sets the inscription to inactive state.
        """
        self.ensure_one()
        self.write({"state": INSCRIPTION_STATE_INACTIVE})

    def cancel_inscription(self):
        """
        Cancel the inscription

        Sets the inscription to cancelled state.
        """
        self.ensure_one()
        self.write({"state": INSCRIPTION_STATE_CANCELLED})

    def mark_for_change(self):
        """
        Mark inscription as requiring changes

        Used when participation quantities or other details need to be updated.
        """
        self.ensure_one()
        self.write({"state": INSCRIPTION_STATE_CHANGE})

    def is_active(self):
        """
        Check if inscription is in active state

        Returns:
            bool: True if active, False otherwise
        """
        self.ensure_one()
        return self.state == INSCRIPTION_STATE_ACTIVE

    def is_editable(self):
        """
        Check if inscription can be edited

        Returns:
            bool: True if editable, False otherwise
        """
        self.ensure_one()
        return self.state in (INSCRIPTION_STATE_INACTIVE, INSCRIPTION_STATE_CHANGE)

    def get_participation_percentage(self):
        """
        Calculate participation as percentage of total project power

        Returns:
            float: Participation percentage
        """
        self.ensure_one()
        if (
            not self.selfconsumption_project_id.power
            or not self.participation_real_quantity
        ):
            return 0.0
        return (
            self.participation_real_quantity / self.selfconsumption_project_id.power
        ) * 100

    def get_display_name(self):
        """
        Get formatted display name for the inscription

        Returns:
            str: Formatted name with partner and CUPS
        """
        self.ensure_one()
        partner_name = self.partner_id.name if self.partner_id else _("No Partner")
        cups_code = self.code if self.code else _("No CUPS")
        return f"{partner_name} - {cups_code}"

    def validate_for_distribution_table(self):
        """
        Validate inscription is ready for distribution table assignment

        Returns:
            bool: True if valid, False otherwise

        Raises:
            ValidationError: If validation fails with specific error
        """
        self.ensure_one()

        if not self.is_active():
            raise ValidationError(
                _("Inscription must be active to be included in distribution table")
            )

        if not self.supply_point_id:
            raise ValidationError(_("Inscription must have a valid supply point"))

        if (
            not self.participation_real_quantity
            or self.participation_real_quantity <= 0
        ):
            raise ValidationError(
                _("Inscription must have a positive participation quantity")
            )

        return True

    def get_energy_share_info(self):
        """
        Get energy share information for this inscription

        Returns:
            dict: Dictionary with energy share details
        """
        self.ensure_one()
        total_power = self.selfconsumption_project_id.power or 0.0
        participation = self.participation_real_quantity or 0.0

        return {
            "participation_kw": participation,
            "total_power_kw": total_power,
            "percentage": self.get_participation_percentage(),
            "annual_consumption_kwh": self.annual_electricity_use or 0.0,
        }
