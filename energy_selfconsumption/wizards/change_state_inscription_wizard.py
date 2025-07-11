import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..config import (
    INSCRIPTION_STATE_ACTIVE,
    INSCRIPTION_STATE_CHANGE,
    INSCRIPTION_STATE_INACTIVE,
)

# Constants for change state inscription wizard
PARTICIPATION_PRECISION = 2
MIN_PARTICIPATION_QUANTITY = 0.0

# State selection values
STATE_VALUES = [
    (INSCRIPTION_STATE_ACTIVE, _("Active")),
    (INSCRIPTION_STATE_INACTIVE, _("Inactive")),
    (INSCRIPTION_STATE_CHANGE, _("Change")),
]

logger = logging.getLogger(__name__)


class ChangeStateInscriptionWizard(models.TransientModel):
    """
    Change State Inscription Wizard

    This wizard allows users to modify the state and participation quantities
    of multiple inscriptions in a self-consumption project.

    Features:
    - Bulk state changes for inscriptions
    - Participation quantity modifications
    - Automatic state transitions based on quantity changes
    - Comprehensive validation and error handling
    - Detailed logging of all changes
    """

    _name = "energy_selfconsumption.change_state_inscription.wizard"
    _description = "Change State Inscription Wizard"

    # Line relationships
    change_state_inscription_lines_wizard_ids = fields.One2many(
        "energy_selfconsumption.change_state_inscription_lines.wizard",
        "change_state_inscription_wizard_id",
        string="Inscription State Changes",
        help="Lines for managing inscription state and participation changes",
    )

    @api.model
    def default_get(self, default_fields):
        """
        Set default values for wizard fields

        Loads selected inscriptions from context and prepares them
        for state and participation quantity modifications.

        Args:
            default_fields: List of field names to get defaults for

        Returns:
            dict: Default values including inscription lines

        Raises:
            ValidationError: If no inscriptions are selected
        """
        defaults = super().default_get(default_fields)

        try:
            # Validate selection
            active_ids = self._get_active_ids_from_context()

            # Prepare inscription lines
            lines = self._prepare_inscription_lines(active_ids)
            defaults["change_state_inscription_lines_wizard_ids"] = lines

            return defaults

        except Exception as e:
            logger.error(f"Error setting default values: {e}")
            raise UserError(_("Error loading inscription data. Please try again."))

    def _get_active_ids_from_context(self):
        """
        Get active IDs from context and validate selection

        Returns:
            list: List of inscription IDs

        Raises:
            ValidationError: If no inscriptions are selected
        """
        active_ids = self.env.context.get("active_ids", [])
        if not active_ids:
            raise ValidationError(_("You must select at least one inscription."))
        return active_ids

    def _prepare_inscription_lines(self, inscription_ids):
        """
        Prepare wizard lines for selected inscriptions

        Args:
            inscription_ids: List of inscription IDs

        Returns:
            list: List of line values for wizard
        """
        lines = []

        for inscription_id in inscription_ids:
            try:
                inscription = self._get_inscription_by_id(inscription_id)
                line_values = self._create_inscription_line_values(inscription)
                lines.append(line_values)
            except Exception as e:
                logger.warning(f"Error processing inscription {inscription_id}: {e}")
                continue

        return lines

    def _get_inscription_by_id(self, inscription_id):
        """
        Get inscription record by ID

        Args:
            inscription_id: ID of the inscription

        Returns:
            inscription: Inscription record

        Raises:
            UserError: If inscription not found
        """
        inscription = self.env[
            "energy_selfconsumption.inscription_selfconsumption"
        ].browse(inscription_id)
        if not inscription.exists():
            raise UserError(
                _("Inscription with ID {id} not found").format(id=inscription_id)
            )
        return inscription

    def _create_inscription_line_values(self, inscription):
        """
        Create line values for an inscription

        Args:
            inscription: Inscription record

        Returns:
            tuple: Line creation values
        """
        # Determine participation quantity based on current state
        participation_quantity = (
            inscription.participation_real_quantity
            if inscription.state == INSCRIPTION_STATE_ACTIVE
            else inscription.participation_assigned_quantity
        )

        return (
            0,
            0,
            {
                "change_state_inscription_wizard_id": self.id,
                "inscription_id": inscription.id,
                "state": inscription.state,
                "participation_real_quantity": participation_quantity,
            },
        )

    def change_state_inscription(self):
        """
        Apply state and participation changes to inscriptions

        Main method that processes all wizard lines and applies the
        specified changes to the corresponding inscriptions.

        Returns:
            bool: True if changes were applied successfully

        Raises:
            UserError: If validation fails or errors occur during processing
        """
        self.ensure_one()

        try:
            # Validate wizard data
            self._validate_wizard_data()

            # Process each line
            changes_count = 0
            for line in self.change_state_inscription_lines_wizard_ids:
                if self._process_inscription_line(line):
                    changes_count += 1

            # Log results
            logger.info(f"Successfully processed {changes_count} inscription changes")

            if changes_count == 0:
                raise UserError(_("No changes were detected to apply."))

            return True

        except Exception as e:
            logger.error(f"Error changing inscription states: {e}")
            if isinstance(e, (UserError, ValidationError)):
                raise
            else:
                raise UserError(_("Error applying changes. Please try again."))

    def _validate_wizard_data(self):
        """
        Validate wizard data before processing

        Raises:
            ValidationError: If validation fails
        """
        if not self.change_state_inscription_lines_wizard_ids:
            raise ValidationError(_("No inscription lines found to process"))

        # Validate each line
        for line in self.change_state_inscription_lines_wizard_ids:
            self._validate_inscription_line(line)

    def _validate_inscription_line(self, line):
        """
        Validate individual inscription line

        Args:
            line: Wizard line to validate

        Raises:
            ValidationError: If line validation fails
        """
        if line.participation_real_quantity < MIN_PARTICIPATION_QUANTITY:
            raise ValidationError(
                _(
                    "Participation quantity cannot be negative for inscription '{inscription}'"
                ).format(inscription=line.inscription_id.name)
            )

    def _process_inscription_line(self, line):
        """
        Process a single inscription line and apply changes

        Args:
            line: Wizard line to process

        Returns:
            bool: True if changes were applied, False if no changes needed
        """
        inscription = line.inscription_id
        changes = {}

        # Check for state change
        if inscription.state != line.state:
            changes["state"] = line.state
            logger.info(
                f"State change for inscription {inscription.id}: {inscription.state} -> {line.state}"
            )

        # Check for participation quantity change
        quantity_change = self._check_participation_quantity_change(inscription, line)
        if quantity_change is not None:
            changes["participation_assigned_quantity"] = quantity_change
            logger.info(
                f"Participation change for inscription {inscription.id}: {quantity_change}"
            )

        # Apply changes if any
        if changes:
            inscription.write(changes)
            return True

        return False

    def _check_participation_quantity_change(self, inscription, line):
        """
        Check if participation quantity needs to be updated

        Args:
            inscription: Inscription record
            line: Wizard line

        Returns:
            float or None: New participation quantity if change needed, None otherwise
        """
        current_quantity = (
            inscription.participation_real_quantity
            if inscription.state == INSCRIPTION_STATE_ACTIVE
            else inscription.participation_assigned_quantity
        )

        new_quantity = line.participation_real_quantity

        # Compare with precision
        if round(current_quantity, PARTICIPATION_PRECISION) != round(
            new_quantity, PARTICIPATION_PRECISION
        ):
            return new_quantity

        return None

    # Utility methods
    def get_wizard_summary(self):
        """
        Get summary information about the wizard

        Returns:
            dict: Summary information
        """
        self.ensure_one()

        total_lines = len(self.change_state_inscription_lines_wizard_ids)
        state_changes = len(
            [
                line
                for line in self.change_state_inscription_lines_wizard_ids
                if line.inscription_id.state != line.state
            ]
        )

        return {
            "total_inscriptions": total_lines,
            "state_changes": state_changes,
            "quantity_changes": total_lines - state_changes,  # Approximate
        }

    def preview_changes(self):
        """
        Preview changes without applying them

        Returns:
            dict: Preview information
        """
        self.ensure_one()

        changes_preview = []

        for line in self.change_state_inscription_lines_wizard_ids:
            inscription = line.inscription_id
            preview_item = {
                "inscription_name": inscription.name,
                "partner_name": inscription.partner_id.name,
                "current_state": inscription.state,
                "new_state": line.state,
                "state_changed": inscription.state != line.state,
                "current_quantity": (
                    inscription.participation_real_quantity
                    if inscription.state == INSCRIPTION_STATE_ACTIVE
                    else inscription.participation_assigned_quantity
                ),
                "new_quantity": line.participation_real_quantity,
            }

            preview_item["quantity_changed"] = round(
                preview_item["current_quantity"], PARTICIPATION_PRECISION
            ) != round(preview_item["new_quantity"], PARTICIPATION_PRECISION)

            changes_preview.append(preview_item)

        return {
            "changes_preview": changes_preview,
            "total_changes": len(
                [
                    item
                    for item in changes_preview
                    if item["state_changed"] or item["quantity_changed"]
                ]
            ),
        }


