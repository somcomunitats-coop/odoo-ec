from odoo import _, fields, models

from .config import PACK_TYPE_SELFCONSUMPTION

# Pack type values for self-consumption
PACK_VALUES = [
    (PACK_TYPE_SELFCONSUMPTION, _("Selfconsumption Pack")),
]


class PackTypeMixin(models.AbstractModel):
    """
    Pack Type Mixin Extension for Self-consumption

    This abstract model extends the base pack type mixin to add
    self-consumption specific pack types, including:
    - Self-consumption pack type definition
    - Integration with existing pack type functionality
    - Support for self-consumption product categorization
    """

    _inherit = "pack.type.mixin"

    # Extended pack type selection
    pack_type = fields.Selection(
        selection_add=PACK_VALUES,
        help="Type of pack for contract and invoice processing",
    )

    # Business logic methods
    def is_selfconsumption_pack(self):
        """
        Check if this record has self-consumption pack type

        Returns:
            bool: True if self-consumption pack, False otherwise
        """
        self.ensure_one()
        return self.pack_type == PACK_TYPE_SELFCONSUMPTION

    def get_pack_type_display(self):
        """
        Get human-readable pack type for display

        Returns:
            str: Pack type display text
        """
        self.ensure_one()

        pack_type_dict = dict(self._fields["pack_type"].selection)
        return pack_type_dict.get(self.pack_type, self.pack_type or "Unknown")

    def get_selfconsumption_pack_info(self):
        """
        Get information about self-consumption pack configuration

        Returns:
            dict: Pack information for self-consumption
        """
        self.ensure_one()

        return {
            "is_selfconsumption": self.is_selfconsumption_pack(),
            "pack_type": self.pack_type,
            "pack_type_display": self.get_pack_type_display(),
            "supports_energy_billing": self.is_selfconsumption_pack(),
        }
