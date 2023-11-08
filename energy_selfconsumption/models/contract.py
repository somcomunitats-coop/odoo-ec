from odoo import fields, models


class Contract(models.Model):
    _inherit = "contract.contract"

    supply_point_assignation_id = fields.Many2one(
        "energy_selfconsumption.supply_point_assignation",
        string="Selfconsumption project",
    )
    project_id = fields.Many2one(
        "energy_project.project",
        ondelete="restrict",
        string="Energy Project",
        related="supply_point_assignation_id.distribution_table_id.selfconsumption_project_id.project_id",
    )