class ChangeStateInscriptionLinesWizard(models.TransientModel):
    """
    Change State Inscription Lines Wizard

    Individual line for managing inscription state and participation
    quantity changes in the change state wizard.
    """

    _name = "energy_selfconsumption.change_state_inscription_lines.wizard"
    _description = "Change State Inscription Lines Wizard"

    # Parent wizard relationship
    change_state_inscription_wizard_id = fields.Many2one(
        "energy_selfconsumption.change_state_inscription.wizard",
        string="State Change Wizard",
        required=True,
        ondelete="cascade",
        help="Parent wizard for inscription state changes",
    )

    # Inscription information
    inscription_id = fields.Many2one(
        "energy_selfconsumption.inscription_selfconsumption",
        string="Inscription",
        required=True,
        help="Inscription record being modified",
    )

    state = fields.Selection(
        STATE_VALUES,
        required=True,
        string="New State",
        help="New state for the inscription",
    )

    participation_real_quantity = fields.Float(
        string="Participation Quantity",
        required=True,
        help="New participation quantity for the inscription",
    )

    # Computed fields for display
    current_state = fields.Selection(
        related="inscription_id.state",
        string="Current State",
        readonly=True,
        help="Current state of the inscription",
    )

    partner_name = fields.Char(
        related="inscription_id.partner_id.name",
        string="Partner",
        readonly=True,
        help="Partner associated with the inscription",
    )

    # Validation constraints
    @api.constrains("participation_real_quantity")
    def _check_participation_quantity(self):
        """
        Validate participation quantity

        Raises:
            ValidationError: If participation quantity is invalid
        """
        for record in self:
            if record.participation_real_quantity < MIN_PARTICIPATION_QUANTITY:
                raise ValidationError(
                    _(
                        "Participation quantity cannot be negative for inscription '{inscription}'"
                    ).format(inscription=record.inscription_id.name)
                )

    # Onchange methods
    @api.onchange("participation_real_quantity")
    def _onchange_participation_real_quantity(self):
        """
        Auto-adjust state based on participation quantity changes

        Automatically sets the state to 'change' when participation quantity
        is modified from the original value, and back to 'active' when restored.
        """
        if not self.inscription_id:
            return

        original_quantity = self.inscription_id.participation_real_quantity
        current_quantity = self.participation_real_quantity

        # Check if quantity changed from original
        quantity_changed = round(current_quantity, PARTICIPATION_PRECISION) != round(
            original_quantity, PARTICIPATION_PRECISION
        )

        # Auto-adjust state based on quantity change
        if quantity_changed and self.state == INSCRIPTION_STATE_ACTIVE:
            self.state = INSCRIPTION_STATE_CHANGE
        elif not quantity_changed and self.state == INSCRIPTION_STATE_CHANGE:
            self.state = INSCRIPTION_STATE_ACTIVE

    # Utility methods
    def get_line_summary(self):
        """
        Get summary information for this line

        Returns:
            dict: Line summary information
        """
        self.ensure_one()

        return {
            "inscription_name": self.inscription_id.name,
            "partner_name": self.inscription_id.partner_id.name,
            "current_state": self.inscription_id.state,
            "new_state": self.state,
            "participation_quantity": self.participation_real_quantity,
            "state_changed": self.inscription_id.state != self.state,
            "state_display": dict(STATE_VALUES).get(self.state, "Unknown"),
        }
