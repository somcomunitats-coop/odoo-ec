import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..config import (
    INSCRIPTION_STATE_ACTIVE,
    INSCRIPTION_STATE_CANCELLED,
    INSCRIPTION_STATE_CHANGE,
    INSCRIPTION_STATE_INACTIVE,
    INSCRIPTION_STATE_VALUES,
)

# Constants for change distribution table wizard
WIZARD_STATE_OLD = "old"
WIZARD_STATE_NEW = "new"
WIZARD_STATE_DELETE = "delete"
WIZARD_STATE_CHANGE = "change"

WIZARD_STATE_VALUES = [
    (WIZARD_STATE_OLD, _("Old")),
    (WIZARD_STATE_NEW, _("New")),
    (WIZARD_STATE_DELETE, _("Delete")),
    (WIZARD_STATE_CHANGE, _("Change")),
]

logger = logging.getLogger(__name__)


class ChangeDistributionTableImportWizard(models.TransientModel):
    """
    Change Distribution Table Import Wizard

    This wizard manages the process of changing distribution tables by handling
    inscription state transitions and participation quantity modifications.

    Features:
    - Multi-step wizard interface
    - Inscription state management
    - Participation quantity tracking
    - Distribution table creation integration
    - Comprehensive validation and error handling
    """

    _name = "change.distribution.table.import.wizard"
    _description = "Change Distribution Table Import Wizard"

    # Line relationships
    change_distribution_table_import_line_wizard_ids = fields.One2many(
        "change.distribution.table.import.line.wizard",
        "change_distribution_table_import_wizard_id",
        string="Distribution Change Lines",
        help="Lines for managing distribution table changes",
    )

    change_distribution_table_import_line_wizard_news_ids = fields.One2many(
        "change.distribution.table.import.line.wizard",
        "change_distribution_table_import_wizard_id",
        string="New Distribution Lines",
        domain=[
            ("state", "in", [INSCRIPTION_STATE_INACTIVE, INSCRIPTION_STATE_CANCELLED])
        ],
        help="Lines for new inscriptions to be added",
    )

    change_distribution_table_import_line_wizard_views_ids = fields.One2many(
        "change.distribution.table.import.line.wizard",
        string="Current View Lines",
        compute="_compute_change_distribution_table_import_line_wizard_ids",
        help="Filtered lines based on current wizard state",
    )

    # Wizard state
    state = fields.Selection(
        WIZARD_STATE_VALUES,
        required=True,
        string="Wizard Step",
        default=WIZARD_STATE_OLD,
        help="Current step in the distribution table change process",
    )

    @api.model
    def default_get(self, default_fields):
        """
        Set default values for wizard fields

        Loads all inscriptions from the project and categorizes them
        by their current state for the wizard workflow.

        Args:
            default_fields: List of field names to get defaults for

        Returns:
            dict: Default values including inscription lines
        """
        defaults = super().default_get(default_fields)

        try:
            project_id = self._get_project_id_from_context()

            # Load active and change state inscriptions
            main_lines = self._prepare_main_inscription_lines(project_id)
            defaults["change_distribution_table_import_line_wizard_ids"] = main_lines

            # Load inactive and cancelled inscriptions
            new_lines = self._prepare_new_inscription_lines(project_id)
            defaults[
                "change_distribution_table_import_line_wizard_news_ids"
            ] = new_lines

            return defaults

        except Exception as e:
            logger.error(f"Error setting default values: {e}")
            raise UserError(_("Error loading inscription data. Please try again."))

    def _get_project_id_from_context(self):
        """
        Get project ID from context

        Returns:
            int: Project ID

        Raises:
            UserError: If project ID not found in context
        """
        project_id = self.env.context.get("default_selfconsumption_project_id")
        if not project_id:
            raise UserError(_("No self-consumption project specified"))
        return project_id

    def _prepare_main_inscription_lines(self, project_id):
        """
        Prepare lines for active and change state inscriptions

        Args:
            project_id: ID of the self-consumption project

        Returns:
            list: List of line values for active and change inscriptions
        """
        lines = []

        # Add active inscriptions
        active_inscriptions = self._get_inscriptions_by_state(
            project_id, INSCRIPTION_STATE_ACTIVE
        )
        for inscription in active_inscriptions:
            lines.append(
                self._create_line_values(
                    inscription, inscription.participation_real_quantity
                )
            )

        # Add change state inscriptions
        change_inscriptions = self._get_inscriptions_by_state(
            project_id, INSCRIPTION_STATE_CHANGE
        )
        for inscription in change_inscriptions:
            lines.append(
                self._create_line_values(
                    inscription, inscription.participation_assigned_quantity
                )
            )

        return lines

    def _prepare_new_inscription_lines(self, project_id):
        """
        Prepare lines for inactive and cancelled inscriptions

        Args:
            project_id: ID of the self-consumption project

        Returns:
            list: List of line values for new inscriptions
        """
        lines = []
        states = [INSCRIPTION_STATE_INACTIVE, INSCRIPTION_STATE_CANCELLED]

        inscriptions = self._get_inscriptions_by_states(project_id, states)
        for inscription in inscriptions:
            lines.append(
                self._create_line_values(
                    inscription, inscription.participation_assigned_quantity
                )
            )

        return lines

    def _get_inscriptions_by_state(self, project_id, state):
        """
        Get inscriptions by project and state

        Args:
            project_id: Project ID
            state: Inscription state

        Returns:
            recordset: Inscription records
        """
        return self.env["energy_selfconsumption.inscription_selfconsumption"].search(
            [
                ("selfconsumption_project_id", "=", project_id),
                ("state", "=", state),
            ]
        )

    def _get_inscriptions_by_states(self, project_id, states):
        """
        Get inscriptions by project and multiple states

        Args:
            project_id: Project ID
            states: List of inscription states

        Returns:
            recordset: Inscription records
        """
        return self.env["energy_selfconsumption.inscription_selfconsumption"].search(
            [
                ("selfconsumption_project_id", "=", project_id),
                ("state", "in", states),
            ]
        )

    def _create_line_values(self, inscription, participation_quantity):
        """
        Create line values for an inscription

        Args:
            inscription: Inscription record
            participation_quantity: Participation quantity to use

        Returns:
            tuple: Line creation values
        """
        return (
            0,
            0,
            {
                "change_distribution_table_import_wizard_id": self.id,
                "inscription_id": inscription.id,
                "state": inscription.state,
                "participation_real_quantity": participation_quantity,
            },
        )

    @api.depends("state", "change_distribution_table_import_line_wizard_ids")
    def _compute_change_distribution_table_import_line_wizard_ids(self):
        """
        Compute visible lines based on wizard state

        Filters the lines to show based on the current step of the wizard,
        allowing users to review different categories of inscriptions.
        """
        for wizard in self:
            try:
                wizard.change_distribution_table_import_line_wizard_views_ids = (
                    wizard._get_filtered_lines()
                )
            except Exception as e:
                logger.error(f"Error computing wizard lines: {e}")
                wizard.change_distribution_table_import_line_wizard_views_ids = (
                    wizard.change_distribution_table_import_line_wizard_ids
                )

    def _get_filtered_lines(self):
        """
        Get filtered lines based on wizard state

        Returns:
            recordset: Filtered lines for current wizard state
        """
        all_lines = self.change_distribution_table_import_line_wizard_ids

        if self.state == WIZARD_STATE_OLD:
            return all_lines.filtered(
                lambda line: line.state == INSCRIPTION_STATE_ACTIVE
            )
        elif self.state == WIZARD_STATE_DELETE:
            return all_lines.filtered(
                lambda line: line.state == INSCRIPTION_STATE_CHANGE
                and line.participation_real_quantity == 0
            )
        elif self.state == WIZARD_STATE_CHANGE:
            return all_lines.filtered(
                lambda line: line.state == INSCRIPTION_STATE_CHANGE
                and line.participation_real_quantity > 0
            )
        elif self.state == WIZARD_STATE_NEW:
            return all_lines.filtered(
                lambda line: line.state
                in [INSCRIPTION_STATE_INACTIVE, INSCRIPTION_STATE_CANCELLED]
            )
        else:
            return all_lines

    # Navigation methods
    def next_step(self):
        """
        Navigate to the next step in the wizard

        Returns:
            dict: Action to display next step or create distribution table
        """
        try:
            if self.state == WIZARD_STATE_OLD:
                self.state = WIZARD_STATE_DELETE
                return self._get_wizard_action()
            elif self.state == WIZARD_STATE_DELETE:
                self.state = WIZARD_STATE_CHANGE
                return self._get_wizard_action()
            elif self.state == WIZARD_STATE_CHANGE:
                self.state = WIZARD_STATE_NEW
                return self._get_wizard_action()
            elif self.state == WIZARD_STATE_NEW:
                return self._create_distribution_table()
            else:
                return self._get_wizard_action()

        except Exception as e:
            logger.error(f"Error navigating to next step: {e}")
            raise UserError(_("Error navigating wizard. Please try again."))

    def previous_step(self):
        """
        Navigate to the previous step in the wizard

        Returns:
            dict: Action to display previous step
        """
        try:
            if self.state == WIZARD_STATE_NEW:
                self.state = WIZARD_STATE_CHANGE
            elif self.state == WIZARD_STATE_CHANGE:
                self.state = WIZARD_STATE_DELETE
            elif self.state == WIZARD_STATE_DELETE:
                self.state = WIZARD_STATE_OLD

            return self._get_wizard_action()

        except Exception as e:
            logger.error(f"Error navigating to previous step: {e}")
            raise UserError(_("Error navigating wizard. Please try again."))

    def _get_wizard_action(self):
        """
        Get action to redisplay the wizard

        Returns:
            dict: Wizard action configuration
        """
        action = self.env.ref(
            "energy_selfconsumption.button_action_change_distribution_table_import_wizard"
        ).read()[0]
        action.update({"res_id": self.id})
        return action

    def _create_distribution_table(self):
        """
        Create distribution table with selected inscriptions

        Returns:
            dict: Action to open distribution table creation wizard
        """
        try:
            # Get inscriptions that should be included (not deleted)
            valid_lines = (
                self.change_distribution_table_import_line_wizard_ids.filtered(
                    lambda line: not (
                        line.state == INSCRIPTION_STATE_CHANGE
                        and line.participation_real_quantity == 0
                    )
                )
            )

            if not valid_lines:
                raise UserError(
                    _("No valid inscriptions found for distribution table creation")
                )

            action = self.env.ref(
                "energy_selfconsumption.create_distribution_table_wizard_action"
            ).read()[0]

            action.update(
                {
                    "context": {
                        "active_ids": valid_lines.inscription_id.ids,
                        "active_model": "energy_selfconsumption.inscription_selfconsumption",
                    }
                }
            )

            return action

        except Exception as e:
            logger.error(f"Error creating distribution table: {e}")
            raise UserError(_("Error creating distribution table. Please try again."))

    # Utility methods
    def get_wizard_summary(self):
        """
        Get summary information about the wizard state

        Returns:
            dict: Summary information
        """
        self.ensure_one()

        total_lines = len(self.change_distribution_table_import_line_wizard_ids)
        visible_lines = len(self.change_distribution_table_import_line_wizard_views_ids)

        return {
            "current_step": self.state,
            "total_inscriptions": total_lines,
            "visible_inscriptions": visible_lines,
            "step_description": dict(WIZARD_STATE_VALUES).get(self.state, "Unknown"),
        }

    def validate_wizard_data(self):
        """
        Validate wizard data before proceeding

        Returns:
            bool: True if validation passes

        Raises:
            ValidationError: If validation fails
        """
        if not self.change_distribution_table_import_line_wizard_ids:
            raise ValidationError(_("No inscriptions found to process"))

        # Validate participation quantities
        for line in self.change_distribution_table_import_line_wizard_ids:
            if line.participation_real_quantity < 0:
                raise ValidationError(
                    _(
                        "Participation quantity cannot be negative for inscription {inscription}"
                    ).format(inscription=line.inscription_id.name)
                )

        return True


