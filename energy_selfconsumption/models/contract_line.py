from odoo import api, fields, models


class ContractLine(models.Model):
    _inherit = "contract.line"

    supply_point_assignation_id = fields.Many2one(
        "energy_selfconsumption.supply_point_assignation",
        string="Selfconsumption project",
    )
