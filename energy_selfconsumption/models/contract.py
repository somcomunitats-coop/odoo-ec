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
    code = fields.Char(related="supply_point_assignation_id.supply_point_id.code")
    supply_point_name = fields.Char(
        related="supply_point_assignation_id.supply_point_id.name"
    )


class ContractRecurrencyMixin(models.AbstractModel):
    _inherit = "contract.recurrency.mixin"

    next_period_date_start = fields.Date(store=True)
    next_period_date_end = fields.Date(store=True)
