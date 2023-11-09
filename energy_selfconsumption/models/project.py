from odoo import fields, models


class EnergyProject(models.Model):
    _inherit = "energy_project.project"

    selfconsumption_id = fields.One2many(
        "energy_selfconsumption.selfconsumption", "project_id"
    )
    contract_ids = fields.One2many("contract.contract", "project_id", readonly=True)
