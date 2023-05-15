from odoo import fields, models


class SupplyPoint(models.Model):
    _inherit = "energy_selfconsumption.supply_point"

    cooperator_id = fields.Many2one(
        "res.partner",
        string="Cooperator",
        required=True,
        domain=[("member", "=", True)],
    )
