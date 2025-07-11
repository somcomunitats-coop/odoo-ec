from stdnum.es import cups, referenciacatastral
from stdnum.eu import vat
from stdnum.exceptions import *

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.energy_communities.config import STATE_ACTIVE, STATE_INACTIVE

from ..config import TARIFF_2_0TD, TARIFF_3_0TD, TARIFF_6_1TD
from ..utils.validation_utils import (
    validate_cadastral_reference,
    validate_cups_code,
)

# Constants for tariff validation
TARIFF_2_0TD_MAX_POWER = 15  # kW
TARIFF_3_0TD_MIN_POWER = 15  # kW

# Access tariff values
ACCESS_TARIFF_VALUES = [
    (TARIFF_2_0TD, TARIFF_2_0TD),
    (TARIFF_3_0TD, TARIFF_3_0TD),
    (TARIFF_6_1TD, TARIFF_6_1TD),
    ("6.2TD", "6.2TD"),
    ("6.3TD", "6.3TD"),
    ("6.4TD", "6.4TD"),
]

# Used in self-consumption values
USED_IN_SELFCONSUMPTION_VALUES = [
    ("yes", _("Yes")),
    ("no", _("No")),
]


class SupplyPoint(models.Model):
    """
    Energy Supply Point Model

    This model represents energy supply points (CUPS) associated with
    self-consumption projects, including:
    - Supply point identification and validation
    - Owner and cooperator management
    - Address and location information
    - Tariff and power configuration
    - Self-consumption usage tracking
    """

    _name = "energy_selfconsumption.supply_point"
    _description = "Energy Supply Point"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    _sql_constraints = [
        (
            "unique_code_company_id",
            "unique(code, company_id)",
            _("A supply point with this code already exists."),
        )
    ]

    # Basic identification fields
    name = fields.Char(
        compute="_compute_supply_point_name",
        store=True,
        help="Computed name based on partner and address",
    )
    code = fields.Char(
        string="CUPS",
        help="Universal Supply Point Code (CUPS) - unique identifier for the supply point",
    )

    # Partner relationships
    owner_id = fields.Many2one(
        "res.partner",
        string="Owner",
        required=True,
        help="Partner with the legal obligation of the supply point",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Cooperator",
        required=True,
        help="Cooperator subscribed to the self-consumption project",
    )

    # Company and external relationships
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        readonly=True,
        help="Company that owns this supply point record",
    )
    reseller_id = fields.Many2one(
        "energy_project.reseller",
        string="Reseller",
        domain=[("state", "!=", "Baja")],
        help="Energy reseller associated with this supply point",
    )
    supplier_id = fields.Many2one(
        "energy_project.supplier",
        string="Supplier",
        help="Energy supplier for this supply point",
    )

    # Address fields
    street = fields.Char(required=True, help="Primary address line")
    street2 = fields.Char(help="Secondary address line")
    zip = fields.Char(change_default=True, required=True, help="Postal code")
    city = fields.Char(required=True, help="City name")
    state_id = fields.Many2one(
        "res.country.state",
        string="State",
        ondelete="restrict",
        domain="[('country_id', '=?', country_id)]",
        required=True,
        help="State or province",
    )
    country_id = fields.Many2one(
        "res.country",
        string="Country",
        ondelete="restrict",
        required=True,
        help="Country where the supply point is located",
    )

    # Technical and administrative fields
    cadastral_reference = fields.Char(
        string="Cadastral reference",
        help="Official cadastral reference for the property",
    )
    contracted_power = fields.Float(
        string="Maximum contracted power",
        digits=(10, 6),
        help="Maximum contracted power in kW",
    )
    tariff = fields.Selection(
        ACCESS_TARIFF_VALUES,
        string="Access tariff",
        help="Electricity access tariff applied to this supply point",
    )
    used_in_selfconsumption = fields.Selection(
        USED_IN_SELFCONSUMPTION_VALUES,
        string="Used in selfconsumption",
        help="Indicates if this supply point is used in self-consumption",
    )

    # Relationships and status
    supply_point_assignation_ids = fields.One2many(
        "energy_selfconsumption.supply_point_assignation",
        "supply_point_id",
        readonly=True,
        help="Distribution table assignments for this supply point",
    )
    active = fields.Boolean(
        default=True,
        help="If unchecked, this supply point will be hidden from most views",
    )

    # Computed fields and onchange methods
    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """Set owner to partner by default when partner changes"""
        self.owner_id = self.partner_id

    @api.depends("partner_id", "street")
    def _compute_supply_point_name(self):
        """Compute supply point name based on address"""
        for record in self:
            if record.partner_id and record.street:
                record.name = f"{record.street}"
            else:
                record.name = _("New Supply Point")

    # Validation methods
    @api.constrains("code")
    def _check_valid_code(self):
        """
        Validate CUPS code format using centralized validation

        Raises:
            ValidationError: If CUPS format is invalid
        """
        for record in self:
            if record.code:
                try:
                    # Use centralized validation utility
                    validate_cups_code(record.code, "CUPS", len(record.code))
                except ValidationError:
                    # Re-raise with supply point specific context
                    raise ValidationError(
                        _("Invalid CUPS code for supply point: {code}").format(
                            code=record.code
                        )
                    )

    @api.constrains("cadastral_reference")
    def _check_valid_cadastral_reference(self):
        """
        Validate Spanish cadastral reference format

        Raises:
            ValidationError: If cadastral reference is invalid
        """
        for record in self:
            if record.cadastral_reference:
                try:
                    validate_cadastral_reference(record.cadastral_reference)
                except ValidationError as e:
                    # Re-raise with supply point specific context
                    raise ValidationError(
                        _(
                            "Invalid cadastral reference for supply point: {error}"
                        ).format(error=str(e))
                    )

    @api.constrains("owner_id")
    def _check_valid_vat(self):
        """
        Validate owner VAT number format

        Raises:
            ValidationError: If VAT format is invalid
        """
        for record in self:
            if not record.owner_id.vat:
                continue

            original_vat = record.owner_id.vat

            # Ensure VAT starts with country code
            if not original_vat.startswith("ES"):
                original_vat = "ES" + original_vat

            try:
                vat.validate(original_vat)
            except Exception as e:
                raise ValidationError(
                    _("Invalid VAT for supply point owner: {error}").format(
                        error=str(e)
                    )
                )

    @api.constrains("tariff", "contracted_power")
    def _check_contracted_power(self):
        """
        Validate contracted power based on tariff type

        Raises:
            ValidationError: If power doesn't match tariff requirements
        """
        for record in self:
            if not record.tariff or not record.contracted_power:
                continue

            if record.tariff == TARIFF_2_0TD:
                if not (0 <= record.contracted_power <= TARIFF_2_0TD_MAX_POWER):
                    raise ValidationError(
                        _(
                            "For the {tariff} rate, the maximum contracted power must be between 0 and {max_power} kW."
                        ).format(tariff=TARIFF_2_0TD, max_power=TARIFF_2_0TD_MAX_POWER)
                    )
            elif record.tariff == TARIFF_3_0TD:
                if record.contracted_power <= TARIFF_3_0TD_MIN_POWER:
                    raise ValidationError(
                        _(
                            "For the {tariff} rate, the maximum contracted power must be greater than {min_power} kW."
                        ).format(tariff=TARIFF_3_0TD, min_power=TARIFF_3_0TD_MIN_POWER)
                    )

    # Business logic methods
    def get_display_address(self):
        """
        Get formatted display address for the supply point

        Returns:
            str: Formatted address string
        """
        self.ensure_one()
        address_parts = [self.street]

        if self.street2:
            address_parts.append(self.street2)

        address_parts.extend(
            [
                self.zip,
                self.city,
                self.state_id.name if self.state_id else "",
                self.country_id.name if self.country_id else "",
            ]
        )

        return ", ".join(filter(None, address_parts))

    def is_available_for_assignment(self):
        """
        Check if supply point is available for distribution table assignment

        Returns:
            bool: True if available, False otherwise
        """
        self.ensure_one()

        # Check if already assigned to an active distribution table
        active_assignments = self.supply_point_assignation_ids.filtered(
            lambda a: a.distribution_table_id.state == STATE_ACTIVE
        )

        return not active_assignments

    def get_current_assignment(self):
        """
        Get current active distribution table assignment

        Returns:
            supply_point_assignation: Current assignment or False
        """
        self.ensure_one()

        return self.supply_point_assignation_ids.filtered(
            lambda a: a.distribution_table_id.state == STATE_ACTIVE
        )

    def toggle_active(self):
        """Toggle active state of the supply point"""
        for record in self:
            record.active = not record.active
