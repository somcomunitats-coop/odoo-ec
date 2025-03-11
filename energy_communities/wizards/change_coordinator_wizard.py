from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

from ..utils import get_successful_popup_message


class ChangeCoordinatorWizard(models.TransientModel):
    _name = "change.coordinator.wizard"
    _description = "Change the coordinator of an existing energy community"

    incoming_coordinator = fields.Many2one("res.company", string="Incoming Coordinator")
    change_reason = fields.Text("Change reason")

    def execute_change(self):
        if "active_ids" in self.env.context.keys():
            impacted_companies = self.env["res.company"].browse(
                self.env.context["active_ids"]
            )
            for company in impacted_companies:
                company.with_delay().change_coordinator(
                    self.incoming_coordinator, self.change_reason
                )
            return get_successful_popup_message(
                _("Coordinator change successful"),
                _("This community has been moved to a new coordinator"),
            )