class ChangeDistributionTableImportLineWizard(models.TransientModel):
    """
    Change Distribution Table Import Line Wizard

    Individual line for managing inscription state changes and
    participation quantity modifications in the distribution table wizard.
    """

    _name = "change.distribution.table.import.line.wizard"
    _description = "Change Distribution Table Import Line Wizard"

    # Parent wizard relationship
    change_distribution_table_import_wizard_id = fields.Many2one(
        "change.distribution.table.import.wizard",
        string="Distribution Change Wizard",
        required=True,
        ondelete="cascade",
        help="Parent wizard for distribution table changes",
    )

    # Inscription information
    inscription_id = fields.Many2one(
        "energy_selfconsumption.inscription_selfconsumption",
        string="Inscription",
        required=True,
        help="Inscription record being modified",
    )

    state = fields.Selection(
        INSCRIPTION_STATE_VALUES,
        required=True,
        string="Inscription State",
        help="Current state of the inscription",
    )

    participation_real_quantity = fields.Float(
        string="Participation Quantity",
        required=True,
        help="Real participation quantity for this inscription",
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
            if record.participation_real_quantity < 0:
                raise ValidationError(
                    _(
                        "Participation quantity cannot be negative for inscription '{inscription}'"
                    ).format(inscription=record.inscription_id.name)
                )

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
            "current_state": self.state,
            "participation_quantity": self.participation_real_quantity,
            "state_display": dict(INSCRIPTION_STATE_VALUES).get(self.state, "Unknown"),
        }
