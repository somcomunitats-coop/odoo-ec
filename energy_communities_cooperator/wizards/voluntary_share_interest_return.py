from odoo import api, fields, models
from odoo.tools.translate import _


class VoluntaryShareInterestReturn(models.TransientModel):
    _name = "voluntary.share.interest.return.wizard"
    _description = "Calculate and prepare interests to be returned in voluntary shares"

    interest = fields.Float(string="Interest")

    def execute_return(self):
        if "active_ids" in self.env.context.keys():
            impacted_companies = self.env["res.company"].browse(
                self.env.context["active_ids"]
            )
            for company in impacted_companies:
                print("APPLY ON COMPANY")
                print(company.name)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": "success",
                    "title": _("Interest generation successful"),
                    "message": _(
                        "We have calculated and generated the moves to pay voluntary share interest for this company."
                    ),
                    "sticky": False,
                    "next": {"type": "ir.actions.act_window_close"},
                },
            }
