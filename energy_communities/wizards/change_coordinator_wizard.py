from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class ChangeCoordinatorWizard(models.TransientModel):
    _name = "change.coordinator.wizard"
    _description = "Change the coordinator of an existing energy community"

    coordinator_destination = fields.Many2one(
        "res.company", string="Destination Coordinator"
    )
    change_reason = fields.Text("Change reason")

    def execute_change(self):
        if "active_ids" in self.env.context.keys():
            impacted_companies = self.env["res.company"].browse(
                self.env.context["active_ids"]
            )
            for company in impacted_companies:
                print("Company: {}".format(company.name))
