from odoo import _, fields, models

from ..config import (
    SELFCONSUMPTION_INVOICING_MODE_ENERGY_DELIVERED,
    SELFCONSUMPTION_INVOICING_MODE_LABELS,
    SELFCONSUMPTION_INVOICING_MODE_NONE,
    SELFCONSUMPTION_INVOICING_MODE_VALUES,
)

INVOICE_SELFCONSUMPTION_INVOICING_MODE_VALUES = [
    (
        SELFCONSUMPTION_INVOICING_MODE_NONE,
        SELFCONSUMPTION_INVOICING_MODE_LABELS[SELFCONSUMPTION_INVOICING_MODE_NONE],
    )
] + SELFCONSUMPTION_INVOICING_MODE_VALUES


class AccountMoveLine(models.Model):
    """
    Account Move Line Extension for Self-consumption

    This model extends account move lines to support self-consumption
    energy projects by adding relationships to self-consumption projects.
    """

    _inherit = "account.move.line"

    # Self-consumption relationship
    selfconsumption_id = fields.One2many(
        "energy_selfconsumption.selfconsumption",
        related="contract_line_id.contract_id.project_id.selfconsumption_id",
        help="Self-consumption project associated with this invoice line",
    )

    # Business logic methods
    def get_selfconsumption_project(self):
        """
        Get the self-consumption project for this invoice line

        Returns:
            selfconsumption: Self-consumption project or False
        """
        self.ensure_one()
        return self.selfconsumption_id[0] if self.selfconsumption_id else False

    def is_selfconsumption_line(self):
        """
        Check if this line is related to a self-consumption project

        Returns:
            bool: True if related to self-consumption, False otherwise
        """
        self.ensure_one()
        return bool(self.selfconsumption_id)


class AccountMove(models.Model):
    """
    Account Move Extension for Self-consumption

    This model extends account moves (invoices) to support self-consumption
    energy projects, including:
    - Invoicing mode detection and display
    - Self-consumption project integration
    - Pack type mixin functionality
    """

    _name = "account.move"
    _inherit = ["account.move"]

    # Self-consumption invoicing mode
    selfconsumption_invoicing_mode = fields.Selection(
        INVOICE_SELFCONSUMPTION_INVOICING_MODE_VALUES,
        compute="_compute_selfconsumption_invoicing_mode",
        store=False,
        help="Invoicing mode of the associated self-consumption project",
    )

    energy_delivered = fields.Float(
        string="Energy Delivered",
        help="Energy delivered for energy delivered mode",
    )

    # Computed methods
    def _compute_selfconsumption_invoicing_mode(self):
        """
        Compute the self-consumption invoicing mode for this invoice

        Determines the invoicing mode based on the first invoice line's
        associated self-consumption project.
        """
        for record in self:
            # Default to none
            record.selfconsumption_invoicing_mode = SELFCONSUMPTION_INVOICING_MODE_NONE

            # Check if invoice has lines
            if not record.invoice_line_ids:
                continue

            # Get first line with self-consumption project
            first_line = record.invoice_line_ids[0]

            if first_line.selfconsumption_id:
                selfconsumption = first_line.selfconsumption_id[0]
                record.selfconsumption_invoicing_mode = selfconsumption.invoicing_mode

    # Business logic methods
    def get_selfconsumption_projects(self):
        """
        Get all self-consumption projects associated with this invoice

        Returns:
            recordset: Self-consumption projects from all invoice lines
        """
        self.ensure_one()
        all_selfconsumptions = self.env["energy_selfconsumption.selfconsumption"]

        for line in self.invoice_line_ids:
            if line.selfconsumption_id:
                all_selfconsumptions |= line.selfconsumption_id

        return all_selfconsumptions

    def is_selfconsumption_invoice(self):
        """
        Check if this invoice is related to self-consumption projects

        Returns:
            bool: True if any line is related to self-consumption, False otherwise
        """
        self.ensure_one()
        return any(line.is_selfconsumption_line() for line in self.invoice_line_ids)

    def get_invoicing_mode_display(self):
        """
        Get human-readable invoicing mode for display

        Returns:
            str: Invoicing mode display text
        """
        self.ensure_one()
        return SELFCONSUMPTION_INVOICING_MODE_LABELS.get(
            self.selfconsumption_invoicing_mode, _("Unknown")
        )

    def get_selfconsumption_summary(self):
        """
        Get summary information about self-consumption aspects of this invoice

        Returns:
            dict: Summary with self-consumption details
        """
        self.ensure_one()

        selfconsumption_projects = self.get_selfconsumption_projects()
        selfconsumption_lines = self.invoice_line_ids.filtered("selfconsumption_id")

        return {
            "is_selfconsumption": self.is_selfconsumption_invoice(),
            "invoicing_mode": self.selfconsumption_invoicing_mode,
            "invoicing_mode_display": self.get_invoicing_mode_display(),
            "project_count": len(selfconsumption_projects),
            "selfconsumption_line_count": len(selfconsumption_lines),
            "project_names": selfconsumption_projects.mapped("name"),
        }

    def validate_selfconsumption_invoice(self):
        """
        Validate invoice for self-consumption requirements

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        self.ensure_one()

        if not self.is_selfconsumption_invoice():
            return True

        errors = []

        # Check if all self-consumption lines have consistent invoicing mode
        invoicing_modes = set()
        for line in self.invoice_line_ids.filtered("selfconsumption_id"):
            if line.selfconsumption_id:
                selfconsumption = line.selfconsumption_id[0]
                invoicing_modes.add(selfconsumption.invoicing_mode)

        if len(invoicing_modes) > 1:
            errors.append("Invoice contains lines with different invoicing modes")

        # Check if invoice has required information for energy delivered mode
        if (
            self.selfconsumption_invoicing_mode
            == SELFCONSUMPTION_INVOICING_MODE_ENERGY_DELIVERED
        ):
            if not any(line.quantity > 0 for line in self.invoice_line_ids):
                errors.append("Energy delivered invoices must have positive quantities")

        if errors:
            from odoo.exceptions import ValidationError

            raise ValidationError("\n".join(errors))

        return True
