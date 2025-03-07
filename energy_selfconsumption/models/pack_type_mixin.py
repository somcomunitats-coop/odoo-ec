from odoo import _, fields, models

PACK_VALUES = [
    ("selfconsumption_pack", _("Selfconsumption Pack")),
]


class PackTypeMixin(models.AbstractModel):
    _inherit = "pack.type.mixin"

    pack_type = fields.Selection(selection_add=PACK_VALUES)
