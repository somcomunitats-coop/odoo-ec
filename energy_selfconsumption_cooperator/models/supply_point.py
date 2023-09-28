from odoo import api, fields, models


class SupplyPoint(models.Model):
    _inherit = "energy_selfconsumption.supply_point"

    partner_id = fields.Many2one(
        string="Cooperator",
        help="Cooperator subscribed to the self-consumption project",
    )

    @api.onchange("partner_id")
    def _onchange_cooperator_id(self):
        self.owner_id = self.partner_id
