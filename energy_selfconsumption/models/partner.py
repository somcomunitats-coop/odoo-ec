from odoo import _, fields, models

from odoo.addons.energy_communities.config import STATE_ACTIVE

# Vulnerability situation constants
VULNERABILITY_YES = "yes"
VULNERABILITY_NO = "no"

VULNERABILITY_SITUATION_VALUES = [
    (VULNERABILITY_YES, _("Yes")),
    (VULNERABILITY_NO, _("No")),
]

# Partner type constants
PARTNER_TYPE_OWNER_SELFCONSUMPTION = "owner_self-consumption"


class ResPartner(models.Model):
    """
    Partner Model Extension for Self-consumption

    This model extends the base partner functionality to support
    self-consumption energy projects, including:
    - Supply point relationship management
    - Vulnerability situation tracking
    - Owner-specific partner types
    - Supply point counting and access
    - Integration with self-consumption workflows
    """

    _inherit = "res.partner"

    # Supply point relationships
    supply_ids = fields.One2many(
        "energy_selfconsumption.supply_point",
        "partner_id",
        readonly=True,
        help="Supply points where this partner is the cooperator",
    )
    owner_supply_ids = fields.One2many(
        "energy_selfconsumption.supply_point",
        "owner_id",
        readonly=True,
        help="Supply points where this partner is the legal owner",
    )
    supply_point_count = fields.Integer(
        compute="_compute_supply_point_count",
        help="Total number of supply points (as cooperator or owner)",
    )

    # Vulnerability and social fields
    vulnerability_situation = fields.Selection(
        VULNERABILITY_SITUATION_VALUES,
        string="Vulnerability situation",
        help="Indicates if the partner is in a vulnerable situation",
    )

    # Extended partner type selection
    type = fields.Selection(
        selection_add=[
            (PARTNER_TYPE_OWNER_SELFCONSUMPTION, "Owner self-consumption"),
        ],
        help="Type of partner relationship",
    )

    # Computed methods
    def _compute_supply_point_count(self):
        """
        Calculate total number of supply points for each partner

        Counts unique supply points where the partner is either
        the cooperator or the legal owner.
        """
        for record in self:
            # Get unique supply points (partner can be both cooperator and owner)
            all_supply_points = set(record.supply_ids.ids + record.owner_supply_ids.ids)
            record.supply_point_count = len(all_supply_points)

    # Business logic methods
    def get_partner_with_type(self):
        """
        Get partner with specific self-consumption owner type

        Returns the child partner with 'owner_self-consumption' type if exists,
        otherwise returns the current partner.

        Returns:
            res.partner: Partner record with appropriate type
        """
        self.ensure_one()

        # Look for child partner with owner self-consumption type
        child_with_type = self.child_ids.filtered(
            lambda p: p.type == PARTNER_TYPE_OWNER_SELFCONSUMPTION
        )

        if child_with_type:
            return child_with_type[0]
        else:
            return self

    def get_supply_points(self):
        """
        Open supply points view for this partner

        Shows all supply points where the partner is either
        the cooperator or the legal owner.

        Returns:
            dict: Action dictionary for opening supply points view
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Supply Points"),
            "view_mode": "tree,form",
            "res_model": "energy_selfconsumption.supply_point",
            "domain": ["|", ("partner_id", "=", self.id), ("owner_id", "=", self.id)],
            "context": {
                "create": True,
                "default_owner_id": self.id,
                "default_partner_id": self.id,
                "default_country_id": self.env.ref("base.es").id,
            },
        }

    def get_active_supply_points(self):
        """
        Get active supply points for this partner

        Returns:
            recordset: Active supply points where partner is cooperator or owner
        """
        self.ensure_one()
        return self.env["energy_selfconsumption.supply_point"].search(
            [
                "|",
                ("partner_id", "=", self.id),
                ("owner_id", "=", self.id),
                ("active", "=", True),
            ]
        )

    def get_selfconsumption_inscriptions(self):
        """
        Get all self-consumption inscriptions for this partner

        Returns:
            recordset: Self-consumption inscriptions for this partner
        """
        self.ensure_one()
        return self.env["energy_selfconsumption.inscription_selfconsumption"].search(
            [("partner_id", "=", self.id)]
        )

    def get_active_selfconsumption_projects(self):
        """
        Get active self-consumption projects where partner participates

        Returns:
            recordset: Active self-consumption projects
        """
        self.ensure_one()
        inscriptions = self.get_selfconsumption_inscriptions()
        active_inscriptions = inscriptions.filtered(lambda i: i.is_active())
        return active_inscriptions.mapped("selfconsumption_project_id")

    def is_vulnerable(self):
        """
        Check if partner is in vulnerable situation

        Returns:
            bool: True if vulnerable, False otherwise
        """
        self.ensure_one()
        return self.vulnerability_situation == VULNERABILITY_YES

    def is_selfconsumption_owner(self):
        """
        Check if partner is a self-consumption owner type

        Returns:
            bool: True if owner type, False otherwise
        """
        self.ensure_one()
        return self.type == PARTNER_TYPE_OWNER_SELFCONSUMPTION

    def get_total_participation_power(self):
        """
        Calculate total participation power across all projects

        Returns:
            float: Total participation power in kW
        """
        self.ensure_one()
        inscriptions = self.get_selfconsumption_inscriptions()
        active_inscriptions = inscriptions.filtered(lambda i: i.is_active())
        return sum(active_inscriptions.mapped("participation_real_quantity"))

    def get_supply_point_summary(self):
        """
        Get summary information about partner's supply points

        Returns:
            dict: Summary with counts and details
        """
        self.ensure_one()
        active_supply_points = self.get_active_supply_points()

        return {
            "total_count": self.supply_point_count,
            "active_count": len(active_supply_points),
            "as_cooperator": len(self.supply_ids.filtered("active")),
            "as_owner": len(self.owner_supply_ids.filtered("active")),
            "cups_codes": active_supply_points.mapped("code"),
        }

    def create_selfconsumption_owner_contact(self, owner_data):
        """
        Create a child contact with owner self-consumption type

        Args:
            owner_data (dict): Data for the new owner contact

        Returns:
            res.partner: Created owner contact
        """
        self.ensure_one()

        # Ensure required fields
        owner_data.update(
            {
                "parent_id": self.id,
                "type": PARTNER_TYPE_OWNER_SELFCONSUMPTION,
                "company_type": "person",
            }
        )

        return self.create(owner_data)

    def get_vulnerability_display(self):
        """
        Get human-readable vulnerability situation

        Returns:
            str: Vulnerability situation display text
        """
        self.ensure_one()
        if self.vulnerability_situation == VULNERABILITY_YES:
            return _("Vulnerable")
        elif self.vulnerability_situation == VULNERABILITY_NO:
            return _("Not Vulnerable")
        else:
            return _("Not Specified")

    def validate_for_selfconsumption(self):
        """
        Validate partner data for self-consumption participation

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        self.ensure_one()

        errors = []

        if not self.vat:
            errors.append(
                _("VAT number is required for self-consumption participation")
            )

        if not self.name:
            errors.append(_("Partner name is required"))

        if self.company_type == "person":
            if not hasattr(self, "firstname") or not self.firstname:
                errors.append(_("First name is required for individual partners"))

        if errors:
            from odoo.exceptions import ValidationError

            raise ValidationError("\n".join(errors))

        return True
