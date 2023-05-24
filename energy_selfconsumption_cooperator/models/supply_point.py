from odoo import fields, models, api


class SupplyPoint(models.Model):
    _inherit = "energy_selfconsumption.supply_point"

    cooperator_id = fields.Many2one(
        "res.partner",
        string="Cooperator",
        required=True,
        domain=[("member", "=", True)],
    )

    @api.onchange('cooperator_id')
    def _onchange_cooperator_id(self):
        self.owner_id = self.cooperator_id
