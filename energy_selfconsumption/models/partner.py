from odoo import fields, models, _

_GENDER_VALUES = [
    ("male", _("Male")),
    ("female", _("Female")),
]

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

    gender = fields.Selection(_GENDER_VALUES, string="Gender")

    vulnerability_situation = fields.Selection(_VULNERABILITY_SITUATION_VALUES,
                                               string="Vulnerability situation")

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
