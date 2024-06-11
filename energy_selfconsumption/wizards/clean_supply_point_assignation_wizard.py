from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CleanSupplyPointAssignationWizard(models.TransientModel):
    _name = "clean.supply.point.assignation.wizard"
    _description = "Clean supply point assgination wizard"

    message = fields.Text(string="Message", readonly=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res["message"] = _(
            "Are you sure you want to delete all assigned distribution points?"
        )
        return res

    def action_confirm(self):
        active_ids = self.env.context.get("active_ids")
        for active_id in active_ids:
            distribution_table = self.env[
                "energy_selfconsumption.distribution_table"
            ].browse(active_id)
            if distribution_table.state != "draft":
                raise ValidationError(
                    _(
                        "You can only delete assigned distribution points from a distribution table if it is in draft status"
                    )
                )
            distribution_table.supply_point_assignation_ids.unlink()
        return {"type": "ir.actions.act_window_close"}

    def action_cancel(self):
        return {"type": "ir.actions.act_window_close"}
