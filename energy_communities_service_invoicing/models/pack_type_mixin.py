from odoo import api, fields, models

from odoo.addons.energy_communities.config import (
    PACK_TYPE_DEFAULT_VALUE,
    PACK_TYPE_LABELS,
    PACK_TYPE_NONE,
    PACK_TYPE_SHARE_RECURRING_FEE,
    PACK_TYPE_VALUES,
)


class PackTypeMixin(models.AbstractModel):
    _name = "pack.type.mixin"
    _description = "Add pack_type to any model"

    pack_type = fields.Selection(
        PACK_TYPE_VALUES,
        compute="_compute_pack_type",
        compute_sudo=True,
        string="Pack Type",
        store=True,
        default=PACK_TYPE_DEFAULT_VALUE,
    )

    is_pack = fields.Boolean("Is a pack", compute="_compute_is_pack", store=True)
    is_share_recurring_fee_pack = fields.Boolean(
        "Is a share with recurring fee pack",
        compute="_compute_is_share_recurring_fee_pack",
        store=False,
    )

    def _compute_pack_type(self):
        raise NotImplementedError(
            "This method must be implemented when you inherit pack.type.mixin"
        )

    @api.depends("pack_type")
    def _compute_is_pack(self):
        for record in self:
            record.is_pack = record.pack_type != PACK_TYPE_NONE

    @api.depends("pack_type")
    def _compute_is_share_recurring_fee_pack(self):
        for record in self:
            record.is_share_recurring_fee_pack = (
                record.pack_type == PACK_TYPE_SHARE_RECURRING_FEE
            )
