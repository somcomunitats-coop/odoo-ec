from odoo import _, fields, models

_VULNERABILITY_SITUATION_VALUES = [
    ("yes", _("Yes")),
    ("no", _("No")),
]


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _compute_supply_point_count(self):
        for record in self:
            record.supply_point_count = len(
                set(record.supply_ids + record.owner_supply_ids)
            )

    supply_ids = fields.One2many(
        "energy_selfconsumption.supply_point", "partner_id", readonly=True
    )
    owner_supply_ids = fields.One2many(
        "energy_selfconsumption.supply_point", "owner_id", readonly=True
    )
    supply_point_count = fields.Integer(compute=_compute_supply_point_count)

    vulnerability_situation = fields.Selection(
        _VULNERABILITY_SITUATION_VALUES, string="Vulnerability situation"
    )

    type = fields.Selection(
        selection_add=[
            ("owner_self-consumption", "Owner self-consumption"),
        ]
    )

    def get_partner_with_type(self):
        for partner in self:
            self.ensure_one()
            child_with_type = partner.child_ids.filtered(
                lambda p: p.type == "owner_self-consumption"
            )

            if child_with_type:
                return child_with_type[0]
            else:
                return partner

    def get_supply_points(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Supply Points",
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
