import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..models.config import DISTRIBUTION_STATE_DRAFT

# Constants for clean supply point assignation wizard
ACTION_WINDOW_CLOSE = "ir.actions.act_window_close"
CONFIRMATION_MESSAGE = (
    "Are you sure you want to delete all assigned distribution points?"
)

logger = logging.getLogger(__name__)


class CleanSupplyPointAssignationWizard(models.TransientModel):
    """
    Clean Supply Point Assignation Wizard

    This wizard handles the deletion of all supply point assignations
    from selected distribution tables, with proper validation and confirmation.

    Features:
    - Confirmation dialog for destructive operation
    - Validation of distribution table states
    - Bulk deletion of supply point assignations
    - Comprehensive error handling and logging
    - User-friendly feedback
    """

    _name = "clean.supply.point.assignation.wizard"
    _description = "Clean Supply Point Assignation Wizard"

    # Confirmation message
    message = fields.Text(
        string="Confirmation Message",
        readonly=True,
        help="Confirmation message for the deletion operation",
    )

    # Summary information
    distribution_tables_count = fields.Integer(
        string="Distribution Tables",
        compute="_compute_distribution_tables_count",
        help="Number of distribution tables selected for cleaning",
    )

    assignations_count = fields.Integer(
        string="Total Assignations",
        compute="_compute_assignations_count",
        help="Total number of assignations that will be deleted",
    )

    @api.model
    def default_get(self, fields_list):
        """
        Set default values for wizard fields

        Args:
            fields_list: List of field names to get defaults for

        Returns:
            dict: Default values including confirmation message
        """
        defaults = super().default_get(fields_list)

        try:
            defaults["message"] = _(CONFIRMATION_MESSAGE)
            return defaults
        except Exception as e:
            logger.error(f"Error setting default values: {e}")
            defaults["message"] = _("Confirm deletion of supply point assignations")
            return defaults

    @api.depends()
    def _compute_distribution_tables_count(self):
        """
        Compute the number of selected distribution tables
        """
        for wizard in self:
            active_ids = wizard._get_active_ids()
            wizard.distribution_tables_count = len(active_ids)

    @api.depends()
    def _compute_assignations_count(self):
        """
        Compute the total number of assignations to be deleted
        """
        for wizard in self:
            try:
                distribution_tables = wizard._get_distribution_tables()
                total_assignations = sum(
                    len(table.supply_point_assignation_ids)
                    for table in distribution_tables
                )
                wizard.assignations_count = total_assignations
            except Exception as e:
                logger.error(f"Error computing assignations count: {e}")
                wizard.assignations_count = 0

    def _get_active_ids(self):
        """
        Get active IDs from context

        Returns:
            list: List of distribution table IDs

        Raises:
            ValidationError: If no distribution tables are selected
        """
        active_ids = self.env.context.get("active_ids", [])
        if not active_ids:
            raise ValidationError(_("No distribution tables selected for cleaning"))
        return active_ids

    def _get_distribution_tables(self):
        """
        Get distribution table records from context

        Returns:
            recordset: Distribution table records
        """
        active_ids = self._get_active_ids()
        return self.env["energy_selfconsumption.distribution_table"].browse(active_ids)

    def action_confirm(self):
        """
        Confirm and execute the cleaning operation

        Validates all selected distribution tables and deletes their
        supply point assignations if they are in draft state.

        Returns:
            dict: Action to close the wizard window

        Raises:
            ValidationError: If validation fails
            UserError: If errors occur during deletion
        """
        try:
            # Validate operation
            self._validate_cleaning_operation()

            # Get distribution tables
            distribution_tables = self._get_distribution_tables()

            # Execute cleaning
            deleted_count = self._execute_cleaning(distribution_tables)

            logger.info(
                f"Successfully deleted {deleted_count} supply point assignations"
            )

            return self._get_close_action()

        except Exception as e:
            logger.error(f"Error during cleaning operation: {e}")
            if isinstance(e, (ValidationError, UserError)):
                raise
            else:
                raise UserError(_("Error during cleaning operation. Please try again."))

    def _validate_cleaning_operation(self):
        """
        Validate the cleaning operation before execution

        Raises:
            ValidationError: If validation fails
        """
        distribution_tables = self._get_distribution_tables()

        if not distribution_tables:
            raise ValidationError(_("No valid distribution tables found"))

        # Check that all tables are in draft state
        non_draft_tables = distribution_tables.filtered(
            lambda table: table.state != DISTRIBUTION_STATE_DRAFT
        )

        if non_draft_tables:
            table_names = ", ".join(non_draft_tables.mapped("name"))
            raise ValidationError(
                _(
                    "You can only delete assigned distribution points from distribution tables "
                    "that are in draft status. The following tables are not in draft: {tables}"
                ).format(tables=table_names)
            )

    def _execute_cleaning(self, distribution_tables):
        """
        Execute the cleaning operation on distribution tables

        Args:
            distribution_tables: Distribution tables to clean

        Returns:
            int: Number of assignations deleted
        """
        total_deleted = 0

        for distribution_table in distribution_tables:
            try:
                assignations_count = len(
                    distribution_table.supply_point_assignation_ids
                )

                if assignations_count > 0:
                    distribution_table.supply_point_assignation_ids.unlink()
                    total_deleted += assignations_count

                    logger.info(
                        f"Deleted {assignations_count} assignations from distribution table {distribution_table.id}"
                    )

            except Exception as e:
                logger.error(
                    f"Error cleaning distribution table {distribution_table.id}: {e}"
                )
                raise UserError(
                    _(
                        "Error cleaning distribution table '{table}'. Please check the configuration."
                    ).format(table=distribution_table.name)
                )

        return total_deleted

    def action_cancel(self):
        """
        Cancel the cleaning operation

        Returns:
            dict: Action to close the wizard window
        """
        logger.info("Supply point assignation cleaning cancelled by user")
        return self._get_close_action()

    def _get_close_action(self):
        """
        Get action to close the wizard window

        Returns:
            dict: Window close action
        """
        return {"type": ACTION_WINDOW_CLOSE}

    # Utility methods
    def get_wizard_summary(self):
        """
        Get summary information about the wizard

        Returns:
            dict: Summary information
        """
        self.ensure_one()

        try:
            distribution_tables = self._get_distribution_tables()

            return {
                "distribution_tables_count": len(distribution_tables),
                "assignations_count": sum(
                    len(table.supply_point_assignation_ids)
                    for table in distribution_tables
                ),
                "draft_tables_count": len(
                    distribution_tables.filtered(
                        lambda t: t.state == DISTRIBUTION_STATE_DRAFT
                    )
                ),
                "table_names": distribution_tables.mapped("name"),
            }
        except Exception as e:
            logger.error(f"Error getting wizard summary: {e}")
            return {
                "distribution_tables_count": 0,
                "assignations_count": 0,
                "draft_tables_count": 0,
                "table_names": [],
            }

    def validate_wizard_data(self):
        """
        Validate wizard data before proceeding

        Returns:
            bool: True if validation passes

        Raises:
            ValidationError: If validation fails
        """
        try:
            self._validate_cleaning_operation()
            return True
        except ValidationError:
            raise

    def preview_cleaning_operation(self):
        """
        Preview the cleaning operation without executing it

        Returns:
            dict: Preview information
        """
        self.ensure_one()

        try:
            distribution_tables = self._get_distribution_tables()

            preview_data = {
                "tables_to_clean": [
                    {
                        "name": table.name,
                        "state": table.state,
                        "assignations_count": len(table.supply_point_assignation_ids),
                        "can_clean": table.state == DISTRIBUTION_STATE_DRAFT,
                    }
                    for table in distribution_tables
                ],
                "total_assignations_to_delete": sum(
                    len(table.supply_point_assignation_ids)
                    for table in distribution_tables
                    if table.state == DISTRIBUTION_STATE_DRAFT
                ),
                "valid_tables_count": len(
                    distribution_tables.filtered(
                        lambda t: t.state == DISTRIBUTION_STATE_DRAFT
                    )
                ),
            }

            return preview_data

        except Exception as e:
            logger.error(f"Error previewing cleaning operation: {e}")
            return {
                "tables_to_clean": [],
                "total_assignations_to_delete": 0,
                "valid_tables_count": 0,
            }
