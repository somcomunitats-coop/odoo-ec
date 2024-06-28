from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class VoluntaryShareInterestReturn(models.Model):
    _name = "voluntary.share.interest.return"
    _inherit = ["mail.thread"]

    name = fields.Char(string="Name")
    start_date_period = fields.Date(string="Period start date")
    end_date_period = fields.Date(string="Period end date")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    account_move_ids = fields.One2many(
        "account.move", "voluntary_share_interest_return_id", string="Moves"
    )
    partners_notified = fields.Boolean(string="Partners notified")
    state = fields.Selection(
        [("draft", "Draft"), ("posted", "Posted")], default="draft"
    )

    def action_post_and_send(self):
        for move in self.account_move_ids:
            if self.state != "posted":
                move.action_post()
            if not self.partners_notified:
                self.company_id.get_voluntary_share_return_email_template().send_mail(
                    force_send=False, res_id=move.id
                )
        self._update_status_indicators()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "title": _("Invoices posted and sent"),
                "message": _(
                    "We have calculated and generated the moves to pay voluntary share interest for this company."
                ),
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def _update_status_indicators(self):
        write_dict = {}
        if self.state != "posted":
            write_dict["state"] = "posted"
        if not self.partners_notified:
            write_dict["partners_notified"] = True
        if bool(write_dict):
            self.write(write_dict)
