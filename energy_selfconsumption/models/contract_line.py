from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ContractLine(models.Model):
    """
    Contract Line Model Extension for Self-consumption

    This model extends the base contract line functionality to support
    self-consumption projects, including:
    - Main line designation and validation
    - Enhanced recurring date validation
    - Self-consumption specific constraints
    - Improved error handling and messages
    """

    _inherit = "contract.line"

    # Self-consumption specific fields
    main_line = fields.Boolean(
        "Main line",
        default=False,
        help="Indicates if this is the main line of the contract (only one allowed per contract)",
    )

    # Validation constraints
    @api.constrains("main_line")
    def _check_only_one_main_line(self):
        """
        Ensure only one main line exists per contract

        Validates that each contract has at most one line marked as main line.
        This is important for self-consumption contracts where the main line
        represents the primary service.

        Raises:
            ValidationError: If multiple main lines exist in the same contract
        """
        for line in self:
            if not line.main_line:
                continue

            # Get all contract lines for this contract
            contract_lines = line.contract_id.contract_line_ids
            # Filter main lines excluding current line
            main_lines = contract_lines.filtered(
                lambda l: l.main_line and l.id != line.id
            )

            if main_lines:
                raise ValidationError(
                    _(
                        "Contract '{contract}' can only have one main line. "
                        "Please uncheck the main line flag on other lines first."
                    ).format(
                        contract=line.contract_id.name or line.contract_id.display_name
                    )
                )

    @api.constrains("recurring_next_date", "date_start")
    def _check_recurring_next_date_start_date(self):
        """
        Validate recurring next date is not before start date

        This validation ensures that the next invoice date is not set to a date
        that is before the contract line start date. This is particularly important
        for line-level recurrence in self-consumption contracts.

        Note: This validation is only applied when line_recurrence is enabled
        to fix an issue where the validation was raised during contract creation
        before recurring_next_date was computed.

        Raises:
            ValidationError: If next invoice date is before start date
        """
        for line in self:
            # Skip validation for section lines or lines without recurring date
            if line.display_type == "line_section" or not line.recurring_next_date:
                continue

            # Only validate when line recurrence is enabled and dates are set
            if (
                line.contract_id.line_recurrence
                and line.date_start
                and line.recurring_next_date
            ):
                if line.date_start > line.recurring_next_date:
                    raise ValidationError(
                        _(
                            "The next invoice date ({next_date}) cannot be before "
                            "the start date ({start_date}) of contract line '{line_name}'"
                        ).format(
                            next_date=line.recurring_next_date.strftime("%Y-%m-%d"),
                            start_date=line.date_start.strftime("%Y-%m-%d"),
                            line_name=line.name or _("Unnamed Line"),
                        )
                    )

    # Business logic methods
    def is_main_line(self):
        """
        Check if this line is marked as main line

        Returns:
            bool: True if this is the main line, False otherwise
        """
        self.ensure_one()
        return self.main_line

    def get_contract_main_line(self):
        """
        Get the main line of the contract this line belongs to

        Returns:
            contract.line: Main line record or empty recordset
        """
        self.ensure_one()
        return self.contract_id.contract_line_ids.filtered("main_line")

    def set_as_main_line(self):
        """
        Set this line as the main line of the contract

        This method will unset any existing main line and set this line
        as the new main line.
        """
        self.ensure_one()

        # Unset existing main lines
        existing_main_lines = self.contract_id.contract_line_ids.filtered("main_line")
        if existing_main_lines:
            existing_main_lines.write({"main_line": False})

        # Set this line as main
        self.write({"main_line": True})

    def unset_main_line(self):
        """
        Remove main line designation from this line
        """
        self.ensure_one()
        if self.main_line:
            self.write({"main_line": False})

    def get_line_type_display(self):
        """
        Get human-readable line type for display

        Returns:
            str: Line type description
        """
        self.ensure_one()

        if self.display_type == "line_section":
            return _("Section")
        elif self.display_type == "line_note":
            return _("Note")
        elif self.main_line:
            return _("Main Service Line")
        else:
            return _("Service Line")

    def validate_for_selfconsumption(self):
        """
        Validate contract line for self-consumption requirements

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        self.ensure_one()

        errors = []

        # Check if product is set for service lines
        if not self.display_type and not self.product_id:
            errors.append(_("Service lines must have a product assigned"))

        # Check if main line has required fields
        if self.main_line:
            if not self.name:
                errors.append(_("Main line must have a description"))

            if not self.price_unit and not self.display_type:
                errors.append(_("Main line must have a unit price"))

        # Check recurring configuration
        if self.contract_id.line_recurrence and not self.display_type:
            if not self.recurring_rule_type:
                errors.append(_("Recurring rule type is required for service lines"))

        if errors:
            raise ValidationError("\n".join(errors))

        return True

    def get_line_summary(self):
        """
        Get summary information about the contract line

        Returns:
            dict: Line summary information
        """
        self.ensure_one()

        return {
            "name": self.name or _("Unnamed Line"),
            "product": self.product_id.name if self.product_id else _("No Product"),
            "type": self.get_line_type_display(),
            "is_main": self.main_line,
            "price_unit": self.price_unit,
            "quantity": self.quantity,
            "total": self.price_unit * self.quantity,
            "recurring": bool(self.recurring_rule_type),
            "active": not bool(self.date_end),
        }

    # Onchange methods
    @api.onchange("main_line")
    def _onchange_main_line(self):
        """
        Handle main line flag changes

        When setting a line as main, warn if other main lines exist.
        """
        if self.main_line and self.contract_id:
            existing_main_lines = self.contract_id.contract_line_ids.filtered(
                lambda l: l.main_line and l.id != self.id
            )

            if existing_main_lines:
                return {
                    "warning": {
                        "title": _("Multiple Main Lines"),
                        "message": _(
                            "This contract already has a main line. "
                            "Setting this line as main will unset the existing main line."
                        ),
                    }
                }
